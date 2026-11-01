# Running a build

**Steps:** 1 Preflight, 2 Snapshot, 3 Dispatch, 4 Check the state, 5 Run (the tester's suite),
6 Reconcile, 7 Full run, 8 Close. The build is not done until step 8's report or a stop under
**Stops**: run every step, in this turn.

For the caller only: `/prd-build`, `prd-toolkit:changing-prds` step 5's hand-off, or any session
asked to implement an approved change or to make a failing PRD test go green. The counterpart of
`testing-from-prds/dispatching.md`.

You are the caller, not the builder and not the tester. You dispatch, check, merge, reconcile and
close. You never write or fix code or a test, you never read or run the code to judge a result,
and you write no status the close does not earn. The caller edits the PRD only at the close: a
block's `Status:`, its §11 status and its `Source:`. A test case, a `known-failing:` marker, an AC
or a contract change goes through `/prd-change`. The caller's Red Flags in `SKILL.md` are yours.

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: that is the copy its hooks and CI run. Otherwise `<scripts>` is the plugin's `scripts`
directory, written as a literal absolute path (in double quotes if it holds a space): the plugin
root is two directories above the skill's base directory (Claude Code shows it as "Base
directory for this skill" when the skill loads), and `<scripts>` is `<plugin root>/scripts`.
Glob for `.prd-toolkit/*.py` once to decide, and use the same `<scripts>` for every command.
A script that is not found is a tool error: report it, never guess another path.

The builder prompt carries `<scripts>` as its `Scripts:` line, as an absolute path (the repository
root joined to `.prd-toolkit` when vendored).

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
no `verified`. A failing test reported outside a build (a test that cites a T-id of an approved
requirement fails against the code, "the tester's test is wrong, fix it") runs step 1, then step
2's snapshot before any dispatch (Never skipped, on this route too: a round without its `-before`
files fails), then enters at step 6: reconcile it by quote and route it; the first builder round it
dispatches is followed by steps 4 and 5, as on every route. Never fix the code or the test
yourself, and never let your own test run stand in for the tester's suite.

Both agents must be in the Agent tool's list: `prd-toolkit:prd-builder` and
`prd-toolkit:prd-tester`. When either is missing, or you cannot dispatch subagents, report the
build as not run. A build has no fallback: never write the code or the tests yourself.

**Rounds.** Each T-id gets at most three rounds. Round 1 is a T-id's first builder dispatch (for a
tester's T-id, its first `write`). Each later dispatch that carries the T-id (a builder round, a
test-misread round, a dispatch again after a failed check) is its next round, and a step 4 check
failure counts as a round and is recorded by its finding lines. After a third failed round on one
T-id the build stops and reports it to the user. The stop report carries every round's RECONCILE
record or failure line for that T-id.

**Stops.** A build stops on a dirty working tree in step 1 (no status: nothing has merged), on
a PRD gap (a QUESTIONS line that is not a test dispute, a tester QUESTION the PRD does not answer,
or step 6's PRD-gap row), on a failing test that cites no T-id, on a failed tester state check
(`dispatching.md` step 4), on a failed builder state check only without worktree isolation; with
it, a failed builder check is a failed round (**Rounds**), on a `prd-trace-exit=` other than `0`
in step 7 or the close, and on the third failed round on a T-id. Any stop after the builder's
merge writes `built` for each block whose unit T-ids pass, never `verified`. A stop before the
merge writes no status. Either way, report the stop to the user with its records; a PRD gap also
goes to `/prd-change`.

**One turn.** A build runs to its close, or to a stop under **Stops**, in the same turn. Never end
the turn with a next round announced: dispatch it. You end the turn only after the close's report,
or after a stop's. The one carve-out: before step 2, the caller may stop to ask the user (a dirty
tree, or a branch off the default branch, in step 1) and resumes the build at step 1 once answered.

