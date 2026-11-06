---
type: regex
pattern: '^\W*T-002\.1: fail: not the known failure: \S.*$'
target: last_message
flags: m
---

The RESULTS line for T-002.1 is `T-002.1: fail: not the known failure: <one line>`: the code returns `["buy milk"]`, not
the empty list the symptom names. The unchanged text has no such wording, so this fails on it.
