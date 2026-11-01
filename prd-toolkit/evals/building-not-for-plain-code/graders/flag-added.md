---
type: regex
pattern: '--version'
match: contains
target: { source: file, path: src/greet/cli.py }
---

The flag is added to the CLI.
