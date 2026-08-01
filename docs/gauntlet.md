# The Gauntlet

This document lists pathological cases, failure modes, and mitigations.

## Beelzebub - Multiple difficulties at once and at scale

### Pathology

- Text file inside ZIP64
- ~100M rows per delivery
- UTF-16 encoding
- Multi-byte delimiter

### Why does this happen?

UTF-16 is the default for some things in Windows, and its built-in archiving utility uses ZIP64.
Using multiple printing characters as a delimiter makes it less likely the delimiter string appears in the data.

### Failure modes

### Mitigations


## Baphomet - Delimiters that change over time, re-releases, large files, new columns

### Pathology

- Delimiters may change between deliveries
- Raw data files are several GB
- Later releases supersede earlier ones and must replace them in production
- New columns may be added each year

### Why does this happen?

The systems generating the data extracts may change over time. 
When different personnel take on a role, they may change defaults.
When problems are found in an upstream system, re-releases are sometimes necessary.

### Failure modes

### Mitigations


## Mehphisto - Semi-structured data hand-curated over an extended period

### Pathology

- Schema changes every few files for the historical data
- No candidate keys
- Stored as a collection of Excel files

### Why does this happen?

Lots of data exists in this form because it is far friendlier for most humans in the absence of a well-polished database-backed system.


### Failure modes

### Mitigations
