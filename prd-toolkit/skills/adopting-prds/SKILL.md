---
name: adopting-prds
description: Use when bringing an existing codebase or one of its areas under a PRD - "adopt this repo", "write a PRD for what this already does", "reverse-engineer the requirements", /prd-adopt - extracts as-built requirements with sources, confirms intent with the user, and closes each area with characterization tests run by prd-tester
---

# Adopting PRDs

## Overview

**The code says what the system does. Only the user says what it should do.** Adoption brings a
running system under a living PRD, `docs/prd/<slug>/`, one area at a time. Every requirement
starts as `as-built`, with the line of code it was read from, and becomes a requirement only on
the user's word. An area is closed by a characterization suite that `prd-tester` writes from the
PRD alone and runs against the system.

**Core principle:** reading the code tells you its behaviour, never its intent. A PRD written
"from what the code does" protects every bug in it, and the next builder treats each one as a
promise.

**Violating the letter of these rules is violating the spirit.** "The code clearly intends
this", "just write down what it does", "the code is the proof" and "do it all in one go" change
nothing below.

Grammar: `${CLAUDE_PLUGIN_ROOT}/references/prd-format.md`: the adoption map (`adoption.md`, `| Area | State | Boundary |`; §8 holds only `See adoption.md.`),
`as-built` blocks with `Source: <file>:<line> @<commit>`, the `errors.md` ledger and
`known-failing: E-nnn`. Read it before writing. Lint, the mechanical gate:

```bash
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"
```

The gate is the `prd-lint-exit=` value lint prints: `0` clean, `1` violations, `2` usage or internal error. Ignore the Bash call's own success; the trailing echo always succeeds. Use this form every time you run lint.

## Non-negotiable rules

1. **One area at a time.** An area is one feature file, `features/<area>.md`, with its
   `test-cases/<area>.yaml`, bounded by the file globs in its adoption-map Boundary cell. Never
   extract a second area while another is past `not started` and not yet `adopted`. "Adopt the
   whole repo" gets the bootstrap, the map of candidate areas, and the first area the user picks.
2. **States move forward one step at a time:** `not started` → `extracted` → `confirmed` →
   `adopted`. Each step below has a gate; never skip a step or set a state its gate has not
   passed.
3. **An apparent bug never becomes a requirement.** Code that contradicts its docs, its name,
   its comments, its commit messages or its siblings becomes an `E-nnn` entry in `errors.md`
   (`Resolution: open`). No requirement text and no test-case `expect` encodes it. Only the
   user's word turns it into intended behaviour (step 3).
4. **Confirmation is the user's word, requirement by requirement.** Silence, "looks fine
   overall", the code being obvious and "the code clearly intends it" confirm nothing. Never
   write an answer the user did not give. When no answer can come (a headless run, the user
   gone), stop and present the confirmations; the area stays `extracted`.
5. **`adopted` only on a suite.** An area is `adopted` only on a suite that `prd-tester` ran in
   which every T-id of the area is `pass` or `known-failing E-nnn` with that entry open, plus
   lint, the checklist, a `prd-tester` dry run and the user's approval (step 5). Reading the
   code is not a test, and neither is running it by hand.
6. **Adoption changes no code.** Not a one-line fix, not the bug the user just agreed is a bug.
   A real bug stays in the code, recorded as an open `E-nnn` and a `known-failing` case; fixing
   it is a later change through `prd-toolkit:changing-prds`.
7. **Never offer to break a rule "if the user insists".** A user who refuses a gate gets an area
   that stays where it is, and the reason; never an offer to adopt, approve or confirm anyway.

## Versions

- The bootstrap PRD is a Draft at the template's `0.1.0`, and stays `0.1.0` until its first area
  is adopted. Extraction, confirmation and characterization never bump it.
