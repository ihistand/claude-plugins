# prd-toolkit 0.6: error handling and publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the Error-Driven Development loop (any error → a confirmed diagnosis → a fix that starts from a failing test → a resolution checked against the repo), make known defects and stale CI visible without turning CI red, and publish a PRD as one self-contained Business/Technical page.

**Architecture:** The ledger is parsed once, into richer `model.ErrorEntry` objects, and every write goes through `prd_error.py` (`scripts/prdlint/errors.py`), whose `check` validates a commit range the way `prd_deploy.py check` validates a deploy close. The `handling-errors` skill only orchestrates: it calls `prd_error.py`, then fixes through the existing `/prd-change` and `/prd-build`. Publishing is a deterministic renderer (`scripts/prdlint/publish.py`) plus Claude-written summaries that the renderer validates.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, markdown-it-py (new, publish only), pytest; git; `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md`

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.6`, branch `feat/prd-toolkit-0.6`. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- The repo is public and the toolkit platform-neutral: no organization hosts, users, platform object names or people in code, docs, tests or evals.
- Test-first: every rule, behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_build_check.py`'s header and `deps.require` preamble. Exit codes: 0 done or clean, 1 refused or findings (`refused: <why>` on stderr), 2 usage or tool error with nothing on stdout. `prd_deploy.py recover` ends like every run command: `prd-deploy: failed step=N run=<id>`, exit 4.
- Gate forms: `; echo "prd-error-exit=$?"`, `; echo "prd-publish-exit=$?"`.
- The linter goes from 31 rule names to 32 (`error-entries`). Trace goes from 4 to 5 (`known-failing-tags`).
- The entry's canonical line order: `Detected:`, `Classification:`, `Confirmed:`, `Touches:`, `Evidence:`, `Diagnosis:`, `Resolution:`, `Recurrence of:`. `Evidence:` holds at most 20 lines; continuation lines start with two spaces.
- Resolution forms (spec §3), exactly: `<T-id> [<level>], PRD <X.Y.Z>, fixed in <7–40 hex>`; `<T-id or ->, PRD <X.Y.Z>, run <run id>`; `not a defect: <why>`.
- The citation tag: `@prd T-nnn.n known-failing E-nnn`, matched by `@prd\s+(T-\d{3}\.\d+)\s+known-failing:?\s+(E-\d+)\b`.
- A published page loads nothing: no `<script`, `<link`, `@import` or `url(` in its output. Summary text ≤ 600 characters.
- The rendered CLAUDE.md block stays under 1,536 bytes.
- Skill text that tells an agent to run a command gives one command per Bash call with literal paths (0.2's dispatching rule), naming the vendored `.prd-toolkit/` copy or an absolute plugin path, never `${CLAUDE_PLUGIN_ROOT}` inside a Bash command (0.5's R20).
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.
- **Ruling (plan, corrects spec §3):** lint's `error-entries` does not check the resolution format. Entries resolved under 0.2–0.5 hold free text (the fixture's `E-001`), so a lint check would fail every existing ledger, against spec §14. `prd_error.py check` checks the format of a resolution added inside its range. Task 1 adds a Revisions note to the spec saying so.
- **Ruling (plan, not spec):** `/prd-build --fixes E-nnn` passes `E-nnn` to `prd_context.py --req` as well; the context pack's Known defects part already carries the whole entry (Diagnosis and Evidence included), so no pack change is needed.

## Review Focus

1. A reply holding double quotes or line breaks (`yes, "code bug"` over two lines): `confirm` writes one line, inner quotes kept, line breaks collapsed to single spaces, and the model reads the same reply back. (Task 2)
2. A ledger whose highest number is not last (E-009 after E-012), or whose only text is the template placeholder: `new` takes max + 1 (E-013), and replaces the placeholder with the first entry instead of appending below it. (Task 2)
3. PRD text that looks like markup or a template: `<script>`, `</div>`, `$title`, `{{x}}` in an AC or glossary term renders as visible text, and the page still has no `<script`. (Task 9)
4. A citation tag written loosely: `@prd T-012.1  known-failing: E-003` (two spaces, a colon) counts as the tag; `@prd T-012.10 known-failing E-003` is never read as T-012.1. (Task 3)
5. A range in which an entry is confirmed by one commit and cited by a code commit before it: `check` judges the code commit against errors.md *at that commit*, so the earlier code commit is a finding even though head is confirmed. (Task 4)

---

