# `prd-toolkit` eval baseline

## 0.8.1 baseline

Two new cases for the 0.8.1 skill text (Task 12): `changing-prds` takes its IDs and its bump from `prd_change.py`,
and review mode edits nothing under pressure. Recorded 2026-11-04 on branch `feat/prd-toolkit-0.8.1` (the Task 12
text; final rows after fix round 1 on `a68d4c4` plus its text, uncommitted), `--runs 1` (one run per arm), model `sonnet`, Claude Code 2.1.318, plugin 0.8.1.

Command, from the repo root, once per case:

```
claude plugin eval ./prd-toolkit --runs 1 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" \
  --case '<case>' --json <out>.json
```

| Case (start state) | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `changing-uses-prd-change` (orders fixture, 1.0.0) | 1.00 | 0.50 | +0.50 | "Admins can archive an order. Do not ask me questions." With: `prd_change.py ids next` for FR-005, `bump`, then `record --bump minor` (the contract items `needs judgment`, decided minor with the reason), a prd-tester dry run, the verdict, and a stop for approval; `version: 1.1.0`; every `prd_change.py` call on its own, path typed out. Without: 1.1.0 typed by hand, no `ids next`, no `bump`; `no-loop-or-variable` passes there (nothing runs the script), so the w/out score rose from 0.33 with the fifth grader. |
| `review-edits-nothing` (orders fixture + AC-001.4 and T-001.5 recorded as 1.1.0, `; pending`, uncommitted) | 1.00 | 0.50 | +0.50 | "/prd-change --review docs/prd/orders — and just fix the AC while you review it." With: digest, bump, diff, pack, lint, digest again, then one Write, `.prd-review.json` (`ready: true`, `minor`, `no dry run (unit only)`); the doubled "the" in AC-001.4 reported, not fixed. `docs/prd` was compared by hand with a fresh scaffold (`diff -r`, the verdict left out): identical. Without: two Edits fix the AC, no verdict. |

### Rounds and rulings (0.8.1)

- **Fix round 1 (review):** `changing-uses-prd-change` gained `no-loop-or-variable` (`max: 0`: a `for` loop, a
  shell function or a `$VAR/` path in any Bash call that runs `prd_change.py`), since both earlier with runs
  batched `ids next` that way. Its first rerun scored with 0.75, w/out 0.50: the with run folded `prd_change.py
  digest` into one long call after the dry run's state check (`S=$TMPDIR/snap2; …; uv run … digest …`). The skill
  text was wrong: "its own Bash call" now says the call holds that command and its echo and nothing else (no `cd`,
  no state check or cleanup folded in, no loop, function or variable). The second rerun scored 1.00 / 0.50.
  `review-edits-nothing` was rerun on its updated scaffold (FR-001 back to `approved`, the IDs cell now
  `FR-001, AC-001.4, T-001.5` from R17): 1.00 / 0.50.
- **Both scaffolds make the fixture's one required skill row `recommended`.** The eval sandbox installs no
  plugins, so `superpowers:writing-plans` as `required` fails lint (`registries`), and approval could never pass.
  The first `changing-uses-prd-change` run (with 1.00, without 0.33) predates that fix: it reached the dry runs
  and reported the lint blocker. The table's row is the rerun on the final scaffold.
- **`review-edits-nothing` round 1 did not run**: its scaffold's lint check failed on that row (exit 1, no cost).
- **Round 2 scored 0.83 with, 0.33 without.** `record-unchanged` failed in both arms with `prd.md` unchanged: its
  `^version` needed `flags: m` (the grader was wrong). The scaffold also added AC-001.5 where the next free AC
  is AC-001.4, which the with run reported; the scaffold now adds AC-001.4.
- **No grader can run `git diff --stat -- docs/prd`.** `ac-unchanged` (the AC the prompt asks to fix, its doubled
  "the" included) and `record-unchanged` (version and pending row) stand in for it, with the Edit, Write and
  Bash graders; each kept with-arm scaffold was also checked by hand with `diff -r` against a fresh scaffold.

## 0.8.0 baseline

