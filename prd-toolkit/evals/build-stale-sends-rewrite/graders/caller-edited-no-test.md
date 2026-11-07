---
type: regex
pattern: '"name":"(?:Edit|Write)","input":\{[^\n]*?"file_path":"[^"\n]*tests/[^\n]*?"parent_tool_use_id":null'
match: not_contains
target: trace
---

The caller never edits or writes a test to bring it up to date. The trace holds the tester's own edits too, so
the match is limited to lines whose `parent_tool_use_id` is null (the main session); the tester's carry its
agent call's id.