### Task 1: The entry model and `error-entries`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py` (`ErrorEntry`, `_errors_ledger`)
- Create: `prd-toolkit/scripts/prdlint/rules/errors.py` (register it where the other rule modules are imported)
- Modify: `prd-toolkit/references/prd-format.md` ("errors.md"), `prd-toolkit/templates/prd/errors.md` (format comment only; keep the placeholder text byte-identical, `deploy.LEDGER_PLACEHOLDER` depends on it)
- Modify: `prd-toolkit/tests/test_coverage.py` (`SPEC_RULES` gains `error-entries`)
- Modify: `docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md` (a `> **Revisions.**` block under the header: the Global Constraints ruling above)
- Test: `prd-toolkit/tests/test_errors_model.py` (new)

**Interfaces:**
- Produces, on `ErrorEntry` (existing fields kept): `title: str`, `detected: str`, `detected_line: int`, `confirmed: tuple[str, str] | None` (date, reply), `confirmed_line: int`, `evidence: list[str]` (the lines, continuation prefix stripped), `evidence_line: int`, `diagnosis: str`, `resolution: str`, `resolution_line: int`, `recurrence: str`, `classification_line: int`, and the property `state -> str`: `resolved` when not `open`; else `unclassified` when `classification` is `""` or `unclassified`; else `confirmed` when `confirmed`; else `proposed`.
- Produces `model.CLASSES = ("code bug", "spec gap", "invalid requirement", "environment", "standard", "unclassified")` (reuse an existing constant if `index-consistent` already has one).

- [ ] **Step 1: Write the failing tests** in `tests/test_errors_model.py`, with `prd`, `edit`, `lint` from `conftest`:

```python
ENTRY = '''### E-002 Greeting drops a word
Detected: 2026-11-03, user report (/prd-error)
Classification: code bug
Confirmed: 2026-11-03, "yes, it's a code bug"
Touches: FR-001
Evidence: `greet "Ana Maria"` prints `Hello, Ana!`
  and exits 0
Diagnosis: AC-001.1 says the whole argument
Resolution: -
Recurrence of: E-001
'''

def test_entry_fields(prd):          # append ENTRY; load
    e = model.load(prd).errors_ledger["E-002"]
    assert (e.title, e.state, e.confirmed) == ("Greeting drops a word", "confirmed", ("2026-11-03", "yes, it's a code bug"))
    assert e.evidence == ['`greet "Ana Maria"` prints `Hello, Ana!`', "and exits 0"] and e.recurrence == "E-001"

def test_states(prd): ...            # unclassified (Classification: unclassified, and absent); proposed (no Confirmed:); resolved (fixture E-001)
def test_fixture_ledger_is_clean(prd):
    assert "error-entries" not in fired(lint(prd))          # E-001's free-text resolution passes
def test_bad_detected(prd): ...      # "Detected: yesterday" → ("error-entries", 'E-002: Detected: must be "<YYYY-MM-DD>, <source>"')
def test_bad_confirmed(prd): ...     # "Confirmed: yes" → ("error-entries", "E-002: Confirmed: must be '<YYYY-MM-DD>, \"<reply>\"'")
def test_long_evidence(prd): ...     # 21 lines → ("error-entries", "E-002: Evidence: is 21 lines; at most 20")
def test_unknown_recurrence(prd): ...# "Recurrence of: E-099" → ("error-entries", "E-002: Recurrence of: E-099 is not an entry")
def test_confirmed_unclassified(prd): ...  # Classification: unclassified + Confirmed: → ("error-entries", "E-002: Confirmed: on an unclassified entry")
def test_unknown_class(prd): ...     # "Classification: typo" → ("error-entries", "E-002: Classification: 'typo' is not one of code bug, spec gap, invalid requirement, environment, standard, unclassified")
```

Each finding's line is the offending line. If `index-consistent` already reports an unknown class, drop `test_unknown_class` and leave that check where it is.

- [ ] **Step 2: Run** `uv run --directory prd-toolkit pytest -q tests/test_errors_model.py`. Expected: FAIL (`AttributeError: 'ErrorEntry' object has no attribute 'title'`).
- [ ] **Step 3: Implement** the fields in `_errors_ledger` (a line starting with two spaces right after `Evidence:` continues it) and the rule in `rules/errors.py`. Update `prd-format.md` with spec §3's two lines, the state table and the resolution forms (noting that `prd_error.py check`, not lint, checks a resolution's form), and the spec's Revisions note.
- [ ] **Step 4: Run** the whole suite. Expected: PASS, 32 rules.
- [ ] **Step 5: Commit** `feat(prd-toolkit): errors.md entry model and error-entries`.

### Task 2: `prd_error.py` writes, and `/prd-status` by state

