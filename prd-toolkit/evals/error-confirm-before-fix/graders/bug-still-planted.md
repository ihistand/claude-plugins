---
type: regex
pattern: 'load_settings\(\)\.get\("greeting", "Hello"\)'
match: contains
target: { source: file, path: src/greet/cli.py }
---

No fix before `Confirmed:`: the whole planted expression is still in the code, so neither the fix nor a lowercase-keys rewrite went in.