- The first adopted area takes the first-approval path: authoring phase 7 sets `1.0.0`.
- Each later area is one change through `prd-toolkit:changing-prds`: adding an area adds
  behaviour to the PRD and changes none, so it is a **minor** bump (`1.0.0` → `1.1.0`).
- A confirmed requirement is `live (since <version>)`, where `<version>` is the version its area's
  adoption will carry: `1.0.0` for the first area, the next minor for a later one.
- A later area edits an Approved PRD, so set the status to `In review` when you write its first
  block (`prd-toolkit:changing-prds` step 2). One exception to changing-prds rule 1 (PRD before
  code): characterization tests the tester writes in step 4 are allowed before a later area's
  approval, since they are its evidence. `In review` allows no `[NEEDS CLARIFICATION]`
  marker, so the area's open questions are §13 bullets (`- Q-nn <question> (FR-nnn)`), in a
  Draft as well.

## The flow

| # | Step | Area state after | Gate |
|---|---|---|---|
| 0 | Bootstrap (first adoption only) | every candidate `not started` | the `prd-lint-exit=` value is `0`; the map lists every candidate area with a Boundary |
| 1 | Bound | `not started` | the user picked the area; its Boundary globs are recorded |
| 2 | Extract | `extracted` | every block `as-built` with a checked `Source:` line; every apparent bug an open `E-nnn`; the `prd-lint-exit=` value is `0` |
| 3 | Confirm | `confirmed` | the user's word on every requirement and every `E-nnn` of the area; the `prd-lint-exit=` value is `0` |
| 4 | Characterize | `confirmed` | a `prd-tester` suite with every T-id `pass` or `known-failing E-nnn`; the integrity check clean |
| 5 | Gate and approve | `adopted` | lint, checklist, dry run, the trace on the `adopted` row, and the user's approval, per the version path |

### 0. Bootstrap

Only when the repo has no `docs/prd/` folder for this system. If one exists, read its `adoption.md` and
§14: resume the area that is past `not started` and not `adopted`, at the step its state names;
a row `adopted` whose adoption has no §14 row is step 5 interrupted: resume at 5.3.

- **Slug:** the repo's name, lowercased to `^[a-z][a-z0-9-]*$`; say which you chose.
- **Copy:** `mkdir -p docs/prd/<slug>`, then Read each file under
  `${CLAUDE_PLUGIN_ROOT}/templates/prd/` and Write it to the same relative path under
  `docs/prd/<slug>/` (Glob `**/*` in the template lists them; each `.gitkeep` sits beside a
  README.md and may be skipped). Never copy with a shell command: a sandbox that denies the
  plugin folder as a copy source blocks `cp`, and Read and Write are the granted tools.
- **Fill the project-wide sections from the repo**, as `prd-toolkit:authoring-prds` phases 1
  and 2 say: the stack (§1), the glossary (§3), standards rows from detected linter configs (§5)
  and skills rows from this session's skills listing (§6), every row's Decision `proposed`; the
  four `{{…}}` slots; each optional contract populated or declared `Not applicable`; the
  Harness in `testing.md`, with `Test roots:`. Anything only the user knows (the owner, intent,
  environments, secrets) stays a `[NEEDS CLARIFICATION: …]` marker.
- **Test roots:** list every directory that already holds the project's tests (find them with
  Glob: test files, test configs, a test framework's own folder), each backticked, then any new
  directory the characterization suite needs. Never leave an existing test directory out: the
  project's tests are part of its harness, the Levels table names a command for each, and a
  root missing from the list is one the tester cannot write to and trace cannot read. A
  directory that mixes tests with the code they test is never a test root, because a root is
  readable by the tester: name its tests' command in the Levels table instead, and say so in
  the Layout bullet.
- **The adoption map:** create `adoption.md` (`# Adoption map`, then the `| Area | State | Boundary |` table) and replace §8's marker with `See adoption.md.`; one row
  per candidate area (a package, a module, a dashboard, an entry point that does one job), each
  `not started`, its Boundary the backticked globs of its files, comma-separated. Areas never
  overlap.
