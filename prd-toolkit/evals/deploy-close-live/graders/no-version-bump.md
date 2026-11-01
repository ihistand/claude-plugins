---
type: regex
pattern: 'version: 1\.0\.0\n'
match: contains
target: { source: file, path: docs/prd/greet/prd.md }
---

A deploy is progress, not behaviour: `version` stays 1.0.0.
