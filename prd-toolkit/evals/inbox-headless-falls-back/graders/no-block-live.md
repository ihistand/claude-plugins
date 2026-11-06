---
type: regex
pattern: 'Status: live'
match: not_contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

No requirement of the notes area is `live` when the run ends: nothing was confirmed.
