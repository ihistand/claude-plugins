---
type: tool_used
tool: Bash
input_match: 'prd_change\.py\S* ids next'
min: 1
---

The new requirement's ID comes from `prd_change.py ids next`, not from a count by hand. `\S*` lets a quoted
script path through (`prd_change.py\" ids next` in the call's JSON).
