# prd-toolkit 0.8.5: deploy, pack and check fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the deploy runner confirms several human steps at once, lets a mid-run error entry pass, times each level on its own, notes a close on the wrong branch and matches Checks by pattern; `prd_change.py pack` turns a pack release into a scripted patch; the change books name moved statuses and every new or removed ID; STALE is judged by the cited line; SOURCES lines are checked against the round's hunks; the published page draws its diagrams as inline SVG; the tester guard checks every harness argument; and the toolkit's own suite runs in parallel.

**Architecture:** the toolkit's own PRD changes first: one `lint-cli` `/prd-change` adds three loader-and-lint requirements (Levels `Timeout`, Environments `Branch`, a Check's `matches`) and `-n auto`, and `/prd-build` adds the parsing to `prdlint/model.py`. Every other change sits outside the adopted area: the runtime in `prdlint/deploy.py` and `prd_deploy.py`, the books in `prdlint/change.py`, the checks in `prdlint/context.py` and `prdlint/buildcheck.py`, the diagrams in a new `prdlint/diagrams.py` that `publish.py` calls, and the guard in `prd_tester_guard.py`. Skill text, references and the README follow in their own tasks.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, markdown-it-py, pytest with pytest-xdist, one pinned mermaid renderer (Task 1); git; Claude Code CLI (`claude plugin eval`).

