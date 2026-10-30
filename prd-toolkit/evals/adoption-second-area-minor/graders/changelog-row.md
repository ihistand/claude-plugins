---
type: regex
pattern: '\|\s*1\.1\.0\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|'
match: contains
target: { source: file, path: docs/prd/notes/prd.md }
---

The 1.1.0 release has a changelog row (`| 1.1.0 | <date> |`; the §11 Since cell `| 1.1.0 |` that the
scaffold already holds does not match).
