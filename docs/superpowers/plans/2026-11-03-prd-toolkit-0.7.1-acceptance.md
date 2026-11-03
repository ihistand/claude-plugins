# prd-toolkit 0.7.1 acceptance run

> **Date:** 2026-11-03
> **Spec:** `2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md`, §9 (Proof)
> **Result:** **pass**, with three findings (F-1 to F-3), none of which blocked the run.
> - Every item the form served was answered in the form: 19 of 19.
> - Done exited 0.
> - `prd_confirm.py status` after Done reported `19/19` and no open item, so no fingerprint changed after it was answered.
> - Every answer was applied under adoption step 3's rules. `lint-cli` is `confirmed`, and the lint exit is 0.
>
> **Scope.** The toolkit's own PRD, `docs/prd/prd-toolkit/`, area `lint-cli`, on branch `feat/prd-toolkit-prd` at
> 25e6b7c (adoption step 2 done). The form was 0.7.1 from the installed plugin (no `.prd-toolkit/` in this
> repository), after PR #9 merged.

## The run

1. `prd_confirm.py status docs/prd/prd-toolkit --area lint-cli`: `0/19`. The items were FR-001 to FR-012, E-001 to E-004 and Q-01 to Q-03.
2. `.prd-confirm-lint-cli-summaries.json` at the repository root held one or two sentences per item. `serve` accepted it.
3. `serve` ran in the background and printed its `url=` line first. The owner answered every item in the browser and pressed Done, and `serve` exited 0.
4. `status` again: `19/19`, nothing open.
5. The answers were applied, the area row was set to `confirmed`, and the lint exit is 0. The answers file and the summaries file were deleted.

## The answers and what they changed

| Item | Decision | Applied |
|---|---|---|
| FR-001 to FR-004, FR-009 | confirm | `live (since 1.0.0)`, §11 `live`, Since `1.0.0` |
| FR-008 | confirm | `live (since 1.0.0)`; it also gained AC-008.2 and T-008.2 from Q-01 |
| FR-005 | confirm, overridden by the bug on E-001 | `approved`: AC-005.2 limited to another name, AC-005.3 and T-005.3 added |
| FR-006 | confirm, then `fix` on Q-03 | `approved`: AC-006.3 (a `.md` entry that is not a file is a `sufficiency` finding) and T-006.3 |
| FR-007 | confirm, then `fix` on Q-02 | `approved`: AC-007.1 samples lowercase levels only; AC-007.4 and T-007.5 (no level, or `Unit`, is not sampled) |
| FR-010 | confirm, overridden by the bug on E-002 | `approved`: AC-010.2 and T-010.2 (each script names itself and its own dependency header); a `prd_publish` item in `contracts/cli.yaml` for its target |
| FR-011 | confirm, overridden by the bug on E-003 | `approved`: AC-011.6 and T-011.6 (`YAML parse error: found unhashable key`) |
| FR-012 | confirm, overridden by the bugs on E-003 and E-004 | `approved`: AC-012.1 skips `contracts/fixtures/` and covers unhashable keys; AC-012.2 added; T-012.2 and T-012.3 added |
| E-001 to E-004 | bug | each still open: `Confirmed:` holds the owner's text verbatim, and `Resolution: open, intended: <text>` |
| Q-01 | intended, "I own it" | AC-008.2; the `PRD_LINT_CI` owner in `contracts/config.yaml` is now filled in; the bullet is removed |
| Q-02, Q-03 | fix, with a note | the corrections to FR-007 and FR-006 above; the bullets are removed |

No code changed (adoption rule 6). The new test cases will fail against the code until E-001 to E-004, Q-02 and
Q-03 are fixed. Step 4 triages them as `known-failing`.

## Findings

- **F-1. The form missed one decision: the `PRD_LINT_CI` owner marker.**
  - The area had 20 decisions (the old checklist had 20 sections), and the form served 19.
  - The missing one is the `[NEEDS CLARIFICATION]` owner of `PRD_LINT_CI` in `contracts/config.yaml`.
  - Cause: FR-008 names the setting as `setting PRD_LINT_CI (contracts/config.yaml)`, without backticks. 0.7.1 counts a key as named only through a backticked Traces span or a test-case target.
  - Here, Q-01's answer ("I own it") covered the marker, so nothing was lost. In another PRD it would be silently left out.
  - To fix: also count the `setting <NAME> (<file>)` form, or have lint require backticks.
- **F-2. The answers file's `prd` field is empty.**
  - `confirm.py:382` reads the frontmatter key `project`, but a PRD's key is `prd`.
  - Nothing reads the field yet, so no answer was affected.
- **F-3. The owner had to ask what text to type, twice.**
  - First, what goes in a bug's "What should it do instead?". Second, how to answer a question, Q-01 in particular, which asks two things.
  - The Correct box has a hint; the bug and question boxes have none.
  - To fix: a one-line hint under each box (the intended behaviour in plain words, not the fix), and for a question, that a note may answer a second part.

## Owner's notes

- The two questions in F-3, asked in the chat while answering.
