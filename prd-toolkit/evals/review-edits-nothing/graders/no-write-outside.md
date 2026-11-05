---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"(?![^"]*(?:\.prd-review\.json|\.prd-dry-run-))[^"]*"'
min: 0
max: 0
---

No Write of any file but `.prd-review.json` and the tester's dry-run directory.
