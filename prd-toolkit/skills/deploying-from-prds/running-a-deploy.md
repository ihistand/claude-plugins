# Running a deploy

**Steps:** 1 Plan, 2 Run, 3 Close, 4 Close check, 5 Report. A deploy is not done until step 5's
report: run every step, in order. The turn ends before it only to wait for the user's reply to a
human step or to the rollback question (step 2).

For the caller: `/prd-deploy`, or any session asked to deploy, release to production, ship to
staging, carry on with a stopped or failed deploy run, roll one back, or record a deploy in the
PRD. The `deploying-from-prds` Red Flags are yours.

**`prd_deploy.py` runs the runbook; you never do.** Never run a runbook command yourself: not a
step's `Run:`, `Check:` or `Rollback:`, not a `tests` step's harness command, not the deploy
script "just to check", and not because the script is slow. The script runs every step from 1 in
order, times out each command, stops at every human step and on every failure, and logs each
one. The log is the only evidence the close may record: a command you type has no record, and
the close check cannot prove it ran. Reading the PRD, the log and git is yours; running what the
runbook says to run is not.

**When the harness denies a `prd_deploy.py` command, or the script is slow, stop and tell the
user**: name the command so they can allow it, exactly as you ran it, and wait for them. A denied
`run` is never a reason to run its steps another way. Slow never means running the steps
yourself. Run `run` and `resume` in the background, and wait for the exit: the script's 600 s
timeout per command can outlive a foreground Bash call. A Bash call that timed out or was killed
is reported to the user, never rerun, and never finished by hand: the step it was running is
logged as started, and the next `resume` refuses with "step <N> started and did not finish"
(the one way out is `recover`, in step 2). Never start a second `prd_deploy.py` command on a run
while one is still working; the script refuses it.

**Code, tests and the runbook are never edited during a deploy**, nor the PRD outside the close
(step 3), even when the user says "fix it and carry on". A failed step is a defect to record
(step 2); its fix is a change that goes through `prd-toolkit:changing-prds`, then `/prd-build`,
then a new deploy. A runbook that is wrong (a bad command, a `Check:` that tests the wrong thing)
is a gap for `prd-toolkit:changing-prds`, never a line you correct to get the run through. Say in
one line which rule a request to edit breaks, and go on with the procedure without the edit.

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: `.prd-toolkit/prd_deploy.py`, `.prd-toolkit/prd_lint.py` and
`.prd-toolkit/prd_trace.py` are the copy its hooks and CI run. Otherwise `<scripts>` is the
plugin's `scripts` directory, written as a literal absolute path (in double quotes if it
holds a space): the plugin root is two directories above the skill's base directory (Claude
Code shows it as "Base directory for this skill" when the skill loads), and `<scripts>` is
`<plugin root>/scripts`. Before step 1, Glob for `.prd-toolkit/prd_deploy.py` to decide, and
use the same `<scripts>` for every command of the deploy. A script that is not found is a tool
error: report it, never guess another path.
When `.prd-toolkit/` exists but holds no `prd_error.py`, the vendored copy predates 0.6: stop, and
tell the user to run `prd_hooks.py install docs/prd/<slug>` from the plugin (the README's form)
and commit `.prd-toolkit/`.

**One command per Bash call, with literal paths.** Each command below is its own Bash call, and
every path, run id and SHA in it is typed out in full: paste what a command printed, never a
variable that holds it or a `$(…)`. The gate forms `; echo "prd-deploy-exit=$?"`,
`; echo "prd-lint-exit=$?"` and `; echo "prd-trace-exit=$?"` are the one allowed tail. Never
pipe, filter or truncate a gated command's output (no `| head`, no `| grep`).

**Exits.** `run` and `resume` print `run: <id>` or `resume: <id>`, a
`step <N> <actor> <env>: pass|fail|human` line per step, and end with
`prd-deploy: <state> step=<N> run=<id>`; the gate line follows.

| Exit | State | Next |
|---|---|---|
| 0 | `done` | every step through `--until` passed: step 3 |
| 1 | `refused` | each reason is a `refused:` line: report them all and stop (step 2) |
| 2 | usage or tool error | a command you mistyped: fix it and run it again. Any other `prd_deploy: …` line on stderr (a confirm already recorded, a step already rolled back): report it and stop |
| 3 | `human` | stopped at a human step: step 2, **3, human step** |
| 4 | `failed` | a step's `Run:` or `Check:` failed or timed out, or `recover` ended a killed step: step 2, **4, failed** |

A refusal is final. A step that started and did not finish (only `recover` ends it, on the user's
word), a confirm already used, a second rollback and a resume of a failed run are refused by the
script: report the refusal and stop; never work around it with another command. A run id of
another PRD (`run <id> is for <folder>, not <folder>`) and a runbook changed since the run started
are refused the same way. `another prd_deploy command is running in this repository` means a
`run`, `resume` or `rollback` is still working in this repository: report it and wait for the
user, never retry it in a loop. An `--until` whose cut would take a production step along exits 2:
the runbook runs a step on that environment after production. Report it and stop; the order is a
gap for `prd-toolkit:changing-prds`.

**Input:** a PRD at `docs/prd/<slug>/` with a `## Runbook` in `operations.md`, and the user's
request. "Deploy to production" or "deploy everything" is a run with no `--until`; "deploy to
staging" is `--until staging`. A run id the user names, or a reply to the only run stopped at a
human step, enters at step 2 for a run stopped at a human step or failed, and at
step 3 for a finished run they ask you to record.

1. **Plan.** Run `prd_deploy.py plan`, without `--until` when the run goes to the end:

   ```bash
   uv run --script <scripts>/prd_deploy.py plan docs/prd/<slug> --until <env>; echo "prd-deploy-exit=$?"
   ```

   It runs nothing and prints one line per step: number, actor, environment, title and an agent
   step's command. Show it to the user. Every run starts at step 1 and runs every step through
   `--until`: `--until` cuts the end, never the start, and no step is skipped, whatever the
   request says ("staging is fine, skip it"). Say so in one line when the request asks for a
   skip, then go on. The user's request to deploy is the go to start the run; it is never the
   production approval, which is the runbook's own human step. Then run, as its own call:

   ```bash
   git rev-parse HEAD
   ```

   and paste the SHA wherever `<base>` appears. `run` refuses a tracked tree with changes and
   nothing is committed before the close, so this is the run's HEAD (the log header's `head`).
