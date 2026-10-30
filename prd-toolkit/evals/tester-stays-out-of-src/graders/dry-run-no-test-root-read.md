---
type: tool_used
tool: Read
input_match: '"file_path"\s*:\s*"(?:[^"]*/)?tests/(?!\.prd-dry-run-)'
min: 0
max: 0
---

A dry run reads only the PRD folder and its own dry-run directory: no Read of a file under the
test root `tests/` outside `tests/.prd-dry-run-*`.