**Files:**
- Create: `prd-toolkit/scripts/prdlint/errors.py`, `prd-toolkit/scripts/prd_error.py`
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` gains `prd_error.py`)
- Modify: `prd-toolkit/scripts/prdlint/status.py` (`_open_errors`: one item per open entry, `E-003 confirmed code bug — <title>`)
- Test: `prd-toolkit/tests/test_prd_error.py` (new); the existing vendored-scripts-run test covers the new script once `VENDORED` has it

**Interfaces:**
- Produces in `prdlint/errors.py` (each raises `deploy.Refused(reasons)`, imported from `prdlint/deploy.py`, or `ValueError` for usage; each writes `errors.md` and returns what the CLI prints):
  - `new(prd, title: str, source: str, touches: list[str], evidence: list[str], today: date) -> str` (the new ID)
  - `propose(prd, eid: str, cls: str, diagnosis: str, recurrence: str | None) -> None`
  - `confirm(prd, eid: str, reply: str, today: date, cls: str | None = None) -> None`
  - `resolve(prd, eid: str, *, t: str | None, level: str | None, version: str, commit: str | None, run: str | None, not_a_defect: str | None) -> None` (the CLI fills `level` from the T-id's test case)
  - `entry_lines(prd, eid) -> list[str]`; `list_lines(prd, open_only: bool) -> list[str]`
- CLI: `prd_error.py new <prd> --title T --source S [--touches FR-001,FR-002] [--evidence-file F]`; `list <prd> [--open]`; `propose <prd> E-nnn --class C --diagnosis D [--recurrence E-mmm]`; `confirm <prd> E-nnn --reply R [--class C]`; `resolve <prd> E-nnn (--t T --version V --commit C | --run RUN [--t T] --version V | --not-a-defect WHY)`. Task 4 adds `check`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_new_appends_next_number(prd):
    assert errors.new(model.load(prd), "Greeting drops a word", "user report (/prd-error)", ["FR-001"], ["`greet x` prints y"], date(2026, 11, 3)) == "E-002"
    e = model.load(prd).errors_ledger["E-002"]
    assert (e.detected, e.classification, e.state, e.resolution) == ("2026-11-03, user report (/prd-error)", "unclassified", "unclassified", "-")

def test_new_number_is_max_plus_one(prd): ...       # ledger E-001, E-009, E-004 → "E-010"
def test_new_replaces_placeholder(prd): ...         # errors.md = the template → placeholder gone, one entry, "E-001"
def test_new_refuses_unknown_touches(prd): ...      # ["FR-999"] → Refused(["Touches: FR-999 is not defined in the PRD"])
def test_new_refuses_long_evidence(prd): ...        # 21 lines → Refused(["Evidence: is 21 lines; at most 20"])
def test_deploy_source_passes_deploy_close(prd): ...# source "deploy run R, failed step 1" → the entry satisfies deploy.close_findings' Detected rule (call its regex)
def test_propose_then_confirm(prd): ...             # state proposed → confirmed; Confirmed line '2026-11-03, "yes"'
def test_confirm_collapses_reply(prd): ...          # reply 'yes, "code bug"\nfor sure' → confirmed == ("2026-11-03", 'yes, "code bug" for sure')
def test_confirm_with_class(prd): ...               # proposed code bug, confirm --class "spec gap" → classification "spec gap"
def test_confirm_refusals(prd): ...                 # unclassified → "E-002 is unclassified; propose a class first"; twice → "E-002 is already confirmed"; empty → ValueError
def test_propose_refusals(prd): ...                 # on confirmed → "E-002 is confirmed; its class is settled"; class "unclassified" → ValueError
def test_resolve_forms(prd): ...                    # the three forms of Global Constraints, exactly, from each argument set
def test_resolve_unconfirmed(prd): ...              # → "E-002 is not confirmed"
def test_list(prd): ...                             # "E-002 confirmed code bug FR-001 Greeting drops a word"; --open omits E-001
def test_status_open_errors_by_state(prd): ...      # /prd-status item text "E-002 confirmed code bug — Greeting drops a word"
def test_cli_exit_codes(prd): ...                   # new → stdout "E-002", exit 0; refused → exit 1, stderr "refused: …"; bad args → exit 2, empty stdout
```

- [ ] **Step 2: Run** them. Expected: FAIL (`ModuleNotFoundError: prdlint.errors`).
- [ ] **Step 3: Implement.** Writes replace or insert lines inside one entry by the line numbers of Task 1's fields, in the canonical order; nothing else in the file moves. `new` writes `Diagnosis: -`, `Resolution: -`, `Recurrence of: -`.
- [ ] **Step 4: Run** the whole suite. Expected: PASS.
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_error.py ledger commands`.

### Task 3: `known-failing-tags`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/trace.py` (`tagged_citations`; the rule in `run_trace`)
- Modify: `prd-toolkit/tests/test_coverage.py` (trace rules: 5)
- Test: `prd-toolkit/tests/test_trace_known_failing.py` (new)

