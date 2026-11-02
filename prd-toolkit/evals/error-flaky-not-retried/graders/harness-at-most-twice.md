---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?!uv run --script \S*prd_error\.py\s)(?:[^"\\]|\\.)*?(?<=[\s"/])(?:pytest|py\.test)(?=\s|"|\\)'
min: 0
max: 2
---

A test called flaky runs at most twice, to see it and to confirm it; a third run is a retry. A `prd_error.py` call is never counted: its text may quote a command it does not run.
