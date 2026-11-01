---
type: tool_used
tool: Edit
input_match: '"new_string"\s*:\s*"[^"]*Status: (?:verified|live)'
min: 0
max: 0
---

A build that stops on a PRD gap never closes `verified`, and never writes `live`. No Edit gives a
block `Status: verified` or `Status: live`. `built` is allowed: when the gap surfaces after the
builder's commit is merged (no worktree isolation in the eval harness, so the builder's commit is
already on the build branch), `running-a-build.md`'s **Stops** writes `built` for the block whose
unit T-ids pass, and the report says so. A stop before the merge writes no status.
