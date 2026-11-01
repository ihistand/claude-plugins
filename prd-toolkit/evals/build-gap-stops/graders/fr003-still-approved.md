---
type: regex
pattern: '### FR-003 Count notes\nStatus: (?:verified|live)'
match: not_contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

FR-003 is not `verified` or `live` at the end of the run, however the file was written (an Edit, or
a Bash `sed`). `approved` (stopped before the merge) and `built` (stopped after it) both pass.
