---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-tester"[\s\S]*Mode: suite|Mode: suite[\s\S]*"subagent_type"\s*:\s*"(?:prd-toolkit:)?prd-tester"'
min: 1
---

An area is adopted only on a suite: prd-tester (by `subagent_type`, not a mention in a prompt) is
dispatched with `Mode: suite`.
