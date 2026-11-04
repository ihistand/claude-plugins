---
type: regex
flags: m
pattern: '^version: 1\.1\.0\n[\s\S]*\| 1\.1\.0 \| \d{4}-\d\d-\d\d \| an import skips a blank line between rows; pending \| AC-001\.4, T-001\.5 \|\n'
target: { source: file, path: docs/prd/orders/prd.md }
---

The recorded version and the pending §14 row stay as `record` wrote them: no re-record, no approval.