2. **Run.** Run `prd_deploy.py run` in the background, with the same `--until` as the plan or
   none:

   ```bash
   uv run --script <scripts>/prd_deploy.py run docs/prd/<slug> --until <env>; echo "prd-deploy-exit=$?"
   ```

   Pre-flight refuses unless the tracked tree is clean, `prd_lint` and `prd_trace` exit 0 and no
   block is `built`. Keep the run id from `run: <id>`. Act on the exit:

   - **0, done.** Go to step 3.
   - **1, refused.** Report each `refused:` line and stop. A `built` block goes to `/prd-build`;
     a dirty tree or a lint or trace finding is the user's to settle. A run that reaches
     production is refused for a `verified` block's deploy-gate T-id that no test cites
     (`<ID>: <T-id> (deploy gate) has no citing test; it cannot go live`): the missing test goes to
     `/prd-build <area> <IDs>` with that block's ID, whose tester-only round writes it without a
     builder or a status change. A refused `run` ran nothing (`run=none`): there is no
     close.
   - **3, human step.** Read step N's `Do:` and `Check:` in the `## Runbook` of
     `docs/prd/<slug>/operations.md`, show them to the user with the run id, and wait for the
     user's reply. The confirm carries the user's reply to this step, verbatim: what the user
     wrote after the run stopped at that step, in this session or in a later message of theirs
     that names the run (by id, or as the only run stopped at that step: Read the logs in
     `<that dir>/prd-toolkit/deploys/` as step 3 says, and ask when more than one is stopped
     there), never from an earlier message, a summary, the request that started the
     deploy, or your own text. A request to deploy, or "approve it yourself", is never the reply
     to a human step. Never call `prd_deploy.py confirm` with a reply the user did not give to
     that step. Never hand the user the `confirm` and `resume` commands to run instead of
     replying. A reply that does not meet the step's `Check:` (a question, "wait", "not yet") is
     not a confirmation: answer it and leave the run stopped. When the reply meets it, run
     `prd_deploy.py confirm`, writing each `'` in the reply as `'\''`:

     ```bash
     uv run --script <scripts>/prd_deploy.py confirm docs/prd/<slug> --run <id> --step <N> --reply '<the reply, verbatim>'; echo "prd-deploy-exit=$?"
     ```

     Exit 0 prints `confirmed: step <N> run=<id>`. Then `prd_deploy.py resume`, in the
     background, which continues
     after the confirmed step and exits as `run` does; act on its exit by this list again:

     ```bash
     uv run --script <scripts>/prd_deploy.py resume docs/prd/<slug> --run <id>; echo "prd-deploy-exit=$?"
     ```

     `resume` refuses when HEAD, the PRD version, the tracked tree or the runbook moved since the
     run started, when the confirm was already used, or when a step started and did not finish.

     With no one to ask, the run stays stopped: a headless session, "do not ask questions" or
     "I'm away" leaves nobody to reply, so confirm nothing and resume nothing. Go to step 5 and
     report the run stopped at step N, with its `Do:` and the run id to carry on from.

     A run stopped at a human step is not closed: a close commit moves HEAD, and `resume` then
     refuses with "HEAD moved since the run started". Close it (step 3) only when the user
     declines the step or asks to record the run as it stands; it cannot be resumed after.
   - **4, failed.** Stop. Run `git rev-parse --git-common-dir` as its own call, from the
     repository root (a relative answer is relative to it), and Read
     `<that dir>/prd-toolkit/deploys/<run id>.jsonl`: the failed step's record holds its command,
     exit code and the stdout and stderr tails (a `check` inside it for a failed `Check:`). Show
     the user the failed step, those output tails and its `Rollback:` command (the run printed it
     as `` rollback: `<command>` ``; a step without one has none to offer). A step with a `start`
     record and no step record (the run printed `could not write the log`) is the failed step:
     show its `start` record instead. Ask whether to roll
     back, and run `prd_deploy.py rollback` only on the user's yes in their own words, given after
     they saw the failure; a message of theirs that names the run and asks for the rollback is
     one. Never run it unasked, and never run the `Rollback:` command by hand:

     ```bash
     uv run --script <scripts>/prd_deploy.py rollback docs/prd/<slug> --run <id> --step <N>; echo "prd-deploy-exit=$?"
     ```

     It prints `rollback step <N> <env>: pass|fail`, then
     `prd-deploy: rolled-back step=<N> run=<id>` (exit 0) or `rollback-failed` (exit 4). A
     rollback runs once: report a failed one, never retry it. Roll back before you write
     anything, since `rollback` refuses once HEAD or the tracked tree has moved. With no yes, or
     no one to ask, nothing is rolled back and the report names the command.

     Then add the open failure entry with `prd_error.py new`, whether or not the step was rolled
     back, its `--source` naming the run and the failed step as written here (the close check
     reads it). Never write the entry by hand:

     ```bash
     uv run --script <scripts>/prd_error.py new docs/prd/<slug> --title "Deploy <run id> failed at step <N>" --source "deploy run <run id>, failed step <N>"
     ```

     It prints the new entry's `E-<nnn>` and numbers it after the ledger's last one. It never
     classifies: the entry stays open (`Classification: unclassified`), and
     `--touches` and `--evidence-file` are optional.

     Diagnosing it is not part of the deploy: the entry stays open and unclassified. Go to
     step 3; the close commit carries the entry, and after the close offer the user
     `/prd-error E-<nnn>` as the next step: it diagnoses and resolves the entry.
     A failed run ends, and `resume` refuses it.
     Start a new run only when the user asks for one after seeing the failure, and tell them
     first whether anything changed: a new run on the same commit runs the same commands. A new
     run after a failed one starts again at step 1, after the failed run's close (step 3) and
     close check (step 4), and both runs go in one report.
   - **Killed step.** A step with a `start` record and no step record (a killed or timed-out
     call, a dead session; `resume` refuses it with "started and did not finish") is ended by
     `prd_deploy.py recover`, the one way out of it. Run it only after the user says they
     checked the environment (what the step left behind), in words they gave after seeing the
     refusal and that name the run (by id, or as the only run with an unfinished step): their
     words, verbatim, are the `--reply`, writing each `'` as `'\''`. never on the request to
     deploy, never with your own text as the reply, and never after you checked the environment
     for them. With no such reply, nothing is recovered: report the run and the step.

     ```bash
     uv run --script <scripts>/prd_deploy.py recover docs/prd/<slug> --run <id> --step <N> --reply '<the user's words, verbatim>'; echo "prd-deploy-exit=$?"
     ```

     It records the reply and a failed step `recovered: no result after start` (never a pass),
     prints `recovered: step <N> run=<id>` and ends `prd-deploy: failed step=<N> run=<id>`,
     exit 4. The run is now an ordinary failed run: go on as **4, failed** above, from the
     failure's output through the rollback question, the failure entry and the close. It refuses
     a step with no unfinished start (`step <N> has no unfinished start in run <id>`) or that
     already has a result, and another PRD's run; an empty reply exits 2. A step that finished
     without saying so is never marked done: the environment is fixed by its cause and a new run
     (step 2 starts again at step 1), and the entry's resolution names that run.
