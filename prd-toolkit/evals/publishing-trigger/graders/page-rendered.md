---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?:[^"\\]|\\.)*?prd_publish\.py(?:\\")?\s+render\s'
min: 1
---

The page comes from the plugin's `prd_publish.py render`. Without the skill there is no such script in the
repo (the vendored copy has none), and RED's U2 ran a driver of its own (`/tmp/prdpub/render.py`), which
this grader does not count.
