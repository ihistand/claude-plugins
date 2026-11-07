---
type: regex
pattern: 'status: In review'
match: contains
target: { source: file, path: docs/prd/notes/prd.md }
---

Both questions are Harness conventions, so the round is harness-only: the status stays `In review`.
