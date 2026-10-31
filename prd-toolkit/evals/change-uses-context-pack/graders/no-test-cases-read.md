---
type: tool_used
tool: Read
input_match: '"file_path"\s*:\s*"[^"]*test-cases/api\.yaml"'
min: 0
max: 0
---

The run never reads the other area's test cases, `test-cases/api.yaml`. The area's own file,
`test-cases/import.yaml`, is not covered: the dry-run tester of step 3 reads it to write its tests
(these graders see subagent calls too), so a read of it is not a pack bypass.
