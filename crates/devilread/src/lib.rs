//! Streaming read adapters for hostile tabular data.
//!
//! `devilread` holds the byte-level machinery that Devil's Datasets uses for
//! hostile-but-realistic ingestion cases: transcoding non-UTF-8 input, reading
//! members from archives, and adapting multi-byte delimiters for CSV engines
//! that only accept a single-byte delimiter.

use std::collections::VecDeque;
use std::io::{self, Read};

use clap::ValueEnum;
use encoding_rs::{Decoder, UTF_16LE, UTF_8, WINDOWS_1252};

/// Replacement byte fed to downstream single-byte-delimiter CSV parsers.
///
/// ASCII Unit Separator is deliberately obscure in ordinary tabular exports. A
/// future version should let callers override this and/or diagnose if it appears
/// literally in the input stream.
pub const STAND_IN: u8 = 0x1f;

/// Input encoding handled by [`TranscodingReader`].
#[derive(Clone, Copy, Debug, Eq, PartialEq, ValueEnum)]
pub enum InputEncoding {
    Utf8,
    #[value(name = "utf16le", alias = "utf16-le")]
    Utf16Le,
    #[value(name = "windows1252", alias = "windows-1252")]
    Windows1252,
}

/// Streaming transcoder from a known input encoding to UTF-8 bytes.
///
/// The decoder keeps its own partial-code-unit state, so callers can stack this
/// over slow files, ZIP members, sockets, or tiny test chunkers without needing
/// to align reads on character boundaries.
pub struct TranscodingReader<R: Read> {
    inner: R,
    decoder: Decoder,
    output: VecDeque<u8>,
    finished: bool,
}

impl<R: Read> TranscodingReader<R> {
    pub fn new(inner: R, input_encoding: InputEncoding) -> Self {
        let decoder = match input_encoding {
            InputEncoding::Utf8 => UTF_8.new_decoder_with_bom_removal(),
            InputEncoding::Utf16Le => UTF_16LE.new_decoder_with_bom_removal(),
            InputEncoding::Windows1252 => WINDOWS_1252.new_decoder(),
        };
        Self {
            inner,
            decoder,
            output: VecDeque::new(),
            finished: false,
        }
    }

    fn fill_output(&mut self) -> io::Result<()> {
        if self.finished {
            return Ok(());
        }

        let mut raw = [0u8; 8192];
        let n = self.inner.read(&mut raw)?;
        let last = n == 0;
        let mut decoded = String::with_capacity(n.saturating_mul(2).saturating_add(16));
        let (_result, _read, had_errors) =
            self.decoder.decode_to_string(&raw[..n], &mut decoded, last);
        if had_errors {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "input contained bytes invalid for the declared encoding",
            ));
        }
        self.output.extend(decoded.into_bytes());
        if last {
            self.finished = true;
        }
        Ok(())
    }
}

impl<R: Read> Read for TranscodingReader<R> {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        if buf.is_empty() {
            return Ok(0);
        }

        while self.output.is_empty() && !self.finished {
            self.fill_output()?;
        }

        let mut written = 0;
        while written < buf.len() {
            let Some(byte) = self.output.pop_front() else {
                break;
            };
            buf[written] = byte;
            written += 1;
        }
        Ok(written)
    }
}

/// Streaming `Read` adapter for multi-byte CSV delimiters.
///
/// The Rust `csv` crate, like many fast CSV engines, accepts only a single-byte
/// delimiter. This adapter scans the byte stream and replaces occurrences of a
/// caller-provided delimiter with [`STAND_IN`]. It is quote-aware for ordinary
/// RFC4180-style quoted fields, so delimiter text inside quoted values remains
/// data instead of being rewritten.
pub struct MultiDelimReader<R: Read> {
    inner: R,
    delimiter: Vec<u8>,
    pending_match: Vec<u8>,
    output: VecDeque<u8>,
    input: [u8; 8192],
    input_pos: usize,
    input_len: usize,
    eof: bool,
    in_quotes: bool,
    after_quote_in_quotes: bool,
    at_field_start: bool,
}

