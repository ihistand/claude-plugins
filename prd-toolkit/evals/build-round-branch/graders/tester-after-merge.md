---
type: regex
pattern: '^(?:(?!"subagent_type":"(?:prd-toolkit:)?prd-tester")[\s\S])*"command":"git merge --ff-only prd-round/[\s\S]*"subagent_type":"(?:prd-toolkit:)?prd-tester"'
target: trace
---

The first prd-tester dispatch comes after the `--ff-only` merge of the round, and there is one: the tester's `write`
works in the same worktree, so it never runs beside the builder.
