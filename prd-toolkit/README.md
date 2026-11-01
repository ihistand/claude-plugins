# prd-toolkit

A living PRD as the single authority agents build, test and deploy from: a PRD folder in the
repo with contracts and black-box test cases, a 32-rule linter and trace checks, a test agent
that cannot read your code, skills to author, adopt and change it, and a builder that takes an
approved change to verified code, and a deploy script that takes verified code to a running
environment. Version 0.5.0.

Design: [docs/superpowers/specs/2026-10-29-prd-toolkit-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-design.md),
for 0.2 [docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md),
for 0.3 [docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md](../docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md),
for 0.4 [docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md](../docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md),
and for 0.5 [docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md](../docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md).

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
- `--list-rules` prints the 32 rules. `--sample-tids N` prints up to N randomly chosen T-ids for the authoring
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

- A `test-<level>` job runs the whole harness command, so it stays red while any case is
  `known-failing` on an open `E-nnn`, until 0.6.
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
command>`, so a compound command (`cd tools && bash gate.sh`) sees both variables. Both start by
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
- `check`: the run is another PRD's run, or its log names no PRD folder, as its only line; every
  other exit 1 of `check` prints close-check findings.

Exit 2 (usage error, nothing run), with the reason printed:

- `plan` or `run`: an `--until <env>` whose cut would take a production step along (a step on
  `<env>` after a production one), unless `<env>` is production itself;
- `rollback`: a second rollback of the same step, or a rollback of a step that is not the run's
  failed step or has no `Rollback:`;
- `confirm`: another PRD's run, or another `prd_deploy` command working on this run; a step that
  already has a `confirm` record, or that is not the human step the run stopped at; or an empty
  reply.

`run`, `resume` and `rollback` hold a repository-wide lock while they run commands; a run stopped
at a human step holds none, and `plan`, `check` and `confirm` take none.

A failed step exits 4 and prints its `Rollback:` command; the script never runs it unasked.

**Known limit.** The script cannot prove that a person wrote a `confirm` reply. The skill requires
the user's own message, verbatim, the log keeps it, and the close report quotes it, but a `confirm`
reply is trusted to be the user's. Steps run in a shell on the session's machine with its
credentials; the toolkit adds no sandbox.

## Assumption status `awaiting <who>`

An assumption row in section 12 has status `open`, `confirmed`, `corrected` or `awaiting <who>`,
where `<who>` is a named person (`awaiting Sam Rivera`; a bare `awaiting` is a violation).
`awaiting <who>` is for intent only that person can confirm. Unlike `open`, it does not block
approval and may stay while the PRD is Approved. Adoption uses it for requirements whose intent
the user cannot state.

## Changelog

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