1. **Preflight.** Run each line as its own call:

   ```bash
   uv run --script <scripts>/prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"
   git status --porcelain --untracked-files=all
   git branch --show-current
   uv run --script <scripts>/prd_context.py docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"
   ```

   `<IDs>` is joined with commas for `--req`, as `--req FR-006,FR-001`, never space-separated: a
   space-separated list is a usage error (exit 2).

   `prd-lint-exit=` must be `0`. Grep `^status:` with the path `docs/prd/<slug>/prd.md`: it must be
   `status: Approved`. The status output must be empty: a dirty tree stops the build, and you ask
   the user what to do with it. On the repository's default branch, ask the user before branching.
   When there is no one to ask (a headless run, or "do not ask questions"), run
   `git switch -c <branch>` as its own call with the branch `prd-build/<area>-<IDs>`, the IDs
   joined by `-`, and say so in the report. Every build runs on its own branch; never merge onto
   the default branch. From the pack, check each block's `Status:`, then split the T-ids on each
   block's `Tests:` line by the pack's Levels part: **unit** (level `unit`) for the builder, and
   **build-gate non-unit** (a level whose `Gate` is `build`) for the tester. Deploy-gate T-ids are
   not run in 0.4. Then run `git rev-parse HEAD` as its own call and paste the SHA it prints
   wherever `<base>` appears.
2. **Snapshot**, as `dispatching.md` step 2: a new `<SNAP>` directory outside the repository and
   the five commands into `-before` files, each its own call, with its check that the harness
   caches are git-ignored. A build has no dry-run directory. Never skipped: without the
   `-before` files, step 4 cannot tell the tester's changes from anything else, and the round
   fails.
3. **Dispatch both in one message**: two Agent tool calls in the same message.
   - `prd-toolkit:prd-builder`, with `isolation: worktree`, and the builder prompt (below) with
     its slots filled and nothing else: no summary of the PRD, no hints, no pointers into the code.
   - `prd-toolkit:prd-tester`, with the tester prompt (below) as `Mode: write` and the
     build-gate non-unit T-ids, each with its test-case file.

   With no non-unit build-gate T-ids, dispatch the builder alone: the tester has no `write`.

   When the Agent tool offers no worktree isolation, dispatch the builder first and the tester
   after it returns, each followed by its step 4 check. The builder then commits on the build
   branch itself, so there is no merge: its commits land on the build branch, and its range is
   `<base>..HEAD`, for `prd_build_check.py --diff <base>..HEAD` and
   `git log --format=%B <base>..HEAD`. The merge, for every rule below, is the moment that
   check passes. `git status --porcelain --untracked-files=all` must print nothing after the
   builder: take step 2's snapshot after the builder's check passes and before the tester's
   dispatch. Without worktree isolation, a builder round that fails its state check stops the
   build and reports its commits to the user; never re-record `<base>` past them.
4. **Check the state.** Both checks must pass before anything merges.
   - **The builder.** Take the branch from its COMMIT line and run:

     ```bash
     uv run --script <scripts>/prd_build_check.py docs/prd/<slug> --diff <base>..<builder branch>; echo "prd-build-check-exit=$?"
     git log --format=%B <base>..<builder branch>
     ```

     `prd-build-check-exit=1` fails the round: each line names a file in the PRD folder or a
     tester's test the builder touched; record the lines as the round's failure. `2` is a usage
     error: fix the command. Every commit message in the log carries a `Refs:` line naming the
     build's IDs; one without it fails the round. Then judge the report: its five fields in order
     (CHANGES, UNIT, SOURCES, QUESTIONS, COMMIT), one UNIT line per unit T-id, each `pass`, and
     one SOURCES line per block. A QUESTIONS line that is not a test dispute is a PRD gap and
     stops the build, as **Stops** says: `built` if a merge happened, otherwise no status. A test
     dispute, `<T-id>: test dispute: "<assertion, verbatim>" vs "<ac:/expect quote, verbatim>"`,
     does not stop it: the caller reconciles each test dispute by quote at step 6, as a test
     misread or a code bug. A UNIT line that is not `pass` fails the round, and the next builder
     round carries it as its `Failure:`, with the quote of that T-id's test case and its unit test
     as `Failing test:`. With worktree isolation, a failed round merges nothing; dispatch the
     builder again, as the next round of each of its unit T-ids. A failed round's builder branch
     is kept and listed in the report; never delete one with `-D`. Without worktree isolation, a
     failed builder check stops the build instead, as step 3 says. Without worktree isolation,
     `<base>` does not move on a UNIT-failure round: the range keeps the earlier commits, and the
     check covers them all.
   - **The tester.** `dispatching.md` step 4: the five commands into `-after` files and the
     diffs, each its own call. A write's check exempts the test roots. If the Agent tool placed
     the builder's worktree inside the repository, that one new path is the builder's, not the
     tester's; every other changed path outside the test roots fails the check, and you report
     it as `dispatching.md` step 4 says: the changed paths to the user, nothing restored, and the
     build stops. Then judge the report as `dispatching.md` step 5 says: TESTS holds one line per
     dispatched T-id, and a `write` report that holds RESULTS fails the round. Each tester
     QUESTION the PRD answers is dismissed by an exact quote of the line that answers it; any
     other is a PRD gap and stops the build.

   When both pass, run each line as its own call, the tester's paths typed out from its TESTS and
   HARNESS CHOICES:

   ```bash
   git merge <builder branch>
   git add <tester path> <tester path>
   git commit -m "test(<area>): <T-ids> from the PRD" -m "Refs: <IDs>"
   ```

   If the merge refuses because a tester's file is in the way, stop and report both paths to the
   user.