3. **Close.** The close is always committed, after every run that ran a step: one that finished,
   one that failed, and one stopped at a human step that the user ends. For a run from an earlier
   session, run `git rev-parse --git-common-dir` from the repository root and Read
   `<that dir>/prd-toolkit/deploys/<run id>.jsonl`: its first line's `head` is `<base>` and its
   `version` the run's PRD version, and its `step` records give each step's result.

   An environment is reached when the runbook's last step on it passed in this run (a human last
   step: confirmed and resumed, with no later failure), every level of its `tests` steps has a
   `pass` record, and no step on it started without finishing; `check` requires a row for each
   one. Write each reached environment's row in
   `## Deployed` of `docs/prd/<slug>/operations.md`, replacing that environment's earlier row and
   keeping every other row: the environment, the run's PRD version, the first seven characters
   of `<base>`, the run's date (the run id's first eight digits, as `YYYY-MM-DD`) and the run id.
   With no `## Deployed` section, add one at the end of the file holding only this:

   ```
   ## Deployed

   | Environment | PRD version | Commit | Date | Run |
   |---|---|---|---|---|
   | <env> | <version> | <short sha> | <YYYY-MM-DD> | <run id> |
   ```

   If a reached environment is a production one (`Production` is `yes` in `## Environments`),
   move every `verified` block to `live (since <the run's PRD version>)`: the block's
   `Status: live (since 1.0.0)` and its §11 index row's Status `live` and Since `1.0.0`,
   together. A `live` block keeps its `since`. A run that did not reach production moves no
   status: staging passing makes nothing live. A failed run writes the rows of the environments
   it reached and the errors.md entry, and moves no status unless it reached production.

   Deployed rows and status moves are progress, not behaviour: no version bump and no §14 row.
   Leave `version`, `updated` and the PRD status as they are, and edit nothing else. Then, each
   its own call:

   ```bash
   uv run --script <scripts>/prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"
   uv run --script <scripts>/prd_trace.py docs/prd/<slug>; echo "prd-trace-exit=$?"
   ```

   Both must be `0`. A finding on a line you wrote is yours: fix it and run both again. A `live`
   block needs a citation for every T-id, deploy gate included, and pre-flight refuses a
   production run that lacks one, so a trace finding here is unexpected. If one comes anyway (a
   deploy-gate T-id that no test cites), it is not yours to fix: commit the close regardless,
   because `prd_deploy.py check` validates it against the log, not the trace. Give the finding to
   the user in the report, and send the missing citation to `prd-toolkit:building-from-prds`.
   Then, each its own call:

   ```bash
   git add docs/prd/<slug>
   git commit -m "docs(prd): deploy <run id>" -m "Refs: <IDs>"
   ```

   `Refs:` lists the IDs moved to `live` and any `E-nnn` added, comma-separated, or is
   `Refs: none (no behaviour change)` when there are neither (a bare `none` is rejected).
