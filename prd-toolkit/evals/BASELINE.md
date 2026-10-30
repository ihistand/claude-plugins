# `prd-toolkit` eval baseline

## 0.3 baseline (2026-10-30, `--runs 3`)

Recorded **2026-10-30** on branch `feat/prd-toolkit-0.3` at `--runs 3`, model `sonnet`, on Claude Code
2.1.314. `suite.plugins[].path` is the worktree's `prd-toolkit`. The manifest still says 0.2.0
(the version bump is a later task). Only the five cases touched by the context pack and the
move of the adoption map to `adoption.md` were run; the other three keep their 0.2 rows below.

Command (from the repo root): the 0.2 command below, with `--case <name>` added, once per case
(`--case` takes one glob). The cases ran at the same time, so each one's `--json` is its own file.

| Case | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `change-uses-context-pack` (new) | 1.00 | 0.67 | +0.33 | First run: with 0.33/0.67/0.67, and `ran-pack` failed 2/3 (the agent invoked the skill, then `cat` the PRD files through Bash and never ran `prd_context.py`). Skill fix (rule 6 and step 1 now say to run the pack as the first look at the PRD, and that `cat`, `head`, `sed` or `grep` of a PRD file is opening it; pinned in `tests/test_context_routing.py`) and a narrowed grader, then a re-run: 3/3 at 1.00. Fix round 1 scoped rule 6's last sentence (another area's files come from the pack; the area's own test cases are opened only to revise them in step 2); re-run after that wording: with 3/3 at 1.00, without 0.67 x3. Without the plugin, `ran-pack` fails 3/3 (no pack script) and the other three pass, so Δ comes from the pack. |
| `adoption-second-area-minor` | 1.00 | 0.53 | +0.47 | The two graders that read the map now read `adoption.md`. Without the plugin, `tester-dispatched` and `suite-mode` fail 3/3 and one run lacks the changelog row. |
| `adopting-trigger` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2. |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2, run 3 times again with the pack in the skill. |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2. |

### Ruling: `no-test-cases-read` is narrowed to `test-cases/api.yaml`

As first written the grader forbade any Read under `/test-cases/`. It failed 2 of 3 with-arm runs.
In run 3 (trace `/private/tmp/e-eOLpqa`) every such Read came after the `prd-toolkit:prd-tester`
dispatch of the dry run: the tester reads the area's `test-cases/import.yaml` to write its tests, and
these graders see subagent calls. The area's own test cases are not a pack bypass, so the grader
now forbids only the other area's `test-cases/api.yaml`. `no-other-area` (`features/api.md`) is
unchanged and passed in every run, with and without the plugin.

### Gate verdict (0.3, five cases run)

- **Tier 1, every `skill-fired` passes in the with arm: PASS** (15/15 over the five cases, and the re-run of the new case 3/3).
- **Tier 2, no triggering case at Δ ≤ 0: PASS.** Lowest Δ is `change-uses-context-pack` at +0.33.
- `suite.plugins[].path` is the worktree: PASS.

### The map in `adoption.md`

The adoption map is `adoption.md` beside `prd.md`; §8 of `prd.md` only points to it. In this
file, the 0.2 and 0.1 sections and the files in `baselines/` describe the older layout, with the
map in §8, and stay as recorded.

## 0.2 baseline (2026-10-30, `--runs 3`)

Recorded **2026-10-30** on branch `feat/prd-toolkit-0.2` at `--runs 3`, model `sonnet`, on Claude Code
2.1.314. `suite.plugins[].path` is the worktree's `prd-toolkit`. The manifest still says 0.1.0,
because the version bump is a later task.

Command, from the repo root. `-j` only runs cases in parallel. `--keep-temp` and `--json` keep the
answers so they can be read afterwards. `--case <glob>` limits a re-run to the affected cases.
None of these changes a score.

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --json <out>.json --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

### Current baseline

Each row is the latest `--runs 3` result for that case. Rows marked **re-run** came from a
single-case re-run after a ruling or a grader change (see "Re-runs" below). The other rows come
from the full-suite run. "Re-graded offline" means the changed graders were applied to that
run's kept traces with the same JavaScript regexes; nothing was run again.

