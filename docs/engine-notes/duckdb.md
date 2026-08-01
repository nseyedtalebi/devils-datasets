# DuckDB engine notes

These notes describe observed behavior from the initial pathological CSV suite. They are version-sensitive; re-run `uv run scripts/probe_duckdb.py` after DuckDB upgrades.

## Known useful behavior

- `read_csv_auto(..., sample_size=-1)` can catch late type flips that the default sample window would miss.
- DuckDB currently preserves leading-zero identifiers as `VARCHAR` in the provided fixture.
- UTF-8 BOM headers, quoted embedded delimiters, quoted embedded newlines, and wide CSVs are handled well in the small fixtures.

## Known traps

- Ragged rows may collapse into a single VARCHAR column instead of failing loudly.
- Mixed line endings can hard-fail sniffing and may require pre-normalization.
- Non-UTF-8 files require explicit encoding. Verify whether the SQL function and Python relational API accept the same option names in your DuckDB version.
- Blanket lenient/error-ignoring modes can make failures worse. Use targeted retries for named pathologies.
- Comment-prefixed lines are not automatically inferred as comments; pass an explicit comment option if that is the contract.
- ZIP-contained CSV streaming is not covered by this first fixture suite. It is a planned archive/reader stress area.
