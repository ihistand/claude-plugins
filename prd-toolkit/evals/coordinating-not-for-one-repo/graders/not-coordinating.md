---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:prd-toolkit:)?coordinating-prds"'
min: 0
max: 0
arm: both
---

A change that touches no item another PRD cites is a single-repository change: coordinating-prds must not fire (changing-prds does).
