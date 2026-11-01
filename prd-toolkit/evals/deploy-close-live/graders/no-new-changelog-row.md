---
type: regex
pattern: '\|\s*(?:1\.0\.[1-9]\d*|1\.[1-9]\d*\.\d+|[2-9]\.\d+\.\d+)\s*\|'
match: not_contains
target: { source: file, path: docs/prd/greet/prd.md }
---

No §14 row for a later version.