impl<R: Read> MultiDelimReader<R> {
    pub fn new(inner: R, delimiter: Vec<u8>) -> Self {
        assert!(!delimiter.is_empty(), "delimiter must not be empty");
        Self {
            inner,
            delimiter,
            pending_match: Vec::new(),
            output: VecDeque::new(),
            input: [0u8; 8192],
            input_pos: 0,
            input_len: 0,
            eof: false,
            in_quotes: false,
            after_quote_in_quotes: false,
            at_field_start: true,
        }
    }

    fn next_byte(&mut self) -> io::Result<Option<u8>> {
        if self.input_pos >= self.input_len {
            if self.eof {
                return Ok(None);
            }
            self.input_len = self.inner.read(&mut self.input)?;
            self.input_pos = 0;
            if self.input_len == 0 {
                self.eof = true;
                return Ok(None);
            }
        }
        let byte = self.input[self.input_pos];
        self.input_pos += 1;
        Ok(Some(byte))
    }

    fn emit_literal(&mut self, byte: u8) {
        self.output.push_back(byte);
        self.at_field_start = matches!(byte, b'\n' | b'\r');
    }

    fn flush_pending_match_as_literals(&mut self) {
        let pending = std::mem::take(&mut self.pending_match);
        for byte in pending {
            self.emit_literal(byte);
        }
    }

    fn emit_delimiter(&mut self) {
        self.output.push_back(STAND_IN);
        self.at_field_start = true;
    }

    fn process_outside_quotes(&mut self, byte: u8) {
        if self.at_field_start && byte == b'"' {
            self.flush_pending_match_as_literals();
            self.in_quotes = true;
            self.after_quote_in_quotes = false;
            self.emit_literal(byte);
            self.at_field_start = false;
            return;
        }

        let matched = self.pending_match.len();
        if byte == self.delimiter[matched] {
            self.pending_match.push(byte);
            if self.pending_match.len() == self.delimiter.len() {
                self.pending_match.clear();
                self.emit_delimiter();
            }
            return;
        }

        if !self.pending_match.is_empty() {
            self.flush_pending_match_as_literals();
            self.process_outside_quotes(byte);
            return;
        }

        self.emit_literal(byte);
    }

    fn process_byte(&mut self, byte: u8) {
        if self.in_quotes {
            if self.after_quote_in_quotes {
                if byte == b'"' {
                    // Doubled quote: literal quote inside the quoted field.
                    self.output.push_back(byte);
                    self.after_quote_in_quotes = false;
                } else {
                    // The prior quote closed the quoted field. Reprocess this
                    // byte outside quotes so a following delimiter is recognized.
                    self.in_quotes = false;
                    self.after_quote_in_quotes = false;
                    self.process_outside_quotes(byte);
                }
                return;
            }

            self.output.push_back(byte);
            if byte == b'"' {
                self.after_quote_in_quotes = true;
            }
            return;
        }

        self.process_outside_quotes(byte);
    }

    fn fill_output(&mut self) -> io::Result<()> {
        while self.output.is_empty() {
            match self.next_byte()? {
                Some(byte) => self.process_byte(byte),
                None => {
                    self.flush_pending_match_as_literals();
                    break;
                }
            }
        }
        Ok(())
    }
}

impl<R: Read> Read for MultiDelimReader<R> {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        if buf.is_empty() {
            return Ok(0);
        }

        self.fill_output()?;

        let mut written = 0;
        while written < buf.len() {
            let Some(byte) = self.output.pop_front() else {
                break;
            };
            buf[written] = byte;
            written += 1;
            if self.output.is_empty() && written < buf.len() {
                self.fill_output()?;
                if self.output.is_empty() {
                    break;
                }
            }
        }
        Ok(written)
    }
}

/// Convenience constructor for the common hostile-reader stack:
/// known-encoding bytes → UTF-8 → quote-aware multi-byte delimiter adapter.
pub fn adapt_reader<R: Read>(
    reader: R,
    input_encoding: InputEncoding,
    delimiter: Vec<u8>,
) -> MultiDelimReader<TranscodingReader<R>> {
    MultiDelimReader::new(TranscodingReader::new(reader, input_encoding), delimiter)
}
