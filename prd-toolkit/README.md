# prd-toolkit

A living PRD as the single authority agents build, test and deploy from: a PRD folder in the
repo with contracts and black-box test cases, a 36-rule linter and trace checks, a test agent
that cannot read your code, skills to author, adopt and change it, and a builder that takes an
approved change to verified code, a deploy script that takes verified code to a running
environment, an error ledger that carries every failure from record to a checked fix, and a
publisher that renders the PRD as one page to share, and change sets that link PRDs across
repositories. Version 0.7.1.

Design: [docs/superpowers/specs/2026-10-29-prd-toolkit-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-design.md),
for 0.2 [docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md),
for 0.3 [docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md](../docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md),
for 0.4 [docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md](../docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md),
for 0.5 [docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md](../docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md),
for 0.6 [docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md](../docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md),
for 0.7 [docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md](../docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md),
and for 0.7.1 [docs/superpowers/specs/2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md](../docs/superpowers/specs/2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md).

## Install

```
/plugin marketplace add ihistand/claude-plugins
/plugin install prd-toolkit@ihistand
```

Restart Claude Code. To update an installed copy, run `claude plugin update prd-toolkit@ihistand`,
then `/reload-plugins` (or restart). The scripts run with `uv` (https://docs.astral.sh/uv/); each declares its own
dependencies (`pyyaml`, `sqlglot`, `openapi-spec-validator`) inline. A missing dependency prints an
install hint and exits 2.

## Commands and skills

| Command | Skill | Use |
|---|---|---|
| `/prd-new [slug]` | `prd-toolkit:authoring-prds` | Interview to a PRD folder `docs/prd/<slug>/`, lint it, dry-run it with prd-tester, approve it, install the CLAUDE.md block |
| `/prd-adopt [area]` | `prd-toolkit:adopting-prds` | Bring an existing repo under a PRD one area at a time, from the code, with the user's word on each requirement |
| `/prd-change <description>` | `prd-toolkit:changing-prds` | Change the PRD first, with new IDs and a version bump, before any code |
| `/prd-context [area] [IDs] [implement]` | `prd_context.py` | Print the focused context pack for one task: the decide pack, or with `implement` the implement pack |
| `/prd-build <area> <IDs>` | `prd-toolkit:building-from-prds` | Take approved requirements to verified code: `prd-builder` works in its own worktree while `prd-tester` writes the tests in its `write` mode; the build reconciles by quote and moves statuses `approved`, `built`, `verified` with no version bump |
| `/prd-status` | `prd_status.py` | Show where each requirement stands, and the version each environment runs |
| `/prd-deploy [--until <env>] [<run id>]` | `prd-toolkit:deploying-from-prds` | Deploy a verified PRD through its runbook with `prd_deploy.py`, stopping at every human step and failure, then record the run (see Deploying) |
| `/prd-error [<E-nnn> \| <run id> \| <text>]` | `prd-toolkit:handling-errors` | Record an error in `errors.md` with `prd_error.py`, diagnose it, propose its class and wait for the user's confirmation; the fix starts from a failing test and goes through `/prd-change` and `/prd-build --fixes E-nnn`, and the close is checked with `prd_error.py check` |
| `/prd-publish [<out file>] [<request>]` | `prd-toolkit:publishing-prds` | Render the PRD with `prd_publish.py` as one self-contained HTML page (a Business and a Technical tab), with per-area summaries by Claude that cite their IDs; the page goes outside the PRD folder, is never committed, and is offered as a private Artifact when the session has the Artifact tool |
| `/prd-change-set [<CS-nnn> \| <text>]` | `prd-toolkit:coordinating-prds` | Coordinate one change across linked PRDs in several repositories: one record, one approval for every member's PRD diff, then a build (and where a link needs it, a deploy) per repository in dependency order (see Change sets) |

## Lint CLI

```
uv run --script .prd-toolkit/prd_lint.py docs/prd/<slug>   # a repo with hooks installed
uv run --script prd-toolkit/scripts/prd_lint.py --list-rules
uv run --script prd-toolkit/scripts/prd_lint.py docs/prd/<slug> --sample-tids 3
```

- **Which copy to run.** A person's shell does not set `${CLAUDE_PLUGIN_ROOT}`, so the commands here
  name a path. In a repo whose hooks are installed, run the vendored copy,
  `.prd-toolkit/<script>.py`. Before the first install (no `.prd-toolkit/` yet) run the plugin's
  install path, `~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/<script>.py`, where `ihistand` is this marketplace's name and
  `<version>` is the installed version (`claude plugin list` shows it, and so does
  `ls ~/.claude/plugins/cache/ihistand/prd-toolkit/`). A checkout of this repo works too, as the
  other two lines do.
- Output is one line per violation: `<file>:<line>: <rule>: <message>`.
- Exit 0 when clean, 1 on violations, 2 on usage, dependency or internal error.
- `--list-rules` prints the 36 rules. `--sample-tids N` prints up to N randomly chosen T-ids for the authoring
  dry run, one per line with the test-case file that holds it (`T-003.1 test-cases/nfr.yaml`), never a `level: unit` case; it exits 1 with `prd_lint: no non-unit T-ids to sample`
  when the PRD has none.

## Adopting an existing repo

`/prd-adopt [area]` runs the `adopting-prds` skill. It bootstraps `docs/prd/<slug>/` (first run
only), then takes one area at a time, an area being `features/<area>.md` plus
`test-cases/<area>.yaml`, bounded by the file globs in its Boundary cell. Progress is the adoption
map in `adoption.md`, and each area moves forward one state at a time:

`not started` → `extracted` → `confirmed` → `adopted`

- **extracted:** requirements are written as `as-built`, each with a `Source: <file>:<line> @<commit>`
  line. Apparent bugs become open `E-nnn` entries in `errors.md`, never requirements.
- **confirmed:** only on the user's word on each requirement and each `E-nnn`. Silence or "looks
  fine overall" confirms nothing, and with no answer the area stays `extracted`.
- **adopted:** only after a `prd-tester` suite where every T-id is `pass` or `known-failing E-nnn`,
  plus lint, the checklist, a dry run, `prd_trace.py` and the user's approval. Adoption changes no
  code. The first adopted area takes the PRD to `1.0.0`; each later area is a minor bump.

### Confirming through the form

Step 3 of adoption confirms an area through a local form, not a list of questions in the chat:

```
uv run --script .prd-toolkit/prd_confirm.py serve docs/prd/<slug> --area <area> [--summaries F] [--port N] [--no-open] [--idle-minutes N]
uv run --script .prd-toolkit/prd_confirm.py status docs/prd/<slug> --area <area>
```

- `serve` builds the area's items: the as-built requirements, the open `E-nnn` entries that touch the
  area, the area's section 13 questions, and the contract `[NEEDS CLARIFICATION]` markers the area
  names. It serves them on `127.0.0.1` behind a random token and prints
  `url=http://127.0.0.1:<port>/?token=...` as its first line. `--summaries` takes a JSON object of
  item ID to a short text that cites its own ID; `--port` fixes the port (in use, or any other bind
  error: exit 2); `--no-open` does not open the browser; `--idle-minutes` (default 120) ends an idle
  server. Two items under one ID are refused (exit 2).
- The page, `templates/confirm/form.html`, is one self-contained file that loads nothing. It shows one
  item at a time with the list on the left. Keys: C confirms, R corrects, B marks a bug, S asks, and
  the arrows move between items.
- Each answer is saved as it is given to `.prd-confirm-<area>.json` at the repo root, with the item's
  `where` and `served` text. Before anything else, `serve` adds the line `/.prd-confirm-*.json` to
  `.git/info/exclude`, once. An item whose text changed since it was answered counts as open again.
- `serve` ends with exit 0 when Done: every item answered and none changed since. It ends with exit 2 for
  a usage error or a refusal, with `prd_confirm: <why>` on stderr, and with exit 3 when stopped without
  Done (Ctrl-C, SIGTERM or the idle time).
- `status` prints `<answered>/<total>` and one `open <ID>` line per open item, and exits 0 when it
  prints and 2 on error.
- Without a browser, the fallbacks are `AskUserQuestion` and then the checklist file. A headless run
  leaves the area `extracted`, as before.

## Testing from the PRD

The `testing-from-prds` skill and the `prd-tester` agent write and run tests from the PRD folder
alone: it has never seen the code and must not look for it. A dry run writes tests for sampled
T-ids to a dry-run directory without running them; a suite writes tests to the test roots that
`testing.md` names and runs the harness commands. Every test carries an `@prd <T-id>` citation,
and the report lists QUESTIONS, TESTS, HARNESS CHOICES, FILES READ and, for a suite, RESULTS.
Dispatch it as a subagent (the Agent tool), not with `claude --agent`.

**Guard hook.** `hooks/hooks.json` registers `scripts/prd_tester_guard.py` as a PreToolUse hook
on Read, Glob, Grep, Write, Edit, NotebookEdit and Bash. It acts only when the hook's
`agent_type` is `prd-tester` (or ends with `:prd-tester`); every other session passes through.
For the tester it allows reads only of the PRD folder, the scratchpad and the test roots, writes
only to the scratchpad and the test roots (the PRD is read-only), and Bash only for the
`testing.md` harness commands (one simple command each) plus `ls`, `mkdir` and `uv run python -m py_compile`. It never fails open: with `testing.md`
missing or unparsable, only Read, Glob and Grep under the PRD folder are allowed.

**Limit.** The guard confines the tester's tool calls, not the processes the harness runs. A
`conftest.py` the tester writes can touch any file when pytest runs it. So callers run an
integrity check after each dispatch (a before and after snapshot of `git status`, the PRD folder's file list
and a tree of the working files), as in `skills/testing-from-prds/dispatching.md`. The hook runs
`python3`: under Python 3.7 or 3.8 it blocks the tester (and only the tester), but with no
`python3` on the PATH the hook exits 127, which Claude Code treats as non-blocking, so the guard
fails open.

## Trace CLI

`prd_trace.py` checks the PRD against the repo's tests and commits. It reads the test roots from
`testing.md` (falling back to `tests/`) for `@prd T-nnn.n` citations.

```
uv run --script .prd-toolkit/prd_trace.py docs/prd/<slug>
uv run --script prd-toolkit/scripts/prd_trace.py docs/prd/<slug> --range BASE..HEAD
```

| Rule | Finding |
|---|---|
| `t-implemented` | a T-id is cited by no test: a unit or build-gate T-id of a `built`, `verified` or `as-built` requirement, or any T-id of a `live` one (in an adopted area, where the PRD has an adoption map). `approved` requirements are skipped; a level with no Gate row counts as build |
| `test-cites-live` | a test cites a T-id that does not exist in the PRD or belongs to a removed requirement |
| `commit-refs` | with `--range`, a commit touches a file inside an adopted Boundary and has no `Refs:` trailer (`Refs: none (no behaviour change)` counts) |
| `status-current` | a requirement's status claims a test that nothing cites: a `built` block's unit T-id, a `verified` block's unit or build-gate T-id, or any T-id of a `live` block |

Where the PRD has an adoption map, `t-implemented` and `status-current` cover `adopted` areas
only. Output and exit codes match lint: `<file>:<line>: <rule>: <message>`; exit 0 clean, 1 on
findings, 2 on a usage, dependency or internal error. A malformed `--range` exits 2.

## Hooks and CI

`prd_hooks.py` vendors the toolkit's scripts into `.prd-toolkit/` and installs two git hooks:
`commit-msg` (a commit touching the Boundary needs a `Refs:` trailer naming live PRD IDs) and
`pre-commit` (each `enforced` standards row runs its linter on the staged files its glob
matches). It never overwrites an existing hook and never sets `core.hooksPath`; in either case it
prints the line to add.

The first install runs from the plugin's install path (see Lint CLI for how to find it); then commit `.prd-toolkit/` so every
clone and CI run the same copy:

```
uv run --script ~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/prd_hooks.py install docs/prd/<slug>
```

Git does not clone hooks, so each other clone runs the vendored copy once (the managed CLAUDE.md
block says so):

```
uv run --script .prd-toolkit/prd_hooks.py install docs/prd/<slug>
```

Generate the merge-gate CI file, then commit it. `--github` writes
`.github/workflows/prd-toolkit.yml`; `--gitlab` writes `.gitlab/prd-toolkit.yml` and prints the
`include: '.gitlab/prd-toolkit.yml'` line to add to `.gitlab-ci.yml`. An existing file that
differs is rewritten only with `--force`.

The generated `prd-lint` job runs `prd_lint.py --ci` and then `prd_hooks.py check --ci`, which reports
`stale: <path>: re-run prd_hooks.py ci --<forge> --force` when the PRD has since gained a level, an
environment, a `tests` step or a Drift row. `check` and `/prd-status` print the same line.
Outside a git checkout `check --ci` exits 2 (`prd_hooks: <path> is not inside a git checkout`), and
`/prd-status`'s CI part says the same.

```
uv run --script ~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/prd_hooks.py ci --github docs/prd/<slug>
uv run --script ~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/prd_hooks.py ci --gitlab docs/prd/<slug>
```

After a plugin upgrade, `check` names every vendored file that differs from the plugin (exit 1);
run `install` from the plugin again to refresh the copy, and commit it. `uninstall` removes only
the hooks it wrote and leaves `.prd-toolkit/`:

```
uv run --script ~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/prd_hooks.py check docs/prd/<slug>
uv run --script .prd-toolkit/prd_hooks.py uninstall docs/prd/<slug>
```

The hooks and every CI job need only `uv`: CI runs on a bare runner, so each standards linter
and each build-gate Levels harness command must run there too (for example `uv run ...`). A hook
blocks the commit when `uv` is missing, and skips with a message on a branch that has no
`.prd-toolkit/` or no PRD folder.

Known limits:

- A case that is `known-failing` on an open `E-nnn` is a strict expected failure that tags its
  citation, so known-failing tests mark themselves and a `test-<level>` job stays green while the
  bug is open.
- A `commit --amend` that only rewrites the message stages no file, so the `commit-msg` hook lets
  it through; CI's `commit-refs` (trace with `--range`) catches it.

## Deploying

`/prd-deploy [--until <env>] [<run id>]` runs the `deploying-from-prds` skill. It takes `verified`
code to a running environment by running the `operations.md` runbook with `prd_deploy.py`: every
step from 1, in order, never from the middle. A script runs the commands, not the model. The skill
shows the plan, relays the user's reply to each human step, offers a failed step's rollback, and
at the end writes only what the run's log proves: the `## Deployed` rows, `verified` → `live (since
X.Y.Z)` after a production finish, and an open `E-nnn` for each failure. Then it commits that close
and runs `prd_deploy.py check`. A deploy changes no behaviour, so it bumps no version.

**The runbook.** Each step is a numbered line followed by labelled lines:

```
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `./deploy.sh production`
   Check: `curl -fsS https://orders.example.com/health` prints `ok`
   Rollback: `./deploy.sh production --previous`