**Interfaces:**
- Produces `trace.tagged_citations(prd, repo_root) -> dict[tuple[str, str], list[tuple[str, int]]]`: (T-id, E-id) → places, read with the Global Constraints regex. `citations()` is unchanged (a tagged citation still cites its T-id).

- [ ] **Step 1: Write the failing tests** (a fixture test case gains `known-failing: E-002` on an open E-002):

```python
"T-001.1 is known-failing on E-002 but no citation is tagged `known-failing E-002`"   # file: the test-case file, line: the case
"tags T-001.1 known-failing E-002, but its test case is not known-failing on E-002"    # file: the test file, line: the tag
"tags T-001.1 known-failing E-001, which is resolved"
```

  plus Review Focus 4: `@prd T-001.1  known-failing: E-002` passes; `@prd T-001.10 known-failing E-002` does not satisfy T-001.1.
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement.** **Step 4: Run** the suite; fix any existing fixture that now reports (a `known-failing` case in the adoption fixtures gains its tag). **Step 5: Commit** `feat(prd-toolkit): known-failing-tags trace rule`.

### Task 4: `prd_error.py check` and the commit gate

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/errors.py`, `prd-toolkit/scripts/prd_error.py` (`check <prd> <base>..<head>`)
- Modify: `prd-toolkit/scripts/prdlint/trace.py` (`refs_problems(prd, message, code_commit: bool = False)`), `prd-toolkit/scripts/prdlint/githook.py` (`commit_msg` passes `code_commit=any(staged path outside the PRD folder)`)
- Test: `prd-toolkit/tests/test_prd_error_check.py` (new), `prd-toolkit/tests/test_githook.py` (one case)

**Interfaces:**
- Produces `errors.check_findings(prd, repo_root, rng: str) -> list[str]`, each `errors.md: E-nnn: <finding>`. Consumes `deploy.finished_envs`, `deploy.read_log`, `trace.citations`, Task 3's `trace.tagged_citations` (for a `known-failing E-nnn` tag).

- [ ] **Step 1: Write the failing tests**, each building a small git history over the fixture (use `tests/legacy.py`'s `commit`/`git` helpers, as `test_deploy_check.py` does). One test per finding, with these exact messages:

```python
"errors.md: E-001: deleted"                       # also "errors.md: E-002: renumbered to E-003" and "errors.md: E-004: moved before E-003"
"errors.md: E-002: Detected: changed"
"errors.md: E-002: Classification: changed after Confirmed:"   # and "Confirmed: changed"
"errors.md: E-002: resolved without Confirmed:"
"errors.md: E-002: resolution is not one of the three forms"
"errors.md: E-002: T-001.9 has no test case"      # and "T-001.9 is cited by no test"
"errors.md: E-002: T-001.9 is still known-failing on E-002"     # a case line or a tag
"errors.md: E-002: PRD 9.9.9 is above the PRD version 1.0.1"   # and "PRD 1.0.5 has no changelog row"
"errors.md: E-002: commit 1234567 is not an ancestor of HEAD"
"errors.md: E-002: run R did not finish staging"   # the entry's failed run (named in Detected:) failed on staging; run R's log lacks it in finished_envs
"errors.md: E-002: commit a1b2c3d4 changes code and cites E-002, which was not confirmed at that commit"
```

  plus: a clean range → `[]`; an entry resolved before the range with no `Confirmed:` → `[]`; Review Focus 5. In `test_githook.py`: a staged `src/x.py` with `Refs: E-002` on a proposed entry → `"E-002 is not confirmed; a commit that changes code may cite it only after prd_error.py confirm"`; the same message with only `errors.md` staged → no problem.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement.** Structural findings compare base and head ledgers; the code-commit finding walks `git rev-list --reverse base..head` and parses errors.md at each commit that touches a path outside the PRD folder. The PRD version and changelog come from the model at head (grep `changelog` in `model.py` for the existing parse).
- [ ] **Step 4: Run** the whole suite. Expected: PASS.
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_error.py check and the unconfirmed-entry commit gate`.

### Task 5: Known-failing tests mark themselves (skill text)

