# The Gauntlet

This document lists pathological cases, failure modes, and mitigations.

## Beelzebub - multiple kinds of pain at once

### Pathology

- Text file inside ZIP64
- ~100M rows per delivery
- UTF-16 encoding
- Multi-byte delimiters
- No header

### Why does this happen?

UTF-16 is the default for some things in Windows, and its built-in archiving utility uses ZIP64.
Using multiple printing characters as a delimiter makes it less likely the delimiter string appears in the data.

### Failure modes

### Mitigations
