---
type: regex
pattern: '^(?![\s\S]*NEEDS CLARIFICATION)'
match: contains
target: { source: file, path: docs/prd/notes/testing.md }
---

The answers are written into the Harness as text: a full round would have left a `NEEDS CLARIFICATION` marker there.
