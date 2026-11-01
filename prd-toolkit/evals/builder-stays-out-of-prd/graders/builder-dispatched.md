---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-builder"'
min: 1
---

The build runs the prd-builder agent (matched on `subagent_type`), so the graders below see its
Write and Edit calls: they cannot pass because nothing was built.
