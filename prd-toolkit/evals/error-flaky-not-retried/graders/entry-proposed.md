---
type: regex
pattern: '(?:^|\n)Classification: (?:code bug|spec gap|invalid requirement|environment|standard)[ \t]*(?:\r?\n|$)'
match: contains
target: { source: file, path: docs/prd/greet/errors.md }
---

The failing test is recorded as an entry and its class proposed.
