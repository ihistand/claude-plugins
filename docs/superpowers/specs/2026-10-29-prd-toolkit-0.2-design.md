# prd-toolkit 0.2: adoption, the tester and trace — design

> **Date:** 2026-10-29
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec). Section numbers below refer to
> that spec. Where this addendum and the base spec disagree, this addendum wins for 0.2.
> **Lessons from 0.1:** `../plans/2026-10-29-prd-toolkit-0.1-acceptance.md`

## 1. Scope

0.2 delivers milestone 0.2 of base spec section 9:
- `adopting-prds` and `/prd-adopt`;
- `testing-from-prds`;
- `prd_trace.py`;
- the `prd-tester` agent, which replaces 0.1's general-purpose dry-run subagent.

It also carries the 0.1 acceptance note's remaining polish items. It is **proven by** adopting
one dashboard area of a production Looker project, with its characterization tests passing
against the live instance.

### Decisions

| Decision | Choice |
|---|---|
| How characterization tests reach Looker | **Both:** pytest with the Looker SDK for the tiles and explores users see, and LookML `test:` blocks for model-level invariants. Everything is read-only, and runs as the automation user in its dev workspace. |
| The Looker area's boundary | One dashboard file, the explores its tiles query, and the views and fields those tiles use. Other fields of those views stay outside the area. |
| Stable expectations against live data | Exact values for closed windows older than a cutoff (45 days), each pinned to a fixed date range. A backfill that changes one fails the test, and the error loop classifies it. |
| Who confirms intent | Ivan confirms what he knows and signs off acceptance. Intent only a business owner can confirm stays an `[ASSUMPTION A-nn]` that names who would confirm it. |
| Plan shape | One plan (approach A). The toolkit is built generically and proven on a synthetic legacy repo, the Looker contract type comes early, and the interactive Looker adoption is the last task. |

### Open items of base spec section 11, resolved

- **Tester read restriction.** Plugin-shipped agents cannot carry `hooks`. A plugin's global
  `hooks/hooks.json` PreToolUse hook does receive `agent_type` when it fires inside a subagent,
  so a global hook that acts only for the tester enforces the restriction (section 3 below).
- **Non-interactive evals.** The 0.1 suite ran with `--scaffold` and prompts that say "Do not ask
  me questions". It needed no AskUserQuestion turns, so 0.2 keeps that pattern.
- **Looker test reach.** API queries plus `test:` blocks, as above.

## 2. Packaging additions

| Piece | Purpose |
|---|---|
| `skills/adopting-prds/SKILL.md`, `commands/prd-adopt.md` | Reverse-engineer one area of an existing repo (section 4) |
| `skills/testing-from-prds/SKILL.md` | Write tests from the PRD alone, in dry-run or suite mode (section 3) |
| `agents/prd-tester.md` | The black-box tester. Tools: Read, Glob, Grep, Write, Edit, Bash. Loads `testing-from-prds`. |
| `hooks/hooks.json`, `scripts/prd_tester_guard.py` | Enforce the tester's restrictions (section 3) |
| `scripts/prd_trace.py` | Trace rules (section 5) |
| `tests/fixtures/legacy/` and a `make_legacy_repo()` test helper | A small Python service with git history and no PRD. The `.git` is built in a temp dir at test time and never committed. |
| Eval cases | Adoption triggers, the tester refusing to read source, the version bump on a later adoption |

The plugin version becomes 0.2.0 in `plugin.json` and `marketplace.json`.

## 3. Testing and the tester

**`testing-from-prds`** has two modes that share one report format: QUESTIONS, TESTS,
HARNESS CHOICES and FILES READ. The quote rule and the HARNESS CHOICES rule from 0.1 apply
unchanged.

- **Dry run.** This is called by authoring phase 6 and changing step 4. It writes tests for the
  sampled T-ids into a fresh scratch subdirectory. Both skills dispatch `prd-tester`, and fall
  back to the 0.1 general-purpose prompt only when the agent is not installed.
- **Suite.** This is called by adoption step 4, and by building in 0.4. It writes the area's
  tests into the repo's test roots, runs them with the Levels harness commands, and adds a
  RESULTS section giving `pass`, `fail` or `known-failing E-nnn` per T-id. The tester never
  edits code or the PRD. Every failure is returned as a change request or an `E-nnn`
  candidate.

**`prd_tester_guard.py`** is a global PreToolUse hook. It acts only when the hook input's
`agent_type` is `prd-tester` or `prd-toolkit:prd-tester`; for every other session it exits 0.

- **Allowed roots:**
  - the PRD folder (`docs/prd/*/`);
  - the hook input's `scratchpad_dir`;
  - the test roots.

  The test roots come from a required `Test roots:` line in the Harness Layout slot of
  `testing.md`, which lists backticked directories, for example
  ``Test roots: `tests/`, `z_tests/` ``.
- **File tools.** Read, Glob, Grep, Write, Edit and NotebookEdit are allowed only under the
  allowed roots. Any other path exits 2 with a message naming the allowed roots.
- **Bash.** A command is allowed when it starts with one of the Levels table's harness commands,
  or is `ls`, `mkdir` or `uv run python -m py_compile` with every path argument inside the
  allowed roots. Anything else exits 2.
- **Failure.** A missing or unparsable `testing.md` blocks every tool except reads inside the PRD
  folder, so the tester can report the gap. The guard never fails open.

**The Looker harness** is part of the looker repo's own Harness section, answered during the
adoption, not built into the toolkit. The expected shape:
- pytest with the Looker SDK as a dedicated automation user, never through a person's own
  credentials;
- `test:` blocks under `z_tests/`, run with `run_lookml_tests` in the automation dev workspace;
- fixed closed windows older than 45 days for exact values.

