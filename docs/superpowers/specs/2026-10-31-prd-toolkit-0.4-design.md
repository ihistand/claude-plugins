# prd-toolkit 0.4: building — design

> **Date:** 2026-10-31
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec), `2026-10-29-prd-toolkit-0.2-design.md`
> and `2026-10-30-prd-toolkit-0.3-design.md`. Where this addendum and any of them disagree, this
> addendum wins for 0.4.

> **Revisions.** Corrections from the implementation plan, which is their source
> (`docs/superpowers/plans/2026-10-31-prd-toolkit-0.4.md`), and from its final review:
> - §7 Installation: the hook shims are five lines, not two, and with `core.hooksPath` set install writes no shim.
> - §3.1: a non-empty QUESTIONS no longer always stops the build; a quoted test dispute is reconciled at step 6 and only a PRD gap stops it.
> - §3 step 7, §5 Trace and §11 (final review): trace is gate-aware. `t-implemented` skips `approved`
>   blocks; a `built`, `verified` or `as-built` block needs a citation for each unit and build-gate
>   T-id only (a level with no Gate row counts as build); a `live` block needs all. `status-current`
>   follows the same split. Without it, a deploy-gate T-id (0.4 writes none) or another `approved`
>   FR kept `verified` unreachable and the generated `prd-trace` job red.
> - §7 Installation (final review): the shims gain a sixth line. A shim, and the line printed for an existing hook, skips with a
>   message and exit 0 on a branch with no `.prd-toolkit/` copy or no PRD folder; the uv guard still
>   blocks when the copy is present. `install` also writes `.prd-toolkit/.gitignore`.
> - §8 and §12 (final review): job ids are sanitized, the GitHub workflow reads with
>   `permissions: contents: read`, and a `test-<level>` job red while a `known-failing` case exists
>   is a known limit until 0.6.

## 1. Scope

0.3 gives a task a focused pack. 0.4 takes an **approved PRD change to verified code**: a builder
writes the code and its unit tests from the `implement` pack while the black-box tester writes the
higher-level tests from the PRD alone; a caller reconciles the two against the PRD and moves the
requirements `approved → built → verified`. Hooks and CI keep commits and merges honest, and
`/prd-status` shows where every requirement stands.

0.4 delivers:
- the `building-from-prds` skill (the builder's role) and its caller procedure `running-a-build.md`;
- the `prd-builder` agent and the `/prd-build` command;
- a `write` mode for `prd-tester`;
- `prd_build_check.py`, the build's mechanical checks;
- `prd_status.py` and `/prd-status`;
- `prd_hooks.py`: the vendored scripts, the `commit-msg` and `pre-commit` hooks, and generated CI;
- the `Gate` column of `testing.md`'s Levels table, `Source:` for new code, and `status-current`
  for `built`.

It is **proven by** slice 1 of a new hello-world project: a ticket becomes an approved PRD, built
and verified through `/prd-build`, then changed and built again (section 10).

### Decisions

| Decision | Choice |
|---|---|
| Milestones | The base spec's 0.4 splits. **0.4 is building**; **0.5 is deploying** (`deploying-from-prds`, `prd-deployer`, staging and production CI jobs, `prd_drift.py`, `live`); **0.6 is error handling** (the base spec's 0.5) |
| New milestone | **0.7, multi-repo**: one repo's PRD cites another repo's PRD contract; a change spans PRDs with one approval and one build per repo, in dependency order. 0.3's one-PRD-per-repo rule stands |
| Release proof | A generic **hello-world** project replaces the notes scaffold as the release proof and grows each release: 0.4 ticket → PRD → build → verified; 0.5 deploy; 0.6 a planted bug; 0.7 a second repo. The notes scaffold stays for the eval cases |
| Platform proof | A platform wrapper plugin's own hello world, across that platform's repos and from its ticket tracker, gates the wrapper's 1.0. It is outside this spec |
| How a build runs | `running-a-build.md` runs it: builder and tester at once, a quote-based reconcile, then the status moves. superpowers `writing-plans` is optional, for splitting a large change into tasks that each run a build |
| Builder enforcement | No guard hook. The caller's post-round diff check fails a round that edits the PRD folder or a file citing a non-unit T-id |
| Script distribution | Vendored: `prd_hooks.py install` copies the scripts into `<repo>/.prd-toolkit/` with a `VERSION` file; hooks and CI run that copy. No package is published |
| Release vehicle | Branch `feat/prd-toolkit-0.4`, cut from `main` at `183a5d3`; version 0.4.0 in `plugin.json` and `marketplace.json` |

