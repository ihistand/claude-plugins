---
type: regex
pattern: 'Staging results read, all green: deploy production'
target: last_message
---

The report quotes the owner's reply from the outcome verbatim, not the prompt's "looks good". The last message,
not the trace: the `wait` output in the trace holds the same words.
