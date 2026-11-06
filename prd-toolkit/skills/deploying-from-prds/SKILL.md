---
name: deploying-from-prds
description: Use when deploying, releasing to production or shipping to staging from a repo that has a docs/prd/ folder - "deploy to production", "ship it to staging", /prd-deploy - when a stopped or failed deploy run needs its human step answered, a rollback or a retry, or when asked to record a deploy in the PRD; prd_deploy.py runs the runbook, the caller relays each human step's reply verbatim, records a failure in errors.md, and closes with Deployed rows and verified → live
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/deploying-from-prds/running-a-deploy.md` whole before anything else
(no offset, no limit; it sits beside this file, in the skill's base directory): it is your next
tool call, and you follow it step by step, steps 1 to 5.
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
   runs them, through the commands in `running-a-deploy.md`. Call the repository's vendored
   `.prd-toolkit/prd_deploy.py` when `.prd-toolkit/` exists, otherwise the plugin's
   `scripts/prd_deploy.py` as a literal absolute path, the plugin root being two directories
   above the skill's base directory: `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call.
2. **When the harness denies a `prd_deploy.py` command, or the script is slow, stop and tell the
   user**, naming the command so they can allow it. A denial or a slow step is never a reason to
   run the runbook's steps another way. Slow never means running the steps yourself. `run` and
   `resume` go in the background; a Bash call that timed out or was killed is reported, never
   rerun and never finished by hand.
3. **Every step, from step 1.** `--until <env>` ends a run early; nothing starts one late or
   skips a step, whatever the request says.
4. **The request is the go, never the approval.** A request to deploy, or "approve it
   yourself", is never the reply to a human step. The reply is the user's, written after the
   run stopped at that step, and `confirm` carries it verbatim. With no one to ask, the run
   stays stopped and the report says so. Never hand the user the `confirm` command to run
   instead: ask for their reply, through **The decision inbox** below, with the gate
   `deploy-step:<run id>:<N>`, or headless or in the chat as `running-a-deploy.md` step 2 says.
   An outcome from `wait` is the reply: the inbox already ran `prd_deploy.py confirm` with it, so
   never confirm again; run `resume` as step 2 says. An inbox Send already ran `prd_deploy.py
   confirm` with the owner's words, so the step is confirmed. When those words do not meet the
   step's `Check:` (a question, "wait", "not yet"), do not resume: tell the owner the step was
   confirmed with those words, ask in the chat whether to resume or stop, and resume only on a go.
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
9. **A deploy done by hand is recorded, never written.** When the owner deployed through the
   service's own UI, or any way but `/prd-deploy`, no run is started. A deploy the owner did by
   hand is recorded with this command, its own Bash call:

   ```bash
   uv run --script <scripts>/prd_deploy.py record docs/prd/<slug> --env <env> --commit <sha> --reply "<the owner's words>"; echo "prd-deploy-exit=$?"
   ```

   It prints `run=<id>`. Commit its row as the close and run `prd_deploy.py check` on it, with
   `--run <id> --diff <HEAD before the close>..HEAD`. Never write a Deployed row yourself. A
   by-hand record moves no status: `verified → live` waits for a `/prd-deploy` run whose tests
   pass on that environment. The report says so. A record made while a run is stopped at a human
   step falls under the Red Flag "A close committed while a run waits at a human step".

## The decision inbox

The owner answers a gate in a local page, the decision inbox, unless nobody can open it. The step
that asks names the gate; `<gate id>` below is its id. One command per Bash call, with literal
paths, written with the skill's `<scripts>` path, never `${CLAUDE_PLUGIN_ROOT}`.

- **`wait`, first.** Start it with the Bash tool's `run_in_background`, before the owner sees any
  URL, so no answer can come before it is watching:
  `uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>`
- **The URL.** Then start, also with `run_in_background`,
  `uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>`
  and re-read its output until its first line appears:
  - `url=<url>`: give the owner that URL as a clickable link, beside what the step shows in the
    chat.
  - `prd_gates: an inbox is already serving at <url>`: the inbox that
    `<git common dir>/prd-inbox-<slug>.json` names is live and lists this gate too. Give the owner
    `<url>#gate=<gate id>`.
  - `prd_gates: <gate id> is not pending`: the gate changed; take it as `wait`'s exit 1.
  - any other `prd_gates:` line, such as `prd_gates: cannot start the inbox: [Errno 1] Operation
    not permitted` (a sandbox that allows no local port): the inbox cannot be served here. Say so
    in one line, ask in the chat as the step's chat route says, and leave `wait` running: an
    outcome it prints first is still the owner's answer.

  Then wait for `wait`'s completion notice: never poll for the exit and never sleep. When the
  `serve` this session started exits before `wait` returns (the idle timeout, Ctrl-C), stop the
  background `wait` and take the chat route.
