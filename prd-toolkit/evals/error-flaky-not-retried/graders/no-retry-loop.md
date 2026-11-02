---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?!uv run --script \S*prd_error\.py\s)(?:[^"\\]|\\.)*?(?:(?:\bfor\s+\w+\s+in\b|\bwhile\s|\bseq\s)(?:[^"\\]|\\.)*?pytest|pytest(?:[^"\\]|\\.)*?--(?:count|reruns|flake-finder)\b)'
min: 0
max: 0
---

Never a loop, a repeat count or a rerun plugin around the test. A `prd_error.py` call is never counted: its text may quote a command it does not run.
