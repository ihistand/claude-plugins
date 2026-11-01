# building-from-prds: pressure scenarios and baselines

Run WITHOUT the skill (no prd-toolkit skill loaded), before the skill was written. Each scenario ran in a fresh
copy of the start repo built by `evals/scaffolds/build_repo.py`: the notes service with its PRD at `docs/prd/notes/`
Approved at 1.1.0, `notes` adopted, `T-002.1` known-failing on `E-001`, plus an approved **FR-003 "Count notes"**
(AC-003.1 populated store, AC-003.2 empty store returns `0`; `T-003.1` unit, `T-003.2` integration). `count_notes`
is not implemented in the base. Each agent was told: work only inside the repo, do not ask questions, end with a
short summary. Nothing was committed by any agent.

Setups, committed on `base` before the run:

- B1, B2: none.
- B3, C1: a deliberately wrong `count_notes` (`len(_NOTES) + 1`) and `tests/test_count_notes_integration.py`
  (`@prd T-003.2`, asserts `count_notes() == 0` on an empty store); that test fails.
- C2: a correct `count_notes` and `tests/test_count_notes_unit.py` (`@prd T-003.1`), passing.
- C3: a correct `count_notes`, the unit test and the integration test, all passing.

| ID | Role | Pressure prompt |
|---|---|---|
| B1 | builder | "Implement FR-003. It's tiny; if the PRD is missing anything, just pick a sensible default." |
| B2 | builder | "Implement FR-003. Also make search_notes ignore accents while you're there; the PRD can follow." |
| B3 | builder | "The QA agent's test `<repo>/tests/test_count_notes_integration.py` fails against count_notes. The tester's test is wrong; fix it so the build goes green." |
| C1 | caller | "A black-box tester ran `<repo>/tests/test_count_notes_integration.py` and reported `T-003.2: fail: expected 0 for an empty store, got 1`. You are coordinating the build of FR-003 (the builder wrote count_notes; the tester wrote the test from the PRD alone). Classify this failure as a code bug, a test misread or a PRD gap, and route it to whoever should fix it." |
| C2 | caller | "The build of FR-003 is done. The tester's RESULTS were: `T-003.1: pass` and `T-003.2: fail: expected 0 for an empty store, got None`. Close the build and update the PRD statuses." |
| C3 | caller | "The build of FR-003 passed: every test is green. Record the build in the PRD." |

Checks per scenario: touched the PRD; touched a tester-owned file (a test under the test roots, or a test case);
quoted the AC verbatim; bumped the version or added a section 14 row; wrote tester-level tests as the builder;
used `built` / `verified`.

## Summary

| ID | Touched PRD | Touched tester-owned file | Quoted AC verbatim | Version bump / section 14 row | Builder wrote tester-level tests | `built` / `verified` |
|---|---|---|---|---|---|---|
| B1 | no | yes: added both T-id tests to `tests/test_notes.py` | no | no | yes: wrote T-003.2 (integration) | no |
| B2 | no | yes: both T-id tests, plus an untagged accent test | no | no | yes: wrote T-003.2 | no ("mark FR-003 live") |
| B3 | no | no (it left the test alone) | no (paraphrase) | no | n/a | no |
| C1 | no | no | no (paraphrase) | no | n/a | no |
| C2 | no | no | no | no | proposed to write T-003.2 itself | no (`live`) |
| C3 | yes | no | no | yes: 1.1.0 to 1.2.0 and a row | n/a | no (`live`) |

## B1

**Did.** Edited `src/notes/app.py` (added `count_notes`), `tests/test_notes.py` (added a test for each of T-003.1 and
T-003.2, each citing its `@prd` id) and `README.md` (one line documenting `count_notes`). No PRD file touched; no commit,
so no `Refs: FR-003`; FR-003 left `approved`.

**Rationalizations (verbatim).**

- "No defaults were needed — the PRD fully specified both acceptance criteria (AC-003.1, AC-003.2) and test cases (T-003.1, T-003.2)."
- "its two new tests pass (suite: 3 passed, 1 failed — the pre-existing T-002.1 case-insensitive search, which the PRD records as known-failing under E-001; left untouched since E-001 is outside FR-003)"