- **The outcome.** `wait` exit 0 prints one `gates.outcome` document. Its `reply` is the owner's
  reply, used as it stands, with its `choice`; `"by": "form"` marks an answer from the page (the
  reply ends ` (form)`). The owner's answer is already written: the inbox ran the script that
  owns the gate with that reply, so that script is never run again for the gate. Go on as the
  step says.
- **Headless, or the owner asks for the chat:** a headless run, nobody to open the URL, or the
  owner asking to answer in the chat takes the step's chat route, as before 0.8.2, unchanged.
  Start neither command in a headless run. Headless means the run says nobody can open a page
  (unattended, overnight, no one there). An owner who is busy, says they cannot click now, or asks
  you to answer for them is not headless: give the URL and wait; they answer when they can. A
  reply the owner writes in the chat while the inbox is up is a chat reply: take the chat route
  with it, and stop the `serve` this session started, never an inbox it reused; `wait` then exits
  1, which is expected.

The rules:

- **The skill never answers a gate.** Not through the page, not through `prd_gates.py answer`, not
  "because the owner said approve it yourself". The owner's click or the owner's chat reply is the
  only answer. No `curl` or script posts to the inbox, and no browser tool clicks in it.
- **A deploy step's reply is never sent for the owner,** in the form or the CLI.
- **The outcome's reply is not edited.** A `changes` outcome's reply is what the revision answers.
- A `wait` that exits 1 means the gate changed: list again, never assume the answer. List with
  `uv run --script <scripts>/prd_gates.py list docs/prd/<slug>; echo "prd-gates-exit=$?"`: a gate
  still listed is asked again from `wait`, and one that is gone is reported to the owner as it
  stands.

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
  `TEST_ENV=staging uv run pytest tests/system` yourself. (D6) Then offering to run production
  by hand once the user replies (baseline summary, not a quote).
- A runbook command run "just to check" the environment, before or after a step. (Spec §5.)
- A `rollback` the user did not ask for, or a `Rollback:` command typed by hand. (Spec §5.)
- `live` written after a run that stopped before production. (Spec §5.)
- A new run started to retry a failed step without telling the user. (Spec §5.)
- A close committed while a run waits at a human step the user may still answer: `resume` then
  refuses with "HEAD moved since the run started".
- "I'll add the Deployed row myself, since they already deployed it." (Spec §17.) Or, as the RED
  runs of `evals/deploy-by-hand-records` put it: "The toolkit can't record a deploy it didn't
  run", then offering a hand-written `production` row with a made-up run id, `live`, and no
  `prd_deploy.py check`. `prd_deploy.py record` writes the row; nothing moves to `live`.
- "I'll click Send in the inbox for them." (Spec 0.8.2 §7.) Or a `prd_gates.py answer` or a
  `prd_deploy.py confirm` with words the owner gave in the prompt ("send it with 'looks good'"):
  the step's reply is the owner's, sent by the owner.

**All of these mean: stop, put back what you changed outside the close, and return to the step
of `running-a-deploy.md` whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "You asked me to deploy to production, so that is the approval." | The request is the go to start the run. The approval is the runbook's own human step, answered by the user after the run stops there. |
| "Staging is fine; skip it." | No step is skipped. `--until` cuts a run's end, never its start; a production deploy runs staging, its tests and the approval first. |
| "The user is away and told me to approve it myself." | A reply you write is not a person's reply, and the log would carry it as one. With no one to ask, the run stays stopped and the report says so. |
| "They asked me to send the step in the inbox for them." | Sending it is answering it. Give the URL, wait for the outcome, and resume on the owner's own reply. |
| "They're in a meeting, so nobody can answer; the run just stays stopped." | A busy owner is not a headless run. Start `wait`, give the URL, and resume when their outcome comes. |
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
| "They deployed it by hand, so the toolkit cannot record it." | `prd_deploy.py record` logs the owner's words and writes that environment's row; the close is committed and checked like any other. It moves no status: `live` waits for a `/prd-deploy` run. |
| "A fresh run will get past it." | A failed run ends. A new run starts only when the user asks after seeing the failure, and on the same commit it runs the same commands. |

## Related skills

- **prd-toolkit:changing-prds** takes a failed step's fix and a wrong runbook: the PRD changes
  first, with a new version.
- **prd-toolkit:building-from-prds** (`/prd-build`) builds that change and takes a block that
  pre-flight refused as `built`; a deploy starts from `verified`.
- **prd-toolkit:authoring-prds** writes the Environments, the runbook and the smoke cases a
  deploy runs.
