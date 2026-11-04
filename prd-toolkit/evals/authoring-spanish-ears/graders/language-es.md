---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/[^"]*/prd\.md"[\s\S]*\\nlanguage: es\\n'
min: 1
---

`prd.md` is written with the frontmatter line `language: es`, so lint reads its ACs with the Spanish table.
