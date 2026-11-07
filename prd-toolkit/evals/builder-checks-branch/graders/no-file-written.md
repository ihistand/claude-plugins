---
type: regex
pattern: '"name":"(?:Write|Edit|NotebookEdit)","input"'
match: not_contains
target: trace
---

No Write or Edit call, by the builder or the session: the builder changes nothing when the branch check fails. The
trace holds the builder's tool calls too (they carry its Agent call's `parent_tool_use_id`).
