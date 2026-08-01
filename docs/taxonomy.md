# Pathology taxonomy

Devil’s Datasets names ingestion failure modes so they can become repeatable tests instead of private folklore.

## Structural pathologies

- Ragged rows: too few or too many fields relative to the header.
- Trailing delimiters and phantom columns.
- Empty files, header-only files, and valid one-column files.
- Very wide files and very large cells.
- Duplicate column names.

## Dialect pathologies

- Embedded delimiters inside quoted fields.
- Embedded newlines inside quoted fields.
- Mixed quote escaping conventions.
- Unterminated quotes and inconsistent quoting.
- Multi-byte delimiters, including cases mainstream CSV readers do not support.

## Encoding and byte pathologies

- UTF-8 BOMs.
- Non-UTF-8 encodings.
- Embedded NUL bytes or binary garbage.
- Mixed line endings within a single file.

## Semantic inference pathologies

- Ambiguous null sentinels.
- Leading-zero identifiers that must remain strings.
- Numeric-looking strings with currency, percent signs, separators, or scientific notation.
- Mixed boolean spellings.
- Ambiguous date formats and date-name heuristic false positives.
- Late type flips after default sniffing sample windows.

## Archive/transport pathologies

- One huge CSV member inside a ZIP archive.
- Many small CSV members inside a ZIP archive.
- ZIP member names with nested paths, odd encodings, or repeated basenames.
- Archive formats that break streaming assumptions in otherwise streaming ingestion engines.
