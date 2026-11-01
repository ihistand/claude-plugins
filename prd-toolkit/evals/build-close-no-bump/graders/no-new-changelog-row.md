---
type: regex
pattern: '\|\s*(?:1\.1\.[1-9]\d*|1\.[2-9]\d*\.\d+|[2-9]\.\d+\.\d+)\s*\|'
match: not_contains
target: { source: file, path: docs/prd/notes/prd.md }
---

No §14 row for a later version: the last changelog row is still 1.1.0, so the close added none.