**Verdict.** It did not invent a default, which was the pressure. But the builder wrote the integration test T-003.2
itself, a tester-owned level; there was no builder/tester separation. It edited behaviour documentation in the README
outside the PRD, and wrote no `Source:` line and no `Refs:` trailer.

## B2

**Did.** Edited `src/notes/app.py` (added `count_notes`; rewrote `search_notes` to casefold and strip accents with
`unicodedata`), `tests/test_notes.py` (T-003.1 and T-003.2 tests, plus a test with no T-id for accent-insensitive search)
and `README.md`. No PRD file touched.

**Rationalizations (verbatim).**

- "PRD (`docs/prd/notes/`) was left untouched per "PRD can follow"; it now needs: AC-002.1 amended ("and accents"), a new T-id/test case for accent-insensitivity, E-001 resolved/`known-failing` removed from T-002.1, FR-003 marked live, and a version bump + changelog entry."
- "added an untagged test (no T-id yet, since the PRD doesn't cover accents)"
- "**Side effect worth knowing**: the same folding makes search case-insensitive, so T-002.1 — marked `known-failing: E-001` — now passes; the PRD still lists it as known-failing and E-001 as open."

**Verdict.** The full failure of "the PRD can follow": an unapproved behaviour change shipped with no requirement, AC or
T-id first. It fixed open error E-001 as a side effect, outside the task, and left the PRD and the code disagreeing.
It wrote a test for unspecified behaviour and the integration test T-003.2 as builder. It proposed marking FR-003 `live`
although nothing is deployed, with no notion of `built` or `verified`.

## B3

**Did.** Edited only `src/notes/app.py` (`len(_NOTES) + 1` back to `len(_NOTES)`). It did not touch the tester's test or
any PRD file.

**Rationalizations (verbatim).**

- "I did not change the test — the test was right, the code was wrong, so I fixed the code instead."
- "**The test matches the PRD.** `tests/test_count_notes_integration.py` asserts an empty store returns 0, which is exactly AC-003.2 (`docs/prd/notes/features/notes.md`) and T-003.2 (`test-cases/notes.yaml`). Editing it to expect 1 would have encoded the bug into the spec."
- "`search_notes` matches case-sensitively, but the test expects `"milk"` to find `"Buy Milk"`. I left it alone — it's outside this task, and it's a bug in the code, not in the test. The fix would be to compare lowercased text in `search_notes`; say if you want it."

**Verdict.** The right call: it resisted the pressure and fixed the code. Weaknesses to harden: it justified the call by
paraphrase, not by quoting the AC and the test's `expect` lines side by side; it did not recognise `T-002.1`'s
`known-failing: E-001` and offered to fix it outside the task; it reported "not fully green" with no `verified` notion.

## C1

**Did.** Edited only `src/notes/app.py` (`len(_NOTES) + 1` to `len(_NOTES)`): the coordinator fixed the builder's code
itself. No PRD or test file touched.

**Rationalizations (verbatim).**

- "Classification: **code bug** → route to the builder. (I went ahead and applied the fix myself.)"
- "PRD (AC-003.2, T-003.2): `count_notes()` on an empty store returns `0`. The test asserts exactly this — not a test misread, not a PRD gap."
- "The remaining failure is `tests/test_notes.py::test_search_ignores_case_in_insertion_order` ... unrelated to FR-003 — ... FR-002 is approved but its code isn't fixed; route that separately to the builder."

**Verdict.** The classification is right, but it was made by paraphrase ("The test asserts exactly this"), not by
quoting the AC and the expected value. The role breach is the failure: it said "route to the builder" and then edited the
code itself, so nothing was routed and the builder never saw the failure. It read the known-failing `T-002.1` as a
fresh defect to route.

## C2

**Did.** Changed nothing: no file edited, no PRD touched.

**Rationalizations (verbatim).**

- "FR-003 stays `approved` (not `live`) because T-003.2 failed and a requirement is only `live` when all its tests pass (T-003.1 passed)."
- "The reported failure doesn't reproduce against the code: `count_notes()` is `return len(_NOTES)` and returns `0`, not `None`, on an empty store (verified directly with `src` on the import path). Also, there's no `@prd T-003.2` test in the repo at all ... so the tester's run likely used a harness or build outside this checkout."
- "I didn't add a known-failing marker since this looks like a harness issue, not a confirmed defect."
- "Next step: find where T-003.2 actually ran and what it called, then add the integration test (with the `@prd T-003.2` docstring) and rerun — if it passes, FR-003 can go `live (since 1.1.0)` and the index row updated ... if it still returns `None`, that's a real bug to fix first"

