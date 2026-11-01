---
type: regex
pattern: 'Status: live'
match: not_contains
target: { source: file, path: docs/prd/greet/features/greet.md }
---

Staging passing makes nothing live.
