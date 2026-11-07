---
type: tool_used
tool: Agent
input_match: '"prompt"\s*:\s*"(?=[^"]*Mode: suite)[^"]*(?:\\n|^)Rewrite: T-001\.1\b'
min: 1
---

The tester dispatch (the Agent call whose prompt says `Mode: suite`) carries a `Rewrite: T-001.1` line at the start
of a line: T-001.1's test case changed after its test, and T-002.1's did not.
