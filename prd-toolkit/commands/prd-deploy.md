---
description: Deploy a verified PRD through its runbook with prd_deploy.py, stopping for every human step and failure, and record the run as Deployed rows and verified → live (prd-toolkit)
---

Deploy through the PRD's runbook. Arguments, `[--until <env>] [<run id>]`: $ARGUMENTS

1. Invoke the prd-toolkit:deploying-from-prds skill first. Its first instruction is a Read of
   `${CLAUDE_PLUGIN_ROOT}/skills/deploying-from-prds/running-a-deploy.md`, whole (no offset, no
   limit): make it your next tool call. Run no command and touch no environment before it.
2. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
3. `--until <env>` passes to `prd_deploy.py plan` and `run` as written; an environment name
   alone (`staging`) means `--until staging`. With no `--until`, the run goes to the runbook's
   last step. A run id carries on with that run: step 2 for a run stopped at a human step or
   failed, step 3 for a finished run to record.
4. Follow `${CLAUDE_PLUGIN_ROOT}/skills/deploying-from-prds/running-a-deploy.md` exactly, steps 1
   to 5, and report as its step 5 says. You never run a runbook command yourself, and the
   request to deploy is never the reply to a human step.
