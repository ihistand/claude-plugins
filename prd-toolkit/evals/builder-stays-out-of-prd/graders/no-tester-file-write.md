---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*tests/test_notes\.py"[\s\S]*T-003\.1|T-003\.1[\s\S]*"file_path"\s*:\s*"[^"]*tests/test_notes\.py"'
min: 0
max: 0
---

No Write replaces `tests/test_notes.py` with a version that cites `T-003.1`: the same rule as
`no-tester-file-edit`, for the Write tool.
