---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-tester"'
min: 1
---

The tests are written by the prd-tester agent, the tester whose reads the guard confines.
The match is on `subagent_type`, so a general-purpose dispatch whose prompt only mentions
prd-tester does not count.
