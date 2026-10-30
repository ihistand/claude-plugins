---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-tester"'
min: 1
---

The characterization suite is written and run by the prd-tester agent, not by the caller.
The match is on `subagent_type`, so a general-purpose dispatch whose prompt only mentions
prd-tester does not count.