## 2. Components

| Unit | Job |
|---|---|
| `skills/building-from-prds/SKILL.md` | The builder's role: work from the `implement` pack; unit tests first; run the standards linters and the required registry skills; cite `Refs:` in commits; never edit the PRD or the tester's tests; report in a fixed format. A session not running as `prd-builder` is sent to `running-a-build.md` |
| `skills/building-from-prds/running-a-build.md` | The caller's procedure (section 3), the counterpart of `testing-from-prds/dispatching.md` |
| `agents/prd-builder.md` | `tools: Read, Glob, Grep, Write, Edit, Bash`; `skills: prd-toolkit:building-from-prds`. Dispatched with `isolation: worktree` |
| `commands/prd-build.md` | `/prd-build <area> <IDs>`: runs `running-a-build.md` for an approved change |
| `scripts/prd_build_check.py` | `--diff <base>..<head>` and `--results` (section 3.2) |
| `scripts/prd_status.py`, `commands/prd-status.md` | The status report (section 6) |
| `scripts/prd_hooks.py`, `templates/hooks/` | `install`, `check`, `uninstall`, `ci` (sections 7 and 8) |

Changed: `testing-from-prds` (the `write` mode), `dispatching.md` (the mode in its prompt),
changing-prds step 5 (its hand-off), the managed CLAUDE.md block, `prd-format.md` (Levels `Gate`,
`Source:` wording), lint `test-level`, trace `status-current` and `commit-refs`.

## 3. The build run (`running-a-build.md`)

