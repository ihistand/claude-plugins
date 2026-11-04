---
type: tool_used
tool: Read
input_match: '"file_path"\s*:\s*"[^"]*docs/guide/install\.md"'
min: 0
max: 0
---

Nobody reads the guide: the tester's guard keeps it out of the tester's reads (it is neither the PRD folder
nor a test root), and the caller that reads it is grading it ("The guide may not pass: …", seen in a run whose
skill never fired). The score is `prd_judge.py`'s.
