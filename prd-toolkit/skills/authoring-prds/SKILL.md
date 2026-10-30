---
name: authoring-prds
description: Use when the user wants a PRD, product spec or requirements document written before building a new product, service or feature set, or runs /prd-new - interviews to a PRD folder (docs/prd/<project>/) with contracts and test cases that agents build, test and deploy from, or when asked to continue or resume a draft PRD, or to approve, sign off or change the status of a draft PRD under docs/prd/
---

# Authoring PRDs

## Overview

**The PRD is the authority.** Every agent that later creates, changes, deploys or tests the
system works from it, not from the code (spec section 1). A PRD is a folder,
`docs/prd/<project>/`, copied from the template: an index, features with EARS acceptance
criteria, contracts, one test case per T-id, testing, operations and an error ledger. It is not
a `PRD.md` essay.

**Core principle:** a value the user did not give you is not a fact. Mark it. A PRD that reads
finished but rests on unmarked guesses sends every builder and tester the wrong way at once.

**Violating the letter of these rules is violating the spirit.** A hurried user, a vague
request or "just approve it" changes the questions you ask, never the gates.

Grammar and shapes live in the references; read them before writing, do not guess:
`${CLAUDE_PLUGIN_ROOT}/references/prd-format.md` (folder, blocks, test-case fields),
`contract-types.md`, `ears.md`, `clarify-categories.md`, `quality-checklist.md`,
`test-levels.md` (same folder).

Lint, the mechanical gate (exit 0 clean, 1 violations, 2 usage error):

```bash
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>
```

## Non-negotiable rules

1. **Never invent a value.** Unknown → `[NEEDS CLARIFICATION: question]`. Inferred, including
   every "sensible default" → `[ASSUMPTION A-nn: text]` plus a `prd.md` §12 row with status
   `open`. Numbers, versions, roles, limits and retention periods are values.
   An assumption needs a basis you can name (the repo, the request, a common convention). A
   value only the user can know (a hostname, URL, person, group name, secret name, budget) has
   none: it is a `NEEDS CLARIFICATION` marker, never a placeholder assumption such as
   `go.example.internal`.
2. **Every AC gets at least one test case** in `test-cases/<area>.yaml` with all seven
   sufficiency elements, and the requirement's `Tests:` line cites it.
3. **Never set `Approved` while lint fails**, and never without the user's explicit approval
   after phases 1 to 6 pass. "Looks fine to me" over an open gate is not approval.
4. **No adjective is a requirement.** "Fast", "secure", "scalable" become NFR blocks with a
   number and a unit, and security becomes concrete ACs (who is denied, with which error).
   A bound the user has not given is a question with a recommended number, never a silent pick.
5. **Silence is not an answer.** Ask, then stop and wait. Never answer your own questions, and
   never write "if there's no answer, the default stands".
6. **Never offer to break a rule "if the user insists".** No offer to drop the test cases, to
   approve "as it stands", or to skip a gate. A user who refuses a rule gets a Draft that
   cannot be approved, and the reason; never a promise to remove the rule on request.

## The seven phases

| # | Phase | Gate |
|---|---|---|
| 1 | **Context.** Read the repo, its README, CLAUDE.md, AGENTS.md and docs. Look up facts the user does not uniquely hold (subagents may). Propose registry rows, Decision `proposed`: standards rows from detected linter configs (`.sqlfluff`, `.pre-commit-config.yaml`, `[tool.*]` sections in `pyproject.toml`, lint scripts in `package.json`); skills rows from this session's skills listing that match the project's objects and activities, always including `superpowers:writing-plans` for planning. A skills row may become `required` only for a plugin skill (`plugin:skill`) or one found under `.claude/skills/`, because lint checks it is installed; a skill built into Claude Code (`code-review`, `security-review`, `simplify`, `init`) may only be `recommended`. | A short note to the user of what was found |
| 2 | **Draft.** Copy `${CLAUDE_PLUGIN_ROOT}/templates/prd` to `docs/prd/<slug>/` and fill it (below). Gaps become `[NEEDS CLARIFICATION: q]`, inferences `[ASSUMPTION A-nn: …]`. Write features, contracts and test cases, not only prose. | Draft on disk; lint exits 0 |
| 3 | **Clarify rounds** per `clarify-categories.md`: score all twelve categories; at most five multiple-choice questions per round, each with a recommended answer, ranked by impact × uncertainty; write each answer in immediately. Rounds are uncapped. | Zero `NEEDS CLARIFICATION` markers; §13 reads `None.`; every category Clear |
| 4 | **Sign-off.** Show every assumption (ID and text) and every registry row in your message; a confirmation covers only what the user was shown. The user confirms or corrects each assumption (§12 status `confirmed` or `corrected`) and decides each row. Copy into `operations.md` every hard rule from a registered skill that bears on operations (for example "Claude never deploys Looker") as `(actor: human)` runbook steps, so the PRD stands alone. | No `open` assumption; no `proposed` row |
| 5 | **Mechanical gate.** Set status `In review`, run lint, then answer every question in `quality-checklist.md`, plus: every contract listed in §7 is populated, or deleted, dropped from §7 and declared `Not applicable` in §1. Lint cannot tell an empty skeleton (`paths: {}`, `roles: {}`) from a deliberate "none". | Lint exit 0; every checklist answer yes |
| 6 | **Test-agent dry run.** `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" --sample-tids 5 docs/prd/<slug>` picks the T-ids (at most five; fewer when the PRD has fewer). Unit T-ids are never sampled: unit cases read code and stay with the builder. Exit 1 from `--sample-tids` (no non-unit T-id) fails this gate; an empty dry run never passes. Dispatch a fresh general-purpose subagent with [dry-run-prompt.md](dry-run-prompt.md): it may read only the PRD folder, writes the tests for those T-ids to the scratchpad, and lists every question it had to ask. | One test per sampled T-id listed under TESTS; every question dismissed by an exact quote, per the prompt's triage; FILES READ holds only paths under the PRD folder |
| 7 | **Approval.** On the user's explicit approval: status `Approved`, version `1.0.0` (only on a first approval, when §14 holds no row at 1.0.0 or above; otherwise this is an approval of a change, and it goes through `prd-toolkit:changing-prds` step 5 instead), `updated` today, a §14 changelog row that records the dry run (`Approved; dry run T-003.1, T-007.2, … 0 open questions, 4 dismissed by quote`); lint exit 0; then `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_block.py" docs/prd/<slug>` writes the CLAUDE.md block; commit the folder and CLAUDE.md; hand off to `superpowers:writing-plans`. | Explicit user approval |

