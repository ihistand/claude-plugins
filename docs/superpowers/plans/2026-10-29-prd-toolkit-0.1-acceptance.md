# prd-toolkit 0.1 acceptance run

> **Date:** 2026-10-29
> **Plan:** `2026-10-29-prd-toolkit-0.1.md`, Task 15
> **Result:** passed. `link-shortener` 1.0.0 was authored from scratch and approved, after three
> toolkit fixes found during the run.

## What ran

`authoring-prds`, followed phase by phase, in a scratch git repo
(`scratchpad/prd-sample`). The project was an internal link shortener: Python 3.14 and FastAPI
on Cloud Run, Cloud SQL Postgres 16, and oauth2-proxy sign-in. Ivan answered every clarify
round.

| Phase | Outcome |
|---|---|
| 1 Context | Empty repo; proposed 1 standards row and 3 skills rows |
| 2 Draft | Template copied and filled; lint exit 0 on the first draft; 33 markers, 7 assumptions |
| 3 Clarify | 3 rounds (15 questions), then 3 category gaps covered by assumptions |
| 4 Sign-off | 19 assumptions confirmed; sqlfluff `enforced`; 2 skills `required`, 1 `recommended` |
| 5 Gate | Lint 0; the quality checklist found 7 gaps lint cannot see, all fixed (one new assumption, A-19) |
| 6 Dry run | 12 runs (see below); passed on run 12 |
| 7 Approval | `Approved` 1.0.0; lint 0 at Approved; `prd_block.py` wrote the block; `--check` 0; committed |

The approved PRD has 5 requirements (FR-001, FR-002, FR-004, FR-005 and NFR-003), 4 user
journeys, 26 test cases across unit, integration, component, system and acceptance, 7 error
codes, 5 operations with a full permissions matrix, and a component contract for the My links
page.

## The dry run, run by run

| Run | Questions | Real gaps | What it found |
|---|---|---|---|
| 1 | 11 | 11 | No test harness at all: lifecycle, DB access, fixture paths, browser identity, conventions |
| 2 | 9 | ~7 | HTTP client, fixture loader, effect columns, `confirm` semantics; 2 answered in prd.md but unread |
| 3 | 10 | 5 | A fault-injection test a black-box tester cannot do, no 500 body, log path, content-type rule |
| | | | **Fix 1 (c5955b7):** the tester writes missing helpers itself; their internals go under HARNESS CHOICES |
| 4 | 7 | 2 | Leak matching rule; psql on PATH. The tester never opened `test-cases/nfr.yaml` |
| | | | **Fix 2 (6d0efb1):** `--sample-tids` prints each case's file |
| 5 | 14 | ~8 | First staging-level sample: staging data, staging identity, the p95 definition, sign-off format |
| 6 | 9 | 2 | "no row for handbook", list-item assertion rule; 7 already answered by the PRD |
| | | | **Fix 3 (02257f3):** a question may be dismissed only by an exact PRD quote |
| 7 | 9 | 2 | Environment switch, typed fixture comparison |
| 8 | 11 | 4 | The acceptance case could not run twice (a retired code), k6 base URL, the caller's email, a rule contradiction |
| 9 | 9 | 2 | k6 script location, staging leak check |
| 10 | 13 | 1 | An acceptance step missing for a stated expectation |
| 11 | 10 | 2 | Page text matching, page wait time |
| 12 | 8 | 0 | **Pass:** all 8 dismissed by quote or by the HARNESS CHOICES rule |

**Reading.** The gate did real work: about 50 real gaps over 12 runs. One was a design bug, an
acceptance case that would have failed on its second run. One was an internal contradiction
between two testing rules. Without fixes 1 and 3 it could never pass. The tester asks about
helpers that do not exist yet, and re-asks 5 to 7 questions the PRD already answers in every
run. Both fixes keep the gate strict: a dismissal needs a verbatim quote, and a harness choice
that changes an assertion still fails.

## Toolkit fixes made during the run

All are on `feat/prd-toolkit`, each with a test that fails without it.

| Commit | Fix | Test |
|---|---|---|
| c5955b7 | `dry-run-prompt.md`: write missing harness helpers; report HARNESS CHOICES | `tests/test_dry_run_prompt.py` |
| 6d0efb1 | `--sample-tids` prints `<T-id> <file>`; the prompt passes the file | `test_sample_tids_name_the_file_that_holds_each_case` |
| 02257f3 | Dismissal only by exact quote (DISMISSED list); red flag in both skills; record counts dismissals | `test_pass_terms_allow_dismissal_only_by_exact_quote`, `test_both_skills_flag_a_dismissal_without_a_quote` |

## For 0.1.1

1. **Done on `feat/prd-toolkit`, folded into 0.1.0 because it is not yet released: ship a Harness section in the template's `testing.md`** with slots for everything runs 1
   to 11 asked for:
   - lifecycle and DB access
   - the environment switch (`TEST_ENV`)
   - clean state on throwaway environments only, and seeding on persistent ones
   - layout and file names, including k6 scripts
   - the HTTP client and the fixture loader
   - browser identity
   - assertion rules: unlisted fields, list items, "reads", "above", waits
   - effect rules, including the "unchanged" exception
   - the leak rule: values, matching, flush wait, sinks, and the staging log read
   - tools on the runner

   This would have removed most of runs 1 to 9. It shipped as 15 marked slots. The slot names
   are prose, so they must not collide with a PRD's banned synonyms: "HTTP client" became
   "HTTP requests" after the orders fixture's glossary (which bans "client") flagged it.
2. **Format `refs:` on test cases.** Cases that depend on prd.md content, such as a component
   contract or the skip-auth list, should cite it. The tester reads test-case files, not prd.md.
3. **Template guidance for acceptance cases on persistent environments:** use fresh data per
   run, and assert only what the signer can see.
4. **Authoring phase 2 should write test cases against the harness section,** not before it.
   Most dry-run gaps were harness facts the draft never asked about.
5. **The final review's parked minors** (ledger): hint markers in YAML/SQL comments need deleting
   once answered; Mustache `{{x}}` in YAML values fires `placeholder`; data files and editor
   backups get raw scans; phase 7 rollback should also remove the §14 1.0.0 row; validator
   subprocess encoding.
6. **Lint for harness facts (0.2):** a rule that `testing.md`'s Harness slots are filled, so the
   dry run is not the first place a missing convention shows up.
7. **Run the eval suite again** after fixes 1 to 3. They change both skills' gate text, though
   not their descriptions.
