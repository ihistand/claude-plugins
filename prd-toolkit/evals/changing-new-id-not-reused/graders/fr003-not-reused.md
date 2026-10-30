---
type: regex
pattern: '### FR-003 [^\n]*[Aa]rchiv'
match: not_contains
target: { source: file, path: docs/prd/orders/features/api.md }
---

The removed FR-003 must not be given the archive feature.
