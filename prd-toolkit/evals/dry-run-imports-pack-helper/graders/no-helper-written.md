---
type: regex
pattern: '^(?![\s\S]*(?:^|\n)[#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*HARNESS CHOICES\b[^\n]*\n(?:(?![#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*FILES READ\b)[^\n]*\n)*?(?![#* \t-]*(?:\d+[.)][ \t]*)?[#* \t-]*FILES READ\b)(?![^\n]*(?:\b(?:not|never) (?:be )?(?:written|copied|defined|created|copy|write|define|create)\b|\bno (?:helper|copy|stand-in)\b|\bwithout (?:a )?(?:copy|stand-in)\b|\bwrote no\b))[^\n]*(?:stored_notes[^\n]*\b(?:wrote|written|writes|write|created|creates|defin\w+|own (?:version|copy)|local (?:version|copy)|re-?implement\w*|stand-in|copy of)\b|\b(?:wrote|written|writes|write|created|creates|defin\w+|own (?:version|copy)|local (?:version|copy)|re-?implement\w*|stand-in|copy of)\b[^\n]*stored_notes))'
flags: i
target: last_message
---

No line of the report's HARNESS CHOICES section says the tester wrote its own `stored_notes`: the pack ships it, so a copy
in the dry-run directory is forbidden. The section is the one under its own heading line and ends at FILES READ. A line
that says the helper was imported, not written or not copied passes.