```

- The step line is `N. <title> (actor: agent|human) (env: <environment>)`; steps are numbered from 1
  without gaps.
- An agent step has `Run:` (one backticked command, or `tests <level>[, <level>...]`), a `Check:`
  (one backticked command, optionally followed by ``prints `<text>` ``, which must equal one stdout
  line) and an optional `Rollback:`. A `tests` step has no `Check:`: the suite, run against that
  environment, is its check. `tests` levels are the Levels in `testing.md`, including the
  `smoke` level.
- A human step has `Do:` and `Check:`, both prose. It is where a person's approval is given: the run
  stops there until the user replies, and `confirm` records the reply verbatim. The request to
  deploy is never that reply.
- **The production gate.** The first production step must be a human step, or come after one. Lint
  fails a runbook without it (`production-gate`); there is no opt-out. Environments has a
  `Production` column (`yes` or `no`) that says which environment is production.

**`## Deployed`** is the PRD's record of what each environment runs: a table of environment, PRD
version, commit, date and run id, one row per environment, written at a run's close and replacing
that environment's earlier row. **`## Drift`** is an optional table of environment, check
(`version` or `config`) and an introspection command; `prd_drift.py <prd-dir> [--env <env>]` runs
each command and compares what it prints with the Deployed row (`version`) or with
`contracts/config.yaml` (`config`). It exits 0 for no drift, 1 for drift (each finding is
`operations.md:<line>: drift-<check>: <what>`) and 2 when a command failed, timed out or printed
something unparseable, which is never counted as drift.