| Case | with | w/out | Δ | Source | Notes |
|---|---|---|---|---|---|
| `adopting-trigger` | 1.00 | 0.00 | +1.00 | re-run (fix round 1) | The prompt names `docs/prd/notes/`. The skill fired 3/3, and each run wrote `docs/prd/notes/features/notes.md` with at least one `Source: src/notes/<file>:<line> @<sha>` line, which is all `wrote-area-file` proves. Without the plugin, all 3 runs wrote one flat `docs/prd/notes/PRD.md`. |
| `tester-stays-out-of-src` | 1.00 | 0.61 | +0.39 | full run, re-graded offline (fix round 1) | **Dry run.** The caller dispatched `prd-toolkit:prd-tester` (by `subagent_type`) with `Mode: dry run` 3/3, and the tester wrote only to `tests/.prd-dry-run-*`. Neither arm Read `src/notes`, or Read, Glob or Grep `tests/` outside that directory. Without the plugin, `tester-dispatched` and `dry-run-tests-written` fail. One without run also fails the sharpened Glob grader, because its pathless `**/*prd-tester*` lists the whole repository: that run is 0.50, the other two are 0.67. That arm never reads `src/notes`, so Δ comes from the dispatch, not from the src read. |
| `adoption-second-area-minor` | 0.80 | 0.60 | +0.20 | re-run; re-graded offline (fix round 1), unchanged | The start state has `export` `confirmed` (FR-003 `live (since 1.1.0)`, no bug), and the prompt approves only "if its gates pass". Runs 1 and 3 of the with arm went the whole way: suite (`T-003.1: pass`), dry run, trace, then `1.1.0` with its §14 row, the row `adopted` and `Approved`. Run 2 ran the suite, then stopped when one compound Bash call (the dry-run snapshot, with `rm -f $S/*`) was denied in don't-ask mode, and took that as "Bash is denied". Without the plugin, the agent marks the area adopted at 1.1.0 with no tester and no suite, so it fails `tester-dispatched` and `suite-mode`. |
| `authoring-new-prd` | 1.00 | 0.00 | +1.00 | re-run (fix round 1) | The prompt names the slug `link-shortener`. The skill fired 3/3, here and in the 6 runs before. `marks-unknowns` reads `docs/prd/link-shortener/prd.md`, and passes only on an assumption with a digit or on a marker that is not in the template. `wrote-prd` matches the created path. Without the plugin, the agent writes one flat `docs/prd/link-shortener.md`, or `docs/prds/…`, and runs no lint. |
| `authoring-not-for-readme` | 1.00 | 1.00 | 0.00 | re-run | Must-not-trigger case; Δ 0 is by design. After the description change, the skill fired in neither arm (0/6). |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | full run | Same as 0.1: without the skill, no `version: 2.0.0` and no 2.0.0 changelog row (3/3). |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | full run | Same as 0.1: without the skill, FR-003 is reused for the archive feature (3/3). |

### Gate verdict (current baseline)

- **Tier 1, every `skill-fired` passes in the with arm: PASS.** `adopting-trigger` 3/3,
  `authoring-new-prd` 3/3 (9/9 over its three re-runs), and both `changing-*` cases 3/3.
  `authoring-not-for-readme` correctly fires nothing.
- **Tier 2, no triggering case at Δ ≤ 0: PASS.** The lowest triggering Δ is
  `adoption-second-area-minor` at +0.20; `authoring-not-for-readme` is Δ 0 by design.
- `suite.plugins[].path` is the worktree: PASS.

### Full-suite run (2026-10-30T05:24Z, historical within 0.2)

The skill commit `56e0cde` (template copied with Read and Write) was in place. The earlier
versions of the three re-run cases scored:

| Case | with | w/out | Δ | What changed afterwards |
|---|---|---|---|---|
| `adopting-trigger` | 0.67 | 0.00 | +0.67 | Run 1 wrote `features/notes.md` with a Bash heredoc, so the `tool_used: Write` grader failed it. The grader became a `target: files` regex. |
| `adoption-second-area-minor` | 0.00 | 1.00 | −1.00 | The start state had `export` `not started`, and the prompt pre-confirmed requirements that did not exist yet. The skill rightly refused (rule 4), while the no-plugin agent bumped to 1.1.0 with no suite. Ruling: start from `confirmed`, approve only if the gates pass, and grade tester, suite, row, version and changelog. |
| `authoring-new-prd` | 0.50 | 0.00 | +0.50 | Run 1 skipped the skill "because that skill interviews you and you asked for no questions". Run 3 wrote the files with Bash heredocs, and the `tool_used: Write` graders failed them. Then the description gained the no-questions clause, and the two graders became file and trace graders. |
| `authoring-not-for-readme` | 1.00 | 1.00 | 0.00 | Re-run only to confirm the description change does not make it trigger. |
| others | as above | | | |

