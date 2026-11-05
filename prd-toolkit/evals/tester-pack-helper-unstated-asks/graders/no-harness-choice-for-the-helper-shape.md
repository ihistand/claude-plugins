---
type: regex
pattern: '^(?![\s\S]*(?:^|\n)[#* \t-]*HARNESS CHOICES\b[^\n]*\n(?:(?![#* \t-]*(?:FILES READ|RESULTS)\b)[^\n]*\n)*?(?![#* \t-]*(?:FILES READ|RESULTS)\b)(?![^\n]*(?:stand-in|not written|no helper))[^\n]*stored_notes[^\n]*\b(?:returns?|result|shape|takes|argument|parameter|signature)\b)'
flags: i
target: last_message
---

No line of the report's HARNESS CHOICES section chooses the helper's shape (what `stored_notes` takes or
returns): a helper the pack ships already exists, so its parameters and result are not the tester's to choose.
The section is the one under its own heading line (an intro sentence naming it does not count) and ends at
FILES READ or RESULTS. A line that says no stand-in or helper was written passes.
