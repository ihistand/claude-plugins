---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-builder"'
min: 1
---

The code and its unit tests are written by the prd-builder agent, not by the caller.
The match is on `subagent_type`, so a general-purpose dispatch whose prompt only mentions
prd-builder does not count.
