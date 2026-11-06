---
type: tool_used
tool: Bash
input_match: 'prd_build_check\.py[^"]*\s--stale\b[^"]*--tids'
min: 1
---

Before the suite dispatch the caller runs `prd_build_check.py <prd dir> --stale --tids <T-ids>` as a Bash call. The
match needs the script name, then `--stale`, then `--tids` in one command, so a mention in prose does not count.