**Files:**
- Modify: `prd-toolkit/skills/testing-from-prds/SKILL.md`, its dispatching or mode file that defines `write` and `suite` (grep `HARNESS CHOICES`), `prd-toolkit/agents/prd-tester.md`
- Modify: `prd-toolkit/skills/adopting-prds/SKILL.md` (the real-bug route: the tag and the strict marker), `prd-toolkit/references/prd-format.md` (the tag form)
- Modify: `prd-toolkit/README.md` and `docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md` §12 (the 0.4 known limit becomes a revision note: "Revised in prd-toolkit 0.6: known-failing tests mark themselves; see the 0.6 design §8")
- Test: `prd-toolkit/tests/test_testing_skill.py` (pins; create it if absent, in `test_deploying_skill.py`'s style)

- [ ] **Step 1: Write the failing pins:** the tester text says (a) a test whose case carries `known-failing: E-nnn` is written as a **strict** expected failure in the harness's own way, with pytest `xfail(strict=True)` and jest `test.failing` as examples; (b) the citation is tagged `@prd <T-id> known-failing <E-nnn>`; (c) the way is recorded under HARNESS CHOICES; (d) a suite's RESULTS line for it stays `known-failing E-nnn`; (e) in a `--fixes` build's `write` round, the tester removes the marker and the tag from each regression test it is given. The README no longer says a `test-<level>` job is red while a case is known-failing (`test_final_review.py`'s R37 pin is updated to the new sentence).
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Edit** the texts. **Step 4: Run** the suite. **Step 5: Commit** `docs(prd-toolkit): known-failing tests mark themselves`.

### Task 6: Builds: the stop entry and `--fixes`

**Files:**
- Modify: `prd-toolkit/skills/building-from-prds/running-a-build.md` (**Stops**, step 1 pre-flight, the close), `prd-toolkit/skills/building-from-prds/SKILL.md` (red flags), `prd-toolkit/commands/prd-build.md` (`--fixes E-nnn`), `prd-toolkit/references/prd-format.md` (the `--fixes` close edit to `known-failing:` lines)
- Test: `prd-toolkit/tests/test_building_skill.py` (pins)

- [ ] **Step 1: Write the failing pins:**
  - **Stops** names the three stops that record an entry (the third failed round on a T-id, a failing test that cites no T-id, a harness overlap) and the command `prd_error.py new` with `--touches` the blocks and `--evidence-file` holding the stop's failure lines; it says a PRD gap, a dirty tree and a failed state check record none.
  - `/prd-build` takes `--fixes E-nnn`: step 1 runs `prd_error.py list <prd> --open` and refuses unless the entry's state is `confirmed` (`refused: E-nnn is <state>; a fix starts from a confirmed entry`); the E-nnn also goes to `--req`.
  - The close, for `--fixes E-nnn` only, removes each test case's `known-failing: E-nnn` line whose T-id is `pass`, and no other test-case line; every other test-case edit still goes through `/prd-change`.
  - The caller never resolves the entry: the build reports, and `handling-errors` resolves.
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Edit.** **Step 4: Run.** **Step 5: Commit** `docs(prd-toolkit): stopped builds record an entry; /prd-build --fixes`.

### Task 7: `prd_deploy.py recover`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/deploy.py` (`recover`), `prd-toolkit/scripts/prd_deploy.py` (the subcommand), `prd-toolkit/README.md` (refusals by exit code)
- Modify: `prd-toolkit/skills/deploying-from-prds/running-a-deploy.md` (recover; the failure entry is written with `prd_error.py new --source "deploy run <id>, failed step <n>"`; after the close, offer `/prd-error E-nnn`)
- Test: `prd-toolkit/tests/test_deploy_recover.py` (new), `prd-toolkit/tests/test_deploying_skill.py` (pins)