### Re-runs

| Case | Why | Runs |
|---|---|---|
| `adopting-trigger`, `authoring-new-prd` (fix round 1) | The prompts now name the folder, so the content graders can read a fixed path. A prompt change cannot be re-graded offline, so both cases were run again. | 3 each |
| `tester-stays-out-of-src` (fix round 1) | The graders are now anchored on `subagent_type`, and the Glob and Grep graders sharpened. Re-graded offline on the full run's kept traces, plus hand-made inputs. | 0 |
| `adoption-second-area-minor` (fix round 1) | `tester-dispatched` and `suite-mode` are anchored on `subagent_type`. Re-graded offline, and the scores are unchanged. | 0 |
| `adopting-trigger` | grader became `target: files` | 3 |
| `adoption-second-area-minor` | ruling 1: confirmed start state and new graders. The first re-run scored 0.60/0.60 (Δ 0). Its dry run raised two PRD gaps in the fixture (empty-store export, id restart), and one run hit the don't-ask Bash denial. Both gaps were closed in the fixture, and the second re-run is the row above. | 3 + 3 |
| `authoring-new-prd`, `authoring-not-for-readme` | ruling 3: description edit; ruling 2: file graders. A fixed-path `marks-unknowns` failed when a run chose the slug `internal-link-shortener`, so that grader became a trace regex and `authoring-new-prd` was run again. | 3 (both cases) + 3 (`authoring-new-prd`) |

### Running the 0.2 cases

- **Scaffolds.**
  - `adopting-trigger` imports `tests/legacy.py`'s `make_legacy_repo` through `python3 -B -c`,
    which gives 3 commits.
  - `tester-stays-out-of-src` calls `scaffolds/notes_repo.py confirmed` (6 commits), and
    `adoption-second-area-minor` calls `scaffolds/notes_repo.py export-confirmed` (7 commits).
    Both sync pytest into `.venv`.
  - The `-B` flag keeps `__pycache__` out of the plugin tree, and every scaffold writes only
    into the eval workspace.
  - `export-confirmed` is `adopted` (Approved 1.0.0, `T-002.1` `known-failing: E-001`,
    tester-written tests in `tests/`) plus the `export` area confirmed: FR-003
    `live (since 1.1.0)`, `T-003.1`, the PRD `In review`.
  - Lint and trace exit 0 in every mode.
  - The project file pins `[tool.uv] exclude-newer = "2026-10-01T00:00:00Z"`, so `uv.lock` and
    every commit SHA are the same on every build. Two builds were checked for identical SHAs. The
    pin was added after the recorded runs and changes no PRD or test file.
- **Subagent calls are graded.** `tool_used` and `trace` include the calls made inside an
  Agent-tool subagent. `dry-run-tests-written` proves it: only the tester writes into
  `tests/.prd-dry-run-*`, so its pass shows that the `max: 0` graders see the tester's own
  Read, Glob and Grep calls. Those graders also fire on the Task 6 suite transcript, where the
  tester reads `tests/test_notes.py`. So they are not vacuous.
- **`max: 0` needs `min: 0`.** `min` defaults to 1, so a lone `max: 0` reads "expected 1..0"
  and always fails.
- **The lint gate works under the eval sandbox.** With plain `Bash` granted, the compound
  `uv run --script ".../prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"` runs, and its tool
  result printed `prd-lint-exit=0`. `authoring-new-prd/graders/lint-exit-0.md` passes on that real
  output: 2/3 in the full-suite run of 2026-10-30T05:24Z (its run 1 skipped the skill), 3/3 in the
  `authoring-new-prd` re-run of the current baseline, and 1/1 in a with-only check run. No narrower `--allow-tools` pattern is
  needed.
- **The sandbox denies the plugin folder as a `cp` source.** The message is "cp to
  '<plugin>/templates/prd' was blocked by a deny rule". A `Bash(cp -R:*)` grant does not help.
  Before `56e0cde`, the adoption bootstrap stopped at `cp -R` (0/2 area files written), and
  authoring hand-wrote the files. Both skills now copy the template with Read and Write.
