---
name: changing-prds
description: Use when changing what a system does in a repo that has a docs/prd/ folder - a new feature, a changed rule or status code, a bug fix that alters behaviour, a removed requirement - or when /prd-change runs, or when asked to change code and let the PRD follow, or when an agent hits something the PRD does not say; the PRD changes first, with new IDs and a version bump, before any code
---

# Changing PRDs

## Overview

**The PRD changes first.** `docs/prd/<slug>/` is the authority for what the system does. Code
implements it and never defines behaviour it lacks. A behaviour change is a PRD change, approved
by the user, before a line of code moves.

**Violating the letter of these rules is violating the spirit.** "Tiny", "one line", "just
reuse the number" and "the PRD can follow" change nothing below.

Grammar (blocks, removed IDs, test cases): `${CLAUDE_PLUGIN_ROOT}/references/prd-format.md`.
Read it before editing. Lint, the mechanical gate:

```bash
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"
```

The gate is the `prd-lint-exit=` value lint prints: `0` clean, `1` violations, `2` usage or internal error. Ignore the Bash call's own success; the trailing echo always succeeds. Use this form every time you run lint.

## The gap rule

Any agent (builder, tester, deployer, reviewer) that meets something the PRD does not say (a
missing error code, an unknown URL, an unspecified empty state) stops. It does not guess, and it
does not read the code to fill the gap. The gap is a change request: start step 1 here, with
the gap as the change.

## Non-negotiable rules

1. **PRD before code.** Do not edit source, tests or migrations until the user has approved the
   PRD change (step 5). "Just fix the code, the PRD can follow" gets the PRD change first, and
   the code waits.
2. **The version follows behaviour**, not the size of the edit and not the API compatibility
   rules in `prd.md` §9. §9 says what breaks clients; this table says what the PRD version does.
3. **IDs are never reused**, not even when the user asks. Never offer to reuse one "if you
   insist".
4. **Nothing is deleted from the record.** A removed requirement or AC stays, marked removed.
5. **Everything that describes the behaviour moves with it**: ACs, test-case expectations,
   `errors.yaml`, `openapi.yaml`, permissions, schema, fixtures, Observability rows. A stale test
   case is a wrong spec.
6. **Read whole PRD files only to edit them, except step 0's check of §14, or reading a PRD line to quote it verbatim when dismissing a dry-run question, as step 4 requires.** Work from the `prd_context.py` pack. Open another
   PRD file only for what the pack's closing lines name. Run the pack before you open any PRD
   file, however small the PRD looks: `cat`, `head`, `sed` or `grep` of a PRD file through Bash
   is opening it. Another area's files come from the pack, never from a read; the area's own test cases are opened only to revise them in step 2.

## Version rule

| Level | When | Examples |
|---|---|---|
| **Major** | existing behaviour changes or is removed | getOrder answers 410 instead of 404 for a deleted order: 1.0.0 → **2.0.0**. Dropping the empty-file rule AC-001.3: major. |
| **Minor** | behaviour is added, nothing existing changes | admins can archive an order, a new FR-005: 2.0.0 → **2.1.0**. Accepting CSV files with a BOM: minor. |
| **Patch** | wording only; no AC, test expectation, contract or result changes | a typo, a clearer Flow line |

If any existing AC, test-case `expect`, error code, status code or response changes meaning or
disappears, it is major. Ask "can a test that passes today fail after this?" Yes means major.

## ID rules

- **Next free FR or NFR number** = the highest FR or NFR number in the PRD, across both kinds and
  removed ones included, + 1. With FR-001..FR-003 and NFR-004, the next is **FR-005**.
- **Next free AC number** in a block = its highest AC number, removed ones included, + 1.
- **Next free T number** for a requirement = the highest it has ever used, + 1. Count the T-ids
  on its `Tests:` line, in `test-cases/` and in every §14 changelog row: a deleted test case
  survives only in the changelog. T-ids are per requirement: `T-005.1` belongs to FR-005.
- `id-removed-reused` fails when a test case, `x-prd-ids` or `Traces:` cites a removed ID.

| Item | Changed | Removed |
|---|---|---|
| Requirement block | revise it; `Status: approved` | `Status: removed (since X.Y.Z)`; keep the block and its ACs |
| Index row (§11) | status `approved` | status `removed` |
| AC | revise its text, same ID | `- AC-001.3 (removed in 2.0.0) <original text>` |
| Test case | revise `expect` and inputs | delete it; drop its T-id from `Tests:` |
| Contract items | revise | delete only what nothing else cites (`error-codes` checks) |
| `errors.md` ledger | existing entries stay as written | existing entries stay as written |

