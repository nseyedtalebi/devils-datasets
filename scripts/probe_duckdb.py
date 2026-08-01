#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "duckdb>=1.0",
# ]
# ///
"""Run each pathological CSV through DuckDB using a SQL-level
`read_csv_auto('path', sample_size=-1)` call. This intentionally probes the SQL
surface rather than the Python relational `con.read_csv(...)` API; DuckDB versions
may differ in option names and behavior between those surfaces.

For each file this prints the default outcome, then a case-specific
"recommended" outcome using extra read_csv_auto options, so gaps are visible
without hand-running DuckDB per file.

Usage: uv run scripts/probe_duckdb.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parents[1] / 'fixtures' / 'pathological_csv'


def ql(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_lit(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return ql(str(v))


# filename -> extra read_csv_auto(...) options for the "recommended" attempt ({} = no better option exists)
RECOMMENDED: dict[str, dict] = {
    "01_ragged_rows_short.csv": {"null_padding": True},
    "02_ragged_rows_long.csv": {"ignore_errors": True},
    "03_trailing_delimiter.csv": {},
    "04_single_column_no_delim.csv": {},
    "05_wide_many_columns.csv": {},
    "06_header_only_no_rows.csv": {},
    "07_empty_file.csv": {},
    "08_embedded_newline_quoted.csv": {},
    "09_embedded_delimiter_quoted.csv": {},
    "10_escaped_quotes_doubled.csv": {},
    "11_escaped_quotes_backslash.csv": {"escape": "\\"},
    "12_unterminated_quote.csv": {"ignore_errors": True},
    "13_inconsistent_quoting.csv": {},
    "14_mixed_line_endings.csv": {},  # no fix short of pre-normalizing line endings before ingest
    "15_utf8_bom.csv": {},
    "16_latin1_encoding.csv": {"encoding": "latin-1"},
    "17_null_bytes_binary_garbage.csv": {"ignore_errors": True},
    "18_semicolon_delim_comma_decimal.csv": {"delim": ";", "decimal_separator": ","},
    "19_pipe_delimited.csv": {"delim": "|"},
    "20_null_representation_variants.csv": {},
    "21_type_flip_late_row.csv": {"sample_size": 20480},  # contrasts default sample window with full-file scan
    "22_numeric_formatting_edge_cases.csv": {"all_varchar": True},
    "23_leading_zero_ids.csv": {"all_varchar": True},
    "24_boolean_variants.csv": {"all_varchar": True},
    "25_duplicate_header_names.csv": {},
    "26_ambiguous_date_formats.csv": {"all_varchar": True},
    "27_date_hint_edge_cases.csv": {},
    "28_huge_single_field.csv": {},
    "29_comment_lines_interspersed.csv": {"comment": "#"},
}


def read_csv_auto_sql(path: Path, **opts) -> str:
    opts.setdefault("sample_size", -1)  # full-file scan catches late type flips
    args = [ql(str(path))] + [f"{k}={sql_lit(v)}" for k, v in opts.items()]
    return f"read_csv_auto({', '.join(args)})"


def try_read(path: Path, **opts) -> tuple[bool, str, int, int]:
    con = duckdb.connect()
    try:
        expr = read_csv_auto_sql(path, **opts)
        cols = con.execute(f"DESCRIBE SELECT * FROM {expr}").fetchall()
        n_rows = con.execute(f"SELECT count(*) FROM {expr}").fetchone()[0]
        return True, "ok", n_rows, len(cols)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc).splitlines()[0][:110], -1, -1
    finally:
        con.close()


def main() -> None:
    files = sorted(HERE.glob("*.csv"))
    print(f"{'file':<38} {'default':<7} {'rows':>7} {'cols':>5}   {'recommended':<12} {'rows':>7} {'cols':>5}")
    print("-" * 106)
    for f in files:
        ok1, msg1, r1, c1 = try_read(f)
        opts = RECOMMENDED.get(f.name, {})
        ok2, msg2, r2, c2 = try_read(f, **opts) if opts else (ok1, msg1, r1, c1)

        d_status = "OK" if ok1 else "ERROR"
        r_status = "OK" if ok2 else "ERROR"
        note = "" if opts else "(same, no override)"
        print(f"{f.name:<38} {d_status:<7} {r1 if ok1 else '-':>7} {c1 if ok1 else '-':>5}   "
              f"{r_status:<12} {r2 if ok2 else '-':>7} {c2 if ok2 else '-':>5}  {note}")
        if not ok1:
            print(f"    default error: {msg1}")
        if opts and not ok2:
            print(f"    recommended ({opts}) still errors: {msg2}")


if __name__ == "__main__":
    main()
