---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/[^"]*/test-cases/[^"]*"[\s\S]*\b(?:is clear|reads well|easy to follow|is good|is helpful|is appropriate|is user-friendly)\b'
min: 0
max: 0
---

No test-case file is written holding a judgement word ("is clear", "reads well", ...): a rubric item no quote
can prove. The same words anywhere else in a test-case file fail it too, which a test case never needs.
