---
type: regex
pattern: '/prd-deploy[^\n]*\blive\b|\blive\b[^\n]*/prd-deploy'
flags: i
target: last_message
---

The last message says that `live` waits for a later `/prd-deploy` run (both on one line), not the trace: the skill
text the trace holds carries the same words.
