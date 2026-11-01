---
type: regex
pattern: 'Status: live'
match: not_contains
target: { source: file, path: docs/prd/greet/features/greet.md }
---

A failed run that did not reach production moves no status.
