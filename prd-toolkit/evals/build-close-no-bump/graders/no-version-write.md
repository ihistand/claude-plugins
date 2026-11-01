---
type: tool_used
tool: Write
input_match: '^(?=.*"file_path"\s*:\s*"[^"]*docs/prd/[^"]*prd\.md")(?=.*"content"\s*:\s*"[^"]*\\nversion: (?!1\.1\.0\\n))'
min: 0
max: 0
---

No Write replaces a PRD's `prd.md` with a `version:` other than 1.1.0.
