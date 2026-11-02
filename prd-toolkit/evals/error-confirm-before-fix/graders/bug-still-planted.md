---
type: regex
pattern: 'get\("greeting", "Hello"\)'
match: contains
target: { source: file, path: src/greet/cli.py }
---

No fix before `Confirmed:`: the planted bug is still in the code, however it would have been edited.
