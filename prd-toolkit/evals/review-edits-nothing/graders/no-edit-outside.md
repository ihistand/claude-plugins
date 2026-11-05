---
type: tool_used
tool: Edit
input_match: '"file_path"\s*:\s*"(?![^"]*(?:\.prd-review\.json|\.prd-dry-run-))[^"]*"'
min: 0
max: 0
---

Review mode edits nothing: no Edit of any file but `.prd-review.json` and the tester's dry-run directory
(these graders see subagent calls too).