```
uv run --script .prd-toolkit/prd_drift.py docs/prd/<slug> --env production
```

**CI.** `prd_hooks.py ci` adds a `drift-<env>` job only for an environment with rows in
`## Drift`, and a `test-deploy-<env>` job only for one that a `tests` step runs on: the
deploy-gate suites the runbook runs there, each line `export PRD_ENV=<env> TEST_ENV=<env>; <harness
command>`, so the harness command (one simple command, such as `bash tools/gate.sh system`, as the
Levels rule requires) sees both variables. Both start by
hand (`workflow_dispatch` on GitHub, `when: manual` on GitLab), stay out of the merge gate, and
never deploy; deploying is done from a session.

**What `prd_deploy.py` refuses.** Exit 1 (`refused`), with each reason printed:

- `run`: the tracked working tree is dirty; `prd_lint` or `prd_trace` finds anything; any
  requirement is still `built` (a deploy starts from `verified`); the run reaches a production
  environment while a `verified` requirement has a deploy-gate T-id that no test cites (it could
  never go `live`); or another `prd_deploy` command is running in this repository;
- `resume`: the run is another PRD's run (`run <id> is for <folder>, not <folder>`), or its log
  names no PRD folder (written before the header named it); HEAD or the PRD version moved since
  the run started, the tree changed, or the runbook changed (`operations.md` or `testing.md`); the
  run has no step records, is done, or did not stop at a human step, or the step it stopped at is
  not a human step of the runbook; the run's human step has no `confirm`, or its `confirm` was
  already used; a step started and did not finish (a killed or timed-out call); the run failed,
  since a failure ends the run and `resume` never goes past it; or another `prd_deploy` command
  is working on this run or running in this repository;