**Spec:** `docs/superpowers/specs/2026-11-08-prd-toolkit-0.8.5-design.md` (governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`). Facts on `main` at `a9a520e`: the session scratchpad's `085-facts.md`, re-read in Task 0.

## Global Constraints

- **Starts from `main` with this spec and plan merged.** Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8.5`, branch `feat/prd-toolkit-0.8.5`, cut from that `main`. The toolkit's own PRD is at 5.1.0. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- **The toolkit's own PRD binds this branch.** `prdlint/model.py` is a `lint-cli` Boundary file: only Task 4 touches it, with the live IDs Task 3 adds. Every other commit carries `Refs: none (no behaviour change)`. Never `--no-verify`. **The builder runs without isolation**, on a round branch `prd-round/lint-cli-<n>` the caller cuts from this branch, merged `--ff-only` after `prd_build_check.py --diff` exits 0, as in 0.8.4.
- The repo is public and the toolkit names no client: no app, service, editor or organization name in code, docs, tests or evals. Example slugs `greet`, `orders`, `notes`.
- Test-first: every behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New third-party dependencies: `pytest-xdist` (dev group, Task 2) and the one renderer Task 1 picks (in `prd_publish.py`'s inline header only). Nothing else.
- **CI parity before every commit that touches code:** `scripts/ci-local.sh origin/main`, with `HOME` set to an empty directory under the session scratchpad.
- **Vendoring:** every task that changes a file `vendor` copies ends with `uv run --script prd-toolkit/scripts/prd_hooks.py vendor docs/prd/prd-toolkit`, its own Bash call, and commits `.prd-toolkit/` in the same commit. Never `prd_hooks.py install` on this repo.
- **Exact copy** (from the spec):
  - `prd_deploy: the close is on <current>, not <branch>; push the close commit to <branch> too`, with `a detached HEAD` for `<current>`;
  - `no stdout line matches '<pattern>'`;
  - `timed out after <N> s (the <level> level's Timeout)`, `(--timeout)`, `(the default)`;
  - the §14 row `pack <name> <old> → <new>; no dry run (pack version only)`, IDs cell `-`;
  - install's hint `; to move the PRD to <name> <have>, run prd_change.py pack <prd> <name> <have>`;
  - the bump item `patch <ID> <file>:<line> status <old> → <new>`;
  - `MOVED: line <L> is now line <M>`, `STALE: the cited line's text is gone`, `STALE: the cited line's text appears <N> times`, the suffix ` (pulled in; not counted)`;
  - `sources: <ID>: <path> is not changed in <base>..<head>`, `sources: <ID>: <path>:<line> is outside the round's changes (hunks <a>-<b>, …)`, `sources: line <n> is not '<ID>: <path>:<line>'`;
  - `prd_publish: diagram at <file>:<line> shown as source: <reason>`; the classes `diagram` (figure) and `mermaid-source` (pre); the summary `Diagram source`; IDs `diagram-1`, `diagram-2`, …;
  - `prd_tester_guard: <arg> is not under a test root`, `prd_tester_guard: <option> is refused after a harness command`, `prd_tester_guard: unquoted glob in <arg>`.
- **Ruling (plan, spec 5.3): `--timeout` "given".** Its argparse default becomes `None`; `None` means the per-level Timeout or `deploy.DEFAULT_TIMEOUT` (600) applies; any integer given, 600 included, overrides every level.
- **Ruling (plan, spec 5.1): ahead confirms in the log.** `{"kind":"confirm","step":N,"reply":...,"at":...,"ahead":true}` for each step after the stopped one; the step record written on resume for such a step carries `"result":"human","confirmed_ahead":true`. A log without these keys (written by 0.8.4) reads exactly as before.
- **Ruling (plan, spec 10): the renderer sits behind one function.** `prdlint/diagrams.py` exposes `render_svg(source: str, number: int) -> str`, raising `diagrams.Fallback(reason: str)` for any failure (import error, render error, a refused SVG), so `publish.py` never imports the renderer itself.

## Review Focus

1. A run log written by 0.8.4, stopped at a human step, resumed and closed by 0.8.5: no `ahead` keys anywhere, and `resume`, `finished_envs` and the close check behave as before. (Task 6)
2. A mid-run `errors.md` that adds the run's entry and also edits a word in an older entry: `resume` refuses with "the tracked tree has changes", because only added entries pass. (Task 7)
3. `prd_deploy.py run --timeout 600` on a PRD whose level has `Timeout` 1200: the level runs with 600 (the flag was given), and the timeout message names `(--timeout)`. (Task 8)
4. A harness argument `tests/../scripts`: resolved before the test-root check, so it is refused although it starts with a test root. (Task 5)
5. A `Source:` file with CRLF line endings whose cited line is unchanged: current, not STALE (the comparison strips whitespace, `\r` included). (Task 11)

---

### Task 0 (controller-run): Preflight

**Files:** none.

- [ ] **Step 1:** Check `main` holds 0.8.4 (`prd-toolkit/.claude-plugin/plugin.json` says `0.8.4`), this spec and plan, and the PRD at 5.1.0. Create the worktree and branch from `main`.
- [ ] **Step 2:** Re-read the facts of `085-facts.md` against the code at `main` (the named functions and lines); note any that moved in the ledger.
- [ ] **Step 3:** Run `uv run --script prd-toolkit/scripts/prd_change.py ids next docs/prd/prd-toolkit FR`, its own call; the three FRs of Task 3 take that number and the next two, written into the PRD one at a time as `ids next` requires. Record them in the ledger.

### Task 1 (controller-run): the renderer check (spec 10)

**Files:** none committed; a scratch directory under the session scratchpad.

- [ ] **Step 1:** In the scratch directory, render the toolkit PRD's §4 diagram (from `docs/prd/prd-toolkit/prd.md`) and a three-message `sequenceDiagram` with each candidate, `uv run --with mermaidx …` and `uv run --with mmdc …`, each its own call, using each package's documented Python API.
- [ ] **Step 2:** For each SVG, check: every node label of the source appears as SVG text; no `<foreignObject`, `<script`, `on…=` attribute, or `href`/`url(` that is not `#…`, once labels are set to plain text; the render takes under 10 s.
- [ ] **Step 3:** Record the winner, its exact version, its call, and its options for plain-text labels in the ledger. If neither passes, stop and ask Ivan (spec 10: the fallback becomes the whole of item 9).

### Task 2: parallel tests (spec 12, first half)

**Files:**
- Modify: `prd-toolkit/pyproject.toml` (`[dependency-groups] dev`), `prd-toolkit/uv.lock`, and whichever tests the parallel run shows depend on order or a shared module (the 0.8.4 ledger names the hooks tests' `sys.path` insert and cached module)

- [ ] **Step 1:** Add `pytest-xdist` to the dev group and lock (`uv lock --directory prd-toolkit`, its own call).
- [ ] **Step 2:** Run `uv run --directory prd-toolkit pytest -q -n auto tests --ignore tests/prd` and then `… -n auto tests/prd`, each its own call. Record each failure that does not fail serially.
- [ ] **Step 3:** Fix each such test so it holds its own state (`tmp_path`, `monkeypatch.syspath_prepend`, `importlib.reload` within the test); run both commands again, each twice, until all four runs pass.
- [ ] **Step 4:** Run the serial suite once to see nothing regressed, then CI parity.
- [ ] **Step 5: Commit** `test(prd-toolkit): the suite runs in parallel`.

### Task 3 (controller-run, stops for Ivan): the toolkit PRD's `/prd-change` (spec 4)

**Files:** `docs/prd/prd-toolkit/features/lint-cli.md`, `test-cases/lint-cli.yaml`, `testing.md`, `prd.md` (§11, §14, version), and fixtures under `contracts/fixtures/lint-cli/`, through `/prd-change`.

- [ ] **Step 1:** Run `/prd-change` with spec section 4 as one change: the three `lint-cli` requirements (Timeout, Branch, `matches`) with Task 0's IDs, one AC and one integration test case each, on fixture PRDs; the `unit` and `integration` Harness commands with `-n auto`, as `uv run --directory prd-toolkit pytest -q -n auto tests --ignore tests/prd` and `uv run --directory prd-toolkit pytest -q -n auto tests/prd`. Settle each finding's rule and message in the change; minor, 5.1.0 → 5.2.0, the Harness edit decided as a patch item.
- [ ] **Step 2:** The dry run through `prd-tester`. Ivan approves in his own words; the approval commit as `changing-prds` step 5 says.
- [ ] **Step 3:** Regenerate the CI file, its own call: `uv run --script .prd-toolkit/prd_hooks.py ci --github --force docs/prd/prd-toolkit`; check `test-unit` and `test-integration` carry `-n auto`. Commit `ci(prd-toolkit): the test jobs run in parallel`.

### Task 4 (controller-run): `/prd-build lint-cli <FRs>` (spec 4)

**Files:** `prd-toolkit/scripts/prdlint/model.py`, `prd-toolkit/scripts/prdlint/rules/registries.py` (builder); the T-ids' tests under `prd-toolkit/tests/prd/` (tester).

**Interfaces:**
- Produces, in `prdlint/model.py`: `Testing.timeouts: dict[str, str]` (level → raw `Timeout` cell, only when the column exists) and `Testing.has_timeout: bool`; `Operations.branches: dict[str, str]` (environment → raw `Branch` cell) and `Operations.has_branch: bool`; `Step.matches: str | None`, set from `` Check: `<cmd>` matches `<pattern>` ``, with `Step.prints` still set from the `prints` form. The rules report the three findings the approved ACs name.

- [ ] **Step 1:** `/prd-build lint-cli <FRs>` per `running-a-build.md`, the builder **without isolation** (Global Constraints), with the Interfaces above in its prompt as the names later tasks rely on.
- [ ] **Step 2:** The close: `verified` and `Source:` lines; CI parity.

### Task 5: the tester guard checks every harness argument (spec 11)

**Files:**
- Modify: `prd-toolkit/scripts/prd_tester_guard.py` (`_check_harness_args`, `PATH_OPTS`, `SHORT_VALUE_OPTS`, `_looks_like_path` removed or unused), `prd-toolkit/agents/prd-tester.md`, `prd-toolkit/skills/testing-from-prds/SKILL.md`
- Test: `prd-toolkit/tests/test_guard.py`, `prd-toolkit/tests/test_tester_agent.py`

**Interfaces:**
- Produces: `REFUSED_OPTS = frozenset({"--pyargs", "--doctest-modules", "--doctest-glob", "--rootdir", "--confcutdir"})`; `VALUE_OPTS: dict[str, str]` mapping each value-taking option (short and long) to `"path"`, `"count"` (`-n`) or `"text"`; `_check_harness_args(ctx, rest: list[str], base: Path) -> str | None` returns the deny message or `None`.

- [ ] **Step 1: Write the failing tests** in `test_guard.py`, each a harness command from the toolkit's `testing.md` followed by the extra arguments:
  - refused with `is not under a test root`: `scripts`, `.`, `..`, `prdlint`, `tests/../scripts` (Review Focus 4);
  - refused with `is refused after a harness command`: each of `REFUSED_OPTS`, `--pyargs prdlint`, `-p xdist`, `-pxdist`;
  - refused with `unquoted glob in`: `-k s*`, `tests/test_[a]*.py`, and zsh's `^` and `#` in an argument;
  - `-n 3` and `-n auto` pass; `-n many` refused;
  - pass: `tests/prd/test_x.py`, `tests`, `-p no:cacheprovider`, `--tb=short`, `-k 'T-015*'`, `-q -x`, `--maxfail 2`;
  - the 0.8.4 leftovers: `grep -e x <outside path>`, `grep --exclude-from=x <test path>`, `grep --exclude-dir=x <test path>` refused; `grep 'a^b' <test path>` passes quoted and is refused unquoted.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** spec section 11; then pin in `test_tester_agent.py` that `prd-tester.md` and `testing-from-prds` name the refused options and the unquoted-glob rule, and edit both texts.
- [ ] **Step 4: Run `test_guard.py` and `test_tester_agent.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `fix(prd-toolkit): the tester guard checks every harness argument`.

### Task 6: several human steps in one confirm (spec 5.1)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/deploy.py` (`confirm`, `run_steps`, `finished_envs`, `_used_or_unfinished`), `prd-toolkit/scripts/prd_deploy.py` (`confirm`'s argv), `prd-toolkit/scripts/prdlint/gates.py` (the deploy-step gate)
- Test: `prd-toolkit/tests/test_deploy.py`, `prd-toolkit/tests/test_deploy_check.py`, `prd-toolkit/tests/test_gates_list.py`

**Interfaces:**
- Produces: `deploy.confirm(prd, repo_root, run_id, pairs: list[tuple[int, str]]) -> None`, all-or-nothing under `run_lock`, raising `ValueError` naming the bad pair; `prd_deploy.py confirm <prd> --run ID --step N --reply TEXT [--step N --reply TEXT …]` (argparse `action="append"` for both, equal counts checked); the log keys of the Global Constraints ruling.

- [ ] **Step 1: Write the failing tests** on the `deploy_fixture.py` repo with a runbook of agent step 1, human steps 2, 3 and 4, agent step 5:
  - stopped at 2, `confirm` with pairs 2, 3, 4 then one `resume`: steps 3 and 4 recorded `confirmed_ahead`, step 5 runs, exit 0, the close check exits 0;
  - pairs 2, 4 (a gap), 2, 3, 5 (an agent step), 3 alone (not the stopped step), an empty reply, unequal `--step`/`--reply` counts, a step past `--until`: each exit 2, nothing appended;
  - `prd_gates.py list` after the ahead confirm shows no gate for steps 3 or 4;
  - Review Focus 1: a 0.8.4-shaped log (no `ahead` keys), stopped at 2, confirmed for 2 alone and resumed, stops at 3 as before.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_deploy*.py`, `test_gates_*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): one confirm covers consecutive human steps`.

### Task 7: an error entry during a stopped run (spec 5.2)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/deploy.py` (`_moved`, `close_findings`, `detected_names_failure`)
- Test: `prd-toolkit/tests/test_deploy.py`, `prd-toolkit/tests/test_deploy_check.py`

**Interfaces:**
- Produces: `deploy.run_entries_only(prd, repo_root, header, run_id) -> bool`, true when the tracked tree's only change is `errors.md` gaining entries, each open, unclassified, with `Detected:` naming `run_id` and a step; `_moved` skips its tracked-tree reason when it is true; `close_findings` accepts such entries on any run.

- [ ] **Step 1: Write the failing tests:**
  - a stopped run, `prd_error.py new` with `Detected:` naming the run and step 2, uncommitted: `resume` proceeds; the close commit holds the entry and the close check exits 0 on a run that did not fail;
  - refused, each with "the tracked tree has changes": an entry naming another run; an entry plus an edit to another file; Review Focus 2 (the entry plus one word changed in an older entry); a committed entry (HEAD moved, as today);
  - a failed run's own entry still passes the close check, as today.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_deploy*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): an error entry recorded mid-run passes resume`.

### Task 8: level timeouts, the branch note and `matches` at deploy (spec 5.3, 5.4, 5.5)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/deploy.py` (`_execute`, `_prints_ok`, `_agent_record`, `_tests_records`, `run_steps`, `close_findings`), `prd-toolkit/scripts/prd_deploy.py` (`--timeout` default, the branch note), `prd-toolkit/scripts/prdlint/packs.py` (a level's optional `timeout`, a positive integer), `prd-toolkit/references/prd-format.md` (the `Timeout` and `Branch` columns, `matches`, the backtick limit), `prd-toolkit/references/contract-types.md` (a level's `timeout`)
- Test: `prd-toolkit/tests/test_deploy.py`, `prd-toolkit/tests/test_deploy_check.py`, `prd-toolkit/tests/test_packs.py`

**Interfaces:**
- Consumes: Task 4's `Testing.timeouts`, `Operations.branches`, `Step.matches`.
- Produces: `deploy.level_timeout(prd, level: str, given: int | None) -> tuple[int, str]` (seconds and the message's parenthesis); `run_steps(..., timeout: int | None)`; `deploy.branch_note(prd, repo_root, envs: list[str]) -> str | None`; `_matches_ok(out: bytes, pattern: str) -> bool`.

- [ ] **Step 1: Write the failing tests:**
  - a `tests` step with two levels, one `Timeout` 2 running `sleep 5` and one with no Timeout running `true`: the first fails with `timed out after 2 s (the <level> level's Timeout)`, the second passes; with `--timeout 30` both pass; Review Focus 3;
  - a `Run:` command still times out at the default when no `--timeout` is given (shorten through the module constant, as `buildcheck.TIMEOUT` is in 0.8.4's tests);
  - Environments with `Branch` `release` and the run on `work`: stderr holds the note at the finish, exit unchanged; on `release`, no note; detached HEAD names `a detached HEAD`; `prd_deploy.py check` prints the note and exits 0;
  - `matches` `^deployed [0-9a-f]{7,40}$` passing on `deployed 3a27030` and failing with `no stdout line matches '…'` on `deployed`;
  - a pack level `timeout: 0` or `timeout: x` is a manifest error; `timeout: 1200` loads.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement; write the reference text.**
- [ ] **Step 4: Run them and `test_deploy*.py`, `test_packs.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): per-level deploy timeouts, the close-branch note and matches Checks`.

### Task 9: `prd_change.py pack` (spec 6)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py` (a `pack` function, a `BUMP_RULES` row), `prd-toolkit/scripts/prd_change.py` (the `pack` subcommand), `prd-toolkit/scripts/prdlint/change_approve.py` (`_commit` stages the re-vendored pack), `prd-toolkit/scripts/prdlint/hooks.py` (install's hint)
- Test: `prd-toolkit/tests/test_change_record.py`, `prd-toolkit/tests/test_change_approve.py`, `prd-toolkit/tests/test_hooks_packs.py`, `prd-toolkit/tests/test_changing_scripts.py` (the table test)

**Interfaces:**
- Produces: `change.pack(repo_root: Path, prd_root: Path, name: str, version: str, today: str) -> Recorded` (as `record` returns), raising the existing `change.ChangeError(text)` for the refusals of spec 6, which `prd_change.py` already prints as `refused: <text>` with exit 1; `prd_change.py pack <prd_dir> <name> <X.Y.Z>` with exits 0, 1 (`refused: …`), 2; `change_approve.approve` stages `.prd-toolkit/packs/<name>/` and `.prd-toolkit/pack-sources.json` when the base-to-working diff moves a `Pack:` or `Target: pack` version.

- [ ] **Step 1: Write the failing tests** on a scratch PRD naming `notes-pack 0.1.0` in §1 and in one `Target:` line, with a plugin source holding `0.1.1`:
  - `pack … notes-pack 0.1.1`: both lines move, sources kept; version and `updated` bumped as a patch; the §14 row and IDs cell of the Global Constraints;
  - refused (exit 1): a pack no line names; `0.1.2`, which the source does not hold; an uncommitted edit elsewhere in the PRD folder; a PRD naming only the built-in default (no version line);
  - `bump` on that diff reports `patch` for each moved line, and the skill-table test holds `changing-prds`' table equal to `BUMP_RULES` with the new row;
  - `install` against the `0.1.1` source before the change: the refusal ends with the hint;
  - after `pack`, `install` and `approve`: the approval commit holds the PRD, `.prd-toolkit/packs/notes-pack/` and `pack-sources.json`; lint exits 0 on it.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_change_*.py`, `test_hooks_*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_change.py pack moves a PRD to a new pack version`.

### Task 10: complete IDs cells (spec 7)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py` (`_IGNORED_FIELDS`, `_diff_blocks`, `_diff_cases`)
- Test: `prd-toolkit/tests/test_change_bump.py`, `prd-toolkit/tests/test_change_record.py`, `prd-toolkit/tests/test_change_ids.py`

**Interfaces:**
- Produces: a `BumpItem` per moved `Status:` value, level `patch`, reason `status <old> → <new>`; `_diff_blocks` and `_diff_cases` emit items for a new or removed block's ACs and its cases' T-ids at that block's level.

- [ ] **Step 1: Write the failing tests:**
  - FR-003 `live (since 1.0.0)` → `approved`: `bump` prints `patch FR-003 features/<area>.md:<line> status live (since 1.0.0) → approved`; `record`'s IDs cell holds `FR-003`; the level stays `patch`;
  - a new FR-012 with AC-012.1 and T-012.1: the cell holds `FR-012, AC-012.1, T-012.1`; the level stays `minor`;
  - a block removed with its test case T-004.2 deleted: the cell holds the block's ID, its ACs and `T-004.2`; then `ids next … T-004` prints `T-004.3`;
  - the `Source:` and `Acceptance (EARS)` fields are still ignored.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_change_*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `fix(prd-toolkit): the change books name moved statuses and every new or removed ID`.

### Task 11: STALE judged by the cited line (spec 8)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/context.py` (`_stale_reason`, `_excerpt`, `_code`, `build_pack`'s stale scope), `prd-toolkit/scripts/prd_context.py` (the exit)
- Test: `prd-toolkit/tests/test_context_implement.py`

**Interfaces:**
- Produces: `context.line_state(root: Path, path: str, line: int, sha: str) -> tuple[str, int | None, str | None]`, the state `"current"`, `"moved"` (with the new line) or `"stale"` (with the reason); `Item.stale` set only for blocks in scope; `Item.counted: bool`, false for a block pulled in through `Traces:`.

- [ ] **Step 1: Write the failing tests** on the `context_fixture.py` repo:
  - the file edited elsewhere, cited line unchanged: no STALE, exit 0;
  - two lines inserted above the cited line: `MOVED: line 10 is now line 12`, exit 0;
  - the cited line deleted: `STALE: the cited line's text is gone`, exit 1; the text now on two lines: `… appears 2 times`, exit 1;
  - a blank cited line in a changed file: STALE by the old rule;
  - `--req FR-002` where FR-002 is current and the UJ it traces is stale: the UJ's line ends ` (pulled in; not counted)`, exit 0;
  - Review Focus 5: a CRLF file, cited line unchanged: current.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_context*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): STALE judged by the cited line, the exit scoped to the blocks asked for`.

### Task 12: `--sources` in the build check (spec 9)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/buildcheck.py` (a `sources_findings` beside `diff_findings`), `prd-toolkit/scripts/prd_build_check.py` (`--sources FILE`, with `--diff` only)
- Test: `prd-toolkit/tests/test_build_check.py`

**Interfaces:**
- Produces: `buildcheck.sources_findings(repo_root: Path, rng: str, text: str) -> list[str]`, run through `_run` so its `git diff -U0` keeps `TIMEOUT`; `--diff R --sources F` prints `diff_findings` then `sources_findings`, exit 1 when either is non-empty.

- [ ] **Step 1: Write the failing tests** on a repo with one round commit changing lines 12–30 and 55–61 of `src/x.py` and deleting lines after 80:
  - `FR-012: src/x.py:20` passes; `src/x.py:40` gives the outside line with `hunks 12-30, 55-61`; `src/y.py:1` (unchanged) gives the not-changed line; the deletion point passes at both lines the spec names; `garbage` gives the malformed line;
  - `--sources` without `--diff` is a usage error, exit 2; `--diff` without `--sources` is unchanged.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them and `test_build_check*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): the build check holds SOURCES lines to the round's hunks`.

### Task 13: the published page draws its diagrams (spec 10)

**Files:**
- Create: `prd-toolkit/scripts/prdlint/diagrams.py`, `prd-toolkit/tests/test_diagrams.py`
- Modify: `prd-toolkit/scripts/prdlint/publish.py` (`_fence`, the page's figure style), `prd-toolkit/scripts/prd_publish.py` (the dependency header, stderr notes), `prd-toolkit/templates/publish/page.html` (the `figure.diagram` style), `prd-toolkit/tests/test_publish.py`, `prd-toolkit/tests/test_publish_overview.py`, `prd-toolkit/tests/fixtures/publish/orders.html` (regenerated once)

**Interfaces:**
- Consumes: Task 1's renderer, version and call.
- Produces: `diagrams.render_svg(source, number) -> str` and `diagrams.Fallback(reason)` (Global Constraints ruling); `diagrams.check_svg(svg: str) -> str | None` (the refusal reason, or `None`); `publish` collects `(file, line, reason)` notes, and `prd_publish.py` prints each.

- [ ] **Step 1: Write the failing tests:**
  - `test_diagrams.py`: the toolkit's §4 diagram renders to `<svg` holding each node label, with `id="diagram-1"`, really rendered (never skipped); `check_svg` refuses each of `<script`, `onload=`, `href="http…"`, `<foreignObject`, `url(http…)`, and allows `url(#arrow)`; a source with a syntax error raises `Fallback`;
  - `test_publish_overview.py`: with `render_svg` stubbed to return a fixed SVG, the Overview and Technical tabs hold `<figure class="diagram">`, the closed `<details>` with `Diagram source` and `<pre class="mermaid-source">`, and no `pre class="mermaid"`; with it stubbed to raise `Fallback("x")`, today's `<pre class="mermaid">` and the stderr note naming `prd.md:<line>`; the render exits 0 either way;
  - `test_publish.py`: `test_loads_nothing` passes on the page with a stubbed SVG.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement; regenerate the golden page once with the renderer stubbed,** and read its diff: only the diagram markup and its style change.
- [ ] **Step 4: Run them and `test_publish*.py`, the vendor refresh, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): the published page draws its diagrams as inline SVG`.

### Task 14: the skills (spec 13)

Required skill: `superpowers:writing-skills`.

**Files:**
- Modify: `prd-toolkit/skills/deploying-from-prds/SKILL.md`, `running-a-deploy.md` (items 1 to 5), `prd-toolkit/skills/changing-prds/SKILL.md` (item 6's flow and its bump row; item A's ignore list), `prd-toolkit/skills/building-from-prds/SKILL.md`, `running-a-build.md` (MOVED and the new STALE reasons; step 4's `--sources`), `prd-toolkit/skills/publishing-prds/SKILL.md` (rule 5), `prd-toolkit/skills/authoring-prds/SKILL.md`, `prd-toolkit/skills/adopting-prds/SKILL.md` (a pack level's `timeout` into Levels)
- Test: `prd-toolkit/tests/test_deploying_skill.py`, `test_building_skill.py`, `test_publishing_skill.py`, `test_packs_skills.py`; Create: evals `prd-toolkit/evals/deploy-confirms-named-steps/` and `prd-toolkit/evals/publish-own-artifact/` (`case.yaml`, `prompt.md`, `scaffold.sh`, `graders/`, as `adopting-confirm-headless-fallback/`)

- [ ] **Step 1: Write the failing pins:** `deploying-from-prds` passes a later `--step` only for a step the owner's reply names, never asks whether later steps are done, records a mid-run entry without committing it, names the Timeout column and that `--timeout` overrides it, tells the owner to push the close to the branch the note names and never pushes it, and shows `matches`; `changing-prds` runs `prd_change.py pack` then `install` from the plugin then the approval, with its bump row, and no longer lists block `Status:` lines as ignored; `running-a-build.md` step 4 writes the SOURCES field to a file outside the PRD folder and passes `--sources`, and both build texts name MOVED; `publishing-prds` rule 5 says its own Artifact, never a file inside another; authoring and adoption copy a level's `timeout`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: The evals' RED baselines** on the unchanged skills: (a) a stopped run at step 2 and the reply "done with 2; 3 and 4 were done in the same session" — record whether the session confirms 3 and 4 with their own words, and whether it confirms a step the reply does not name; (b) "publish the PRD into the design artifact as `prd.html`" — record whether it publishes the page as its own Artifact. Write both to `evals/BASELINE.md`.
- [ ] **Step 4: Edit the skills.**
- [ ] **Step 5: Run the pins, then both evals at 3 runs** (`claude plugin eval`); record the with/without scores. Below 3/3 is fixed in the skill text, never the grader.
- [ ] **Step 6: The vendor refresh, CI parity. Commit** `feat(prd-toolkit): the skills for multi-step confirm, mid-run entries, pack bumps, MOVED, --sources and own-Artifact publishing`.

### Task 15: release text and 0.8.5 (spec 13)

**Files:**
- Modify: `prd-toolkit/README.md` (Deploying, Packs, Publishing, Hooks and CI; Known limits (0.8.5); the 0.8.5 changelog entry and upgrade note; the 0.8.4 entry's live-proof line; the mermaid lines at today's :682, :762, :798), `docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md` (section 8's mermaid line, with a Revisions line), `prd-toolkit/tests/test_release_0_6.py` (its README sentence), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` (version `0.8.5`), the repo's `.prd-toolkit/`
- Create: `prd-toolkit/tests/test_release_0_8_5.py` (as `test_release_0_8_4.py`)

- [ ] **Step 1: Write the failing pins:** the three version files say `0.8.5`; the changelog entry names each item 1–11, A and B, the three `lint-cli` FRs of Task 3, and the upgrade note's three sentences; the 0.8.4 entry holds the live-proof line of spec 13; the README says where a diagram draws, and no longer says "No viewer draws it".
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Write the text; bump the versions; the vendor refresh;** then `uv run --script .prd-toolkit/prd_block.py docs/prd/prd-toolkit`, its own call, which refreshes the READMEs and `CLAUDE.md` for 5.2.0.
- [ ] **Step 4: Run the pins, CI parity,** `uv run --script .prd-toolkit/prd_block.py --check docs/prd/prd-toolkit; echo "prd-block-exit=$?"` (0), lint and trace (each `; echo "prd-…-exit=$?"`, both 0).
- [ ] **Step 5: Commit** `feat(prd-toolkit): 0.8.5 release text and version`, staging the READMEs and `CLAUDE.md` by path.

### Task 16 (controller-run, with Ivan): Proof (spec 16)

**Files:** none committed but the proof record in the 0.8.5 changelog entry.

- [ ] **Step 1:** In a scratch repository under the session scratchpad, a PRD whose runbook has three consecutive human steps, a `tests` step whose level has `Timeout` 2, an Environments `Branch` the run is not on, and a `matches` Check: run it; at step 2 record an error entry with `prd_error.py new` naming the run, uncommitted; confirm 2, 3 and 4 in one call; resume once; close; `prd_deploy.py check` exits 0 and prints the branch note. Read each behaviour of spec 5 off the log.
- [ ] **Step 2:** In a scratch repository, `prd_change.py pack` moves a PRD from a pack's `0.1.0` to `0.1.1`; install, approve on a reply typed for the scratch repo (Ivan's standing authorization covers routine replies in scratch repos only); the approval commit holds the vendored pack; lint exits 0.
- [ ] **Step 3:** `/prd-publish` the toolkit's PRD and publish it as its own private Artifact; in Chrome its diagrams are SVG on the Overview and Technical tabs; open the HTML file in Chrome straight from disk and the diagrams draw there too. Show Ivan; delete the Artifact only on his word.
- [ ] **Step 4:** Dispatch `prd-tester` in `suite` mode for one `lint-cli` T-id, with a caller note to run the harness once with each refused example of spec 11; check from its report that each was refused with its message and the plain harness ran.
- [ ] **Step 5 (Ivan):** on his request in his own words, push and open the PR. Record `test-unit`'s CI time against PR #22's 21 minutes.
- [ ] **Step 6:** Record what was proven (the commits, the CI run and times) in the 0.8.5 changelog entry. Commit `docs(prd-toolkit): 0.8.5 proof record`.
