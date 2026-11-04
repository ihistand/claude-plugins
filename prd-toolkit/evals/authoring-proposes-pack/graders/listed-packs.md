---
type: tool_used
tool: Bash
input_match: 'prd_lint\.py\S* --list-packs'
min: 1
---

Phase 1 lists the packs on this machine before proposing one. D1's RED run never ran it.

`\S*` lets a quoted path's closing quote sit between the script and the flag: the first 0.8.0 run's with arm
ran `uv run --script "<plugin>/scripts/prd_lint.py" --list-packs`, which reaches the grader as
`prd_lint.py\" --list-packs`, and the first form of this pattern (`prd_lint\.py --list-packs`) missed it.
