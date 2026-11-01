# prd-toolkit 0.4 acceptance run

> **Date:** 2026-10-31
> **Plan:** `2026-10-31-prd-toolkit-0.4.md`, Task 14
> **Result:** pass on every pass-line item except two, adapted by R35 and R41. The implement-pack
> `Source:` item failed (F1, fixed in `9fb7c76`, not yet re-run). The no-reads-outside-the-pack item
> is partial (three caller reads, G1 and G2; rule 6 binds the caller by text only). A new PRD went
> from ticket to `Approved` 1.0.0, a partial build verified one requirement, a major change added a
> second, and a final build verified the changed requirement and the two it touched. Lint exited 0,
> trace exited 0 in CI form (`main..HEAD`) but 1 over the full range (commit `0fd78fc`, F3), the
> hook refused a commit with no `Refs:`, and every generated CI job exited 0 locally. The run found
> three small defects in toolkit text (F1 to F3), fixed with pins afterward, and gaps G1 and G2,
> dispositioned below. No reconcile classification was needed.
>
> **Scope.** A one-command Python project, run locally. Deploy gates, `live` and staging jobs are
> 0.5 and are not exercised.

## Run setup

- Scratch repository `<repo>`, outside this repo, never committed to here, never pushed. The
  scaffold `evals/scaffolds/hello_repo.py` created it: one commit holding `TICKET.md` and a
  `.gitignore`.
- Headless `claude -p`, `--model sonnet`, `--output-format stream-json --verbose`, with
  `--plugin-dir` set to this branch's `prd-toolkit` and the installed copy disabled so it could not
  shadow the branch. No permission-bypass flag.
- Each prompt carried the owner's approval of the gates and the instruction to choose the
  recommended answer and ask nothing. The prompts and transcripts are kept with the ledger
  (`S<n>.prompt.md`, `S<n>.jsonl`).
- Branch adaptation (ruling R41). The plan assumed FR-001 was the only requirement. The authored
  PRD has area `core` with UJ-01, FR-001 to FR-003, NFR-004 and NFR-005, so S2 built FR-001 alone
  (a partial build, leaving FR-002 and FR-003 `approved`), the `--shout` change took the next free
  ID (FR-006), and S4 built it. S3 and S4 ran on S2's build branch, as a user continuing the work
  would. The plan's "FR-002" reads as FR-006 below.
- Gate-aware trace (ruling R35): `approved` blocks need no tests yet, and a `built` or `verified`
  block needs citations for unit and build-gate T-ids only.

## The four sessions

| Session | Command | Outcome | Commits (scratch repo) |
|---|---|---|---|
| S1 | `/prd-new` from `TICKET.md`, then hooks and CI | PRD `hello` Approved at 1.0.0 with area `core`. The dry run took two rounds: round 1 found one gap (assumption A-11), the PRD was fixed, round 2 passed with 0 open questions and 5 dismissed by quote. Hooks installed, GitHub CI include generated | `0fd78fc` PRD and CLAUDE.md block; `c22450a` hooks and CI |
| S2 | `/prd-build core FR-001` | Read `running-a-build.md` first. Branch `prd-build/core-FR-001`. Builder wrote unit tests and code, tester wrote the integration tests. All T-ids passed in round 1. Lint and trace exit 0 with FR-002 and FR-003 `approved`. FR-001 `verified` with `Source: hello/__init__.py:4 @6378794` | `b211864` code; `6378794` tests; `c39304d` FR-001 verified |
| S3 | `/prd-change` add a `--shout` option | Major bump to 2.0.0, justified in the session: `--shout` was a valid name before, so FR-001's and FR-003's ACs and UJ-01 changed. FR-006 added; FR-001, FR-003 and UJ-01 back to `approved`. Dry run on the new and revised integration T-ids: 0 open questions, 2 dismissed by quote. See F1 | `540009d` PRD change |
| S4 | `/prd-build core FR-006 FR-001 FR-003` | FR-001, FR-003 and FR-006 `verified`, each with a `Source:` line. All T-ids passed in round 1. T-006.1 failed before the code and passed after (unit tests first, as the builder skill requires). The tester found T-001.2 to T-001.4 already written and kept them. See F2 | `9ec6739` code; `e5d31a3` tests; `8af6fc7` three requirements verified |

