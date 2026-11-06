---
type: regex
pattern: 'def count_notes'
match: not_contains
target: { source: file, path: src/notes/app.py }
---

`count_notes` is not written, by any tool: a Bash heredoc or `sed` the Write and Edit grader cannot see is caught here.