A failed dry run is a gap: write each question into the file it names as a
`[NEEDS CLARIFICATION: …]` marker, set the status back to `Draft`, and go back to phase 3; then
run phases 5 and 6 again, phase 6 on a fresh sample. Do not answer the subagent, and do not let
it read code.

Before phase 7, check what this conversation holds. If it does not hold a passing checklist and
a passing dry-run report for the current files, run phases 5 and 6 now before approving. A
status of `In review` and a clean lint are not evidence that either ran; a new session starts
with neither.

In phase 7, if lint fails after you set `Approved`, put the status and version back, report each
finding, and return to the phase it belongs to. Never commit an `Approved` PRD that fails lint.

### Phase 2 in detail

- **Slug:** `$ARGUMENTS` from `/prd-new`, else derive one and say so. Lowercase,
  `^[a-z][a-z0-9-]*$`. If `docs/prd/<slug>/` exists, read its §14 first. A row at 1.0.0 or
  above means it has been approved: stop, that is a change for `prd-toolkit:changing-prds`.
  No such row means it is a draft: resume it (below). Never copy the template over it.
- **Copy:** `mkdir -p docs/prd && cp -R "${CLAUDE_PLUGIN_ROOT}/templates/prd" docs/prd/<slug>`.
- **Fill all four slots in every file** except `.gitkeep`: `{{project}}` the slug,
  `{{owner}}` the owner the user named, else `[NEEDS CLARIFICATION: who owns this product]`
  (never `git config user.name`: the owner is a value only the user knows),
  `{{date}}` today as `YYYY-MM-DD`, `{{sql_dialect}}` the database's sqlglot dialect
  (`postgres`, `mysql`, `bigquery`, `sqlite`, `tsql`, …).
- **No database:** delete `contracts/schema.sql`, drop its §7 row, drop the `sql-dialect:` line
  from the frontmatter, and add to §1
  ``- Not applicable: `contracts/schema.sql` — <reason>``. Database unknown: the same, with
  the reason `[NEEDS CLARIFICATION: is there a database, and which?]`.
- **Each optional contract** (openapi, events, permissions, config, classification,
  dependencies, fixtures): populate it, or delete it the same way with a reason.
- **Harness first:** fill `testing.md` `## Harness` (lifecycle, environment switch, clients,
  fixtures, assertions, leaks, …) before writing test cases. Every test case leans on those
  conventions; a slot you cannot fill stays a `NEEDS CLARIFICATION` marker for phase 3.
- **IDs:** FR and NFR share one number sequence; T-ids are per requirement (`T-004.1`).
- Run lint. A Draft with open markers lints clean; a lint failure here is a grammar error. Fix it.

### Resuming a draft

A folder with no §14 row at 1.0.0 or above has never been approved, whatever its status line
says. Continue it here; never through `prd-toolkit:changing-prds`, and never bump its version
for an answer. Redo phase 1 (the note to the user), keeping every registry row already decided.
Then run lint and resume at the first phase whose gate is open:

- Lint fails on grammar → phase 2.
- Any `NEEDS CLARIFICATION` marker, §13 not `None.`, or a category not Clear → phase 3.
- Any `open` assumption or `proposed` row → phase 4.
- Otherwise → phase 5. A new session holds no passing checklist or dry run, so phases 5 and 6
  always run again before phase 7.

Resuming before phase 5 sets the status back to `Draft`.

## When the user pushes