5. **Run.** On every route, after each builder round, step 5 runs: the snapshot (`dispatching.md`
   step 2) and then `prd-tester` `Mode: suite` on the build's non-unit build-gate T-ids. Its
   RESULTS, checked with `prd_build_check.py --results`, are the only evidence for those T-ids. The
   caller's own harness run is step 7 and never replaces step 5. The snapshot goes into a new
   `<SNAP>`, and the dispatch takes the tester prompt below. When the build has no non-unit
   build-gate T-ids, step 5 is skipped: there is nothing to dispatch, and the close's `verified`
   needs only the builder's UNIT lines, your step 7 run and `prd-trace-exit=0`. Save the tester's
   whole report, verbatim, with the Write tool to `<SNAP>/suite-report.md`, then run:

   ```bash
   uv run --script <scripts>/prd_build_check.py docs/prd/<slug> --results <SNAP>/suite-report.md --tids <T-id>,<T-id>; echo "prd-build-check-exit=$?"
   git status --porcelain --untracked-files=all
   ```

   `prd-build-check-exit=1` fails the round: a dispatched T-id with no line, a line for a T-id not
   dispatched, a duplicate, or a line in none of the three forms. Outside a test-misread round a
   suite writes nothing, so the status output must be empty; on a test-misread round only that
   T-id's test may change: run `dispatching.md` step 4, then commit the test with
   `git commit -m "test(<area>): <T-id> matches the PRD" -m "Refs: <IDs>"` after its `git add`.
   A `known-failing E-nnn` line for a case that carries `known-failing: E-nnn` is expected: it is
   not reconciled, and it is not a pass.
6. **Reconcile** each `fail` line and each test dispute, one at a time. Read the T-id's entry in
   its test-case file (the block's `Tests:` line names the file) and the test that cites it (TESTS
   names it). Quote verbatim the test case's `ac:` line, the `expect` entry the failure concerns
   and the test's assertion. Your evidence is those quotes and the RESULTS line; never the code,
   and never a run of it. Write this record, then classify:

   ```
   RECONCILE  <T-id>  round <n> of 3
   ac:        "<the test case's ac: line, verbatim>"
   expect:    "<the expect entry, verbatim>"
   fail:      <the RESULTS line, or the test dispute line, verbatim>
   test:      <path>:<line> "<the assertion, verbatim>"
   class:     code bug | test misread | PRD gap
   next:      <the table's Next>
   ```

   | Class | Means | Next |
   |---|---|---|
   | code bug | the code contradicts the quote | a builder round with the failure line and the quote; the builder may now read the failing test |
   | test misread | the test contradicts the quote | a tester `suite` round with the quote |
   | PRD gap | the quote admits both readings, or is silent | **stop**: the gap goes to `/prd-change`; the status follows **Stops** |

   A classification without its quote does not count. The quote is all three, each verbatim: the
   `ac:` line, the `expect` entry and the test's assertion. A builder round is a new
   `prd-toolkit:prd-builder` dispatch with `isolation: worktree`, the builder prompt and its three
   code-bug lines, and `<base>` re-recorded with `git rev-parse HEAD` before it. A tester round is
   a `Mode: suite` dispatch carrying
   `Misread: <T-id>: "<verbatim quote of the test case's ac: line and the expect entry>"`, one line
   per affected T-id, added only after you have checked the test against the quote.

   Each round repeats steps 4 and 5 for the agent that ran. A builder round runs steps 4 and 5
   again: the suite reruns. Count rounds as **Rounds** says; on a T-id's third failed round,
   stop as **Stops** says.
