---
type: tool_used
tool: Bash
input_match: '(?:\bfor \w+ in\b|\b\w+ ?\(\) ?\{|\$\{?\w+\}?/).*prd_change\.py'
min: 0
max: 0
---

Each `prd_change.py` command is its own Bash call with its path typed out: no `for` loop, no shell function
(`nx() {`) and no variable in the path (`$S/prd_change.py`) in a call that runs it. The skill's own literal paths
(`.prd-toolkit/prd_change.py`, an absolute plugin path) do not match.
