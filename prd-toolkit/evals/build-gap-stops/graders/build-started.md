---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:prd-toolkit:)?building-from-prds"'
min: 1
---

The build is started with the building-from-prds skill, so a later changing-prds call is a stop and
not a plain change request. Graders cannot check order; "after the build starts" is pinned by the
skill text (Stops: a PRD gap goes to `/prd-change`) and its pytest pin.
