---
type: regex
pattern: '^version: 1\.1\.0$'
flags: m
target: { source: file, path: docs/prd/orders/prd.md }
---

A new requirement adds behaviour and changes nothing existing: 1.0.0 becomes 1.1.0 (`record --bump minor`).
