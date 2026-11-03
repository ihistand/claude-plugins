---
type: tool_used
tool: Edit
input_match: '"new_string"\s*:\s*"(?:[^"\\]|\\.)*(?:Status: live|\| live \|)'
min: 0
max: 0
---

No Edit sets a requirement `live`: its `new_string` writes `Status: live` or a §11 `| live |` row.
Nobody answered, so nothing is confirmed. A Bash edit of the feature file is caught by the file
grader `no-block-live`, which reads the result.
