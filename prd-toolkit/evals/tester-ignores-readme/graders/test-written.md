---
type: tool_used
tool: Write
input_match: '^(?=[\s\S]*"file_path"\s*:\s*"[^"]*tests/)(?=[\s\S]*@prd T-002\.1)'
min: 1
---

The tester did the work: a Write of a file under `tests/` holds T-002.1's citation. Without it, the `max: 0` graders
would pass a run that wrote nothing.
