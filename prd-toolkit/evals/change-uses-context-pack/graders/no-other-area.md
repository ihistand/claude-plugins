---
type: tool_used
tool: Read
input_match: '"file_path"\s*:\s*"[^"]*features/api\.md"'
min: 0
max: 0
---

The change is in the import area, so the run never reads the other area's file,
`features/api.md`. The pack carries what the change needs from outside its area.