- Run lint. A Draft with open markers lints clean; a failure is a grammar error. Fix it.

### 1. Bound

The user picks the area. An area named in the request (or in `/prd-adopt`'s argument) is picked.
Otherwise show the map, recommend one area and why, and stop for the user's pick.

- Show the area's Boundary and the files it matches; correct it if the user does.
- The first area renames the template's `features/core.md` and `test-cases/core.yaml` to
  `features/<area>.md` and `test-cases/<area>.yaml`. A later area Reads the template's two
  files (`${CLAUDE_PLUGIN_ROOT}/templates/prd/features/core.md`, `test-cases/core.yaml`) and
  Writes them under its own name.

### 2. Extract

Dispatch a fresh **general-purpose** subagent (Agent tool) with
[extract-prompt.md](extract-prompt.md), its slots filled: `<REPO_ROOT>` the repository's
absolute path (`git rev-parse --show-toplevel`), `<FORMAT>` the absolute path of
`${CLAUDE_PLUGIN_ROOT}/references/prd-format.md` (expanded, since the subagent has no
`${CLAUDE_PLUGIN_ROOT}`), the area, its Boundary, `HEAD`'s short SHA as `<COMMIT>`, the PRD
folder, the next free FR and E numbers (`prd-toolkit:changing-prds` ID rules), the testing.md
Levels, and how to reach the live system read-only, or `none`. Send
nothing else: no summary of the code, no guess at intent. Never send `extract-prompt.md` to `prd-tester`: the tester never reads code, and the extractor must.

Then write what it returns, yourself:

- Its blocks into `features/<area>.md`, each `Status: as-built` with its `Source:` line, and a
  §11 row each (status `as-built`, Since empty).
- Its test cases into `test-cases/<area>.yaml`, all seven elements each, none at `level: unit`;
  its contract items into the contracts.
- Each APPARENT BUGS entry into `errors.md` as `### E-nnn`, `Resolution: open`.
- Each QUESTION as a §13 bullet.
- Check every `Source:` line before you write it: open the file at that line, at that commit,
  and see the behaviour there. A Source that does not show it is dropped, and the block with it.
- Check that no block or `expect` encodes an APPARENT BUGS entry. One that does is rewritten to
  the behaviour not in question, or dropped.

Set the area's row to `extracted` and run lint.

### 3. Confirm

Show the user every `as-built` requirement of the area, one by one: its ID, its ACs and its
`Source:`, and the `E-nnn` entries that touch it. Ask, for each, which of three it is:

- **Confirmed:** it is meant to work this way. Status `live (since <version>)`, the §11 row
  `live` with that Since.
- **Corrected:** it should work differently. The corrected text, status `approved`, and every
  test case of its ACs revised to match.
- **Unknown intent:** the user cannot say, and names who can. Status `approved`, the AC carries
  `[ASSUMPTION A-nn: <the behaviour>; <who> would confirm it]`, and §12 gets the row
  `| A-nn | <the behaviour> | awaiting <who> |`. An `awaiting` row may stay through approval;
  a user who names nobody has not answered.

A test case whose exact expected values came from a live read of a closed window (its `input`
names the query and the date range) is shown with those values: the user confirms them like any
`as-built` item, and a value the user does not confirm is corrected or dropped.

For each `E-nnn` of the area, ask whether it is a real bug. A real bug stays open, and the
requirement it touches is *corrected*, never confirmed: its text says the intended behaviour,
status `approved`, its test cases revised to match. Intended after all: the behaviour becomes
requirement text on the user's word, and the entry's Resolution says who confirmed it and when.

Confirmation is the user's word, requirement by requirement. One reply may answer every
requirement, as long as it answers each one. A reply that names no ID ("looks fine", "all good", "yes") confirms nothing: ask again, ID by ID, and leave every unanswered block `as-built`.
When nobody can answer (a headless run, no reply), stop and present the confirmations, and
leave the area `extracted`.

**How to ask.** Never make the user type IDs and decisions into one prompt. When the
AskUserQuestion tool is available, ask with the AskUserQuestion tool, at most four requirements
per call, one question per requirement, its header the ID. Its preview shows the whole block and its `Source:` excerpt, because a confirmation covers only what the user was shown. The
options:

- **Confirm**: confirmed.
- **Correct**: corrected; the user types the corrected behaviour as the answer's text.
- **It's a bug**: the behaviour is a defect. Write or keep its `E-nnn`, and the requirement is
  corrected to the intended behaviour, which the user states.
- **Someone else decides**: unknown intent; the user types who.

An answer that needs text and has none (a correction without the behaviour, a "someone else"
without a name) is no answer yet: ask for that one item again, in a plain message. Write each answer into the PRD as soon as it arrives (the status, the
ACs, §11, §12, `errors.md`), so a session that stops resumes with only the blocks still
`as-built`. Ask the same way for the area's §13 questions and its `E-nnn` entries, the
question or the entry in the preview.

**The checklist file.** When the AskUserQuestion tool is not available, or the user asks to work
in an editor, write `.prd-confirm-<area>.md` at the repository top, never inside the PRD folder or a test root: its `Source:` excerpts are code, and the tester reads those folders. One
section per item (each requirement, each §13 question of the area, each `E-nnn`): its ID, the
whole block or question, its `Source:` excerpt, and a `Decision:` line the user fills in with
`confirm`, `correct: <behaviour>`, `bug: <intended behaviour>` or `ask: <who>`. When the user
says the file is done, read it and apply each decision as above. A blank or unrecognised `Decision:` line is no answer: list those IDs and ask again. Delete the checklist file once every item is answered; it is never committed. A
headless run writes the file, says where it is, and stops with the area `extracted`.

When every requirement and every `E-nnn` of the area has the user's answer and §13 holds none
of the area's questions, set the row to `confirmed` and run lint.

### 4. Characterize

Dispatch the `prd-toolkit:prd-tester` agent in suite mode, exactly as
`${CLAUDE_PLUGIN_ROOT}/skills/testing-from-prds/dispatching.md` says: the state record before,
the dispatch with `Mode: suite`, `PRD: docs/prd/<slug>/` and every non-unit T-id in
`test-cases/<area>.yaml` (each with its test-case file), which you read yourself:
`--sample-tids` is for dry runs only. Then the integrity check after, and the judgment. Run its commands one command
per Bash call, with literal paths (dispatching.md's first rule): a headless session has denied a
compound with `rm` and a path built from a variable or `$(…)`, and one denial stops the run. A suite has no fallback: when
`prd-tester` is not in the Agent tool's list, the suite has not run and the area stays
`confirmed`.

Triage every `fail` with the user, one T-id at a time:

- **The PRD is wrong:** the user's corrected text goes in, with everything that describes it
  (`prd-toolkit:changing-prds` rule 5 and its ID rules). It is part of this area's change and
  takes no version of its own.
- **A real bug:** an `E-nnn` entry (new, or the open one that already describes it), the requirement drops to `approved`, and its test case gains `known-failing: E-nnn`. The test stays as written.

Then run the suite again. The gate is one RESULTS line per T-id of the area, each `pass` or `known-failing E-nnn` whose entry is open and cited on that case, and an integrity check that found no change outside the test roots. Anything else, and the area stays `confirmed`.

### 5. Gate and approve

Check what this conversation holds first. It must hold a passing suite (step 4) for the current
files; if a test case changed since, run step 4 again.

1. **Gates.**
   - First area (the PRD has no §14 row at 1.0.0 or above): clear what the bootstrap left open
     with `prd-toolkit:authoring-prds` phases 3 and 4 (markers, §13, `open` assumptions,
     `proposed` rows; an `awaiting <who>` row carries through), then its phases 5 and 6:
     `In review`, lint and the checklist, and the `prd-tester` dry run.
   - Later area: `prd-toolkit:changing-prds` step 4, lint and the dry run of the area's T-ids,
     and every question in `${CLAUDE_PLUGIN_ROOT}/references/quality-checklist.md` for the area.
   - Either way, run the dry run's commands one command per Bash call, with literal paths
     (dispatching.md's first rule).
2. **The adoption-map row.** Set only the area's row to `adopted`, uncommitted: trace scopes by
   that row. The status, the version and the §14 row stay untouched until the user approves.
3. **Trace,** before the user's approval and before any commit:

   ```bash
   uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_trace.py" docs/prd/<slug>; echo "prd-trace-exit=$?"
   ```

   `prd-trace-exit=2` is a tool error, never a pass: fix and rerun. A finding on `features/<area>.md`, or a `test-cites-live` finding that names one of the area's T-ids, blocks: set the row back to `confirmed` and return to step 4. Any other finding predates this area: show it to the user as pre-existing; it does not block.
4. **Approval.** Show the user the gates, the suite's RESULTS, the trace result and the version
   the approval will set: 1.0.0 for the first area, its first approval; for a later area, the
   next minor and why it is minor (the area adds behaviour to the PRD and changes none). Wait for
   explicit approval. If the user declines, set the row back to `confirmed`. Only on approval:
   - First area: authoring phase 7's status, version, `updated`, §14 row, lint and
     `prd_block.py` — not its commit or its hand-off. It sets status `Approved`, version `1.0.0`,
     `updated` today and the §14 row that records the suite
     (`Approved; notes area adopted; suite T-001.1 pass, T-002.1 known-failing E-001; dry run …`),
     then the `prd-lint-exit=` value is `0` and `prd_block.py` runs.
   - Later area: `prd-toolkit:changing-prds` step 3, then only step 5's post-approval actions —
     not its commit or its second approval. Step 3 is the minor bump and its §14 row, with `updated`
     today; the row records the suite as the first area's does
     (`| 1.1.0 | <date> | <area> area adopted; suite T-004.1 pass, …; dry run … | <IDs> |`); step
     5's actions are status `Approved`, the `prd-lint-exit=` value is `0`, `prd_block.py` and the
     `docs/superpowers/plans/` grep.

   Then commit the PRD folder, the suite's tests and CLAUDE.md together.

## When the user pushes

| User says | You do |
|---|---|
| "The code clearly intends this, mark it confirmed" | Show each `as-built` requirement with its Source and ask for each one. The blocks stay `as-built` until the user answers for them by ID. |
| "It looks like a bug, but just write down what it does" | Write it as an `E-nnn` in `errors.md`, `Resolution: open`. The requirement covers only the behaviour not in question; step 3 asks the user which it is. |
| "Skip the characterization tests, the code is the proof" | The area stays `confirmed`. Only a `prd-tester` suite moves it to `adopted`; say so, and offer to run it. |
| "Adopt the whole repo in one go" | Bootstrap the PRD and map every candidate area `not started`. Then one area: the user's pick, or your recommendation shown and the pick awaited. |
| "Fix the bug while you're at it" | No code changes during adoption. Record the `E-nnn` and the `known-failing` case; the fix is a later change through `prd-toolkit:changing-prds`. |

## WRONG vs CORRECT

```
WRONG  (asked: "just write down what it does")
### FR-001 Search notes by term
- Matching is **case-sensitive**: `"Milk"` does not match `"buy milk"`.     ← the bug, as a requirement
Source: `src/notes/app.py:13`.                                              ← no commit; a Draft "as-built" essay

CORRECT
### FR-002 Search notes
Status: as-built
Source: src/notes/app.py:13 @47ad27a
Acceptance (EARS):
- AC-002.1 When `notes.app.search_notes(term)` is called, it shall return, in insertion order,
  the text of every stored note that contains `term`.
...
errors.md:
### E-001 search_notes matches case-sensitively
Classification: code bug
Diagnosis: `term in t` misses "Buy Milk" for "milk"; the code's own comment calls it an apparent bug
Resolution: open
```

The test case for AC-002.1 uses notes whose case cannot matter (`buy milk`, `call bob`), and step
3 asks the user about E-001.

## Red Flags - STOP

Quoted from runs without this skill:

- "Then I'll set the adoption map row and FR-001/FR-002 to confirmed and add a changelog
  entry." Any confirmation of a requirement the user never answered for (FR-001 was never asked
  about).
- "Then I'll mark the area confirmed in the adoption map and changelog with you as the
  confirmer". One answer about a bug taken as confirmation of the whole area.
- "It describes what the code does today, not what it should do." An as-built record offered as
  the PRD.
- "**Matching is case-sensitive.** `search_notes("milk")` does not match a note `"Buy Milk"`."
  A behaviour the code itself calls an apparent bug, written as a requirement.
- "I wrote it down as current behavior, not as a fix." The bug in the requirement text with an
  open question beside it.
- "Everything in the PRD comes from reading the source, which is short enough to read with
  confidence." Reading the code as a substitute for the user's word, or for tests.
- "I wrote the PRD for the whole repo at `docs/prd/notes/PRD.md`." Every area at once, in one
  file, outside the template.
- "If you still want to skip writing tests, option 1 can still fix the code and update the docs,
  but the PRD will then say FR-002 is live with no test proving it." Any offer to adopt or
  approve without a suite.
- "If you still want no new tests, I'll check the fix by hand like I did above." A hand-run check
  in place of the suite.
- "Change line 15 to `term.lower() in t.lower()`" or "I fix `search_notes` to be
  case-insensitive". Any code change during adoption.
- A `Source:` line without `@<commit>`, or one you did not open.
- The extract prompt sent to `prd-tester`, or a suite run by anything but `prd-tester`.

**All of these mean: stop, put the area back to the state its last passed gate allows, and ask
the user.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The code clearly intends this." | The code shows what it does. A comment, a name or a habit is evidence, not intent; the user's word is intent. |
| "The user told me to mark it confirmed." | Confirmation is per requirement, and the user has not seen them yet. Show each one; a blanket yes confirms nothing. |
| "Writing down what it does is neutral." | A requirement is a promise. Writing the bug as one tells every builder and tester to keep it. |
| "I flagged it as an open question next to the requirement." | The requirement still says it. The bug goes to `errors.md`, the requirement covers only what is not in question. |
| "The code is the proof." | Code proves what it does, not what the PRD says. Only a suite written from the PRD alone shows that the two agree. |
| "The tests already pass." | Tests written by reading the code encode the code. The characterization suite is written from the PRD by a tester who never saw it. |
| "I ran the inputs by hand and checked." | A hand run is not repeatable and cites no T-id. `adopted` needs the suite. |
| "One pass over the whole repo is faster." | Each area needs the user's word on every requirement and its own suite. Several areas at once means confirmations nobody gave. |
| "The fix is one line; I'll make it while I'm here." | Adoption records the system as it runs. A fix during adoption makes the suite test your change, and the change skipped the PRD. |

## Related skills

- **prd-toolkit:authoring-prds** fills the project-wide sections (phases 1 and 2) and approves the
  first area (phases 3 to 7, `1.0.0`; step 5.4 says which parts of phase 7 apply).
- **prd-toolkit:changing-prds** approves every later area (a minor bump), and takes every later
  fix of an `E-nnn` the adoption recorded.
- **prd-toolkit:testing-from-prds** is what `prd-tester` follows; its `dispatching.md` is step 4's
  suite dispatch and step 5's dry run.
