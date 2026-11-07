---
type: regex
pattern: '^(?![\s\S]*NEEDS CLARIFICATION)'
match: contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

No other PRD file takes a question: the features file holds no `NEEDS CLARIFICATION` marker.