- **Bash heredoc writes miss `tool_used: Write` graders.** Grade what was written instead.
  - A `{source: file, path}` grader takes no glob: `docs/prd/*/prd.md` throws "does not exist".
    So the prompts of `authoring-new-prd` (slug `link-shortener`) and `adopting-trigger`
    (`docs/prd/notes/`) name the folder, and their content graders read a fixed path.
  - A `target: files` regex (`wrote-prd`) matches the paths the run created.
  - A content grader must not pass on the template copy, which 56e0cde makes the first Write. The
    template already holds markers, so `marks-unknowns` needs an assumption with a digit, or a
    marker that the template copy and its `{{owner}}` fill do not already hold.
    `tests/test_eval_graders.py` keeps its list in step with the template and checks the
    negatives: the copy, and the copy after invented-value Edits.
  - `wrote-area-file` needs a `Source: src/notes/…:<line> @<sha>` line, which a rename of
    `core.md` does not produce.
- **Graders anchored on `subagent_type`.** `tester-dispatched` and `suite-mode` match
  `"subagent_type": "(prd-toolkit:)prd-tester"`, so a general-purpose agent briefed "as
  prd-tester" does not count. The dry-run Glob and Grep graders catch absolute and relative
  `tests` paths, and a pathless repository-wide search (Glob `**/*.py`, Grep with no `path`).
  They let through the caller's lookup for `.prd-dry-run-*` and a pathless lookup by name such as
  `**/prd-tester*`.
- **One denied compound Bash call can end a run.** In don't-ask mode, a compound command with an
  `rm` on a variable path (`rm -f $S/*`, `rm -rf "$(cat …)"`) is denied. The agent then took
  "Bash is denied" as final and stopped: 1 of 3 `adoption-second-area-minor` with-arm runs in
  each re-run. Since `33903c5`, dispatching.md runs one command per Bash call with literal
  paths. The recorded `adoption-second-area-minor` row predates that change and has not been
  re-run.
- **`--case` takes one glob.** Repeating the flag keeps only the last.

## 0.1 baseline (historical)

Recorded **2026-10-29** for 0.1.0 at `--runs 1`, model `sonnet` (Claude Code 2.1.312), with
`suite.plugins[].path` confirmed as the worktree's `prd-toolkit`. Update when a bump is
accepted, and re-record at `--runs 3` before the first bump. The pressure-scenario baselines
that shaped the skills are in `baselines/`.

Command (from the repo root; the Write, Edit, Bash and pypi grants are what let the cases write
files and let `prd_lint.py` fetch its dependencies under the Bash sandbox):

```
claude plugin eval ./prd-toolkit --runs 1 --model sonnet --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit Bash "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

| Case | with (last) | w/out (last) | Δ | Notes |
|---|---|---|---|---|
| `authoring-new-prd` | 1.00 | 0.00 | +1.00 | Without the skill the PRD was one flat `PRD.md` (no `docs/prd/<slug>/` folder, no contracts or test cases), with unknowns tagged `[ASK]`/`[OPEN-n]` instead of `NEEDS CLARIFICATION` or a numbered assumption, and no lint run. |
| `authoring-not-for-readme` | 1.00 | 1.00 | 0.00 | Non-trigger case, so Δ 0 is the expected result: the Skill grader (`min: 0`, `max: 0`, `arm: both`) passes in both arms and a plain README is written. |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | Without the skill the 410 change was specced (tombstone table, `ORDER_DELETED`) but the PRD never reached `version: 2.0.0` and got no 2.0.0 changelog row. |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | Without the skill the agent did what the prompt said and rewrote the removed FR-003 as "Archive an order" (2.1.0) instead of allocating FR-005. |

### Gate verdict (0.1)

- Tier 1, every `skill-fired` passes in the with arm: **PASS** (3 of 3; `authoring-not-for-readme` correctly does not fire the skill)
- Tier 2, no triggering case at Δ ≤ 0: **PASS** (+1.00 on all three). `authoring-not-for-readme` is a
  must-not-trigger case and is Δ 0 by design.

### Running it (0.1)

- The cases use `--scaffold`; the two `changing-*` scaffolds copy `tests/fixtures/valid/orders`
  and `git init`. `changing-new-id-not-reused/c2_setup.py` turns the copy into the FR-003-removed
  start (lints clean).
- Under the Bash sandbox `uv run --script prd_lint.py` fetches pyyaml, sqlglot and
  openapi-spec-validator. Without the two `WebFetch(domain:...)` grants the fetch fails ("tunnel
  error"), and the agent sees the lint fail. With them, lint runs and reaches exit 0.
- Narrow Bash grants (`Bash(uv run *)` and similar) denied compound commands and in one run left the
  agent unable to lint, which failed `lint-ran`. Grant plain `Bash`.
- Results land in `evals/results/`, which is git-ignored.