## 4. Adoption (`adopting-prds`, `/prd-adopt <area>`)

The flow runs per area:

0. **Bootstrap** (first adoption only).
   - Copy the template.
   - Fill the project-wide sections from the repo: the stack, the glossary, standards rows from
     detected linters, skills rows from installed plugins.
   - Anything only the user knows stays a marker.
   - The adoption map lists candidate areas as `not started`.
1. **Bound.** The user picks an area. Its boundary is recorded as file globs in the adoption map's
   new **Boundary** column. An area is one feature file, `features/<area>.md`.
2. **Extract.**
   - Subagents read the code, the git history, the docs and, read-only, the live system.
   - Each observed behaviour becomes a requirement block with status `as-built` and a
     `Source: <file>:<line> @<commit>` line.
   - Contracts and test cases are extracted with the requirements.
   - An apparent bug is never written as a requirement. It becomes an `E-nnn` entry in
     `errors.md`.
   - The area becomes `extracted`.
3. **Confirm.** Each `as-built` requirement is shown with its source.
   - **Confirmed:** it becomes `live (since <version>)`, because it already runs in production.
   - **Corrected:** it becomes `approved` with the corrected text.
   - **Unknown intent:** it becomes an `[ASSUMPTION A-nn]` naming who would confirm it.

   The area becomes `confirmed`.
4. **Characterize.**
   - `prd-tester` writes and runs the area's suite from the PRD alone.
   - Each failure is triaged with the user. Either the PRD is wrong, and it is fixed through
     `changing-prds`, or it is a real bug. A real bug gets an `E-nnn`, its requirement drops to
     `approved`, and its test case gains `known-failing: E-nnn`.
5. **Gate and approve.**
   - Authoring phases 5 to 7 run for the area: lint, the checklist, a `prd-tester` dry run and
     the user's approval.
   - The area becomes `adopted` when every test passes, or fails only with an open `E-nnn` cited
     on its case.
   - The first adopted area sets 1.0.0. A later area is a minor bump through `changing-prds`.

## 5. `prd_trace.py`

It uses the same output format and exit codes as `prd_lint.py`. Usage:
`prd_trace.py PRD_DIR [--range BASE..HEAD]`.

- **Scope.** Trace covers the areas whose adoption-map state is `adopted`. A new project (an
  adoption map reading `Not applicable: new project`) counts as all areas adopted.
- **Citations.** `@prd T-x.y` anywhere in a file under the test roots.

| Rule | Fails when |
|---|---|
| `t-implemented` | a T-id of an adopted area is cited by no test (this includes `known-failing` cases) |
| `test-cites-live` | a citation names a T-id that does not exist, or belongs to a `removed` requirement |
| `commit-refs` | a commit in `--range` touches a file inside an adopted Boundary and has no `Refs:` trailer (`Refs: none (no behaviour change)` counts) |
| `status-current` | a requirement is `verified` or `live` while one of its T-ids has no citing test |

## 6. Format additions

All are documented in `references/prd-format.md`. The lint rule count stays at 27.

| Addition | Checked by |
|---|---|
| Adoption map header `\| Area \| State \| Boundary \|` | `sections` (the header), `index-consistent` (an area past `not started` has its `features/<area>.md`) |
| `known-failing: E-nnn` on a test case | `test-refs`: the entry exists in `errors.md` and is not resolved |
| `Test roots:` line in the Harness Layout slot | `sections` |
| A custom contract type whose file is a YAML mapping of item names makes `<type>:<name>` targets resolvable | `test-refs` |
| `Source: <file>:<line> @<commit>` on an `as-built` block | `index-consistent`: an `as-built` block has a Source line |

## 7. Polish carried from 0.1

- The `sections` rule checks that the template's Harness slots are present, with the slot names
  in order.
- A custom-type glob that matches no file is a `contracts-valid` finding, where 0.1 skipped it.
- `index-consistent` flags a duplicate index row.
- The `lint-ran` eval grader requires lint's exit 0, not only a mention of lint.
- The eval baseline is re-recorded at `--runs 3` before the 0.2.0 bump.

## 8. Testing the toolkit

- **pytest:**
  - one failing case per trace rule;
  - guard tests that feed hook JSON on stdin, covering a non-tester pass-through, a blocked
    outside path, an allowed root, the Bash allowlist, and a missing `testing.md`;
  - custom-type resolution, proven on a LookML-shaped fixture;
  - every format addition can fail.
- **Baselines** for `adopting-prds` and `testing-from-prds`, before either is written
  (`superpowers:writing-skills`). Starting scenarios:
  - "the code clearly intends this, mark it confirmed";
  - "it looks like a bug, but just write what it does";
  - "just peek at the handler to see what it returns";
  - "the test failed, so adjust the expected value".
- **Evals:**
  - adoption triggers on "bring this repo under a PRD";
  - the tester does not read source;
  - a second adoption bumps the minor version.

## 9. Proof: the Looker adoption

The last task runs interactively with Ivan in the looker repo, on a feature branch:
- bootstrap;
- the chosen dashboard area through steps 1 to 5;
- characterization tests passing, or known-failing with an open `E-nnn`.

Its PRD folder, tests and `z_tests/` blocks land through a merge request. Claude pushes and opens
the merge request. It never deploys Looker unless Ivan asks in his own words, and running
`run_lookml_tests` in the automation dev workspace needs no deploy. Findings fix the toolkit or
are recorded as 0.3 items, as in 0.1.

## 10. Out of scope for 0.2

`building-from-prds`, `deploying-from-prds`, git hooks, CI templates, `prd_drift.py`,
`/prd-status`, the EDD skill, and adopting any Looker area beyond the first.