## The five steps

0. **Check the PRD was ever approved.** If `prd.md` §14 holds no row at 1.0.0 or above, the PRD
   has never been approved: it is a draft, not a change. Stop and continue it with
   `prd-toolkit:authoring-prds`, which resumes at its first open gate. Never version a clarify
   answer, and never approve a 0.x PRD through step 5; its first approval is authoring phase 7.
1. **Restate the change** in one sentence, then list everything it touches: FR, NFR and AC IDs,
   T-ids, error codes, `openapi.yaml` operations and responses, permissions, schema columns,
   fixtures, Observability rows. Then, as your first look at the PRD, run the pack for the area and the IDs the change touches, one command per Bash call:
   `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs>; echo "prd-context-exit=$?"`.
   If you do not know the area, run the repo pack first (no `--area`); if you do not know the
   IDs, run the area pack (`--area` only) and list the touched IDs from it. Each is its own Bash
   call, with the same `prd-context-exit=` gate. Pass only the UJ, FR and NFR IDs, and a bug fix's `E-nnn`: map an AC, test case or error code to its requirement.
   A new sub-project has no area yet: leave out `--area` and `--req`. A bug fix runs the pack with
   its entry's ID, `--req E-nnn`: the pack then holds the entry, the blocks its `Touches:` line
   names and the parent block of each test case `known-failing` on it. The `prd-context-exit=`
   value must be `0` or `1`; `2` is a usage error, so fix the command. Never pipe, filter or
   truncate the pack's output (no `| head`, no `| grep`): `prd-context-exit=` then reports the
   filter's status, not the pack's. Work from the pack; read no whole PRD file yet. For a design choice
   the request leaves open, pick the recommendation the PRD or repo supports and carry it to
   step 5 as a decision the user confirms. A value only the user knows (a name, URL, limit):
   ask, and stop until answered.
2. **Edit the PRD.** New behaviour gets new IDs (rules above). Changed and new requirements go to
   `approved` in the block and the index. Revise every test case whose AC changed and write one,
   with all seven elements, for every new AC. Revise `errors.yaml` (new code or changed
   `status`), `openapi.yaml` (responses, `x-error-codes`, `x-prd-ids`) and every other contract
   step 1 listed. If a block the change touches has a `Source:` line, run the pack again with
   `--for implement` (its own Bash call, the same gate), re-read each region it marks STALE, and
   rewrite that ref as `<path>:<current line> @<HEAD short sha>`. Set the PRD status to `In review`.
3. **Bump the version** in `prd.md` frontmatter by the table, set `updated` to today, and add a
   §14 changelog row: `| 2.0.0 | <date> | <change>; <dry-run record> | <IDs> |`. The IDs cell
   lists every new, changed and removed ID, T-ids included; it is the only record of a deleted
   test case. Step 4 fills the dry-run record: `dry run T-002.3, T-003.3, 0 open questions, 1 dismissed by quote`,
   `no dry run (removal only)`, `no dry run (unit only)` or `no dry run (wording only)`.
