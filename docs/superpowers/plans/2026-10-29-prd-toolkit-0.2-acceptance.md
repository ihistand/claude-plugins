# prd-toolkit 0.2 acceptance run

> **Date:** 2026-10-30
> **Plan:** `2026-10-29-prd-toolkit-0.2.md`, Task 9
> **Result:** partial. Adoption steps 0 to 4 and step 5 phases 3 to 5 worked on one dashboard area
> of a production Looker project. The run stopped at step 5 phase 6, because the sampled dry run
> did not converge. The area is `confirmed`, not `adopted`. The PRD is paused as a Draft at 0.1.0,
> and nothing was pushed. Seven toolkit fixes found during the run are on this branch, in six
> commits, each with a test. The remaining findings are listed under "Later" below.

## What ran

`adopting-prds`, step by step, in a worktree of the project on a `prd/<area>` branch. A session
loaded the branch's plugin. The project owner answered every question. The area is one dashboard
together with everything its tiles query.

| Step | Outcome |
|---|---|
| 0 Bootstrap | 137 candidate areas in the adoption map. The adopted area's Boundary holds the dashboard file, the model file and 16 view files, the parts its tiles use. Test roots cover the new suite directory and the project's existing test directory |
| 1-2 Extract | Every block `as-built` with a checked `Source:` line. Apparent bugs recorded as `E-nnn` entries. Lint exit 0 |
| 3 Confirm | 42 requirements confirmed one at a time through the question tool: 33 `live` and 9 approved as corrections of open bugs. 11 `E-nnn` entries: 8 open, each carrying the owner's intended behaviour, and 3 resolved as intended or out of scope |
| 4 Characterize | `prd-tester` suite with 117 T-ids, run 4 times in full against production through the API, read-only. Last run: 109 pass, 8 known-failing, every one cited on an open entry. 3 acceptance cases signed off. The integrity check was clean on every run |
| 5 Approve | Phases 3 to 5 passed: 3 clarify rounds, sign-off and the quality checklist. **Phase 6 blocked.** See "The dry run" |

**Caveat on step 3.** The owner gave the confirmation answers to exercise the process, not as
considered sign-offs. Many are right, but the `as-built` requirements and the `E-nnn` entries need
a real review before this PRD is used as the authority.

### Against the plan's Task 9 checks

| Check | Status |
|---|---|
| `prd_lint.py` exits 0 at Approved | Not reached: the PRD stayed a Draft |
| `prd_trace.py` exits 0 | Not run at the gate: step 5 did not reach it |
| Suite passes, or each failure is known-failing with an open `E-nnn` | Met: 109 pass, 8 known-failing |
| `prd-tester` dry run passes under the quote rule | Not met: did not converge |
| The guard blocked an attempt outside its roots, or none was made | Met: it blocked Bash `cat` and `grep` inside the PRD folder on every run, and the tester fell back to Read |
| Branch pushed and merge request opened | Not done: paused before landing |

## The dry run

There were five dry runs in a row, each on 5 sampled T-ids. Each one failed on 4 to 10 harness or
case gaps that the earlier runs had not reached:

- null handling in API results;
- row truncation;
- the JSON shape of pivoted results;
- date forms.

The last round's gaps were recorded as NEEDS CLARIFICATION markers.

0.1's 12 runs converged on a 26-case project. A sample of 5 out of 117 cases on a mature BI area
keeps landing on new conventions. The 5-sample gate measures coverage of the harness's own
conventions too slowly for an area this size.

## Fixed in 0.2 during the run

| Finding | Fix | Commit |
|---|---|---|
| Examples, tests and the 0.2 design named organization-specific hosts, users and objects | Neutral examples throughout | 3538e09 |
| Step 4 did not name the denials a headless run hits | Step 4 names them | 37eb394 |
| Bootstrap listed only a new suite directory as a test root, so the project's existing tests were left out | Every existing test directory is a test root | 89b78a2 |
| A directory that mixes tests with code could become a test root, making that code readable to the tester | A mixed directory is never a root; its command goes in the Levels table | 6a137e5 |
| Confirming dozens of requirements meant pasting IDs into a prompt | Step 3 asks through the question tool, a few at a time, with a checklist-file fallback | b8a43f1 |
| The tester reached for Bash `cat` and `grep` in the PRD folder, and the guard's block surfaced as a QUESTION on every run | The agent and skill say to read and search with the Read, Glob and Grep tools | cc51a7d |
| The `placeholder` rule flagged literal prose such as `<the data_state>` with no remedy | Detection unchanged; the finding and `prd-format.md` say to put literal angle-bracket text in backticks | cc51a7d |

## Later

**Fixed in 0.3** (branch `feat/prd-toolkit-0.3`): the extractor wrote `Touches: FR-nnn` lines into
`errors.md` entries, which the extract interface meant for the report only. 0.3 makes `Touches:`
an official, linted field.

**For a later release:**

1. **Dry runs that converge on a large area.** Candidates:
   - a full-coverage, non-gating dry run before the sampled gate;
   - a checklist of a platform's common API conventions (nulls, truncation, pivots, dates) that the
     harness answers once.
2. **RESULTS ID check.** The tester once reported T-034.2-4 as T-035.2-4. The caller should check
   that the RESULTS IDs equal the dispatched IDs before trusting a run.
3. **Installed plugin shadowing the branch.** An installed 0.1.0 lacked `testing-from-prds`, so lint
   refused the skill as `required`. The README should tell testers to disable the installed copy
   before loading a branch with `--plugin-dir`.
4. **Neutral prose in two references.** `references/contract-types.md:331` and
   `skills/testing-from-prds/dispatching.md:18` still use LookML as their example. A neutral example
   would keep the toolkit platform-free.

**For a platform wrapper plugin** (an organization's own plugin that calls these skills):

5. **Harness identity.** The run's API harness authenticated with a developer's personal API
   credentials rather than the dedicated automation identity the plan required. The reads were
   read-only, but the wrapper's harness must use the service identity.
6. **Boundary.** The first Boundary listed only the dashboard file. The wrapper should define a
   dashboard area as the dashboard plus the model and view files its tiles reach.
7. **Platform contract type.** The project has no custom contract type for its objects, and no
   offline validator for one.
8. **Confirmation UI.** A web form for step 3, for areas with dozens of requirements.

**Carried design limits** (unchanged from the 0.2 final review):

- The guard confines the tester's tool calls, not the harness processes it starts.
- The guard fails open on Python 3.6 or older, or when `python3` is missing.
- An edit to a git-ignored file already in the PRD folder escapes the integrity check.
- `adoption-second-area-minor` was not re-run after the one-command rule.

## Next for this area

The area resumes at step 5 phase 6 when the owner chooses. That means answering the open markers,
dry-running again, then approving. Approval also needs the review of the step 3 answers described
above. Landing it (push and merge request) comes after approval and needs the owner's go-ahead.
