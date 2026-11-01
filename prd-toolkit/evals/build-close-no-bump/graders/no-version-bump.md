---
type: regex
pattern: 'version: 1\.1\.0\n'
match: contains
target: { source: file, path: docs/prd/notes/prd.md }
---

A status move is progress, not behaviour: `version` stays 1.1.0.