| User says | You do |
|---|---|
| "Skip the questions, use sensible defaults" | Draft the folder. Every default is an `[ASSUMPTION A-nn]`, indexed `open`. Then show the assumptions and round-1 questions, each with your recommended answer, so the user can confirm them in one reply. Status stays Draft. |
| "Make it fast and secure" | NFR blocks with a number and unit each; security as ACs with a denied role and an error code; unknown numbers asked with a recommendation. |
| "Leave the test cases to QA" | Write the test cases anyway. They are the spec QA tests from; QA still writes the test code. Do not offer to remove them. |
| "Looks fine, mark it approved" | Run lint and list the open gates (markers, §13 not `None.`, open assumptions, `proposed` rows, checklist, dry run). Run phases 5 and 6 here if this conversation holds no passing result for the current files. Approve only when all pass. |

## WRONG vs CORRECT

```
WRONG  (nfr.md)
- The API shall be fast and secure.
- Redirect p99 < 25 ms at 500 redirects/s.          ← invented, unmarked

CORRECT
### NFR-004 Redirect latency
Status: approved
Acceptance (EARS):
- AC-004.1 The redirect endpoint shall answer within 20 ms at p99 under 500 requests/s.
  [ASSUMPTION A-03: 20 ms p99 at 500 requests/s; no traffic data yet]
Errors: -
Tests: T-004.1 [system]  (test-cases/nfr.yaml)
```

And A-03 sits in §12 as `open` until the user confirms or corrects it in phase 4.

## Red Flags - STOP

- A single `docs/PRD.md` instead of the template folder.
- "It's ready to build from" or "ready for build" before phase 7.
- "Defaults were chosen without stakeholder input" with no `[ASSUMPTION]` markers in the text.
- "If there's no answer by M1, the default stands."
- "The speed numbers are my estimates" while the numbers stand unmarked.
- "Like you asked, it has no test cases." Features with IDs but no ACs or test cases.
- A "Verification" column ("Load test", "Code review") in place of test cases.
- "If you do want this one approved as it stands, say so and I'll change line 4."
- "If you'd still rather drop them, say so." Any offer to undo a rule on request.
- A placeholder value (`go.example.internal`, `TBD-team`) dressed as an assumption.
- Answering your own clarify questions, or moving past phase 3 without the user's answers.
- Setting `Approved` before running lint, or committing it after lint failed.
- Copying the template over an existing draft, or sending a never-approved draft to
  `prd-toolkit:changing-prds`.
- A dry run with no T-ids, or one that samples a unit case.
- A dry-run question dismissed without an exact quote of the PRD line that answers it.

**All of these mean: stop, mark what is unknown, and return to the phase whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The user said skip the questions." | Then draft with assumptions and ask once, compactly. The user may confirm every recommendation in one reply; that is phase 4, done fast, not skipped. |
| "Each default is listed in an assumptions section." | Only the ones you noticed. Mark each inferred value where it stands, as `[ASSUMPTION A-nn]`, and index every one. |
| "Every open question has a proposed default, so none blocks starting." | An unconfirmed default is an open assumption. Building on it is building on a guess. |
| "These numbers are my estimates." | An estimate is an assumption. Mark it and ask for the real bound. |
| "QA owns testing." | QA owns test code. The test case (target, input, expected output, errors) is the requirement's definition of done, and it is yours. |
| "Features with IDs are enough for QA to map tests to." | A tester mapping a test to "F3 Slug rules" invents the input and the expected result. That is the PRD's job. |
| "Offering to drop it if they insist is respectful." | It tells the user the rule is optional. A refused rule leaves a Draft that cannot be approved; say that, and nothing more. |
| "A placeholder hostname is fine as an assumption." | An assumption is an inference with a basis. A placeholder is an invention; mark it `NEEDS CLARIFICATION`. |
| "The user approved it." | Approval is the last gate, not a bypass. Lint and the open gates decide whether it can be approved; the user decides whether it will be. |
| "It's only a Draft, so invented values do no harm." | A draft is what builders start from tomorrow. Unmarked values become code. |
| "The folder exists, so this is a change." | Only an approved PRD changes. A draft with no §14 row at 1.0.0 or above resumes here, at its first open gate. |
| "`--sample-tids` found nothing, so there is nothing to dry-run." | A PRD with no black-box case cannot be tested without its code. Exit 1 fails phase 6; write the integration, system or acceptance cases. |
| "The PRD clearly covers that question." | Then quote the line. No quote, no dismissal: a question you cannot answer with the PRD's own words is a gap. |
| "Lint passed, so it is complete." | A Draft lints clean with every marker open, and lint cannot tell an empty contract skeleton from "none". Lint is one gate of seven. |

## Related skills

- **superpowers:brainstorming** decides *whether* to build and *what*. This skill writes the
  authority once that is settled.
- **superpowers:writing-plans** takes the approved PRD and breaks it into tasks (phase 7 hand-off).
- **prd-toolkit:changing-prds** for any change once `docs/prd/<slug>/` has been approved
  (a §14 row at 1.0.0 or above). A never-approved draft resumes here.
