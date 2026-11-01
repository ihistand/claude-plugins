---
type: regex
pattern: 'Status: live'
match: not_contains
target: { source: file, path: docs/prd/greet/features/greet.md }
---

A run that stopped before production moves no requirement to `live`.
