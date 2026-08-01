# Prior Rust work

Devil’s Datasets did not start from an empty Rust spike. Two earlier Nima-owned Rust repositories contain relevant machinery.

## csvparquet

Repository: <https://github.com/nseyedtalebi/csvparquet>

Relevant artifact: `src/read_adapters.rs`.

The important idea is a streaming adapter chain:

```text
File / ZIP member
  -> TranscodingReader
  -> MultiDelimReader
  -> csv parser
  -> Parquet writer
```

This was built for resource-constrained ingestion: small VMs, slow disks/network, little free space under `/home`, and datasets too large to casually unzip or rewrite before parsing.

`devilread` carries this idea forward as a reusable library in this repo.

## mssql-parquet

Repository: <https://github.com/nseyedtalebi/mssql-parquet>

Relevant artifacts:

- `parquet-typer`: converts all-string Parquet into typed Parquet.
- `staging_loader`: bulk-loads typed Parquet into SQL Server staging tables.

The loader path was far along, but the live repository needs packaging/build repair before it can be treated as a clean dependency: current `master` has gitlink workspace members without `.gitmodules`, and a fresh test build exposed small dependency/API drift issues.

For Devil’s Datasets, the immediately reusable part is the read-adapter mechanism, not the whole SQL Server loading pipeline.

## Design consequence

The first Rust goal here is not “rewrite ingestion.” It is narrower:

```text
hostile bytes + explicit reader contract
  -> bounded-memory UTF-8 record stream
```

RADOR or any other ingestion system can then decide policy, typing, loading, validation, and operational ledger behavior outside this crate.
