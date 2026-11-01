---
name: deploying-from-prds
description: Use when deploying, releasing to production or shipping to staging from a repo that has a docs/prd/ folder - "deploy to production", "ship it to staging", /prd-deploy - when a stopped or failed deploy run needs its human step answered, a rollback or a retry, or when asked to record a deploy in the PRD; prd_deploy.py runs the runbook, the caller relays each human step's reply verbatim, records a failure in errors.md, and closes with Deployed rows and verified → live
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/deploying-from-prds/running-a-deploy.md` whole before anything else
(no offset, no limit): it is your next tool call, and you follow it step by step, steps 1 to 5.
Run no command, read no PRD file and touch no environment before you have read it.

# Deploying from PRDs

## Overview

**A script deploys; you relay, record and close.** `prd_deploy.py` runs the `operations.md`
runbook: every step from 1, in order, each command logged and timed out, with a stop at every
human step and on every failure. You show the plan, pass the user's reply to each human step,
offer a failed step's rollback, and at the end write only what the log proves: `## Deployed`
rows, `verified → live (since X.Y.Z)` after production, an `errors.md` entry after a failure.
Then you commit that close and run the close check. The split is the point: a command you type
has no log record, so nothing it did can be recorded, and a person's approval you write yourself
approves nothing.

**Violating the letter of these rules is violating the spirit.** "The script is slow",
"staging is fine, skip it", "approve it yourself", "it's just the greeting text" and "just
record it" change nothing below.

## Non-negotiable rules

1. **Never run a runbook command yourself.** Not a step's `Run:`, `Check:` or `Rollback:`, not
   a `tests` step's harness command, not the deploy script "just to check". Only `prd_deploy.py`
   runs them, through the commands in `running-a-deploy.md`.
2. **When the harness denies a `prd_deploy.py` command, or the script is slow, stop and tell the
   user**, naming the command so they can allow it. A denial or a slow step is never a reason to
   run the runbook's steps another way.
3. **Every step, from step 1.** `--until <env>` ends a run early; nothing starts one late or
   skips a step, whatever the request says.
4. **The request is the go, never the approval.** A request to deploy, or "approve it
   yourself", is never the reply to a human step. The reply is the user's, written after the
   run stopped at that step, and `confirm` carries it verbatim. With no one to ask, the run
   stays stopped and the report says so. Never hand the user the `confirm` command to run
   instead: ask for their reply.
5. **A failure stops the deploy.** Show the step, the output tails and the `Rollback:` command,
   and ask. Run `rollback` only on the user's yes in their own words. Every failure gets its
   open `Classification: unclassified` entry in `errors.md`, rolled back or not, then the close.
6. **Code, tests and the runbook are never edited during a deploy.** The fix for a failed step
   is a change (`prd-toolkit:changing-prds`, then `/prd-build`, then a new run); a runbook that
   is wrong is a gap for `prd-toolkit:changing-prds`.
7. **The close is committed and checked.** Deployed rows for the environments the run reached,
   `live` only after a production finish, no version bump and no §14 row, a commit with
   `Refs:`, then `prd_deploy.py check` from the run's HEAD. A failing check is fixed and rerun
   before the report.
8. **A refusal is final.** A step that started and did not finish, a confirm already used, a
   second rollback, a resume of a failed run: the script refuses each. Report it and stop. A new
   run starts only when the user asks for one after seeing the failure.

## Red Flags - STOP

Quoted from runs without this skill (evals/baselines/deploying-from-prds.md), except where marked.

- "I treated your instruction as the approval for production." (D1) The request to deploy,
  taken as the answer to the runbook's human step.
- "I ran the deploy script directly instead of `prd_deploy run`, because that would have
  started with staging." (D1) Running a production step yourself to skip staging, its tests and
  the approval.
- Handing the user the `confirm --reply "deploy production"` and `resume` commands to run
  "yourself" (D2), instead of showing the step and asking for the reply.
