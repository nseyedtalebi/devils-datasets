#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Generate the Devil's Datasets pathological CSV fixture set.

Each file isolates one CSV-parsing pathology that an ingestion system has to
either handle, reject loudly, or (worst case) silently mis-parse. See
fixtures/pathological_csv/MANIFEST.md for the rationale behind each case.
"""
from __future__ import annotations

import csv
import io
import random
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'fixtures' / 'pathological_csv'
random.seed(1234)


def w(name: str, text: str, newline: str = "\n", encoding: str = "utf-8") -> None:
    (HERE / name).write_bytes(text.replace("\n", newline).encode(encoding))


def wb(name: str, data: bytes) -> None:
    (HERE / name).write_bytes(data)


# 01 -------------------------------------------------------------- ragged rows, too short
w("01_ragged_rows_short.csv", """\
id,name,city,score
1,Alice,Springfield,95
2,Bob,Shelbyville
3,Carol,Ogdenville,88
4,Dave
""")

# 02 -------------------------------------------------------------- ragged rows, too long
w("02_ragged_rows_long.csv", """\
id,name,city,score
1,Alice,Springfield,95
2,Bob,Shelbyville,80,extra_field,another_extra
3,Carol,Ogdenville,88
""")

# 03 -------------------------------------------------------------- trailing delimiter -> phantom column
w("03_trailing_delimiter.csv", """\
id,name,score,
1,Alice,95,
2,Bob,80,
3,Carol,88,
""")

# 04 -------------------------------------------------------------- single column, no delimiter anywhere
w("04_single_column_no_delim.csv", """\
sku
A1000
A1001
A1002
A1003
""")

# 05 -------------------------------------------------------------- very wide (300 columns)
ncols = 300
header = ",".join(f"c{i}" for i in range(ncols))
rows = [",".join(str(r * ncols + i) for i in range(ncols)) for r in range(5)]
w("05_wide_many_columns.csv", header + "\n" + "\n".join(rows) + "\n")

# 06 -------------------------------------------------------------- header only, zero data rows
w("06_header_only_no_rows.csv", "id,name,city,score\n")

# 07 -------------------------------------------------------------- truly empty file
wb("07_empty_file.csv", b"")

# 08 -------------------------------------------------------------- embedded newline inside quoted field
w("08_embedded_newline_quoted.csv", '''\
id,name,notes
1,Alice,"First line
second line"
2,Bob,"single line"
''')

# 09 -------------------------------------------------------------- quoted field containing the delimiter
w("09_embedded_delimiter_quoted.csv", '''\
id,name,address
1,Alice,"123 Main St, Springfield"
2,Bob,"456 Oak Ave, Shelbyville"
''')

# 10 -------------------------------------------------------------- RFC4180 doubled-quote escaping
w("10_escaped_quotes_doubled.csv", '''\
id,name,quote
1,Alice,"She said ""hello"" to me"
2,Bob,"No quotes here"
''')

# 11 -------------------------------------------------------------- backslash-escaped quotes (non-default escape char)
w("11_escaped_quotes_backslash.csv", r'''id,name,quote
1,Alice,"She said \"hello\" to me"
2,Bob,"No quotes here"
''')

# 12 -------------------------------------------------------------- unterminated quote (genuinely malformed)
w("12_unterminated_quote.csv", '''\
id,name,notes
1,Alice,"This quote never closes
2,Bob,fine
''')

# 13 -------------------------------------------------------------- inconsistent quoting style row-to-row
w("13_inconsistent_quoting.csv", '''\
id,name,city
1,"Alice","Springfield"
2,Bob,Shelbyville
3,"Carol",Ogdenville
''')

# 14 -------------------------------------------------------------- mixed line endings within one file
buf = io.BytesIO()
buf.write(b"id,name,score\n")
buf.write(b"1,Alice,95\r\n")
buf.write(b"2,Bob,80\r")
buf.write(b"3,Carol,88\n")
wb("14_mixed_line_endings.csv", buf.getvalue())

# 15 -------------------------------------------------------------- UTF-8 BOM prefix
wb("15_utf8_bom.csv", b"\xef\xbb\xbf" + "id,name,city\n1,Alice,Springfield\n2,Bob,Shelbyville\n".encode("utf-8"))

# 16 -------------------------------------------------------------- Latin-1 (non-UTF-8) encoding
w("16_latin1_encoding.csv", "id,name,city\n1,François,München\n2,André,Zürich\n", encoding="latin-1")

# 17 -------------------------------------------------------------- embedded NUL bytes / binary garbage
buf = io.BytesIO()
buf.write(b"id,name,notes\n")
buf.write(b"1,Alice,clean row\n")
buf.write(b"2,Bob,dirty\x00row\xff\xfe\n")
buf.write(b"3,Carol,clean again\n")
wb("17_null_bytes_binary_garbage.csv", buf.getvalue())

# 18 -------------------------------------------------------------- semicolon delimiter + comma decimal (EU style)
w("18_semicolon_delim_comma_decimal.csv", """\
id;name;amount
1;Alice;1234,56
2;Bob;89,00
3;Carol;10500,25
""")

# 19 -------------------------------------------------------------- pipe delimiter
w("19_pipe_delimited.csv", """\
id|name|city
1|Alice|Springfield
2|Bob|Shelbyville
""")

# 20 -------------------------------------------------------------- inconsistent null representations in one column
w("20_null_representation_variants.csv", """\
id,name,note
1,Alice,
2,Bob,NULL
3,Carol,NA
4,Dave,\\N
5,Eve,None
6,Frank,n/a
7,Grace,real value
""")

# 21 -------------------------------------------------------------- type flip on a row past DuckDB's default sample window
# default read_csv_auto sample_size is 20480 rows; put a string value at row ~25000
# in a column that looks purely integer for the first 25000 rows.
n_rows = 25_000
flip_at = 24_500
lines = ["id,qty,label"]
for i in range(1, n_rows + 1):
    qty = str(i) if i != flip_at else "unknown"
    lines.append(f"{i},{qty},row{i}")
w("21_type_flip_late_row.csv", "\n".join(lines) + "\n")

# 22 -------------------------------------------------------------- numeric formatting edge cases
w("22_numeric_formatting_edge_cases.csv", """\
id,amount,pct,sci
1,"1,234.56",12%,1.2e10
2,"$1,000.00",50%,3.4E-5
3,-42.00,0%,2e3
4,007,100%,1.0
""")

# 23 -------------------------------------------------------------- leading zeros silently stripped by int coercion
w("23_leading_zero_ids.csv", """\
zip_code,phone_ext,employee_id
02134,0042,000123
94107,0007,000456
00501,1234,000789
""")

# 24 -------------------------------------------------------------- boolean-like column with mixed representations
w("24_boolean_variants.csv", """\
id,is_active
1,true
2,false
3,Y
4,N
5,1
6,0
7,yes
8,no
""")

# 25 -------------------------------------------------------------- duplicate column names in header
w("25_duplicate_header_names.csv", """\
id,name,name,score
1,Alice,A.Smith,95
2,Bob,B.Jones,80
""")

# 26 -------------------------------------------------------------- ambiguous date formats mixed in one column
w("26_ambiguous_date_formats.csv", '''\
id,event_date
1,03/04/2024
2,2024-03-04
3,04/03/2024
4,"March 4, 2024"
5,2024/03/04
''')

# 27 -------------------------------------------------------------- date-name-hint threshold edge case for a profiler's
# own date-detection heuristic (example: lower the evidence gate if a column name looks temporal).
# Both columns are 60% TRY_CAST-parseable as TIMESTAMP:
#   update_day   -> name contains "day" (a DATE_NAME_HINTS substring)   -> gate 0.5 -> 0.6 >= 0.5 -> flagged as date
#   col_generic  -> no name hint                                       -> gate 0.9 -> 0.6 <  0.9 -> NOT flagged
# update_day being flagged is a real false-positive risk: 40% of its values are not dates at all, yet it can end
# up feeding freshness/QC reports as if the column were reliably temporal.
lines = ["id,update_day,col_generic"]
for i in range(1, 21):
    is_date_row = i <= 12  # 12/20 = 60%
    update_day = f"2024-01-{i:02d}" if is_date_row else "pending"
    col_generic = f"2024-01-{i:02d}" if is_date_row else "N/A"
    lines.append(f"{i},{update_day},{col_generic}")
w("27_date_hint_edge_cases.csv", "\n".join(lines) + "\n")

# 28 -------------------------------------------------------------- one enormous single-field value
huge_text = "x" * 200_000
w("28_huge_single_field.csv", f'id,blob\n1,"{huge_text}"\n2,short\n')

# 29 -------------------------------------------------------------- comment lines interspersed (needs `comment` option)
w("29_comment_lines_interspersed.csv", """\
# generated export - do not edit
# source: legacy mainframe dump
id,name,score
1,Alice,95
# row below was a manual correction
2,Bob,80
3,Carol,88
""")

print(f"generated {len(list(HERE.glob('*.csv')))} CSV files in {HERE}")