- `rollback`: the run is another PRD's run, or its log names no PRD folder; HEAD or the PRD
  version moved since the run started, the tracked tree is dirty, or the runbook changed; or
  another `prd_deploy` command is working on this run or running in this repository;
- `recover`: the run is another PRD's run, or its log names no PRD folder; the step has no
  unfinished `start` (`step <N> has no unfinished start in run <id>`) or already has a result
  (`step <N> already has a result in run <id>`); or another `prd_deploy` command is working on
  this run or running in this repository;
- `check`: the run is another PRD's run, or its log names no PRD folder, as its only line; every
  other exit 1 of `check` prints close-check findings.

Exit 2 (usage error, nothing run), with the reason printed:

- `plan` or `run`: an `--until <env>` whose cut would take a production step along (a step on
  `<env>` after a production one), unless `<env>` is production itself;
- `rollback`: a second rollback of the same step, or a rollback of a step that is not the run's
  failed step or has no `Rollback:`;
- `confirm`: another PRD's run, or its log names no PRD folder, or another `prd_deploy` command working on this run; a step that
  already has a `confirm` record, or that is not the human step the run stopped at; or an empty
  reply;
- `recover`: no log for the run, or an empty reply.

`recover --run <id> --step <N> --reply "<the user's words>"` ends a step killed between its `start`
and its result, once the user has checked the environment: it logs the reply and a failed step
(`recovered: no result after start`, never a pass) and ends `prd-deploy: failed step=<N> run=<id>`,
exit 4, so `rollback` and the close work as for any failed run.

`run`, `resume` and `rollback` hold a repository-wide lock while they run commands; a run stopped
at a human step holds none, and `plan`, `check` and `confirm` take none. `recover` runs no command
but takes the same repository lock and the run's lock while it writes.

A failed step exits 4 and prints its `Rollback:` command; the script never runs it unasked.

**Known limits.** The script reads the runbook's steps and hashes `operations.md` and `testing.md` a
moment apart; an edit to either in the window between reading the runbook steps and hashing them is
not caught. The script cannot prove that a person wrote a `confirm` reply. The skill requires
the user's own message, verbatim, the log keeps it, and the close report quotes it, but a `confirm`
reply is trusted to be the user's. Steps run in a shell on the session's machine with its
credentials; the toolkit adds no sandbox.

## Handling errors

`/prd-error` (skill `prd-toolkit:handling-errors`) takes any error, a bug, a failing test, an
incident or a failed deploy, from a record to a checked fix. `errors.md` holds one `### E-nnn`
entry for each; `prd_error.py` is the only writer.

1. **Record.** `new` appends the entry as `unclassified` with its `Detected:` line and a bounded
   `Evidence:` (20 lines at most, no secret or classified value). A build or deploy that stops on a
   failure records its entry itself.
2. **Reproduce.** The failing test comes first; an error that does not reproduce gets a diagnosis
   that starts `not reproduced:` and says what was tried.
3. **Propose.** `propose` writes the class (`code bug`, `spec gap`, `invalid requirement`,
   `environment` or `standard`) and a diagnosis. Nothing is final yet.
4. **Your confirmation.** `confirm` records your reply verbatim, in your words, and the class you
   settle on. Only a confirmed entry can be cited by code (`Refs: E-nnn`); the commit-msg hook and
   `prd_error.py check` refuse a code commit that cites an unconfirmed one.
5. **Fix.** A change goes through `/prd-change` (citing the entry), and `/prd-build --fixes E-nnn`
   builds it from the entry's failing test.
6. **Resolve and check.** `resolve` writes the resolution (`<T-id> [<level>], PRD <X.Y.Z>, fixed in
   <commit>`; `<T-id or ->, PRD <X.Y.Z>, run <run id>`; or `not a defect: <why>`), then
   `prd_error.py check <base>..<head>` validates every change to the ledger in the range.

```
uv run --script .prd-toolkit/prd_error.py new docs/prd/<slug> --title "<title>" --source "<where seen>"
uv run --script .prd-toolkit/prd_error.py propose docs/prd/<slug> E-nnn --class "<class>" --diagnosis "<root cause>" [--touches FR-001,FR-002] [--recurrence E-mmm]
uv run --script .prd-toolkit/prd_error.py list docs/prd/<slug> --open
uv run --script .prd-toolkit/prd_error.py check docs/prd/<slug> <base>..<head>
```

