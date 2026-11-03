---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/[^"]*/features/[^"]*"[\s\S]*- AC-\d+\.\d+ (?:When|While|If|Where|The) '
min: 0
max: 0
---

No features file is written with an AC that opens with an English opener (`When`, `While`, `If`, `Where`,
`The … shall`): D2's failure line.