S1's `result` record gives `num_turns` 33 and `duration_ms` 280341. S2 and S4 each ran in several turns because the builder and
tester ran as background subagents.

## Pass line

The brief's pass line, from spec section 11 as amended by R35 (build-gate T-ids only) and adapted by
R41 (FR-006 for FR-002, the rest `approved`):

| Item | Evidence | Result |
|---|---|---|
| Lint exit 0 | `prd-lint-exit=0` at S1 approval, S2 close, S3 approval, S4 close and the final check | pass |
| Trace exit 0 | `prd-trace-exit=0` in S2 and S4 at close. CI form (`main..HEAD`) 0; full range 1 (commit `0fd78fc`, F3) | pass (CI form) |
| Verified blocks and `/prd-status` | FR-001, FR-003 and FR-006 `verified`. `/prd-status` at version 2.0.0 shows `core: approved 2, verified 3`, `nfr: approved 2`, and not built: UJ-01, FR-002, NFR-004, NFR-005. Not verified: none. Open errors: none. Matrix: every build-gate T-id of FR-001 (T-001.1 to T-001.5), FR-003 (T-003.1 to T-003.3) and FR-006 (T-006.1 to T-006.6) is `cited`; only the `approved` blocks' T-ids are `missing` | pass, as adapted |
| A commit inside the Boundary with no `Refs:` is refused | Two refusals. S1's own approval-time commit of the hook include, with no `Refs:`, was refused by the installed hook, then repeated with `Refs: none (no behaviour change)` (`c22450a`). The deliberate probe, a file under `src/` committed with no trailer, printed "no `Refs:` trailer (`Refs: FR-001`, or `Refs: none (no behaviour change)`)" and the accepted forms, and exited 1 (`proof/refused-commit.txt`) | pass |
| Each generated CI job's commands exit 0 locally | `prd-lint` (CI form) 0; `prd-trace` (CI form, `main..HEAD`) 0; `standards-1` 0; `test-unit` 3 passed, 0; `test-integration` 11 passed, 0 (`proof/ci-jobs-local.txt`) | pass |
| No PRD file read outside the pack and the files edited | Three reads by the caller sessions were outside both (the first three rows of the table below), and each has a disposition. Rule 6 binds the caller by text only | partial |
| No reconcile classification lacks its quote | No build failure needed reconciling: every tester run passed in round 1, so no classification was made and none lacked a quote. The two dry-run dismissals in S3 and the five in S1 each carry a quoted PRD line | pass |
| The `implement` pack shows FR-001's `Source:` excerpt where the change touches FR-001's code | **Failed in the run** (F1): S3 dropped FR-001's `Source:` line, so S4's first implement pack carried no code excerpt for FR-001. Fixed afterward and pinned by text | fail, fixed (not re-run) |

### Reads of PRD files by the caller sessions

Subagent reads (the builder's and tester's) are their job and are not counted. The caller's reads
that were a pack, a closing-line pointer, a file the session edited, or the step 0 and section 14
reading are not listed.

| Session | Call | Read | Why it counts | Disposition |
|---|---|---|---|---|
| S3 | 5 | `grep` over `testing.md` and `operations.md` for option and flag wording | Neither file was edited or pointed to | Gap 1: Later |
| S3 | 5 | `grep` of `nfr.md` and `test-cases/nfr.yaml` for FR and AC references | Neither file was edited or pointed to | Gap 1: Later |
| S4 | 85 | `grep` for status, block heading and `Source:` lines across every `*.md` in the PRD folder, run to find lines to edit at close | Reaches files that were not edited | Gap 2: Later |
| S2, S4 | 8, 9 | `grep ^status:` of `prd.md` | Preflight check that `running-a-build.md` prescribes | allowed: the procedure's own gate |
| S3 | 21 | `grep` of `testing.md` for the dry run's dismissal quotes | Rule 6 allows reading a PRD line to quote it | allowed |
| S2, S4 | 86 to 88, 86 to 87 | Reads and greps of `features/core.md` and `prd.md` to place the close edits | Both files were then edited | allowed: files edited |

