---
type: regex
pattern: '\|\s*FR-00[12]\s*\|[^|\n]*\|\s*live\s*\|'
match: not_contains
target: { source: file, path: docs/prd/greet/prd.md }
---

The §11 index rows stay `verified`.
