---
type: regex
pattern: '(?:^|\n)Classification: (?:code bug|spec gap|invalid requirement|environment|standard)[ \t]*(?:\r?\n|$)'
match: contains
target: { source: file, path: docs/prd/greet/errors.md }
---

The error is recorded and its class proposed: an entry whose class is no longer `unclassified`.