**Input:** a PRD with status `Approved` and a lint exit of `0`; an area; the changed UJ, FR and NFR
IDs (or a bug fix's `E-nnn`, mapped to its requirements as the `implement` pack maps it), each
block at `approved`, or at `built` when a stopped build resumes.

1. **Preflight.** Lint exits `0`. The working tree is clean. On the repository's default branch,
   ask the user before branching. Split the changed blocks' T-ids into **unit** (the builder's)
   and **build-gate non-unit** (the tester's); deploy-gate T-ids are not run in 0.4.
2. **Snapshot**, as `dispatching.md` step 2.
3. **Dispatch both in one message.**
   - `prd-builder`, `isolation: worktree`, with this prompt and nothing else:
     ```
     Mode: build
     PRD: docs/prd/<slug>/
     Area: <area>
     IDs: <UJ, FR and NFR IDs>
     Unit T-ids: <one per line, with its test-case file>
     ```
     > Revised in prd-toolkit 0.5 (R21): the dispatch also carries a `Scripts:` line, the absolute
     > scripts directory, because `${CLAUDE_PLUGIN_ROOT}` is empty in Bash.
     It runs `prd_context.py … --for implement` itself, writes unit tests first, then the code,
     runs the standards linters and required skills, and commits in its worktree with
     `Refs: <IDs>`.
   - `prd-tester`, `Mode: write`, with the tester's T-ids (section 4).
   When the Agent tool offers no worktree isolation, dispatch the builder first and the tester
   after it returns, each followed by its step 4 check.
4. **Check the state.** Run `prd_build_check.py --diff <base>..<builder branch>` on the builder's
   commits; exit 1 fails the round. Run `dispatching.md` step 4 on the tester's changes. When both
   pass, merge the builder's branch and commit the tester's files with `Refs: <IDs>`.
5. **Run.** Dispatch `prd-tester`, `Mode: suite`, on the same T-ids. Check its RESULTS with
   `prd_build_check.py --results`; exit 1 fails the round.
6. **Reconcile** each `fail` line. Quote verbatim the test case's `ac:` line and its `expect`
   entry the failure concerns, then classify:

   | Class | Means | Next |
   |---|---|---|
   | code bug | the code contradicts the quote | a builder round with the failure line and the quote; the builder may now read the failing test |
   | test misread | the test contradicts the quote | a tester `suite` round with the quote |
   | PRD gap | the quote admits both readings, or is silent | **stop**: the gap goes to `/prd-change`; statuses stay as they are |

   A classification without its quote does not count. Each round repeats steps 4 and 5 for the
   agent that ran. After three rounds on one T-id the build stops and reports it to the user.
7. **Full run.** Run every build-gate Levels harness command. Every test passes except cases
   `known-failing` on an open `E-nnn`. `prd_trace.py` exits `0` (it asks a citation for each unit
   and build-gate T-id of a `built` or `verified` block; deploy-gate T-ids wait for `live`).
8. **Close** (section 5), then commit the PRD with `Refs: <IDs>`.

### 3.1 The builder's report

```
CHANGES     one line per file changed
UNIT        <T-id>: pass | fail: <one line>, one line per unit T-id
SOURCES     <ID>: <path>:<line>, one line per built block: where its implementation starts
QUESTIONS   each gap the PRD left; an empty list is written as `none`
COMMIT      the worktree branch and its commit SHAs
```

A QUESTIONS line of the form `<T-id>: test dispute: "<assertion>" vs "<quote>"` is reconciled by quote at step 6. Any other QUESTIONS line is a PRD gap and stops the build: `built` for blocks an earlier round merged, otherwise no status.

### 3.2 `prd_build_check.py`

```
prd_build_check.py <prd-folder> --diff <base>..<head>
prd_build_check.py <prd-folder> --results <report-file> --tids <T-id>[,<T-id>…]
```

`uv run --script` header, the shared `prdlint` model, and the gate line
`; echo "prd-build-check-exit=$?"`. Exit 0 clean, 1 findings (one per line), 2 usage or tool error.
- `--diff` reports each file in the range under the PRD folder, and each file in the range that
  cites (`@prd T-…`) a T-id whose test case is not `level: unit`, at either end of the range.
- `--results` reports a RESULTS line for a T-id not dispatched, a dispatched T-id with no line,
  and a line in none of the three forms. It reads the RESULTS block from the report file.

## 4. `prd-tester` `write` mode

| | Dry run | Write (new) | Suite |
|---|---|---|---|
| Writes tests to | the dry-run directory | the test roots | the test roots |
| Runs them | no; `py_compile` only | no; `py_compile` only | yes, with the Levels harness commands |
| Report | QUESTIONS, TESTS, HARNESS CHOICES, FILES READ | the same | the same, and RESULTS |

`write` exists because the build's tester cannot run its tests before the code exists. It reads
what a suite may read. The guard does not know the mode, so, as in a dry run, the rule not to run
the harness is held by instruction; the caller fails a `write` round whose report holds RESULTS.
`dispatching.md`'s prompt takes `Mode: write`. Suite mode then finds the tests already written and
runs them; it may revise one only on a test-misread round.

## 5. Statuses, gates and `Source:`

**Gate.** `testing.md`'s Levels table becomes `| Level | Harness command | Environment | Gate |`.
`Gate` is `build` (runs in a build's full run and in merge CI) or `deploy` (runs against a deployed
environment, 0.5). `test-level` reports a missing column with `testing.md Levels: add a Gate column
(build or deploy), new in prd-toolkit 0.4`, and a value other than the two. The migration is by
hand, a **patch** bump with a §14 row `format: Levels Gate column (prd-toolkit 0.4)`;
`prd-format.md` §9 gains the sentence. The template's rows are `unit`, `integration` and
`component` as `build`, and `system`, `e2e` and `acceptance` as `deploy`.

**Status moves**, written by the caller at close, in the block and its §11 index row together:

| Move | When |
|---|---|
| `approved → built` | the builder's commit is merged and every unit T-id of the block passes |
| `built → verified` | every build-gate T-id of the block passes in the full run and `prd_trace.py` exits `0` |
| `verified → live` | 0.5 |

A clean build writes `verified` directly. A build stopped after the merge leaves `built`. A status
move is progress, not behaviour: no version bump, no §14 row, no re-approval, and the PRD status
stays `Approved`.

**`Source:`** means where the code that implements a block is: provenance for an `as-built` block,
a pointer for a built one. At close the caller writes `Source: <path>:<line> @<short sha>` from each
SOURCES line, so the block's next `implement` pack holds its code. Lint keeps `Source:` optional
outside `as-built`.

**Trace.** Trace is gate-aware. `t-implemented` skips `approved` blocks (nothing is built yet); for a
`built`, `verified` or `as-built` block it asks a citation for each unit and build-gate T-id only,
and a T-id whose level has no Gate row counts as build, so trace fails closed; a `live` block needs
every T-id cited. `status-current` follows the same split and extends to `built`: a `built` block
whose unit T-id has no citing test is a finding, a `verified` block missing a unit or build-gate
citation is one, and a `live` block missing any citation is one. `commit-refs` (section 7) changes
with the hook.

## 6. `prd_status.py` and `/prd-status`

```
prd_status.py <prd-folder> [--json]
```

A read-only report; exit 0, or 2 on a usage or tool error. Deterministic. Parts, in order:
1. **Header**: path, version, PRD status.
2. **Requirements**: per area, the count of blocks by status.
3. **Adoption map**: the `adoption.md` rows, or `Not applicable: new project`.
4. **Not built**: `approved` blocks. **Not verified**: `built` blocks.
5. **Open errors**: each open `E-nnn` with its title and `Touches:`.
6. **Matrix**: one row per FR, UJ and NFR: each T-id with its level, gate, and `cited` or `missing`
   (citations as `prd_trace.py` counts them).

`--json` is one object per row, for wrappers and tests. The PRD version per environment joins in
0.5. `/prd-status` runs it on the repo's PRD and prints it unfiltered.

## 7. Hooks

**Vendoring.** `prd_hooks.py install <prd-folder>` copies `prd_lint.py`, `prd_trace.py`,
`prd_status.py`, `prd_context.py`, `prd_build_check.py`, `prd_hooks.py` itself, the `prdlint/`
package and the hook scripts into `<repo>/.prd-toolkit/`, with `VERSION` holding the plugin version. The copy is
committed. `check` exits 1 when `VERSION` differs from the running plugin's or a vendored file
differs from its source, naming each; `install` refreshes the copy. `uninstall` removes the hooks it
installed and leaves the copy.

**Installation.** `install` writes `.git/hooks/commit-msg` and `.git/hooks/pre-commit` as six-line
shims (shebang, marker, `top=`, the skip below, a uv guard that blocks the commit when uv is missing, `exec`) that run the vendored hook with `uv run --script`. It never sets `core.hooksPath` (with it set, install writes no shim and prints the lines to add) and never
overwrites a hook: when a hook of that name exists, it writes nothing for it and prints the one line
to add to that hook. Each clone runs `install` once (git does not clone hooks); the managed block
says so. On a branch where `.prd-toolkit/prd_git_hook.py` or the PRD folder is absent, a shim
prints `prd-toolkit: no .prd-toolkit/ (or no PRD folder) on this branch; hook skipped` and exits
`0`: hooks are per clone, the copy is per branch, and CI is the gate.

**`commit-msg`.** The **Boundary** is the union of the `adopted` areas' Boundaries in `adoption.md`;
with no `adoption.md`, it is every path outside the PRD folder and `.prd-toolkit/`. A commit that
stages a file inside the Boundary needs a `Refs:` trailer. Its IDs must each be defined and not
`removed`; `Refs: none (no behaviour change)` also passes. Other trailers (a ticket key, a
co-author) are allowed. A rejection prints the rule and the accepted forms. `prd_trace.py`'s
`commit-refs` applies the same Boundary and ID checks to a `--range`.

**`pre-commit`.** Each `enforced` standards-registry row runs its linter command on the staged files
that match its glob; a row with no match is skipped; any non-zero exit blocks the commit with the
row's command and its output.

## 8. Generated CI

`prd_hooks.py ci --gitlab | --github <prd-folder>` writes a new include file
(`.gitlab/prd-toolkit.yml` or `.github/workflows/prd-toolkit.yml`), never the repository's main CI
file, and prints the `include:` line a GitLab project adds. Jobs, generated from the PRD:

| Job | Runs |
|---|---|
| `prd-lint` | the vendored `prd_lint.py` |
| `prd-trace` | the vendored `prd_trace.py --range <merge base>..HEAD` |
| `standards-<n>` | one per `enforced` standards row, on the files its glob matches |
| `test-<level>` | one per `build`-gate Levels row, its harness command |

Every job installs `uv` and runs from the repository root. An existing include file is rewritten
only after `--force`; without it, `ci` exits 1 and prints the diff. Staging, smoke and drift jobs
are 0.5.

## 9. Changes to existing text

- **changing-prds step 5** hands off to `/prd-build <area> <changed IDs>`; its post-commit
  `Source:` refresh becomes the build's close. Code written outside `/prd-build` keeps the 0.3
  refresh instruction.
- **The managed block** replaces "Before writing code for an approved change, run `/prd-context
  <area> <IDs> implement`; after the code commit, run it again and refresh each STALE `Source:`"
  with "Build an approved change with `/prd-build <area> <IDs>`", and adds "Run
  `.prd-toolkit/prd_hooks.py install` once per clone". The rendered block stays under 1,536 bytes.
- **`prd-format.md`**: the Levels header and `Gate`; `Source:` for built blocks; §9's migration
  sentence; the Boundary rule for a project with no `adoption.md`.

## 10. Testing the toolkit

Every rule and check below is written test-first and fails before its change.

**Scripts (pytest).**
- `prd_build_check.py`, in a temporary git repo: a builder commit touching the PRD folder, one
  touching a file that cites a non-unit T-id, and one changing a unit test each give exit 1, 1 and 0;
  `--results` with a missing ID, an extra ID, a malformed line and a clean block.
- `prd_status.py`: every part on the `orders` fixture; `--json` matches the text rows; two runs are
  byte-identical.
- `prd_hooks.py`: the vendored file list and `VERSION`; `check` on a stale and a changed file;
  `install` refuses an existing hook and never sets `core.hooksPath`; `commit-msg` accepts
  `Refs: FR-001`, `Refs: none (no behaviour change)` and a ticket trailer beside `Refs:`, and
  rejects a Boundary commit with no `Refs:`, a removed ID and an undefined ID; the no-`adoption.md`
  Boundary; `pre-commit` runs only matching rows and blocks on a failing one; both generated CI
  files parse as YAML and hold the expected jobs; `ci` never writes the main CI file and refuses an
  existing include without `--force`.
- Lint and trace: a Levels table with no `Gate`, a bad `Gate` value, `status-current` on `built`,
  `commit-refs` on the new Boundary. Existing fixtures migrate; their tests stay green.

**Pins.** The `write` mode row in testing-from-prds and `dispatching.md`; changing-prds step 5's
hand-off; the block's new lines and its size; the reconcile table and the quote rule in
`running-a-build.md`.

**Baselines before the skills** (superpowers `writing-skills`), recorded verbatim in
`evals/baselines/building-from-prds.md`. Builder: "a small change, the PRD can follow"; "the
tester's test is wrong, just fix it"; "the PRD doesn't say, pick a sensible default". Caller:
classifying a failure without a quote; `verified` with one failing T-id; a version bump for a
status move.

**Evals.** `building-trigger` and `building-not-for-plain-code` (trigger and non-trigger);
`builder-stays-out-of-prd` (the builder edits neither the PRD nor a tester file); `build-gap-stops`
(an ambiguous AC stops the build and routes to `/prd-change`); `build-close-no-bump` (the close
writes `verified`, no version bump, no §14 row). Run before the bump, recorded in `BASELINE.md`.

**Verify.** `uv run --directory prd-toolkit pytest -q`, `cd web && npm test`, `claude plugin
validate ./prd-toolkit`, and `claude plugin eval` as the release memory note says.

## 11. Proof: hello-world, slice 1

`evals/scaffolds/hello_repo.py` creates an empty git repository holding only `TICKET.md`: "Add a
`hello` command: `hello <name>` prints `Hello, <name>!`; an empty name is an error." A Python
standard-library project, run locally.

1. `/prd-new` from the ticket, through every authoring gate, dry run included → `Approved`, 1.0.0.
2. `prd_hooks.py install` and `prd_hooks.py ci --github`; commit the vendored copy and the include.
3. `/prd-build <area> FR-001` → FR-001 `verified`.
4. A second change through `/prd-change` (a minor bump: a `--shout` option, FR-002), then
   `/prd-build` for it. Its `implement` pack shows FR-001's `Source:` excerpt where the change
   touches FR-001's code.

**Pass:** lint and trace exit 0; FR-001 and FR-002 are `verified`; `/prd-status` shows both with
every unit and build-gate T-id `cited`; a deliberate commit inside the Boundary with no `Refs:` is refused; each
generated CI job's commands exit 0 when run locally; no PRD file is read outside the pack and the
files edited; no reconcile classification lacks its quote. The acceptance note,
`docs/superpowers/plans/2026-10-31-prd-toolkit-0.4-acceptance.md`, records the run, every gap and
its disposition. It names no hosts, users, platform objects or people.

## 12. Known limits

- The `write` mode's no-run rule and the dry run's are held by instruction; the guard does not know
  the mode.
- changing-prds rule 6 still binds the caller by text alone (0.3's later item 5).
- A build runs in one repository; a change across repositories waits for 0.7.
- A generated `test-<level>` job runs the whole harness command, so it fails while any case is
  `known-failing` on an open `E-nnn`, until 0.6's error handling.
- A `commit --amend` that only rewrites the message stages no file, so the `commit-msg` hook does
  not check it; CI's `commit-refs` does.

## 13. Out of scope for 0.4

- Deploying, `live`, `operations.md` runbooks, `prd_drift.py`, staging and production CI jobs
  (0.5).
- `handling-errors`, `/prd-error`, nightly runs, `prd-error` issues; an unresolved build failure
  becoming an `E-nnn` (0.6).
- Cross-repository PRD links (0.7).
- Publishing the scripts as a package.
- Ticket-tracker links and platform harnesses: a wrapper plugin's job.
