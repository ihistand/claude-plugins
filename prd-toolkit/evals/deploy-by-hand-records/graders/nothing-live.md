---
type: regex
pattern: 'Status: live'
match: not_contains
target: { source: file, path: docs/prd/greet/features/greet.md }
---

A by-hand record moves no status: both blocks stay `verified`.
