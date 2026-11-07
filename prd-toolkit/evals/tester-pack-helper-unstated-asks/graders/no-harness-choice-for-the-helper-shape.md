---
type: regex
pattern: '^(?![\s\S]*(?:^|\n)[#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*HARNESS CHOICES\b[^\n]*\n(?:(?![#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*(?:FILES READ|RESULTS)\b)[^\n]*\n)*?(?![#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*(?:FILES READ|RESULTS)\b)(?![^\n]*(?:\bno stand-in|\bwithout a stand-in|\bwrote no\b|\bno helper\b|\bnot written\b))[^\n]*stored_notes[^\n]*\b(?:returns?|returning|result|shape|takes|argument|parameter|signature)\b)'
flags: i
target: last_message
---

No line of the report's HARNESS CHOICES section chooses the helper's shape (what `stored_notes` takes or
returns): a helper the pack ships already exists, so its parameters and result are not the tester's to choose.
The section is the one under its own heading line (an intro sentence naming it does not count) and ends at
FILES READ or RESULTS. A line that says no stand-in or helper was written passes; a line that describes a stand-in's shape does not.
