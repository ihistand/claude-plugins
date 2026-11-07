---
type: regex
pattern: 'Layout\.\*\*[^\n]*test_[^\n]*@prd'
match: contains
target: { source: file, path: docs/prd/notes/testing.md }
---

The first answer is written into testing.md's Harness, in the Layout slot.