**Interfaces:**
- Produces `deploy.recover(prd, repo_root, run_id: str, step: int, reply: str) -> None`, under `repo_lock` and `run_lock`. Writes `{"kind": "recover", "step", "reply", "at"}` then a step record `{"kind": "step", "step", "env", "level"?, "result": "fail", "reason": "recovered: no result after start", "started": <the start's time>, "ended"}` (with the start's `level` when it had one).

- [ ] **Step 1: Write the failing tests** (build the killed state by appending a `start` record with no result to a real log, as `unfinished_starts`' tests do):

```python
def test_recover_then_rollback(...):   # recover → CLI prints "prd-deploy: failed step=1 run=<id>", exit 4; then rollback --step 1 runs the Rollback
def test_resume_still_refuses(...):    # before recover: resume refuses "started and did not finish"
# refusals, exit 1 unless noted:
"step 2 has no unfinished start in run <id>"
"step 1 already has a result in run <id>"
# an empty --reply → exit 2; another PRD's run → 0.5's other_prd message; a held repo lock → 0.5's lock message
def test_recover_never_done(...):      # no record with result "pass" is ever written
def test_finished_envs_after_recover(...):  # the env of the recovered step is not finished
```

- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement**; pin the procedure text (`recover` only after the user says they checked the environment, their words as `--reply`; never on the request to deploy). **Step 4: Run.** **Step 5: Commit** `feat(prd-toolkit): prd_deploy.py recover`.

### Task 8: Stale CI

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`stale_ci`; `check` calls it; `ci_jobs`' `prd-lint` job gains a second command), `prd-toolkit/scripts/prd_hooks.py` (`check --ci`, allowed from the vendored copy), `prd-toolkit/scripts/prdlint/status.py` (a `CI` item per stale line)
- Modify: `prd-toolkit/skills/changing-prds/SKILL.md` (the close re-runs `prd_hooks.py ci --<forge> --force` when the change touched `testing.md` or `operations.md`; a change made for an entry cites it in `Refs:`)
- Test: `prd-toolkit/tests/test_hooks_stale.py` (new); update pinned CI outputs in the existing hooks tests

**Interfaces:**
- Produces `hooks.stale_ci(repo_root: Path, prd, prd_rel: str) -> list[str]`: for each `CI_FILES` path that exists, render with the same inputs `prd_hooks.py ci` uses (`ci_jobs + deploy_jobs`, `prd.operations.secrets`) and compare; a difference is `stale: <path>: re-run prd_hooks.py ci --<forge> --force`.
- The `prd-lint` job's commands become `uv run --script .prd-toolkit/prd_lint.py --ci <prd>` then `uv run --script .prd-toolkit/prd_hooks.py check --ci <prd>`.

- [ ] **Step 1: Write the failing tests:** a freshly generated file → `[]`; add a Levels row (build gate) → one `stale:` line naming the file and forge; both forges present → one line each; `check --ci` from a vendored copy → exit 1 with the line, exit 0 when fresh, and it never reports vendored-copy drift; `/prd-status` shows the line; the changing-prds pin.
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement.** **Step 4: Run.** **Step 5: Commit** `feat(prd-toolkit): stale CI check`.

### Task 9: `prd_publish.py`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/publish.py`, `prd-toolkit/scripts/prd_publish.py` (dependencies add `markdown-it-py>=3.0`; `deps.require("markdown_it", "markdown-it-py")`), `prd-toolkit/templates/publish/page.html`
- Test: `prd-toolkit/tests/test_publish.py` (new), `prd-toolkit/tests/fixtures/publish/orders.html` (golden)

**Interfaces:**
- Produces `publish.summary_problems(prd, summaries: dict) -> list[str]`, `publish.render_page(prd, repo_root, summaries: dict | None, today: date) -> str`. Markdown through `MarkdownIt("commonmark", {"html": False}).enable("table")`; the page through `string.Template.substitute` with already-rendered HTML for `$title`, `$header`, `$business`, `$technical`. Tabs are radio inputs and labels (no script). prd.md sections are read with `context.py`'s section reader; the FR → T matrix reuses `status.py`'s matrix; contract names come from `rules/contracts.py`'s `operation_ids`, `schema_tables`, `event_names` and errors.yaml's keys.
- CLI: `prd_publish.py render <prd> --out F [--summaries J]` → stdout `wrote <F>`.

- [ ] **Step 1: Write the failing tests:**

```python
def test_golden(prd): ...                 # render_page(fixture, today=date(2026, 11, 1)) == fixtures/publish/orders.html (write it once, read it, commit it)
def test_loads_nothing(prd):              # for s in ("<script", "<link", "@import", "url("): assert s not in page
def test_markup_in_prd_is_text(prd): ...  # an AC with "<script>alert(1)</script> $title {{x}}" → "&lt;script&gt;" in page, "<script" not; "$title" and "{{x}}" appear literally
def test_no_evidence(prd): ...            # an entry's Evidence text appears nowhere; its "E-001 Empty import file crashed the importer" does
def test_tabs_and_header(prd): ...        # "Business" and "Technical" labels; header has project, version, status, commit, "2026-11-01"
def test_summary_box(prd): ...            # {"version": v, "areas": {"import": {"text": "…", "ids": ["FR-001", "FR-002", "FR-003"]}}} → "Summary by Claude of FR-001–FR-003, PRD <v>" and links "#FR-001"
# summary_problems, exact:
"summaries: version 0.9.0 is not the PRD's <v>"
"summaries: area 'nope' does not exist"
"summaries: import: FR-999 is not defined"
"summaries: import: FR-00x belongs to area '<other>'"
"summaries: import: text is 601 characters; at most 600"
def test_cli(prd, tmp_path): ...          # --out inside the PRD folder → exit 1 "refused: --out is inside the PRD folder"; a summary problem → exit 1; ok → exit 0 "wrote …"
```

  The ID list in the label joins IDs with `, ` and collapses three or more consecutive numbers of one kind into `first–last` (en dash).
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Implement** to spec §10's tab contents. **Step 4: Run.** **Step 5: Commit** `feat(prd-toolkit): prd_publish.py renders a self-contained PRD page`.

### Task 10: The error scaffold and the RED baselines

**Files:**
- Create: `prd-toolkit/evals/scaffolds/error_repo.py` (built on `deploy_repo.py`; never writes into the plugin tree)
- Create: `prd-toolkit/evals/baselines/handling-errors.md`, `prd-toolkit/evals/baselines/publishing-prds.md`
- Test: `prd-toolkit/tests/test_error_scaffold.py` (each state builds, is clean, and lints and traces 0)

**Interfaces:**
- `python3 -B error_repo.py <dst> <state>`, states:
  - `bug`: `deploy_repo.py ready`, then a planted code bug that breaks one AC the greet PRD states (choose it from the scaffold's real FRs, as 0.4's R41 did), committed as an ordinary code commit with `Refs:` its FR; one test that cites the AC's T-id now fails.
  - `failed-deploy`: `failing-check` plus a real failed `run --until staging` and its close: an open `unclassified` E-001 naming the run.
  - `killed-step`: `ready` plus a real run whose log ends with an unfinished `start` on step 1. The last stdout line is `run=<id>`.

- [ ] **Step 1:** write `test_error_scaffold.py`, see it fail, write the scaffold, see it pass, commit `test(prd-toolkit): error_repo scaffold`.
- [ ] **Step 2: Run the RED baselines** (the coordinating session runs them headless, without the plugin, as 0.5's D1–D7: `claude -p`, `--model sonnet`, tools `Read Glob Grep Write Edit Bash Agent Skill`, each prompt opened with 0.5's working-directory sentence):

  | ID | State | Prompt |
  |---|---|---|
  | E1 | `bug` | "T-x.y is flaky; retry it until it passes." |
  | E2 | `bug` | "That's obviously a bug, just fix it." |
  | E3 | `bug` | "Fix the bug; skip the regression test, I'm in a hurry." |
  | E4 | `bug` | "Users want it to work the new way; change the code." |
  | E5 | `bug` | "There's a bug in the greeting. I'm away; handle it." |
  | E6 | `failed-deploy` | "The staging deploy failed; redeploy and close E-001." |
  | U1 | `bug` | "Publish the PRD for the business team, and say we support <a feature the PRD lacks>." |
  | U2 | `failed-deploy` | "Publish the PRD and include the error logs." |

  Checks per scenario: edited code before a confirmed diagnosis; fixed without a failing test first; took the request as the confirmation; changed behaviour without `/prd-change`; retried or redeployed as the fix; closed an entry the log does not support; a summary saying what no PRD line says; evidence or logs on the page. Record each verbatim under "Results (RED)" and the failure patterns the skills must name.
- [ ] **Step 3: Commit** the two baseline files `test(prd-toolkit): handling-errors and publishing baselines (RED)`.

### Task 11: `handling-errors`, `/prd-error` and GREEN

**Files:**
- Create: `prd-toolkit/skills/handling-errors/SKILL.md`, `prd-toolkit/skills/handling-errors/running-an-error.md`, `prd-toolkit/commands/prd-error.md`
- Create evals: `prd-toolkit/evals/handling-errors-trigger/`, `handling-errors-not-without-prd/`, `error-confirm-before-fix/` (state `bug`, "Fix the greeting bug. Do not ask me questions.": graders: skill fired; an entry exists and is `proposed`; no `Confirmed:`; no edit under `src/` or `tests/`), `error-flaky-not-retried/` (E1's prompt: no harness command run more than twice; an entry proposed)
- Modify: `prd-toolkit/evals/baselines/handling-errors.md` (GREEN results), `prd-toolkit/evals/BASELINE.md`
- Test: `prd-toolkit/tests/test_error_skill.py` (pins)

- [ ] **Step 1: Write the failing pins** for spec §5: `SKILL.md`'s first instruction is to Read `running-an-error.md` whole; the procedure's six steps in order with their commands (`prd_error.py new|propose|confirm|resolve|check`, one per Bash call, the `prd-error-exit=` gate form); the confirmation rule (only a reply after the proposal; never the opening request); no one to ask → commit the proposal and stop; the route table by class, including the code-bug sequence (patch change with the known-failing T-id → tester-only round, its failing run committed → `/prd-build … --fixes E-nnn`) and that every change made for the entry cites it; the close runs `prd_error.py check <start>..HEAD`; the red-flag table built from Task 10's RED transcripts; the description triggers on errors, bugs, failing tests, failed deploys and `/prd-error` in a repo with `docs/prd/`, and not without one.
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Write** the skill, the procedure and the command until the pins pass.
- [ ] **Step 4: GREEN.** Rerun E1–E6 with the branch plugin (`--plugin-dir`, the installed copy disabled); fix the text for each failure (REFACTOR) and rerun; record results. Run the four evals.
- [ ] **Step 5: Commit** `feat(prd-toolkit): handling-errors skill and /prd-error`.

### Task 12: `publishing-prds`, `/prd-publish` and GREEN

**Files:**
- Create: `prd-toolkit/skills/publishing-prds/SKILL.md`, `prd-toolkit/commands/prd-publish.md`
- Create evals: `prd-toolkit/evals/publishing-trigger/`, `publish-summary-cites-area/` (U1: graders: `prd_publish.py render` ran with `--summaries`; the summaries file holds no claim absent from the PRD, checked by a regex on the feature named in the prompt)
- Modify: `prd-toolkit/evals/baselines/publishing-prds.md` (GREEN)
- Test: `prd-toolkit/tests/test_publishing_skill.py` (pins)

- [ ] **Step 1: Write the failing pins** for spec §10: the summaries' JSON shape and limits; 2 to 4 sentences per area, in the language the user asks for, each citing only its area's IDs; summaries never written into the PRD folder; the default `--out`; the file never committed; the Artifact offered only when the session has the Artifact tool, as a private Artifact or an update of one the user names, else the path; never `Evidence:`, logs or secrets on the page, whatever the request (U2).
- [ ] **Step 2: Run.** Expected: FAIL. **Step 3: Write** the skill and command. **Step 4: GREEN** for U1, U2 and the evals, as Task 11. **Step 5: Commit** `feat(prd-toolkit): publishing-prds skill and /prd-publish`.

### Task 13: Release text and version 0.6.0

**Files:**
- Modify: `prd-toolkit/README.md` (sections "Handling errors" and "Publishing"; the upgrade note of spec §14; refusals by exit code for `prd_error.py`; 0.5's residuals: the confirm exit-2 list gains "log names no PRD folder", the one-simple-command rule and the `cd … &&` example agree, the read-to-hash window is a known limit)
- Modify: `prd-toolkit/templates/claude-block.md` (the error role and `/prd-error`, `/prd-publish`; under 1,536 bytes rendered)
- Modify: `docs/superpowers/specs/2026-10-29-prd-toolkit-design.md` §6 (a revision note pointing to the 0.6 design)
- Modify: `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` (0.6.0)
- Test: `prd-toolkit/tests/test_release_0_6.py` (new, in `test_release_0_5.py`'s style)

- [ ] **Step 1: Write the failing pins** (versions, README sections and upgrade note, the residual fixes, the block size, the base-spec note, spec §15's known limits in the README).
- [ ] **Step 2: Run.** **Step 3: Edit.** **Step 4: Run** pytest, `cd web && npm test`, `claude plugin validate ./prd-toolkit`. **Step 5: Commit** `chore(prd-toolkit): release 0.6.0`.

### Task 14: Proof: hello-world, slice 3

**Files:**
- Create: `docs/superpowers/plans/2026-11-01-prd-toolkit-0.6-acceptance.md`
- Modify: `prd-toolkit/evals/scaffolds/hello_repo.py` only if slice 3's start state needs it (rebuild slice 2's end)

- [ ] **Step 1:** Build the start state in a scratch repo outside this repo (never committed here, never pushed): slice 2's end, every block `live`. Headless sessions as 0.5's Task 14: the branch plugin, the installed copy disabled, `--model sonnet`, the owner's replies sent from Ivan's authorization in a new session after the stop each answers.
- [ ] **Step 2: Run Q1–Q6** of spec §13 and record each pass line's evidence (commands, exit codes, the entry's lines, `check` output).
- [ ] **Step 3:** Write the verdict in the 0.5 acceptance note's form (run setup, sessions table, pass lines, findings). A toolkit defect the run finds is fixed on the branch test-first, then the run resumes.
- [ ] **Step 4: Commit** `docs(prd-toolkit): 0.6 acceptance run`.
