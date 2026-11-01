---
type: regex
pattern: 'T-003\.1'
match: not_contains
target: { source: file, path: tests/test_notes.py }
---

The tester's file holds no case of the builder's unit T-id, by any tool.
