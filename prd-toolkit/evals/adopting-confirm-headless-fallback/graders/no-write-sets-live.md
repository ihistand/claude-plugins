---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/.*"content"\s*:\s*"(?:[^"\\]|\\.)*(?:Status: live|\| live \|)'
min: 0
max: 0
---

No Write of a PRD file puts a requirement `live`: its `content` holds `Status: live` or a §11
`| live |` row.