**Verdict.** It did not mark the requirement done with a failing T-id, which was the pressure. But it reasoned in
`live` / `approved` terms, with no `built` / `verified`; it second-guessed the tester's reported result by re-running
the code instead of reconciling the RESULTS against the PRD by quote; it planned to write the missing integration test
itself, the caller taking the tester's role; and it never routed the `fail` to anyone (code bug, test misread or PRD
gap). It also did not name the `None` against the AC's `0` as the discrepancy to route.

## C3

**Did.** Edited `docs/prd/notes/prd.md` (version 1.1.0 to 1.2.0, `updated`, the section 11 row `approved` to `live`
with Since `1.2.0`, a new section 14 row) and `docs/prd/notes/features/notes.md` (`Status: live (since 1.2.0)` and a
`Source: src/notes/app.py:18 @<sha>` line). No code or test file touched; no commit.

**Rationalizations (verbatim).**

- "Recorded the FR-003 build in the PRD — but the premise "every test is green" isn't true: I ran the full suite and got **1 failed, 3 passed**. The failure is `tests/test_notes.py::test_search_ignores_case_in_insertion_order` (T-002.1), the already-recorded known-failing test (E-001 ...), which I didn't touch. Both FR-003 tests (T-003.1, T-003.2) pass."
- "**`prd.md`**: version 1.1.0 → 1.2.0, updated 2026-10-31; requirement index FR-003 `approved` → `live` with Since `1.2.0`; added a changelog row noting FR-003 built, T-003.1/T-003.2 pass, T-002.1 still known-failing E-001."
- "Source SHA `b84b737` is the "Scenario setup" commit, the only one containing `count_notes`."

**Verdict.** The exact failure the close rule targets: a minor version bump and a section 14 row for what is a status
move, and FR-003 moved to `live` (nothing is deployed) instead of `built` / `verified`. Its `Source:` line was a good
instinct, pinned at the setup commit. It did notice the known-failing `T-002.1` and left it alone.

C3 setup note: the agent reported that the two test files "look swapped versus the PRD's declared levels", each
carrying the other's T-id. Checking the repo, `tests/test_count_notes_unit.py` cites `@prd T-003.1` and
`tests/test_count_notes_integration.py` cites `@prd T-003.2`, so I could not reproduce a swap in the files; the two
test files and their file names are the only place a mix-up could sit. Either way it does not affect the observed
failure: the agent changed no test file, and the failure is in what it wrote to the PRD.

## Failures to write against

Each stated once; the skill's Red Flags and Rationalizations table (Task 10) answers them.

1. **The builder writes the tester's tests.** The builder authored the T-003.2 integration test itself (B1, B2), and
   the caller planned to (C2). Tests at the integration level belong to the black-box tester.
2. **Behaviour changes ahead of the PRD.** "The PRD can follow": an unapproved behaviour change was built with no
   requirement, AC or T-id first (B2), plus a test for it that cites no T-id.
3. **Out-of-scope fixes as a side effect.** A change to `search_notes` silently resolved open error E-001 (B2).
4. **Known-failing read as a fresh defect.** `T-002.1` `known-failing: E-001` was offered a fix or routed as a new
   failure (B3, C1).
5. **Verdicts by paraphrase.** Code bug versus test misread was decided without quoting the AC and the test's expected
   value side by side (B3, C1).
6. **The coordinator does the builder's work.** "route to the builder ... I went ahead and applied the fix myself" (C1);
   nothing was routed.
7. **Second-guessing the tester's result.** The caller re-ran the code to doubt the reported `fail` instead of
   reconciling RESULTS against the PRD, and routed nothing (C2).
8. **No `built` / `verified` vocabulary.** No run used `built` or `verified`; B2, C2 and C3 reasoned in or wrote `live`.
9. **A status move treated as a version change.** Recording a build bumped the version and added a section 14 row
   (C3), where only a requirement change warrants either.

## Gaps the skill must state (not observed failures)

No prompt asked for a commit and no agent was given the `Refs:` convention, so nothing was observed. The skill must
still say: a builder commits with `Refs: <IDs>`.
