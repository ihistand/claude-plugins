---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/[^"]*/features/[^"]*"[\s\S]*- AC-\d+\.\d+ (?:Cuando|Mientras|Si|Donde|El|La|Los|Las) '
min: 1
---

A features file is written whose ACs open with a Spanish EARS opener or the ubiquitous `El/La … deberá` form.
