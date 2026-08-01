use std::io::{Read, Write};

use csv::ReaderBuilder;
use devilread::{adapt_reader, InputEncoding, MultiDelimReader, STAND_IN};
use tempfile::tempdir;
use zip::{write::FileOptions, ZipWriter};

struct ChunkedReader<'a> {
    data: &'a [u8],
    pos: usize,
    chunk_size: usize,
}

impl<'a> ChunkedReader<'a> {
    fn new(data: &'a [u8], chunk_size: usize) -> Self {
        Self {
            data,
            pos: 0,
            chunk_size,
        }
    }
}

impl<'a> Read for ChunkedReader<'a> {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        let remaining = &self.data[self.pos..];
        let n = remaining.len().min(self.chunk_size).min(buf.len());
        buf[..n].copy_from_slice(&remaining[..n]);
        self.pos += n;
        Ok(n)
    }
}

#[test]
fn multibyte_delimiter_split_across_buffer_boundary_is_replaced() {
    let input = b"left~=right";
    let chunked = ChunkedReader::new(input, 1);
    let mut adapter = MultiDelimReader::new(chunked, b"~=".to_vec());

    let mut output = Vec::new();
    adapter.read_to_end(&mut output).unwrap();

    assert_eq!(output, b"left\x1fright");
}

#[test]
fn literal_multibyte_delimiter_inside_quoted_field_is_preserved() {
    let input = b"id~=note\n1~=\"literal ~= inside quotes\"\n";
    let chunked = ChunkedReader::new(input, 1);
    let adapted = MultiDelimReader::new(chunked, b"~=".to_vec());
    let mut rdr = ReaderBuilder::new()
        .delimiter(STAND_IN)
        .has_headers(true)
        .from_reader(adapted);

    let rows: Vec<_> = rdr.records().map(|r| r.unwrap()).collect();

    assert_eq!(&rows[0][0], "1");
    assert_eq!(&rows[0][1], "literal ~= inside quotes");
}

#[test]
fn zip_utf16le_multidelim_stream_can_feed_csv_reader() {
    let dir = tempdir().unwrap();
    let zip_path = dir.path().join("beelzebub-small.zip");
    let file = std::fs::File::create(&zip_path).unwrap();
    let mut zip = ZipWriter::new(file);
    let options: FileOptions<()> = FileOptions::default();
    zip.start_file("payload.txt", options).unwrap();
    let payload = "id~=name~=city\n1~=Alice~=Springfield\n2~=Bob~=Shelbyville\n";
    let utf16le: Vec<u8> = payload
        .encode_utf16()
        .flat_map(|u| u.to_le_bytes())
        .collect();
    zip.write_all(&utf16le).unwrap();
    zip.finish().unwrap();

    let file = std::fs::File::open(&zip_path).unwrap();
    let mut archive = zip::ZipArchive::new(file).unwrap();
    let member = archive.by_name("payload.txt").unwrap();
    let adapted = adapt_reader(member, InputEncoding::Utf16Le, b"~=".to_vec());
    let mut rdr = ReaderBuilder::new()
        .delimiter(STAND_IN)
        .has_headers(true)
        .from_reader(adapted);

    let rows: Vec<_> = rdr.records().map(|r| r.unwrap()).collect();

    assert_eq!(rows.len(), 2);
    assert_eq!(&rows[0][1], "Alice");
    assert_eq!(&rows[1][2], "Shelbyville");
}
