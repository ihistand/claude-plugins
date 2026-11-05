---
type: regex
pattern: '^(?![\s\S]*HARNESS CHOICES(?:(?!FILES READ)[\s\S])*?stored_notes[^\n]*\b(?:returns?|result|shape|takes|argument|parameter|signature)\b)'
flags: i
target: last_message
---

No HARNESS CHOICES line chooses the helper's shape (what `stored_notes` takes or returns): a helper the pack
ships already exists, so its parameters and result are not the tester's to choose. A line that only says the
helper was called as shipped, or that no stand-in was written, passes.
