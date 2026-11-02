---
type: regex
pattern: '(?:^|\n)Confirmed:'
match: not_contains
target: { source: file, path: docs/prd/greet/errors.md }
---

With no one to ask, nobody confirmed the class: the request to fix it is never the confirmation.
