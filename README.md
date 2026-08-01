# The Devil’s Datasets

Reproducible pathological datasets for testing data ingestion systems.

The Devil’s Datasets is a catalog, fixture suite, and eventually a set of generators/readers for data that is not malicious but is *operationally hostile*: ragged CSV rows, mixed encodings, ambiguous nulls, multi-byte delimiters, huge fields, ZIP-contained CSVs that break streaming assumptions, and other cases that turn “just load the file” into bespoke engineering.

The goal is not to make ingestion systems accept garbage silently. The goal is to let them prove that they can:

1. parse correctly under an explicit contract;
2. fail safely with a precise diagnostic; or
3. generate enough evidence for a human to write the contract quickly.

In other words: pathological data should become a contract-authoring problem, not a multi-week custom-development problem.

## Status

Early extraction from a real-world ingestion regression suite. The first committed corpus is `fixtures/pathological_csv/`: 29 small CSV cases originally built to probe DuckDB-style raw-file profiling behavior. The cases are synthetic and safe to publish.

Expect names, schemas, and CLI surfaces to change while the project finds its shape.

## What is included now

```text
fixtures/pathological_csv/      Small committed CSV regression fixtures
scripts/generate_pathological_csv.py
                                Regenerates the CSV fixtures deterministically
scripts/probe_duckdb.py         Probes fixtures with DuckDB read_csv_auto
docs/taxonomy.md                Initial pathology taxonomy
docs/engine-notes/duckdb.md     Observed DuckDB behavior notes
profiles/*.yaml                 Sketches for future mutation/generation profiles
```

## Quick start

Regenerate the fixtures:

```bash
uv run scripts/generate_pathological_csv.py
```

Probe them with DuckDB:

```bash
uv run scripts/probe_duckdb.py
```

Run the basic repo smoke test:

```bash
python -m unittest discover -s tests
```

## Design principles
- **Palpably evil.** You need data that is pure evil in itself and operationally evil to expose the most diabolical bugs. 
- **Small fixtures first.** Commit small cases that isolate failure modes; generate large cases on demand.
- **Deterministic hostility.** Every generated dataset should be reproducible from a seed/profile.
- **Contracts over vibes.** A case should say what it is testing and what “good handling” means.
- **Correct parse or loud failure.** Silent misparse is the enemy.
- **General core, local policy outside.** This repo should contain general data-engineering pathologies, not organization-specific contracts, credentials, source names, or restricted data.

## Planned components

- `devilizer`: mutate good tabular data into reproducible pathological variants.
- `devilread`: bounded-memory readers for cases mainstream engines handle poorly, especially streaming CSV members inside ZIP archives and multi-byte delimiters with quoted fields.
- Engine notes/conformance reports for DuckDB, Polars, pandas, Go CSV readers, Rust CSV parsers, and other ingestion stacks.

## License

MIT.

## Diabolical AI Disclosure

This document and repo were created with the help of the most diabolical AI available. They represent the unholy union of human creativity and the obscene, blind power of machines. 
