---
type: regex
pattern: '### FR-003 Count notes\nStatus: verified\n'
match: contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

A clean build closes FR-003 at `verified`: the block's `Status:` line, written by the caller's close.
