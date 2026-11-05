---
type: regex
pattern: '### FR-002[^#]*?Status: approved'
match: not_contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

FR-002 is never made `approved` (a correction): the `fix` answer of Q-01 restates its current behaviour, so no
correction is applied for it. (FR-002's own `confirm` makes it `live`.)
