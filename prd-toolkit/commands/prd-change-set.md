---
description: Coordinate one change across linked PRDs in several repositories - one change-set record, one approval for every PRD diff, and the builds in dependency order (prd-toolkit)
---

Coordinate a change across repositories. Arguments, `[<CS-nnn> | <text>]`: $ARGUMENTS

1. Invoke the prd-toolkit:coordinating-prds skill first. Its first instruction is a Read of
   `${CLAUDE_PLUGIN_ROOT}/skills/coordinating-prds/running-a-change-set.md`, whole (no offset, no
   limit): make it your next tool call. Run no command, read no code and edit no file before it.
2. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
3. A `CS-nnn`, or with no arguments a current branch `cs-<nnn>-<slug>`, resumes that record at
   the step its Status names (the procedure's **Where to enter**). Any other text is a new change:
   step 1, with it as the change. With no arguments and no change-set branch, list the records
   under `changes/` that are not `done` or `abandoned`, and ask which one, or what to change.
4. Follow `${CLAUDE_PLUGIN_ROOT}/skills/coordinating-prds/running-a-change-set.md` exactly, steps
   1 to 6, and report as its step 6 says. The toolkit pushes, merges and opens nothing, and the one
   approval is the user's reply to every member's PRD diff.
