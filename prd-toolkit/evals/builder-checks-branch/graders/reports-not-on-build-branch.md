---
type: regex
pattern: 'QUESTIONS[*:\s`-]*worktree is not on the build branch'
target: last_message
---

The report's QUESTIONS field opens with `worktree is not on the build branch`: the current branch is `base`, not the
prompt's `Branch: prd-round/notes-1`. Bold, a colon, a backtick, or the field's line break and a bullet may sit between
the two; any other word before the phrase fails.
