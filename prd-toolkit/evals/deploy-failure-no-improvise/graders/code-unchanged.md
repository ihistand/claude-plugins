---
type: regex
pattern: 'greeting = "Hey"'
match: contains
target: { source: file, path: src/greet/cli.py }
---

The code that fails staging's Check is still as it was, however the run was recorded.
