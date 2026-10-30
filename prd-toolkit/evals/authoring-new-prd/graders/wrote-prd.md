---
type: regex
target: files
pattern: 'docs/prd/[a-z0-9-]+/prd\.md'
---

The PRD is written as docs/prd/<slug>/prd.md, not as a single flat file. The grader reads the
paths the run created, whichever tool wrote them.
