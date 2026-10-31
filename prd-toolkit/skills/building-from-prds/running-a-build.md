# Running a build

For the caller only: `/prd-build`, `prd-toolkit:changing-prds` step 5's hand-off, or any session
asked to implement an approved change. The counterpart of `testing-from-prds/dispatching.md`.

You are the caller, not the builder and not the tester. You dispatch, check, merge, reconcile and
close. You never write or fix code or a test, you never read or run the code to judge a result,
and you write no status the close does not earn. The caller's Red Flags in `SKILL.md` are yours.

**One command per Bash call, with literal paths.** As in `dispatching.md`: each command below is
its own Bash call, and every path and SHA in it is typed out in full: paste what a command printed,
never a variable that holds it or a `$(…)`. The gate form `; echo "<script>-exit=$?"` is the one
allowed tail. Never pipe, filter or truncate a gated command's output (no `| head`, no `| grep`).

**Input:** a PRD with status `Approved` and `prd-lint-exit=0`; an area; the changed UJ, FR and NFR
IDs (or a bug fix's `E-nnn`, mapped to its requirements as the `implement` pack maps it), each
block at `approved`, or at `built` when a stopped build resumes. A draft goes to
`prd-toolkit:authoring-prds`; a block at any other status, or a change not yet approved, goes to
`prd-toolkit:changing-prds`. A request to build anything beyond the approved IDs ("while you're
there", "the PRD can follow") is a change: send it to `prd-toolkit:changing-prds` and build only
the approved IDs. "It's tiny" changes nothing: a change that skips the build earns no `built` and
no `verified`.

Both agents must be in the Agent tool's list: `prd-toolkit:prd-builder` and
`prd-toolkit:prd-tester`. When either is missing, or you cannot dispatch subagents, report the
build as not run. A build has no fallback: never write the code or the tests yourself.

1. **Preflight.** Run each line as its own call:

   ```bash
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"
   git status --porcelain --untracked-files=all
   git branch --show-current
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"
   ```

   `prd-lint-exit=` must be `0`. Grep `^status:` with the path `docs/prd/<slug>/prd.md`: it must
   be `status: Approved`. The status output must be empty: a dirty tree stops the build,
   and you ask the user what to do with it. On the repository's default branch, ask the user
   before branching; with their answer, run `git switch -c <branch>` as its own call. From the
   pack, check each block's `Status:`, then split the T-ids on each block's `Tests:` line by the
   pack's Levels part: **unit** (level `unit`) for the builder, and **build-gate non-unit** (a
   level whose `Gate` is `build`) for the tester. Deploy-gate T-ids are not run in 0.4. Then run
   `git rev-parse HEAD` as its own call and paste the SHA it prints wherever `<base>` appears.
2. **Snapshot**, as `dispatching.md` step 2: a new `<SNAP>` directory outside the repository and
   the five commands into `-before` files, each its own call, with its check that the harness
   caches are git-ignored. A build has no dry-run directory.
3. **Dispatch both in one message**: two Agent tool calls in the same message.
   - `prd-toolkit:prd-builder`, with `isolation: worktree`, and the builder prompt (below) with
     its slots filled and nothing else: no summary of the PRD, no hints, no pointers into the code.
   - `prd-toolkit:prd-tester`, with the tester prompt (below) as `Mode: write` and the
     build-gate non-unit T-ids, each with its test-case file.

   When the Agent tool offers no worktree isolation, dispatch the builder first and the tester
   after it returns, each followed by its step 4 check. The builder then commits on your branch,
   so its range is `<base>..HEAD`, and `git status --porcelain --untracked-files=all` must print
   nothing after it: take step 2's snapshot after the builder's check passes and before the
   tester's dispatch.
4. **Check the state.** Both checks must pass before anything merges.
   - **The builder.** Take the branch from its COMMIT line and run:

     ```bash
     uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_build_check.py" docs/prd/<slug> --diff <base>..<builder branch>; echo "prd-build-check-exit=$?"
     git log --format=%B <base>..<builder branch>
     ```

     `prd-build-check-exit=1` fails the round: each line names a file in the PRD folder or a
     tester's test the builder touched; report the lines. `2` is a usage error: fix the command.
     Every commit message in the log carries a `Refs:` line naming the build's IDs; one without it
     fails the round. Then judge the report: its five fields in order (CHANGES, UNIT, SOURCES,
     QUESTIONS, COMMIT), one UNIT line per unit T-id, each `pass`, and one SOURCES line per block.
     A non-empty QUESTIONS stops the build here, before any merge, at step 6's PRD-gap row. A UNIT
     line that is not `pass` fails the round, and the next builder round carries it as its
     `Failure:`, with the quote of that T-id's test case and its unit test as `Failing test:`.
     A failed round merges nothing. Dispatch the builder again; the round counts toward the three
     rounds of each of its unit T-ids (step 6).
   - **The tester.** `dispatching.md` step 4: the five commands into `-after` files and the
     diffs, each its own call. A write's check exempts the test roots. If the Agent tool placed
     the builder's worktree inside the repository, that one new path is the builder's, not the
     tester's; every other changed path outside the test roots fails the round, and you report
     it as `dispatching.md` step 4 says: the changed paths to the user, nothing restored. Then judge the
     report as `dispatching.md` step 5 says: TESTS holds one line per dispatched T-id, and a
     `write` report that holds RESULTS fails the round. Each tester QUESTION the PRD answers is
     dismissed by an exact quote of the line that answers it; any other is a gap, and it stops the
     build at step 6's PRD-gap row.

   When both pass, run each line as its own call, the tester's paths typed out from its TESTS and
   HARNESS CHOICES:

   ```bash
   git merge <builder branch>
   git add <tester path> <tester path>
   git commit -m "test(<area>): <T-ids> from the PRD" -m "Refs: <IDs>"
   ```

   If the merge refuses because a tester's file is in the way, stop and report both paths to the
   user.
5. **Run.** Take step 2's snapshot again, into a new `<SNAP>`. Dispatch `prd-toolkit:prd-tester`
   with the tester prompt as `Mode: suite`, on the same T-ids. Save its whole report, verbatim,
   with the Write tool to `<SNAP>/suite-report.md`, then run:

   ```bash
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_build_check.py" docs/prd/<slug> --results <SNAP>/suite-report.md --tids <T-id>,<T-id>; echo "prd-build-check-exit=$?"
   git status --porcelain --untracked-files=all
   ```

   `prd-build-check-exit=1` fails the round: a dispatched T-id with no line, a line for a T-id not
   dispatched, a duplicate, or a line in none of the three forms. Outside a test-misread round a
   suite writes nothing, so the status output must be empty; on a test-misread round only that
   T-id's test may change: run `dispatching.md` step 4, then commit the test with
   `git commit -m "test(<area>): <T-id> matches the PRD" -m "Refs: <IDs>"` after its `git add`.
   A `known-failing E-nnn` line for a case that carries `known-failing: E-nnn` is expected: it is
   not reconciled, and it is not a pass.
6. **Reconcile** each `fail` line, one at a time. Read the failing T-id's entry in its test-case
   file (the block's `Tests:` line names the file) and the test that cites it (TESTS names it).
   Quote verbatim the test case's `ac:` line and the `expect` entry the failure concerns. Your
   evidence is the quote, the RESULTS line and the test; never the code, and never a run of it.
   Write this record, then classify:

   ```
   RECONCILE  <T-id>  round <n> of 3
   ac:        "<the test case's ac: line, verbatim>"
   expect:    "<the expect entry, verbatim>"
   fail:      <the RESULTS line, verbatim>
   test:      <path>:<line> asserts <what it asserts>
   class:     code bug | test misread | PRD gap
   next:      <the table's Next>
   ```

   | Class | Means | Next |
   |---|---|---|
   | code bug | the code contradicts the quote | a builder round with the failure line and the quote; the builder may now read the failing test |
   | test misread | the test contradicts the quote | a tester `suite` round with the quote |
   | PRD gap | the quote admits both readings, or is silent | **stop**: the gap goes to `/prd-change`; statuses stay as they are |

   A classification without its quote does not count. A builder round is a new
   `prd-toolkit:prd-builder` dispatch with `isolation: worktree`, the builder prompt and its three
   code-bug lines, and `<base>` re-recorded with `git rev-parse HEAD` before it. A tester round is
   a `Mode: suite` dispatch carrying
   `Misread: <T-id>: "<verbatim quote of the test case's ac: line and the expect entry>"`, one line
   per affected T-id, added only after you have checked the test against the quote. On a PRD gap,
   show the user the record and write no status, not even `built`.

   Each round repeats steps 4 and 5 for the agent that ran. Every round on a T-id counts toward
   its three rounds, a round that a step 4 or step 5 check failed included. After three rounds on
   one T-id the build stops and reports it to the user. The report carries that T-id's three
   records.
7. **Full run.** Run every Levels harness command whose `Gate` is `build`, exactly as testing.md
   writes it, each its own call. Every test passes except cases `known-failing` on an open `E-nnn`
   (Grep `known-failing` with the path `docs/prd/<slug>/test-cases/` to see which). A failure
   here is a `fail` line for its T-id: reconcile it in step 6, against that T-id's own test case
   even when it lies outside this build, and it counts toward that T-id's three rounds. A failing
   test that cites no T-id stops the build: report it to the user. Then:

   ```bash
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_trace.py" docs/prd/<slug>; echo "prd-trace-exit=$?"
   ```

   `prd-trace-exit=` must be `0`.
8. **Close.** Write each block's status in the block and its §11 index row together:

   | Move | When |
   |---|---|
   | `approved → built` | the builder's commit is merged and every unit T-id of the block passes |
   | `built → verified` | every build-gate T-id of the block passes in the full run and `prd-trace-exit=0` |

   A clean build writes `verified` directly. A build stopped after the merge (three rounds on a
   T-id) writes `built` for each block that meets its row, and nothing else. A `known-failing`
   result is not a pass, so its block stays `built`. Never write `live`: it means deployed, and a
   build deploys nothing. Change only the status word; keep any `(since X.Y.Z)` and the index
   row's Since cell as they are.

   Run `git rev-parse --short HEAD` as its own call, after the last merge. From each SOURCES line
   of the builder's latest report for a block, write the block's
   `Source: <path>:<line> @<short sha>`, replacing any `Source:` line it had.

   A status move is progress, not behaviour: no version bump, no §14 row, no re-approval, and the
   PRD status stays `Approved`. Leave `version` and `updated` as they are. Then run each line as
   its own call:

   ```bash
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_trace.py" docs/prd/<slug>; echo "prd-trace-exit=$?"
   git add docs/prd/<slug>
   git commit -m "docs(prd): <IDs> <built or verified>" -m "Refs: <IDs>"
   ```

   `prd-context-exit=` must be `0`: a STALE code item for a block you just wrote means a wrong
   line or SHA, so fix it. `prd-lint-exit=` must be `0`. `prd-trace-exit=` must be `0` for a
   `verified` close; on a stopped build's `built` close, give its findings to the user with the
   stop. Then remove each
   worktree and branch the build's builder rounds left, `git worktree remove <worktree path>` and
   `git branch -d <builder branch>`, each its own call. Report to the user: each block's status,
   each T-id's result, and every reconcile record.

## Prompts

The builder prompt, slots filled, and nothing else:

```
Mode: build
PRD: docs/prd/<slug>/
Area: <area>
IDs: <UJ, FR and NFR IDs>
Unit T-ids: <one per line, with its test-case file>
```

A code-bug round adds three lines after those:

```
Failure: <the RESULTS line, verbatim>
Quote: "<the test case's ac: line>" / "<the expect entry>"
Failing test: <path>
```

It runs `prd_context.py … --for implement` itself, writes unit tests first, then the code, runs the
standards linters and required skills, and commits in its worktree with `Refs: <IDs>`.

The tester prompt, as `dispatching.md` step 3 gives it, with no dry-run directory: `Mode: write` in
step 3, `Mode: suite` in step 5 and on a test-misread round.

```
Mode: write
PRD: docs/prd/<slug>/
T-ids (one per line, each with its test-case file):
<T_IDS>
```

A test-misread round is `Mode: suite` with one
`Misread: <T-id>: "<verbatim quote of the test case's ac: line and the expect entry>"` line per
affected T-id after the T-ids.
