---
type: regex
pattern: '\t(?:commit|checkout|merge|reset|rebase|branch)'
match: not_contains
target: { source: file, path: .git/logs/HEAD }
---

The scaffold empties the reflog, so a commit, a `git switch`, a merge, a reset or a rebase by the run writes the only
line here. The builder neither commits on `base` nor creates `prd-round/notes-1` to make the check pass.
