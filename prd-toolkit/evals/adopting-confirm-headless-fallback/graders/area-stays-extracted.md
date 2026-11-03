---
type: regex
pattern: '\|\s*notes\s*\|\s*extracted\s*\|'
match: contains
target: { source: file, path: docs/prd/notes/adoption.md }
---

The notes area's row in adoption.md is still `extracted`: nobody could answer, so the step stops
there. `confirmed` or `adopted` would mean an answer was written that the user never gave.