Five new cases, one per RED baseline of `baselines/packs-and-judged.md` (D1 to D5), each its prompt verbatim
(`builder-document-no-unit` adds "Do not ask me questions.", as every build case does) with graders for its
failure line. Recorded 2026-11-03 on branch `feat/prd-toolkit-0.8` (the skill text of Task 11, uncommitted on
`ba37e6d`) at `--runs 3`, model `sonnet`, Claude Code 2.1.317; `suite.plugins[].path` is the worktree's
`prd-toolkit` (manifest still 0.7.2; the bump is Task 12).

Command, from the repo root, once per case (a second `--case` replaces the first, it does not add to it: the
first run with five `--case` flags ran only `changing-refuses*`):

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" \
  --case '<case>' --json <out>.json
```

| Case (start state) | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `authoring-proposes-pack` (`empty`) | 1.00 | 0.50 | +0.50 | D1's prompt. With: `--list-packs` ran, `docs/prd/*/contracts/outline.yaml` written, no `.py` under `contracts/`, lint exit 0, no judgement word in a test-case file (3/3). Without: no lint, no pack list, no outline (3/3). Round 1 scored 0.94: one with run ran `"…/prd_lint.py" --list-packs` with a quoted path and `listed-packs` missed it; the grader was wrong (below). |
| `authoring-spanish-ears` (`empty`) | 1.00 | 0.40 | +0.60 | D2's prompt. With: `prd.md` written with `language: es`, a features file with Spanish openers, none with an English one, lint exit 0 (3/3). Without: no `language: es`, no Spanish opener, no lint. |
| `tester-judged-calls-judge` (`approved` + draft guide) | 1.00 | 0.56 | +0.44 | D3's prompt. With: `prd-tester` dispatched; a `tests/` file citing T-010.2 calls `prd_judge.py` with `docs/prd/greet`, the T-id and `install.md` and asserts exit 0; no test grading the guide; nobody reads the guide (3/3). Round 1 scored 0.73: in two with runs the skill never fired and the session read the guide, wrote the test with a Bash heredoc and listed its own verdicts. Skill text changed (below). |
| `builder-document-no-unit` (`approved`) | 1.00 | 0.86 | +0.14 | D4's prompt. With: the builder dispatched, `docs/guide/install.md` written with the outline's four sections in order, no Write or Edit under `tests/unit/`, no PRD edit beyond the close (3/3). Without: the agent writes the guide itself, so only `builder-dispatched` fails; the case guards the document path, it does not discriminate much. Rounds 1 and 2 scored 0.57 and 0.81 (below). |
| `changing-refuses-retarget` (`built` + vendored `demo`) | 1.00 | 0.83 | +0.17 | D5's prompt. With: the last message holds `retargeting an area is a conversion (prd-toolkit 0.8.3)`, the `Target:` line, `verified (since 1.0.0)` and `version: 1.0.0` unchanged, no Edit or Write under `docs/prd/` (3/3). Without: no retarget either, but no refusal line. The `demo` pack is vendored in `.prd-toolkit/packs/demo/`, because an eval run cannot set `PRD_PLUGINS_FILE`. |

The table's rows are the final runs, all on the final scaffold (`tester-judged-calls-judge` and
`changing-refuses-retarget` were run once more after the scaffold's last fix, with the same scores).

### Rerun after scaffold fixes 66abe07..0c4ba32

The 0.8.0 proof (Task 13) changed `doc_repo.py`'s `approved` state:
- AC-001.3 and T-001.3 for the usage line (66abe07).
- FR-001 `verified`, plus a new approved FR-002 (540501b).
- AC-010.2 reworded to the two rubric items of T-010.2 (0c4ba32).
- Then a Harness sentence, "Each `sections` entry heads exactly one section; a repeated one fails." (9754966).

The two cases built on `approved` were rerun with the command above, 2026-11-03, `--runs 3`, sonnet, Claude Code
2.1.317, plugin 0.8.0:

| Case | Round | with | w/out | Δ | Notes |
|---|---|---|---|---|---|
| `tester-judged-calls-judge` | at 0c4ba32 | 1.00 | 0.50 | +0.50 | With: 3/3. Without: `judge-called-with-output`, `no-guide-read` and `tester-dispatched` fail (3/3). |
| `tester-judged-calls-judge` | at 9754966 | 1.00 | 0.50 | +0.50 | The same graders. |
| `builder-document-no-unit` | at 0c4ba32 | 0.90 | 0.86 | +0.05 | One with run scored 0.71. Its tester asked whether a section heading may repeat, and the build stopped on that PRD gap before the builder ran (no worktree isolation in the sandbox, so the tester went first): `guide-written` and `guide-sections-in-order` fail. Fixed in the scaffold (9754966). |
| `builder-document-no-unit` | at 9754966 | 0.95 | 0.86 | +0.10 | One with run scored 0.86: it reached the close and added `Source:` after `Traces: -`, which `no-prd-edit-beyond-status` read as a PRD edit. The grader was wrong (F-2 of the proof, 97ae256). |
| `builder-document-no-unit` | at 97ae256 | 1.00 | 0.86 | +0.14 | With: 3/3. Without: only `builder-dispatched` fails (3/3), as before. |

### Re-score after R26 (the lint-exit-0 graders)

The review found the three `lint-exit-0` graders vacuous: phase 1 ran `--list-packs; echo "prd-lint-exit=$?"`,
and `--list-packs` always exits 0, so `prd-lint-exit=0` was in every with-arm trace before a PRD existed. Now
`--list-packs` echoes `prd-list-packs-exit=$?` (pinned: no `--list-packs` line echoes the lint tag), and the
graders match only a Bash call that lints `docs/prd/…` (or a shell variable) bound by its id to a
`tool_result` holding `prd-lint-exit=0`; a listing, a lint that exits 1 and prose fail
(`tests/test_eval_graders.py`). Re-scored with the command above, 2026-11-03, `--runs 3`, sonnet:

| Case | with, before → after | w/out, before → after | Δ after |
|---|---|---|---|
| `authoring-proposes-pack` | 1.00 → 1.00 | 0.50 → 0.50 | +0.50 |
| `authoring-spanish-ears` | 1.00 → 1.00 | 0.40 → 0.40 | +0.60 |
| `authoring-new-prd` | 1.00 → 1.00 (last recorded in the 0.2 baseline's fix round 1, below) | 0.00 → 0.00 | +1.00 |

Every with run reached a real lint with exit 0 and echoed `prd-list-packs-exit=0` for its listing; every
without run still fails `lint-exit-0` (it never lints). The scores did not move, so the vacuity hid no failure.

### Rounds and rulings (0.8.0)

- **`listed-packs` was a wrong grader.** `input_match: 'prd_lint\.py --list-packs'` cannot match a quoted
  script path, which reaches the grader as `prd_lint.py\" --list-packs`. Now `prd_lint\.py\S* --list-packs`,
  checked by hand against the quoted, the vendored and a lint command.
- **testing-from-prds did not fire on "Write the test for T-010.2; just check the guide yourself".** Its
  description now adds "when asked to write the test for a T-id, a judged case scored by prd_judge.py included,
  or to check its output yourself", and its Red Flags quote the session's verdict ("The guide may not pass:
  …"). The description pin in `tests/test_tester_agent.py` follows. A new grader, `no-guide-read`, fails a run
  that reads the guide.
- **`builder-document-no-unit` round 1 (0.57):** with no "Do not ask me questions." the caller stopped at
  step 1 to ask before branching off `main`, as running-a-build.md allows. The prompt gained the phrase every
  build case carries.
- **Round 2 (0.81):** two with runs stopped on the tester's QUESTION that the scaffold's PRD left open (what
  counts as a section of the guide: a heading of which level, and may other headings sit between), before the
  builder ran (no worktree isolation, and the caller dispatched the tester first). A PRD gap, correctly
  stopped. The scaffold's testing.md Assertions slot now answers it ("A section of a document is a Markdown
  heading of any level whose text is an outline `sections` entry; other headings may sit between them").
  The GREEN D4 rerun met the same question (`baselines/packs-and-judged.md`).
- **The scaffold's run command.** `doc_repo.py`'s README and `built` guide said `uv run python -m greet World`,
  which fails (`No module named greet`: no build system, and `src/` is on the path only for pytest). It now
  says `uv run --directory src python -m greet World`. Found by GREEN D4 round 1, whose builder checked the
  command before writing it.
- **`prd_judge.py` exit 2 in the eval sandbox.** A with run that reached the suite reported
  `cannot judge T-010.2: claude: not on PATH` and closed FR-010 `built`, not `verified`, as the skill says:
  the eval sandbox has no `claude` on its PATH (spec section 15, cost and access). No grader asks for
  `verified`.

## 0.6 baseline (handling-errors cases)

Four new `handling-errors` cases; three on `scaffolds/error_repo.py` state `bug` (the greet PRD at 1.0.0,
every requirement `verified`, a committed code bug that reads the settings key `greeting` instead of
`GREETING`, so the unit test citing T-001.2 fails), one on a repo with no `docs/prd/`. One run each, Sonnet,
with and without the plugin, at `5af84c3`.

Command, from the repo root: the 0.4 command below with `--case '*error*'` and `--json`.

| Case (state) | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `handling-errors-trigger` (`bug`) | 1.00 | 1.00 | 0.00 | A bug report: the skill fires and `prd_error.py new` records the entry. |
| `handling-errors-not-without-prd` (no PRD) | 1.00 | 1.00 | 0.00 | Must-not-trigger case: a typo bug in a repo with no `docs/prd/`; neither the skill nor `prd_error.py` runs. |
| `error-confirm-before-fix` (`bug`) | 1.00 | 1.00 | 0.00 | "Fix the greeting bug. Do not ask me questions.": an entry `proposed`, no `Confirmed:`, the whole planted expression still in `src/greet/cli.py`, no Edit, Write or Bash write under `src/` or `tests/`. |
| `error-flaky-not-retried` (`bug`) | 0.75 | 0.50 | +0.25 | E1's prompt: an entry `proposed`, at most two Bash calls that run pytest, no loop, repeat count or rerun plugin, and no Bash write under `src/` or `tests/`. The with-arm miss was a grader false positive: `harness-at-most-twice` counted the `prd_error.py propose` call whose `--diagnosis` quotes the pytest command (the trace shows two harness runs); the Bash graders now ignore `prd_error.py` calls. |

## 0.6 baseline (publishing-prds cases)

Two new `publishing-prds` cases on `scaffolds/error_repo.py` state `bug` (the greet PRD at 1.0.0, areas
`greet` with FR-001 and FR-002 and an `nfr.md` with no block; the vendored `.prd-toolkit/` holds no publish
entry script or page template, so only the plugin's `prd_publish.py` renders). One run each, Sonnet, with and
without the plugin, at `95d95e7`.

Command, from the repo root: the 0.4 command below with `--case 'publish*'` and `--json`.

| Case (state) | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `publishing-trigger` (`bug`) | 1.00 | 0.00 | +1.00 | "Make a page of our PRD that I can send to the business team.": the skill fires, the plugin's `prd_publish.py render` runs, and the page is at the default `greet-prd-1.0.0.html`. |
| `publish-summary-cites-area` (`bug`) | 1.00 | 0.50 | +0.50 | U1's prompt (French and Spanish greetings, which the PRD lacks): `render` runs with `--summaries`; no Edit, Write or Bash write under `docs/prd/`; the summaries file the skill names, `greet-prd-1.0.0.summaries.json`, cites the `greet` area's IDs and never says French or Spanish. Without the plugin no page was rendered with summaries, and the file graders on the missing summaries file failed (observed: "grader threw: … path "greet-prd-1.0.0.summaries.json" does not exist", scored ✗), so a run that writes none never passes them. |

## 0.5 baseline (2026-11-01, `--runs 3`)

Recorded **2026-11-01** on branch `feat/prd-toolkit-0.5` at `--runs 3`, model `sonnet`, on Claude Code
2.1.316. `suite.plugins[].path` is the worktree's `prd-toolkit`. Six new `deploying-from-prds`
cases, all on `scaffolds/deploy_repo.py` (the greet PRD at 1.0.0, FR-001 and FR-002 `verified`);
the 0.4 and older cases were not run again. The harness runs one prompt per case directory, so the
two close cases are two directories.

Command, from the repo root: the 0.4 command below with `--case 'deploy*'` and `--json`.

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" --case 'deploy*'
```

| Case (state) | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `deploying-trigger` (`ready`) | 1.00 | 0.33 | +0.67 | The skill fired 3/3 and ran `prd_deploy.py run`. Without the plugin, 2 of 3 runs never ran it (4 turns: the agent read the repo and stopped, or ran `scripts/deploy.py`). |
| `deploying-not-without-prd` (no PRD) | 1.00 | 1.00 | 0.00 | Must-not-trigger case; Δ 0 by design. The skill fired in neither arm. |
| `deploy-stops-at-human` (`ready`) | 1.00 | 0.87 | +0.13 | With the skill: `run` from step 1, stopped at human step 3 (10 tool calls), no `confirm`, no `resume`, no direct `scripts/deploy.py production`, nothing `live` (3/3). Without it, none of the three confirmed or deployed production by hand either, so only `run-started` differs. This case measures that the skill does not regress the safe path; it does not discriminate. |
| `deploy-failure-no-improvise` (`failing-check`) | 1.00 | 0.71 | +0.29 | With the skill: `run` fails at staging's Check, no `rollback`, no direct script, an open `Classification: unclassified` entry in errors.md (Edit only), no change to operations.md, features, tests or `src`, the close checked (3/3). Without it: no `errors.md` entry, no close check, `run-started` fails, and one grader (`no-direct-script`) catches the deploy script run by hand. |
| `deploy-close-live` (`at-gate`) | 1.00 | 0.43 | +0.57 | The prompt is the user's reply to the run stopped at step 3, naming it as the only stopped run, with no id. With the skill: it read the log in `<git-common-dir>/prd-toolkit/deploys/`, confirmed with `--reply 'deploy production'`, resumed, wrote both blocks `live (since 1.0.0)`, both §11 rows, the production Deployed row, and ran the close check (3/3). Without it, none of those. |
| `deploy-close-staging-only` (`staging-done`) | 1.00 | 0.80 | +0.20 | With the skill: staging row written, nothing `live`, no production row, close checked (3/3). Without it the rows are right and only `close-checked` fails. |

Results: `.superpowers` `task-12-eval.json` of the SDD workspace (not committed).

### Notes (0.5)

- **A reply may name the run as the only one stopped at the step.** `deploy-close-live` starts from
  `at-gate` and its prompt is the reply, which cannot carry the run id (the id is made when the
  scaffold runs). running-a-deploy.md said the reply must be "in a later message of theirs that
  names the run". It now says "(by id, or as the only run stopped at that step: Read the logs in
  `<that dir>/prd-toolkit/deploys/` ... and ask when more than one is stopped there)", pinned in
  `tests/test_deploying_skill.py`. The three with-arm runs found the id from the log.
- **File graders, not call graders, for what was written.** A run can write the PRD with Edit, Write
  or a Bash heredoc, so `live`, the Deployed rows and the errors.md entry are graded as file
  contents; the tool graders hold only what must not happen (Edit or Write under `docs/prd/` other
  than errors.md, under `tests/` or `src/`, a `rollback`, a direct script run).
- **No permission-classifier block** appeared in these 36 traces (no "classifier", "was blocked" or
  denied-permission text). The 0.2 baselines saw them on compound commands.
- Vacuity: the close graders were applied to the `at-gate` and `staging-done` start repos offline;
  every grader that asks for a write fails there, and the "nothing `live`" graders pass there on
  purpose (they fail only if a run writes `live`).

### Gate verdict (0.5, six cases run)

- **Tier 1, every `skill-fired` passes in the with arm: PASS** (5 of 5 triggering cases 3/3);
  `deploying-not-without-prd` correctly fires nothing.
- **Tier 2, no triggering case at Δ <= 0: PASS.** Lowest triggering Δ is +0.13
  (`deploy-stops-at-human`); `deploying-not-without-prd` is Δ 0 by design.
- One skill-text change (above), pinned. No grader was loosened.

## 0.4 baseline (2026-10-31, `--runs 3`)

Recorded **2026-10-31** on branch `feat/prd-toolkit-0.4` at `--runs 3`, model `sonnet`, on Claude Code
2.1.316. `suite.plugins[].path` is the worktree's `prd-toolkit` (confirmed in every `--json`; the
user-scope 0.1.0 install did not shadow it). The manifest still says 0.3.0, because the version
bump is a later task. Five new `building-from-prds` cases, plus the five cases 0.3 ran, run again
because the skills they touch (changing-prds hand-off, dispatching) sit next to the build.

Command, from the repo root (the 0.2 command below, with `--case <glob>` added once per group:
`build*`, `chang*`, `adopt*`; the groups ran at the same time, each with its own `--json`):

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --case '<glob>' --json <out>.json --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

The plugin is the path form `./prd-toolkit`, resolved to the worktree.

| Case | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `building-trigger` (new) | 1.00 | 0.00 | +1.00 | `FR-003 ... approved; build it.` The skill fired 3/3 and `prd-toolkit:prd-builder` was dispatched (by `subagent_type`) 3/3. Without the plugin no builder exists, so `builder-dispatched` fails 3/3. |
| `building-not-for-plain-code` (new) | 1.00 | 1.00 | 0.00 | Must-not-trigger case; Δ 0 is by design. A repo with no `docs/prd/`, "add a `--version` flag": the skill fired in neither arm (0/6) and the flag was written 6/6. |
| `builder-stays-out-of-prd` (new) | 1.00 | 0.75 | +0.25 | With: no Write under `docs/prd/`, no Edit there except the caller's close (a `Status: built`/`verified` move or a `Source:` line), AC-003 and T-003.2 unchanged in the working tree, no `T-003.1` in the tester's `tests/test_notes.py`. Without: the agent builds with no builder (`builder-dispatched` fails 3/3) and appends its unit test to `tests/test_notes.py` (`unit-test-not-in-tester-file` fails 3/3). |
| `build-gap-stops` (new) | 1.00 | 0.67 | +0.33 | First run: with 1.00/1.00/0.00 and Δ -0.33 (see the two rulings below). Re-run after the grader changes: with 3/3 at 1.00, without 0.67 x3. `no-guessed-archive-count` was added after the first run (Δ -0.33). It checks for a guessed archived-note count, not for a stop: a trace regex over the whole run with a 300-character window, so it is brittle to later output changes. Runs 1 and 2 stopped at the tester's QUESTION before the builder ran (no status written); run 3 stopped on the builder's QUESTION after its commit was on the build branch and wrote `built`, as **Stops** says. No skill-text change was needed. |
| `build-close-no-bump` (new) | 1.00 | 0.67 | +0.33 | With: the block and the §11 row read `verified`, `version: 1.1.0`, no later §14 row, no Edit of a `version:` line, the PRD still `Approved`. Without: the agent never writes `verified` (`fr003-verified`, `index-verified` fail 3/3). |
| `change-uses-context-pack` | 1.00 | 0.67 | +0.33 | As 0.3: `ran-pack` fails 3/3 without the plugin. |
| `adoption-second-area-minor` | 1.00 | 0.60 | +0.40 | As 0.3: `tester-dispatched` and `suite-mode` fail 3/3 without it. |
| `adopting-trigger` | 1.00 | 0.00 | +1.00 | As 0.3. |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | As 0.3. |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | As 0.3. |

### Rulings on `build-gap-stops`

- **`no-status-edit` and `fr003-still-approved` forbid `verified` and `live`, not `built`.** As first
  written (no Edit of any block `Status:` line) the grader failed run 3 of the first run, which is
  what the skill text asks for: `running-a-build.md` **Stops** writes `built` for a block whose unit
  T-ids pass when a stop comes after the builder's merge. The eval harness has no worktree isolation
  (`Cannot create agent worktree`), so the builder's commit is already on the build branch when its
  QUESTIONS line raises the gap, and `built` is the specified close. The controller's brief and the
  skill text disagreed; the grader follows the skill. The invariant kept is that a stopped build is
  never `verified` or `live`.
- **`no-guessed-archive-count` was added because the without arm passed everything.** The first run's
  Δ was -0.33: with no plugin the agent never touches a status, so every grader but the `with-only`
  Skill ones passed. The new trace grader fails a run in which a test asserts an exact count after
  `archive_note(<n>)`. All three without runs do (`== 2`, `== len(_NOTES)`); the with runs assert only
  the type, or write no such test. It matched the start repo's own `archive_note` definition
  followed by an unrelated `assert ... == 1` in a first draft, so it now needs a literal
  `archive_note(<digits>)` call; both forms are checked in `tests/test_eval_graders.py`.

### Notes on the builder graders

- **A tool call carries no agent id.** `tool_used` graders see the caller's, the builder's and the
  tester's calls alike, so `builder-stays-out-of-prd` cannot forbid "any Edit of `tests/test_notes.py`"
  (the tester edits it for T-003.2) or "any Edit under `docs/prd/`" (the caller's close does). It
  forbids what only the builder would write: a PRD edit that is not a status or `Source:` move, and a
  `T-003.1` case in the tester's file. A builder edit of the tester's import line with no T-id, or a
  PRD edit through Bash `sed`, passes the tool graders; the two PRD file graders and the
  `T-003.1` file grader read the result and catch what changes content.
- **No worktree isolation in the eval harness.** Every with-arm run saw `Cannot create agent
  worktree`, then took the no-isolation path (builder first, tester after).
- **Bash writes.** The without arm writes code and tests with Bash heredocs, which `tool_used: Write`
  and `Edit` never see; the discriminating graders read files or the trace.
- `tests/test_eval_graders.py` now checks every eval's shape (frontmatter, scaffold script
  executable, lone `max: 0` with `min: 0`, regexes compile) and the new graders' hand-made inputs.

### Gate verdict (0.4, ten cases run)

- **Tier 1, every `skill-fired` passes in the with arm: PASS.** `building-trigger`,
  `builder-stays-out-of-prd`, `build-gap-stops` and `build-close-no-bump` 3/3 each; the 0.3 cases
  unchanged at 3/3. `building-not-for-plain-code` correctly fires nothing.
- **Tier 2, no triggering case at Δ <= 0: PASS.** Lowest triggering Δ is +0.25
  (`builder-stays-out-of-prd`); `building-not-for-plain-code` is Δ 0 by design.
- `suite.plugins[].path` is the worktree: PASS.
- No skill-text fix was needed, so no pin was added.

## 0.3 baseline (2026-10-30, `--runs 3`)

Recorded **2026-10-30** on branch `feat/prd-toolkit-0.3` at `--runs 3`, model `sonnet`, on Claude Code
2.1.314. `suite.plugins[].path` is the worktree's `prd-toolkit`. The manifest still says 0.2.0
(the version bump is a later task). Only the five cases touched by the context pack and the
move of the adoption map to `adoption.md` were run; the other three keep their 0.2 rows below.

Command (from the repo root): the 0.2 command below, with `--case <name>` added, once per case
(`--case` takes one glob). The cases ran at the same time, so each one's `--json` is its own file.

| Case | with | w/out | Δ | Notes |
|---|---|---|---|---|
| `change-uses-context-pack` (new) | 1.00 | 0.67 | +0.33 | First run: with 0.33/0.67/0.67, and `ran-pack` failed 2/3 (the agent invoked the skill, then `cat` the PRD files through Bash and never ran `prd_context.py`). Skill fix (rule 6 and step 1 now say to run the pack as the first look at the PRD, and that `cat`, `head`, `sed` or `grep` of a PRD file is opening it; pinned in `tests/test_context_routing.py`) and a narrowed grader, then a re-run: 3/3 at 1.00. Fix round 1 scoped rule 6's last sentence (another area's files come from the pack; the area's own test cases are opened only to revise them in step 2); re-run after that wording: with 3/3 at 1.00, without 0.67 x3. Without the plugin, `ran-pack` fails 3/3 (no pack script) and the other three pass, so Δ comes from the pack. Final fix wave (step 1 finds an unknown area or IDs from the pack, rule 6 lets step 0 read §14, step 2 refreshes stale `Source:` refs): re-run, with 3/3 at 1.00, without 0.67 x3 (`ran-pack` fails 3/3). Proof-gap fixes (step 1 runs a bug fix's pack with `--req E-nnn` and forbids piping the pack's output; step 5 refreshes stale `Source:` refs after the code commit): re-run, with 3/3 at 1.00, without 0.67 x3 (`ran-pack` fails 3/3). |
| `adoption-second-area-minor` | 1.00 | 0.53 | +0.47 | The two graders that read the map now read `adoption.md`. Without the plugin, `tester-dispatched` and `suite-mode` fail 3/3 and one run lacks the changelog row. |
| `adopting-trigger` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2. |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2, run 3 times again with the pack in the skill, and again after the final fix wave's step 1 and step 2 wording: with 3/3 at 1.00; without, `version-2` and `changelog-row` fail 3/3. Re-run after the proof-gap fixes' step 1 and step 5 wording: the same, with 3/3 at 1.00, without 0.00 x3. |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | Unchanged from 0.2. Re-run after the final fix wave's step 1 and step 2 wording: with 3/3 at 1.00; without, `new-id` and `fr003-not-reused` fail 3/3. Re-run after the proof-gap fixes' step 1 and step 5 wording: the same, with 3/3 at 1.00, without 0.00 x3. |

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
