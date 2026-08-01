# devilread

Streaming read adapters for hostile tabular data.

`devilread` is the Rust systems layer for Devil’s Datasets. It is derived from the prior `csvparquet` read-adapter idea: keep ingestion memory-bounded by stacking small `Read` adapters instead of materializing, unzipping, transcoding, or rewriting whole files before parsing.

Current adapters:

- `TranscodingReader`: streams UTF-8, UTF-16LE, or Windows-1252 input as UTF-8 bytes.
- `MultiDelimReader`: quote-aware replacement of multi-byte delimiters with ASCII Unit Separator (`0x1f`) so single-byte-delimiter CSV engines can parse them.
- `adapt_reader`: convenience stack for `TranscodingReader -> MultiDelimReader`.

The first tests cover the Beelzebub-shaped small case: UTF-16LE CSV inside ZIP with a `~=` delimiter, plus preservation of literal delimiter text inside quoted fields.

This is not yet a full CLI. It is the reusable library foundation for future `devilread` / `devilizer` tools.
