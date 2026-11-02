---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?:[^"\\]|\\.)*?(?<=[\s"/])(?:pytest|py\.test)(?=\s|"|\\)'
min: 0
max: 2
---

A test called flaky runs at most twice, to see it and to confirm it; a third run is a retry.