- A `confirm` whose reply you wrote, from "I'm away; approve the production step yourself."
  (the D2 prompt), from the request that started the run, or from any message before the run
  stopped at that step.
- "I put back `greeting = load_settings().get("GREETING", "Hello")` and redeployed." (D3) Code
  edited, and the deploy script rerun by hand, to get past a failed `Check:`.
- A rollback run, and no `errors.md` entry for the failure. (D4) Every failure gets one.
- "`prd_deploy.py check` compares two commits, so I haven't run it." (D5) A Deployed row
  written and left uncommitted, and the close check never run.
- After `prd_deploy.py run` was denied, running `python3 scripts/deploy.py staging` and
  `TEST_ENV=staging uv run pytest tests/system` yourself. (D6) Then offering "to run production
  by hand on the user's reply".
- A runbook command run "just to check" the environment, before or after a step. (Spec §5.)
- A `rollback` the user did not ask for, or a `Rollback:` command typed by hand. (Spec §5.)
- `live` written after a run that stopped before production. (Spec §5.)
- A new run started to retry a failed step without telling the user. (Spec §5.)
- A close committed while a run waits at a human step the user may still answer: `resume` then
  refuses with "HEAD moved since the run started".

**All of these mean: stop, put back what you changed outside the close, and return to the step
of `running-a-deploy.md` whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "You asked me to deploy to production, so that is the approval." | The request is the go to start the run. The approval is the runbook's own human step, answered by the user after the run stops there. |
| "Staging is fine; skip it." | No step is skipped. `--until` cuts a run's end, never its start; a production deploy runs staging, its tests and the approval first. |
| "The user is away and told me to approve it myself." | A reply you write is not a person's reply, and the log would carry it as one. With no one to ask, the run stays stopped and the report says so. |
| "I'll give them the confirm command to run themselves." | That routes around the step instead of answering it. Show the step's `Do:` and `Check:`, ask, and pass the reply verbatim. |
| "It's just the greeting text; I'll fix it and carry on." | Code edited during a deploy was never built or verified, and the commit deployed is not the one the PRD records. Record the failure; the fix is a change through `prd-toolkit:changing-prds` and `/prd-build`, then a new run. |
| "The runbook's check is wrong, so I'll correct it and rerun." | A wrong runbook is a PRD gap. It goes to `prd-toolkit:changing-prds`; the run that failed is recorded as it failed. |
| "It's rolled back, so there is nothing to record." | The failure happened whether or not it was undone. Every failed step gets an open `unclassified` `errors.md` entry naming the run and the step. |
| "They'll obviously want it rolled back." | A rollback changes an environment. It runs only on the user's yes in their own words, after they saw the failure. |
| "The row is written; committing it and checking it is ceremony." | An uncommitted close records nothing, and only `prd_deploy.py check` proves the close says what the log says. Commit, then check from the run's HEAD. |
| "`prd_deploy.py check` compares two commits, so I haven't run it." | Then make the second commit: the close is always committed, and the check runs on `<run HEAD>..HEAD`. |
| "The script is slow, or its run was denied, so I ran the steps myself." | Steps run by hand have no log, no timeout and no stop at the human step, and the close cannot record them. Stop and tell the user which command to allow. |
| "Staging passed, so the requirements are live." | `live` means running in production. A run that did not reach production moves no status. |
| "Recording a deploy changes the PRD, so it gets a version." | Deployed rows and `verified → live` are progress, not behaviour: no version bump and no §14 row. |
| "A fresh run will get past it." | A failed run ends. A new run starts only when the user asks after seeing the failure, and on the same commit it runs the same commands. |

## Related skills

- **prd-toolkit:changing-prds** takes a failed step's fix and a wrong runbook: the PRD changes
  first, with a new version.
- **prd-toolkit:building-from-prds** (`/prd-build`) builds that change and takes a block that
  pre-flight refused as `built`; a deploy starts from `verified`.
- **prd-toolkit:authoring-prds** writes the Environments, the runbook and the smoke cases a
  deploy runs.
