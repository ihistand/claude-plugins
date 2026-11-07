---
type: regex
pattern: '^(?![\s\S]*NEEDS CLARIFICATION)'
match: contains
target: { source: file, path: docs/prd/notes/test-cases/notes.yaml }
---

No other PRD file takes a question: the test cases hold no `NEEDS CLARIFICATION` marker.
