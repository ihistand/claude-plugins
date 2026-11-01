---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:prd-toolkit:)?deploying-from-prds"'
min: 0
max: 0
arm: both
---

A deploy in a repo with no `docs/prd/` folder is not a PRD deploy, so deploying-from-prds must not fire.
