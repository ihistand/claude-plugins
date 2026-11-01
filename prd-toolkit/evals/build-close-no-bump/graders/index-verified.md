---
type: regex
pattern: '\|\s*FR-003\s*\|\s*Count notes\s*\|\s*verified\s*\|'
match: contains
target: { source: file, path: docs/prd/notes/prd.md }
---

The §11 index row moves with the block: `| FR-003 | Count notes | verified |`.
