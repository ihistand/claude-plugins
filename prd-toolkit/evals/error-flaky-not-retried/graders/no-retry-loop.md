---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?:[^"\\]|\\.)*?(?:(?:\bfor\s+\w+\s+in\b|\bwhile\s|\bseq\s)(?:[^"\\]|\\.)*?pytest|pytest(?:[^"\\]|\\.)*?--(?:count|reruns|flake-finder)\b)'
min: 0
max: 0
---

Never a loop, a repeat count or a rerun plugin around the test.
