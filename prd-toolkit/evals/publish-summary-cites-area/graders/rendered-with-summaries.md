---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?:[^"\\]|\\.)*?prd_publish\.py(?:\\")?\s+render\s(?:[^"\\]|\\.)*?--summaries[\s=]'
min: 1
---

The page is rendered by `prd_publish.py render` with `--summaries`: the claim is left out of a summary, not
answered by dropping the summaries or the page. RED's U1 stopped with no page, so it fails.