S1 read no existing PRD file: it wrote the PRD itself from the templates and references, which are
plugin files.


### Rounds

| Stage | Rounds |
|---|---|
| S1 authoring dry run | 2 (round 1: one gap, closed; round 2: 0 questions) |
| S2 build, tester | 1 |
| S3 change dry run | 1 (0 open questions) |
| S4 build, tester | 1 |

## Findings

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| F1 | S3 dropped FR-001's `Source:` line from its revised block, saying "/prd-build rewrites it". The next implement pack then had no FR-001 code excerpt, which is the plan's pass line. `changing-prds` step 2 told the session to refresh a STALE `Source:`, not to keep a fresh one | S3 transcript; `Source:` present in `6378794`'s FR-001 block, absent after `540009d` | fixed in `9fb7c76`: step 2 says a revised block keeps its `Source:` line, a STALE one is refreshed to the current line and sha, and it is never dropped; Red Flag quotes the phrase. Pinned by `test_f1_*` in `tests/test_proof_findings.py` |
| F2 | `/prd-build` passed space-separated IDs to `prd_context.py --req`; the call exited 2 and the session retried with commas | S4 calls 8 and 10 | fixed in `9fb7c76`: `commands/prd-build.md` and `running-a-build.md` join the IDs with commas, shown as `--req FR-006,FR-001`. Pinned by `test_f2_*` |
| F3 | The full-range trace flagged S1's approval commit `0fd78fc`, which touches CLAUDE.md inside the Boundary and carries no `Refs:` trailer. The hooks did not exist yet, so nothing refused it. Local CI form (`main..HEAD`) is 0, because the CI range excludes it; a full-range run flags it | `proof/step5-checks.txt` | fixed in `9fb7c76`: authoring phase 7 and `changing-prds` step 5 commit the PRD folder and CLAUDE.md with `Refs: none (no behaviour change)`. Pinned by `test_f3_*`. The scratch repo's `0fd78fc` is left as the proof's record |
| G1 | S3 greps `testing.md`, `operations.md`, `nfr.md` and `test-cases/nfr.yaml` to learn the project's option wording and which requirements the NFRs cite, which the decide pack did not carry | S3 call 5 | Later: measure on a real area whether the decide pack should list the NFRs that cite the touched FRs |
| G2 | The close step greps the whole PRD folder for block headings and `Source:` lines to find the lines to edit | S4 call 85 | Later: the close step should name the block's file from the pack, so the grep is one file |
| G3 | The scaffold's refuse-non-empty test checks only a non-zero exit (from the Task 14 step (a) review) | Task 14 step (a) | fixed: the test now asserts the refusal message |

No toolkit code or text was changed during the run; F1 to F3 were fixed after it, from the
transcripts, and the suite grew by five tests (788 pass).

## Later

1. **The deploy-gate proof** (0.5). Deploy-gate T-ids, `live`, `prd_drift.py` and the staging and
   production CI jobs are not exercised here.
2. **Known-failing CI jobs** (0.6, ruling R37). A generated `test-<level>` job runs the whole
   harness, so it is red while a case is `known-failing` on an open `E-nnn`. The hello-world PRD
   has none; it is a documented known limit.
3. **The plan's FR-002 adapted to FR-006** (ruling R41). A rerun on a PRD where FR-001 is the only
   requirement would give the plan's literal result.
4. **Re-run S3 and S4 on the fixed text.** F1 is pinned by text only. A run of S3 followed by a
   build confirms the implement pack then carries FR-001's `Source:` excerpt.
5. **Pack gaps G1 and G2**, as dispositioned above.
6. **A caller-side guard hook** (0.3 Later item 5): rule 6 still binds the caller by text alone,
   which is why the caller reads in the table above were possible.