4. **Lint and dry run.** The `prd-lint-exit=` value must be `0`. Then dry-run the new and revised T-ids only, never a
   `level: unit` one: unit cases read code, stay with the builder and are never sampled, as in
   authoring phase 6, where exit 1 from `--sample-tids` fails the gate. An empty slot is not a
   dry run and never passes; when every new and revised T-id is unit, record
   `no dry run (unit only)` instead of dispatching. Dispatch
   the `prd-toolkit:prd-tester` agent, those T-ids in its prompt, as
   `${CLAUDE_PLUGIN_ROOT}/skills/testing-from-prds/dispatching.md` says (dry-run directory, state
   check, dispatch, judgment, cleanup). Only when `prd-tester` is not in the Agent tool's list,
   dispatch a fresh general-purpose subagent with
   `${CLAUDE_PLUGIN_ROOT}/skills/authoring-prds/dry-run-prompt.md` instead. Either way it passes
   on the terms that file states, and a state check that finds a changed path outside the
   dry-run directory fails it: report the paths and restore nothing yourself. Then delete the
   dry-run directory, pass or fail (dispatching.md's cleanup step).
   Anything else fails it, and every question is a gap:
   fix the PRD and run it again. A gap that predates this change counts the same, because the
   changed T-ids cannot be tested without its answer: ask the user for it. A removal with no new
   or revised T-ids has no dry run; say so. If you cannot dispatch a subagent, report the dry
   run as not run; the change cannot be approved until it runs.
5. **Approval, then commit.** First check what this conversation holds. If it does not hold a
   passing dry-run report, or the recorded reason there is none, for the current files, run
   step 4 now. `In review` and a clean lint are not evidence that it ran; a new session starts
   with neither. Then show the user the restatement, the changes by ID, the new version and why
   that level, the decisions from step 1, the lint result and the dry-run report. Wait for
   explicit approval. Then: status `Approved`; the `prd-lint-exit=` value is `0`; rerun
   `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_block.py" docs/prd/<slug>`; grep
   `docs/superpowers/plans/` for every changed ID and list each plan file that cites one as
   needing an update; commit the PRD folder and CLAUDE.md. Only now may code change, and each
   behaviour commit cites its IDs (`Refs: FR-005`). Hand off with only the UJ, FR and NFR IDs (map an AC, test case or error code
   to its requirement): write the code from `/prd-context <area> <changed IDs> implement`.
   After the code commit, run the implement pack again (its own Bash call, the same gate), then
   rewrite each STALE `Source:` of a changed block as `<path>:<line> @<new short sha>` and commit
   the PRD. A `Source:` refresh is provenance, not behaviour: it takes no version bump and no
   §14 row, and the status stays Approved with no re-approval.

## Red Flags - STOP

- "I counted this as a minor change because §9 doesn't cover import results."
- "§9 doesn't call a new status code breaking", so minor.
- "As you asked, I left the PRD unchanged." Any edit under `src/` before step 5.
- Editing the PRD and the code in one pass, with no approval between them.
- Deleting an AC line or its block "and everything that existed only for it", with no
  `removed` marker.
- "If you still want FR-003, I'll do it." Any offer to reuse an ID on request.
- A changed status code or error with its test case's `expect` and `errors.yaml` untouched.
- A changelog row whose IDs cell leaves out a removed AC or a deleted test case's T-id.
- Asking the user to pick the ID, the version level or anything else a rule here decides.
- "Approve this change and treat the older gaps as a separate change." Any offer to approve
  over a failed dry run.
- A version bump, a changelog row or an approval on a PRD whose §14 has no row at 1.0.0 or
  above. A never-approved draft goes back to `prd-toolkit:authoring-prds`.
- A dry-run slot holding a unit T-id, or no T-id at all.
- A dry-run question dismissed without an exact quote of the PRD line that answers it.

**All of these mean: stop, put the code back, and return to the step whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "It's a tiny wording fix." | A changed status code is changed behaviour. The version table decides, not the word count. |
| "§9 doesn't list it as breaking." | §9 is about API clients. The PRD version is about behaviour: changed or removed is major. |
| "The user said the PRD can follow." | The PRD never follows. Write the PRD change; the code waits for approval. |
| "It's one line of code." | One line that changes behaviour without the PRD makes the PRD wrong, and every tester then tests the wrong thing. |
| "Deleting the dead AC keeps the PRD clean." | It erases the ID, and the next agent may reuse it. Mark it removed; the record stays. |
| "Reusing the free number is tidier." | Changelog rows, commits and tickets already cite it. A reused ID silently changes their meaning. |
| "I'll fix the code while the PRD waits for approval." | Approval can change the PRD. Code written first encodes the unapproved version. |
| "It is still a draft, so a quick approval here is fine." | A draft's first approval needs authoring phases 4 to 6: sign-off, the checklist and a full dry run. Step 5 checks only a change. |
| "The dry-run questions are old gaps, not mine." | The tester still cannot test the changed T-ids. Ask for the answers; the change waits for them. |

## Related skills

- **prd-toolkit:authoring-prds** writes a new PRD and resumes a never-approved draft (step 0);
  its `dry-run-prompt.md` holds the dry-run pass terms and the fallback prompt.
- **prd-toolkit:testing-from-prds** is what `prd-tester` follows, and its `dispatching.md` is
  step 4's dispatch.
- **superpowers:writing-plans** turns the approved, changed IDs into tasks.
