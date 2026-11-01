---
type: regex
pattern: '## Deployed[\s\S]*\|\s*staging\s*\|\s*1\.0\.0\s*\|'
match: contains
target: { source: file, path: docs/prd/greet/operations.md }
---

A `Deployed` row for staging at PRD version 1.0.0.
