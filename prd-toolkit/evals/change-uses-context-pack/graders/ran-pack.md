---
type: tool_used
tool: Bash
input_match: 'prd_context\.py'
min: 1
---

The change starts from the context pack: a Bash call runs `prd_context.py`. Graders cannot check
order, so "before the first PRD edit" is pinned by step 1 of the changing-prds skill text (and its
pytest pin), not here.