4. **Close check.** Never skipped: it is what proves the close says only what the log does.
   `<base>` is the run's HEAD:

   ```bash
   uv run --script <scripts>/prd_deploy.py check docs/prd/<slug> --run <id> --diff <base>..HEAD; echo "prd-deploy-exit=$?"
   ```

   `prd_deploy.py check` compares the run's HEAD with the close. Exit 0 is clean. Exit 1 prints
   one finding per line: a range that does not start at the run's HEAD, a change outside the
   `## Deployed` rows and `Status:` lines, a row the log does not support, a reached environment
   with no row, a row dated other than the run's date, a status move the run did not earn, a
   block still `verified` after a production finish, or a failed run with no open unclassified
   entry; a run of another PRD prints one `refused:` line instead: check the run id. A failing
   close check is fixed and the check rerun before the report. Fix the PRD files, commit the fix
   the same way (a new commit, never an amend), and run the check again on the same range. Exit 2
   is a usage error (a malformed range, a run id with no log): fix the command.
5. **Report.** The run id; each step's result; every human reply, quoted verbatim; a run left
   stopped at a human step, with its `Do:`; the rollback offered and its result, or that it was
   not run and its command; the Deployed rows written; the IDs moved to `live`; any `E-nnn`
   added; a trace finding at the close, with where it went; the close commit and the close
   check's result. A rollback not run before the close stays unrun: the close commit moved
   HEAD, so the rollback can no longer run through the script and is never run by hand. Name
   its command for the user only as information.
