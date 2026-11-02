---
description: Record an error in the PRD's errors.md, diagnose it, propose its class for the user to confirm, and fix it from a failing test through /prd-change and /prd-build (prd-toolkit)
---

Handle an error through the PRD's ledger. Arguments, `[<E-nnn> | <run id> | <text>]`: $ARGUMENTS

1. Invoke the prd-toolkit:handling-errors skill first. Its first instruction is a Read of
   `${CLAUDE_PLUGIN_ROOT}/skills/handling-errors/running-an-error.md`, whole (no offset, no
   limit): make it your next tool call. Run no command, read no code and edit no file before it.
2. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
3. An `E-nnn` resumes that entry at the step its state names (the procedure's **Where to
   enter**). A deploy run id (`YYYYMMDDTHHMMSSZ-…`) names the entry whose `Detected:` line holds
   it (Grep it in `errors.md`); a run with no entry yet (a failed run not closed, or a killed
   step) goes to `/prd-deploy <run id>` first, whose close records the entry. Any other text is
   the user's report of a new error: step 1, with it as the evidence. With no arguments, list the
   open entries and ask which one, or what went wrong.
4. Follow `${CLAUDE_PLUGIN_ROOT}/skills/handling-errors/running-an-error.md` exactly, steps 1 to 6,
   and report as its step 6 says. You never fix code yourself, and the request is never the
   confirmation: only the user's reply to the proposal is.
