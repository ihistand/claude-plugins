---
type: regex
pattern: 'Classification: unclassified'
match: contains
target: { source: file, path: docs/prd/greet/errors.md }
---

Every failure gets an open `Classification: unclassified` entry in errors.md.
