---
type: regex
pattern: 'status: Approved\n'
match: contains
target: { source: file, path: docs/prd/notes/prd.md }
---

The PRD status stays `Approved`: a build is not a re-approval.
