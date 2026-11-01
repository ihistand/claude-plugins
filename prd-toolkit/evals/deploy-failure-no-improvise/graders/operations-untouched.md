---
type: regex
pattern: '## Deployed'
match: not_contains
target: { source: file, path: docs/prd/greet/operations.md }
---

No environment was reached, so operations.md gets no Deployed row.