7. **Full run.** Never skipped: the agents' reports are not the full run, and `verified` needs
   your own. Run every Levels harness command whose `Gate` is `build`, exactly as testing.md
   writes it, each its own call. Every test passes except cases `known-failing` on an open `E-nnn`
   (Grep `known-failing` with the path `docs/prd/<slug>/test-cases/` to see which). A failure
   here is a `fail` line for its T-id: reconcile it in step 6, against that T-id's own test case
   even when it lies outside this build, as that T-id's next round. A failing test that cites no
   T-id stops the build. Then:

   ```bash
   uv run --script <scripts>/prd_trace.py docs/prd/<slug>; echo "prd-trace-exit=$?"
   ```

   `prd-trace-exit=` must be `0`; anything else stops the build, as **Stops** says. Trace asks a
   citation for each unit and build-gate T-id of a `built` or `verified` block; deploy-gate T-ids
   wait for `live`.
8. **Close.** Write each block's status in the block and its §11 index row together:

   | Move | When |
   |---|---|
   | `approved → built` | the builder's commit is merged and every unit T-id of the block passes |
   | `built → verified` | every unit T-id passes on the builder's UNIT lines, every non-unit build-gate T-id passes on the tester's suite RESULTS, every build-gate T-id passes in your step 7 run, and `prd-trace-exit=0` |

   A clean build writes `verified` directly. A block with no unit and no build-gate T-ids moves
   to `verified` at a clean close, since the `built → verified` conditions hold vacuously for it
   (an NFR whose only test is a deploy-gate `[system]` check, say); its deploy-gate tests run at
   `/prd-deploy`. Never leave it `built` at a clean close: `prd_deploy.py` pre-flight refuses a
   deploy while any block is `built`, so it could never reach `live`. On a stopped build it
   stays `built`, and the next clean build closes it `verified`. A stopped build closes by
   **Stops**: `built` for each block whose unit T-ids pass after the merge, nothing before it. A
   `known-failing` result is not a pass, so its block stays `built`. Never write `live`: it
   means deployed, and a build deploys nothing; deploy-gate tests run at `/prd-deploy`. Change
   only the status word; keep any `(since X.Y.Z)` and the index row's Since cell as they are.
   Edit nothing else in the PRD.

   Run `git rev-parse --short HEAD` as its own call, after the last merge. From each SOURCES line
   of the builder's latest report for a block, write the block's
   `Source: <path>:<line> @<short sha>`, replacing any `Source:` line it had.

   A status move is progress, not behaviour: no version bump, no §14 row, no re-approval, and the
   PRD status stays `Approved`. Leave `version` and `updated` as they are. Run the trace before
   the close commit, so a `verified` commit is never followed by a revert. Run each line as its
   own call:

   ```bash
   uv run --script <scripts>/prd_context.py docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"
   uv run --script <scripts>/prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"
   uv run --script <scripts>/prd_trace.py docs/prd/<slug>; echo "prd-trace-exit=$?"
   ```

   `prd-context-exit=` must be `0`: a STALE code item for a block you just wrote means a wrong
   line or SHA, so fix it. `prd-lint-exit=` must be `0`. `prd-trace-exit=1` after writing
   `verified` reverts those blocks to `built` and stops the build: rewrite the status words
   before you commit. `prd-trace-exit=2` stops the build like `1`: the blocks stay `built`. On a
   stopped build's `built` close, give the trace findings to the user with the stop. Then, each
   its own call:

   ```bash
   git add docs/prd/<slug>
   git commit -m "docs(prd): <IDs> <built or verified>" -m "Refs: <IDs>"
   ```

   Then remove each worktree a passed round left, `git worktree remove <worktree path>` and
   `git branch -d <builder branch>`, each its own call; a failed round's branch stays. Report to
   the user: the build branch, each block's status, each T-id's result, every reconcile record
   and every kept branch.

## Prompts

The builder prompt, slots filled, and nothing else:

```
Mode: build
PRD: docs/prd/<slug>/
Area: <area>
IDs: <UJ, FR and NFR IDs>
Unit T-ids: <one per line, with its test-case file>
Scripts: <scripts directory, as an absolute path>
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