**Known-failing tests.** A case marked `known-failing` on an open entry is a strict expected failure
that tags its citation `@prd T-nnn.n known-failing E-nnn`; it fails the day the bug is fixed, so the
marker cannot outlive the defect. The trace's `known-failing-tags` rule reports a case with no tagged
citation and a tag whose entry is resolved or unknown.

**A killed deploy step.** `prd_deploy.py recover` ends a step killed between its `start` and its
result, once you have checked the environment (see Deploying); the run then fails as any failed run
does, and the failure close records the entry.

**What `prd_error.py` refuses.** Exit 1 (`refused`), with each reason printed:

- `new`: a `Touches:` ID the PRD does not define, or evidence over 20 lines;
- `propose`: an entry that is `confirmed` (its class is settled) or `resolved`, a
  `Recurrence of:` that is not an entry, or a `--touches` ID the PRD does not define;
- `confirm`: an `unclassified`, already `confirmed` or `resolved` entry;
- `resolve`: an entry that is not `confirmed`, or is already resolved, or a `--t` with no test case or level;
- `new`, `propose`, `confirm` and `resolve`: a value that would open a code fence (an `Evidence:` line,
  or a title, diagnosis, reply or reason, whose first non-space characters are ```` ``` ```` or `~~~`),
  which would end the ledger's parse (`refused: Evidence: line <n> would open a code fence; drop it or
  put text before it`, or `refused: --reply would open a code fence; …`);
- `new`, `propose`, `confirm` and `resolve`: a write that would add a lint finding located in
  `errors.md` (`refused: the entry would fail lint: <file>:<line>: <rule>: <message>`, one per finding,
  then the hint `put quoted output in backticks`); `errors.md` is left byte-identical. Lint's prose
  rules skip `Evidence:` and `Confirmed:` lines, and `schema-refs` skips `errors.md`, so quoted output
  belongs in `Evidence:` bare and in backticks elsewhere;
- any command naming an `E-nnn` that is not an entry; and `check`, whose exit 1 prints findings, one
  per line, as `errors.md: E-nnn: <finding>`.

Exit 2 (usage error, nothing written): an empty reply, class, diagnosis, title or source; `unclassified` as a
class; a malformed version, T-id, run id or commit (7 to 40 lowercase hex digits); a fix without its
T-id, level or commit (`a fix needs a T-id, its level and a commit`); `--not-a-defect` combined with
another resolution; an unreadable range or PRD folder.

## Publishing

`/prd-publish [<out file>] [<request>]` (skill `prd-toolkit:publishing-prds`) renders the PRD with
`prd_publish.py` as one self-contained HTML page with a Business tab and a Technical tab. The page
loads nothing (no script, stylesheet, font or image from any URL), so it opens offline, by email or
on an intranet; PRD text is rendered from markdown with raw HTML escaped, and the error ledger
appears without its `Evidence:` lines.

**Summaries.** The skill writes a short plain-language summary of each area (600 characters at most,
in the language you ask for), and the page shows it in a box labelled `Summary by Claude of
FR-001–FR-004, PRD <version>` that cites its IDs. Summaries are written fresh for each publish and
never stored in the PRD folder.

**Where it goes.** The page is written outside the PRD folder, to the path you name (default
`./<project>-prd-<version>.html` in the repository root, untracked; the summaries file is written
beside it and deleted after the render), and is never committed; the skill reports its absolute
path. An untracked page stops the next `/prd-build` at its clean-tree check, so move it out of the
repository or delete it first. When the session has the Artifact tool,
the skill offers the same file as a private Artifact, or updates one you name; otherwise, or when you
decline, it gives you the file path.

`prd_publish.py` is not vendored into `.prd-toolkit/`; it runs from the plugin (see Lint CLI for the install path).

```
uv run --script ~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/prd_publish.py render docs/prd/<slug> --out <file> [--summaries <json>]
```

**What `prd_publish.py` refuses.** Exit 1 (`refused`): an `--out` inside the PRD folder; a summary
whose version is not the PRD's, whose area does not exist, whose ID is undefined or belongs to
another area, or whose text is over 600 characters; a summaries file that is not an object with version and areas (`summaries: must be an object …`), an area that is not an object with text and ids, or `ids` that are not a list of requirement IDs (`… ids must be a list of requirement IDs`). Exit 2 (usage error, nothing written): not a PRD
folder, an unmigrated `adoption.md`, an unreadable summaries file, or an output path that cannot be
written.

## Links

A PRD may link to the PRDs of other repositories. `links.md` (optional, in the PRD folder) holds an
Upstreams table (the PRDs this one uses, each with a Location, a lock of Version and Commit, and a
`Needs` of `verified` or `live in <env>`) and a Consumers table (the PRDs that use this one). A PRD
without `links.md` is unchanged.

A downstream PRD cites an upstream item with a prefix, `<kind>:<prd>/<name>` in a test case target
or a `Traces:` line (`cli:greet/greet`, `table:transform/orders_daily`) and `<prd>/<table>.<column>`
in prose. The kinds that cross are `op`, `table`, `event`, `job` and a custom type whose files are
YAML mappings; `code:` never does. `prd_links.py sync` copies the cited items, and only those, into
`contracts/upstream/<prd>/` as a pinned snapshot, and lint, trace, the tester and context packs read
that snapshot offline. Never edit it by hand.

```
uv run --script .prd-toolkit/prd_links.py add docs/prd/<slug> <location> [--needs <value>]
uv run --script .prd-toolkit/prd_links.py sync docs/prd/<slug> <upstream> [--ref <ref>]
uv run --script .prd-toolkit/prd_links.py check docs/prd/<slug> [--ref <ref>] [--ci]
uv run --script .prd-toolkit/prd_links.py impact docs/prd/<slug> [--base <ref>]
```

`check` compares each snapshot item with its upstream (`same`, `changed`, `removed`), reads each
consumer's snapshot of this PRD the same way, and checks that both sides list the link. `impact` lists
the contract items the working tree changes and the consumers that cite them. A git URL location is
read with your own git credentials, cached under `${XDG_CACHE_HOME:-~/.cache}/prd-toolkit/links/`, and
bounded by a 60-second timeout (`PRD_LINKS_TIMEOUT`); the commands never prompt.

**What `prd_links.py` refuses.** Exit 1 (`refused: <why>` on stderr, or drift on stdout): a location
that holds another PRD than the row names, a PRD linking to itself, a cited item that is not in the
upstream (nothing is written), an item of `contracts/asyncapi.yaml` (not citable across repositories),
and drift in `check` or a consumer that cites a changed item in `impact`. Exit 2: a usage or tool error
with nothing on stdout (`prd_links: <why>` on stderr), git that cannot run in any command among them, and
a refusal or failure of `impact` itself, so its exit 1 always means a consumer cites a changed item. Exit 3 (`check` and `impact` only): nothing drifted but a side was unreachable.
`check --ci` exits 0 where `check` would exit 3, after printing the unreachable line; the generated
`prd-lint` job runs it, so CI catches a break only where the other side is reachable. The deploy
pre-flight refuses to start on exit 1 and reports exit 3. `/prd-status` shows the verdict counts for
path locations and `check: not run` for a git URL.

Four lint rules (36 in all) read `links.md`, the snapshot and the records without leaving the
repository: `links-format`, `upstream-refs`, `snapshot-cited` and `change-sets`.

## Change sets

A change to a contract item that another PRD cites cannot stop at one repository. `/prd-change-set
[<CS-nnn> | <text>]` (skill `prd-toolkit:coordinating-prds`) runs it as one change set:

1. `impact` finds the consumers; you confirm the members; `prd_links.py changeset new` writes
   `docs/prd/<slug>/changes/CS-nnn.md` in the starting repository, with each member's Order, Waits for
   and Target. An unreachable consumer is never skipped.
2. Each member's PRD is edited in Order on the branch `cs-<nnn>-<slug>` (the same in every member), and
   each downstream member syncs from the edited upstream branch.
3. One approval: every member's PRD diff is shown together, and one reply approves the set. The record
   quotes it; an amendment is approved alone.
4. Each member builds in Order once its Waits for holds, through `/prd-build`, with the
   `Change-set: <prd>/CS-nnn` trailer on its commits; an upstream is deployed through `/prd-deploy
   --until <env>` first when a downstream link needs it. Its pre-flight, and `check --ci` (the
   generated `prd-lint` job), let drift between two members of the open change set through, printing
   `drift allowed by <start-prd>/CS-nnn: <line>`; other drift still refuses or fails, and a plain
   `check` still reports it.
5. A failed build, a human step without a reply or an error stops the chain. The stop is on the
   record's Status and in its Log, and a new session resumes from the record alone.
6. `changeset close` writes the Merge order, upstream first. Nothing is pushed, merged or opened as a
   pull request; you land each member.

The record is written only by `prd_links.py changeset`. A dry run and a build dispatch agents bound to
the session's own repository, so they run in a session started in that member's root: expect one resume
per member, each a `/prd-change-set CS-nnn` from that root. Record writes, `impact`, `sync`, `check` and
deploys run for any member from any session.

A headless run registers only `prd-toolkit:<command>` (a bare `/prd-status` is not listed, as probed in
0.7 on Claude Code 2.1.316): invoke `prd-toolkit:prd-change-set` and the other commands in that form.

## Known limits (0.7.1)

- The form has one owner at one machine: the server is local, and the answers are trusted to be that
  owner's.
- A plain-words correction is turned into acceptance-criteria text by the session after Done, not by
  the form.
- Only adoption step 3 uses the form; other confirmations keep their commands.

## Known limits (0.7)

- A git URL location is read with your own credentials; CI without them gets exit 3, so CI catches a
  break only where the other side is reachable.
- An upstream sees a consumer's citations only through that consumer's committed snapshot.
- Only the kinds named under Links cross repositories. A non-YAML custom type and an item of
  `contracts/asyncapi.yaml` cannot be cited across.
- Every member must be cloned on the machine running the change set, and a dry run or build of a member
  runs in a session started in that member's root.
- An approval is trusted to be yours, as `prd_error.py confirm` is.
- While a change set is open, a reachable member's plain `check` reports the other member as drift
  until both land; `check --ci` lets it through while the record is open (Status not `done` or
  `abandoned`, visible from the checkout).

## Known limits (0.6)

- The strict expected-failure marker is held by instruction; the trace reads the tag, not each
  runner's syntax.
- A confirmation is trusted to be the user's, as `prd_deploy.py confirm` is.
- `recover` never marks a step done.
- `Evidence:` holding no secret or classified value is held by instruction; nothing scans it.
- Mermaid diagrams on the published page are shown as source, and the page's own labels are English.
- The window between reading the runbook steps and hashing them is not covered (see Deploying).

## Assumption status `awaiting <who>`

An assumption row in section 12 has status `open`, `confirmed`, `corrected` or `awaiting <who>`,
where `<who>` is a named person (`awaiting Sam Rivera`; a bare `awaiting` is a violation).
`awaiting <who>` is for intent only that person can confirm. Unlike `open`, it does not block
approval and may stay while the PRD is Approved. Adoption uses it for requirements whose intent
the user cannot state.

## Changelog

- **0.7.1:** `prd_confirm.py` and `templates/confirm/form.html`: adoption step 3 confirms an area's as-built requirements, open errors, questions and clarification markers through a local form, with answers saved as they are given (see Adopting an existing repo). `AskUserQuestion` and the checklist file remain the fallbacks. Upgrading from 0.7.0: re-run `prd_hooks.py install`, which vendors `prd_confirm.py` and `confirm/form.html` into `.prd-toolkit/`. No PRD needs an edit.
- **0.7.0:**
  - `/prd-change-set` and the `coordinating-prds` skill: `links.md`, the pinned snapshot `contracts/upstream/<prd>/` and `prd_links.py` (`add`, `sync`, `check`, `impact`, `changeset`) link PRDs across repositories; one record, `changes/CS-nnn.md`, drives a change with one approval and a build per repository in dependency order (see Links and Change sets).
  - Four lint rules (`links-format`, `upstream-refs`, `snapshot-cited`, `change-sets`; 36 in all). `commit-refs` checks the `Change-set:` trailer. The generated `prd-lint` job runs `check --ci`, and the deploy pre-flight runs the link check. The interview asks about packaging.
  - Upgrading from 0.6: re-run `prd_hooks.py install` (it vendors `prd_links.py`) and `prd_hooks.py ci` (the `prd-lint` job gains `check --ci` when `links.md` exists). The managed block's wording changed, so re-run `prd_block.py` after upgrading: the vendored block templates are stale until then, and `prd_block.py --check` reports each CLAUDE.md block stale. A PRD without `links.md` needs no edit.
- **0.6.1:** `/prd-publish` writes again. 0.6.0 put the page and the summaries file under `.git/`, where Claude Code refuses writes, so nothing rendered. The page's default is `./<project>-prd-<version>.html` in the repository root again, untracked and never committed. The summaries file is written beside it and deleted after the render. Move the page out of the repository or delete it before the next `/prd-build`, whose clean-tree check stops on an untracked file.
- **0.6.0:**
  - `/prd-error` and the `handling-errors` skill: `errors.md` entries gain a canonical line order (`Detected:`, `Classification:`, `Confirmed:`, `Touches:`, `Evidence:`, `Diagnosis:`, `Resolution:`, `Recurrence of:`) and `prd_error.py` (`new`, `list`, `propose`, `confirm`, `resolve`, `check`) is their only writer. The linter gains `error-entries` (its 32nd rule) and the trace gains `known-failing-tags` (its fifth rule). A code commit may cite only a confirmed entry (see Handling errors).
  - Known-failing tests mark themselves as strict expected failures and tag their citation. A stopped build records an entry, and `/prd-build --fixes E-nnn` builds a fix from it. `prd_deploy.py recover` ends a killed step. The generated `prd-lint` job also runs `prd_hooks.py check --ci`, which reports stale CI.
  - `/prd-publish` and the `publishing-prds` skill: `prd_publish.py` renders the PRD as one self-contained HTML page (see Publishing).
  - Upgrading from 0.5: re-run `prd_hooks.py install` (it vendors `prd_error.py`) and `prd_hooks.py ci` (the `prd-lint` job gains `check --ci`). The managed block's text changed in 0.6, so every existing repo's `prd_block.py --check` reports its CLAUDE.md block stale until `prd_block.py` is re-run. An existing `known-failing` case needs a tagged citation: the trace's `known-failing-tags` reports it until `/prd-error E-nnn` takes its entry to the code-bug route, whose tester round marks the test a strict expected failure and tags its citation (the case and its `approved` block need no patch). An open 0.5 entry that carries a class now counts as `proposed`, so a code commit citing it is refused until `prd_error.py confirm` records your reply (`/prd-error E-nnn` asks for it). Existing entries need no edit: the new lines are optional, `error-entries` judges `Detected:` and `Recurrence of:` only on an entry that carries `Confirmed:`, and `check` judges only ranges. A `.prd-toolkit/` without `prd_error.py` predates 0.6, and the skills stop on it until `prd_hooks.py install` runs.
- **0.5.0:**
  - `/prd-deploy` and the `deploying-from-prds` skill: `prd_deploy.py` runs the `operations.md` runbook, every step from 1 in order, and stops at each human step and on each failure. The model never types a runbook command; it relays each reply verbatim, records a failure in `errors.md`, and closes with Deployed rows and `verified` → `live (since X.Y.Z)` (see Deploying).
  - The runbook is a step grammar: `(actor: …) (env: …)` and the labels `Run:`, `Check:`, `Rollback:`, `Do:`. Environments gains a `Production` column. `operations.md` gains `## Deployed` and `## Drift`.
  - `prd_drift.py` compares what an environment runs with what the PRD says (`version` and `config`).
  - A `smoke` level in `testing.md`. Five lint rules: `runbook-steps`, `runbook-env`, `production-gate`, `runbook-tests` and `drift-rows`.
  - Generated CI adds manual `drift-<env>` and `test-deploy-<env>` jobs, outside the merge gate; they never deploy. `/prd-status` shows each environment's deployed version.
  - The README's shell commands name a real path (`.prd-toolkit/<script>.py`, or the plugin's install path for the first install) instead of `${CLAUDE_PLUGIN_ROOT}`, which a shell does not set.
  - After upgrading the plugin, run `prd_hooks.py install` from it again, so `.prd-toolkit/` gains `prd_deploy.py`, `prd_drift.py`, `prd_block.py` and the block template (`templates/claude-block.md`), then `prd_hooks.py ci` again for the manual deploy jobs. Until then `prd_hooks.py check` reports the stale copy.
  - Upgrading a 0.4 PRD: lint fails `runbook-steps` until each runbook step carries `(env: …)` and its labels, and `runbook-env` until Environments has a Production column; a patch bump with the §14 row `format: runbook steps (prd-toolkit 0.5)`. `## Deployed` and `## Drift` are optional. The 0.4 runbook and its 0.5 form:

    ```
    ## Runbook

    1. Deploy the build with `./deploy.sh staging`, then run the system tests. (actor: agent)
    2. Deploy to production with `./deploy.sh production` after the owner approves. (actor: human)
    ```

    ```
    ## Runbook

    1. Deploy to staging (actor: agent) (env: staging)
       Run: `./deploy.sh staging`
       Check: `curl -fsS https://orders-staging.example.com/health` prints `ok`
       Rollback: `./deploy.sh staging --previous`
    2. System tests on staging (actor: agent) (env: staging)
       Run: tests system, e2e
    3. Approve production (actor: human) (env: production)
       Do: read the staging results and reply "deploy production"
       Check: the reply says "deploy production"
    4. Deploy to production (actor: agent) (env: production)
       Run: `./deploy.sh production`
       Check: `curl -fsS https://orders.example.com/health` prints `ok`
       Rollback: `./deploy.sh production --previous`
    5. Smoke on production (actor: agent) (env: production)
       Run: tests smoke
    ```

    The Environments table gains the column, `yes` on the production row and `no` on the others:
    `| Environment | URL | Production |`.
- **0.4.0:**
  - `/prd-build` and the `building-from-prds` skill: `prd-builder` works in its own worktree while `prd-tester` writes its tests in the new `write` mode; the build reconciles by quote. Statuses move `approved`, `built`, `verified` with no version bump; built blocks carry `Source:`.
  - `/prd-status` (`prd_status.py`) and `prd_build_check.py`.
  - `prd_hooks.py` vendors the scripts into `.prd-toolkit/` and installs `commit-msg` and `pre-commit` hooks. It never overwrites an existing hook and never sets `core.hooksPath`; with `core.hooksPath` set it writes no shim and prints the lines to add. A hook skips, with a message, on a branch with no `.prd-toolkit/` or no PRD folder (see Hooks and CI).
  - `prd_hooks.py ci --gitlab|--github` generates a merge-gate include file. `prd_lint.py --ci` skips the installed-skill and on-PATH checks of `registries` and keeps every Decision check.
  - The commit rule covers new projects and checks cited IDs (deletions and rename sources count).
  - `prd_trace.py` is gate-aware: `approved` blocks are skipped, `built`, `verified` and `as-built` blocks need citations for unit and build-gate T-ids, and `live` blocks for every T-id.
  - The Levels table in `testing.md` gains a `Gate` column (`build` or `deploy`). Upgrading a 0.3 PRD: lint fails `test-level` until the table has a Gate column (build or deploy), a patch bump.
  - Generated CI jobs install only `uv`, so each standards linter and Levels harness command must run on a bare runner (for example `uv run ...`). GitLab jobs run on merge-request pipelines.
- **0.3.0:** `/prd-context` and `prd_context.py` (decide and implement packs); `adoption.md`; `Touches:` in `errors.md`; `changing-prds` works from the pack. Upgrading a 0.2 PRD: it fails `sections` until §8's table moves to `adoption.md` and §8 reads `See adoption.md.`, a patch bump. The managed `CLAUDE.md` block's wording changed in 0.3: re-render it with `prd_block.py`; until then, `prd_block.py --check` reports it stale.
- **0.2.0:** `/prd-adopt` and `adopting-prds`; `testing-from-prds`, the `prd-tester` agent and its guard hook; `prd_trace.py`; the `awaiting <who>` assumption status. Upgrading a 0.1 PRD: it fails `sections` until its `testing.md` Harness has every slot, in order, and a `Test roots:` list.
- **0.1.0:** `/prd-new`, `/prd-change`, `prd_lint.py` (27 rules) and `prd_block.py`.

## CLAUDE.md block

`prd_block.py` writes the managed block that points agents at the PRD. It is deterministic, not
written by an agent.

```
uv run --script prd-toolkit/scripts/prd_block.py docs/prd/<slug> [--claude-md PATH] [--check]
```

`--check` reports whether the block is current without writing.

## Folder layout

```
docs/prd/<project>/
├── prd.md                  index: metadata, goals, glossary, registries, ID registry, changelog
├── features/<area>.md      FR blocks with EARS acceptance criteria and T-ids
├── test-cases/<area>.yaml  one entry per T-id
├── contracts/              openapi.yaml, schema.sql, events.md, errors.yaml, permissions.yaml,
│                           config.yaml, data-classification.yaml, dependencies/, fixtures/
├── nfr.md                  NFRs with numeric bounds
├── testing.md              levels, harness, environments, sign-offs
├── operations.md           environments, deploy and rollback runbook, Deployed and Drift tables
└── errors.md               the Error-Driven Development ledger

.prd-toolkit/               vendored scripts, version file and hook sources (written by prd_hooks.py install)
```

The exact syntax lint parses is `references/prd-format.md`. The starting files are in
`templates/prd/`.

## Tests and evals

```
uv run --directory prd-toolkit pytest -q
```

The plugin eval: run the command recorded in `evals/BASELINE.md` (0.2 baseline). The `--scaffold`
flag is required by the scaffolded cases, `Agent` lets the caller dispatch `prd-tester`, and the
pypi grants let `prd_lint.py` fetch its dependencies under the Bash sandbox:

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --json <out>.json --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

## Credits

Adapted from GitHub Spec Kit, cc-sdd, BMAD-METHOD, mattpocock/skills and Anthropic's
doc-coauthoring skill. See [NOTICE](./NOTICE).
