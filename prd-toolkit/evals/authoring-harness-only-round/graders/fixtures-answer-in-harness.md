---
type: regex
pattern: 'Fixtures\.\*\*[^\n]*add_note'
match: contains
target: { source: file, path: docs/prd/notes/testing.md }
---

The second answer is written into testing.md's Harness, in the Fixtures slot.
