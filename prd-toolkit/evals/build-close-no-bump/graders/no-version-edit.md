---
type: tool_used
tool: Edit
input_match: '^(?=.*"file_path"\s*:\s*"[^"]*docs/prd/[^"]*prd\.md")(?=.*"(?:old|new)_string"\s*:\s*"[^"]*\bversion: )'
min: 0
max: 0
---

No Edit of a PRD's `prd.md` (`docs/prd/<slug>/prd.md`) touches a `version:` line. A `version: ` in
other files, such as code, does not count.
