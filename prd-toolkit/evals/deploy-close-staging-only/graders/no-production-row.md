---
type: regex
pattern: '\|\s*production\s*\|\s*1\.0\.0\s*\|'
match: not_contains
target: { source: file, path: docs/prd/greet/operations.md }
---

Production was not reached, so it gets no row.
