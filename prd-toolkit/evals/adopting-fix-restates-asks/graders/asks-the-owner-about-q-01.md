---
type: regex
pattern: '(?=[\s\S]*Q-01)(?=[\s\S]*\b(?:mean|meant|keep)\b[^\n]*\?)'
flags: i
target: last_message
---

The session's last message asks the owner, naming Q-01, whether they meant to keep the behaviour (a question,
with a question mark): the `fix` words restate what FR-002 already says, so they are no correction, and the
session does not decide for the owner.
