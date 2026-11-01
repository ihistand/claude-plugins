---
type: tool_used
tool: Edit
input_match: '"file_path"\s*:\s*"[^"]*tests/test_notes\.py"[\s\S]*T-003\.1|T-003\.1[\s\S]*"file_path"\s*:\s*"[^"]*tests/test_notes\.py"'
min: 0
max: 0
---

No Edit of `tests/test_notes.py`, the tester's file, writes the unit T-id `T-003.1`: the builder's
unit tests go in a file of its own. The tester legitimately edits that file for T-003.2 (so the
graders cannot forbid every edit of it, as a tool call carries no agent id), and never cites
T-003.1 there.
