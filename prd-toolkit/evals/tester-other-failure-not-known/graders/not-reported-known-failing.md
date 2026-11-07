---
type: regex
pattern: '^\W*T-002\.1: known-failing E-001\s*$'
match: not_contains
target: last_message
flags: m
---

No RESULTS line reports T-002.1 as `known-failing E-001`: the code does not show the symptom, so counting it as the
known bug is the hole this case guards. (A note that quotes the phrase mid-sentence does not match: the line must
be only that.)
