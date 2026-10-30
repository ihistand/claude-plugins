# prd-toolkit 0.3 acceptance run

> **Date:** 2026-10-30
> **Plan:** `2026-10-30-prd-toolkit-0.3.md`, Task 8
> **Result:** the refusals, the migration, the pack sizes and the stale checks pass. The bug fix
> landed in run 1. The focus rule passed except for one recurring read of a features file, recorded
> as a known limitation (see "Dispositions of the re-run"). The run used a 0.2-format PRD (one area,
> two requirements, one open bug) in a scratch repo, outside this repo and never pushed. 0.3
> refused it, the hand migration cleared the refusals, the packs met the size rule, and a headless
> `changing-prds` session fixed the open bug. No toolkit code or text was changed during the run.
> The gaps were then fixed (see "Gaps found and fixed") and step 5 was run again on a fresh build.
>
> **Scope.** This is a small-PRD proof. Pack sizes on a large real area are not measured here.

## What ran

The 0.2 eval scaffold, exported from `main` and built into a repo whose PRD is Approved at 1.0.0:
one adopted area `notes`, characterization tests, a known-failing `T-002.1` on the open bug
`E-001`, and `Source:` lines at real shas. The adoption map was a table in section 8.

| Step | Outcome |
|---|---|
| 1 Build | PRD at 1.0.0, Approved. Section 8 holds the table; `adoption.md` is absent |
| 2 Refusals | Lint exit 1, and `prd_trace.py`, `prd_block.py --check` and `prd_context.py --area notes` each exit 2 with nothing on stdout. All four print `section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there and leave "See adoption.md."` |
| 3 Migrate | Table moved to `adoption.md`; section 8 is `See adoption.md.`; 1.0.1; one section 14 row. Lint exit 0, trace exit 0, block refresh and `--check` exit 0. `prd.md` 3,284 bytes before, 3,238 after |
| 4 Measure, stale-check | Packs below. Pass rule met. STALE detection works in both states |
| 5 One real change | `changing-prds` loaded from `--plugin-dir`; E-001 fixed; PRD 1.0.2, Approved; `T-002.1` passes. 2 pack gaps |

## Numbers (step 4)

Baseline: `prd.md` 3,238 plus `features/notes.md` 620 = 3,858 bytes.

| Pack | Pack bytes (header line) | Ratio to baseline |
|---|---|---|
| Repo pack | 1,039 | 0.27 |
| `--area notes --for decide` | 2,254 | 0.58 |
| `--area notes --for decide --req FR-001` | 1,914 | 0.50 |
| `--area notes --for implement --req FR-001` | 2,573 | 0.67 |

The single-FR `decide` pack is under 20,000 bytes and smaller than `prd.md` plus the features file
(ratio 0.50): pass. The implement pack exits 0 with current sources.

Stale check on the cited line `src/notes/app.py:6 @47ad27a`:

| State | Exit | Line printed |
|---|---|---|
| Edit uncommitted | 1 | `STALE: uncommitted changes; the cited line may have moved` |
| Edit committed | 1 | `STALE: changed since 47ad27a; the cited line may have moved` |
| Both reverted | 0 | none |

## The headless change (step 5)

Command: `claude -p` with `--plugin-dir` set to this branch's plugin, `--model sonnet`, no
permission-bypass flag, and a prompt of `/prd-change fix E-001: <intended behaviour>`, with the
approval carried in the prompt. The run took about 100 seconds and 9 turns (a first turn ended while
the tester ran in the background, and a second turn finished the work).

Checks:

| Check | Result |
|---|---|
| Plugin loaded from `--plugin-dir` | Yes: first call is Skill `prd-toolkit:changing-prds` |
| Pack ran before the first PRD edit | Yes: `prd_context.py docs/prd/notes --area notes` was call 2, with `prd-context-exit=0`; the first edit was call 5 |
| `prd-tester` dispatched | Yes, once, for a dry run of `T-002.1` (one blocked write outside its roots on a wrong base path, corrected; the tester reported no open questions) |
| Final PRD | 1.0.2, Approved; lint exit 0 |
| Code fix | Landed (`casefold()` on both sides); the suite passes, 2 of 2, `T-002.1` included |
| STALE `Source:` touched | None was stale when read. After the code commit, `FR-002`'s `Source: src/notes/app.py:13 @47ad27a` is stale and was not re-pointed |

`prd_context.py` runs:

| Call | Arguments | `prd-context-exit=` |
|---|---|---|
| 2 | `docs/prd/notes --area notes` (decide) | 0 |
| 26 | `docs/prd/notes --area notes --req FR-002 --for implement`, piped to `head -40` | 0 (the value is `head`'s status, not the script's; see Later) |

Edits to PRD files: one Python heredoc in call 5 changed `errors.md` (added `Touches: FR-002`,
Resolution set), `test-cases/notes.yaml` (removed `known-failing`) and `prd.md` (1.0.2, a section 14
row, status In review). Call 24 set the dry-run text and Approved on `prd.md`. Call 24's
`prd_block.py` refreshed `CLAUDE.md`. Commits: PRD, then code.

### Reads of PRD files by the session

| Call | Tool and path | Classification |
|---|---|---|
| 2 | Bash, `prd_context.py` (the pack) | pack |
| 3 | Bash, `ls -R`, `cat errors.md test-cases/notes.yaml`, `head -20 prd.md`, `grep` of section 14 in `docs/prd/notes` | allowed: files the change edited and the section 14 check |
| 4 | Bash, `cat docs/prd/notes/features/notes.md \| head -5` | **pack gap 1**: not edited, not a closing pointer |
| 4 | Bash, `grep -n "E-001\|known" docs/prd/notes/*.md` | **pack gap 2**: reaches `nfr.md`, `operations.md`, `testing.md` and `adoption.md`, none edited |
| 22, 24 | Bash, `grep` of `^version\|^status` in `prd.md`; lint | allowed: edited file |
| 26 | Bash, the implement pack | pack |
| 27 | Bash, `cat tests/test_notes.py` | not a PRD file |

The tester subagent's own reads (Glob, then Read of `test-cases/notes.yaml`, `testing.md`,
`features/notes.md`, `contracts/errors.yaml`, `errors.md`) are its job and are not counted against
the pack rule; they are listed so a reader can see them. Both gaps came from the session's first
orientation, when it looked for the known-failing marker and the E-001 mentions beyond the pack.

## Gaps

| # | Gap | What the pack lacked | Disposition |
|---|---|---|---|
| 1 | Read of `features/notes.md` head | The format of a features file when the change touches only the test case and the error entry | G1; the re-run still read the file (see Re-run of step 5) |
| 2 | `grep E-001\|known` across the area's PRD files | A list of every place `E-001` and `known-failing` appear, so a fix can edit them without searching | fixed: G1 |

Other findings, neither a read gap:

| # | Finding | Disposition |
|---|---|---|
| 3 | The skill's pack call in the session ended `\| head -40; echo "prd-context-exit=$?"`, which reports `head`'s status. A STALE pack (exit 1) would show as 0 | fixed: G2 |
| 4 | The code fix changed a cited line, and the skill did not re-point `FR-002`'s `Source:` to the new sha, so the PRD is stale after a clean change | fixed: G3 |

Harness deviations, so the run can be repeated:

- The brief's `git archive` command omits `prd-toolkit/tests/fixtures/legacy`, which the scaffold
  copies from; the export needs that path too.
- Placing the prompt after the variadic `--allowedTools` makes `claude -p` read no prompt and exit 1
  ("Input must be provided"); the prompt went first on the command line.

## Gaps found and fixed

Gaps 1 and 2 had one cause: `E-001` (0.2 format) has no `Touches:` line, so the decide pack only
counted it, and the session searched the PRD for it. Findings 3 and 4 became G2 and G3.

| # | Gap | Fix | Commit |
|---|---|---|---|
| G1 | A bug fix could not reach its entry through the pack (gaps 1 and 2) | `prd_context.py --req` takes an `E-nnn`: the whole entry goes into Known defects, and Requirements gets every block its `Touches:` line names plus the parent block of each case `known-failing` on it (the owner of its `ac:`, else the T-id's number). An unknown `E-nnn` is exit 2. changing-prds step 1, `/prd-context` and spec section 3 say so | `a6afefb` (code), `dc81809` (text) |
| G2 | The pack was piped through `head`, which hid its exit (finding 3) | changing-prds step 1, `/prd-context` and adopting step 3: never pipe, filter or truncate the pack's output | `dc81809` |
| G3 | No `Source:` refresh after the code commit (finding 4) | changing-prds step 5: after the code commit, run the implement pack again, rewrite each STALE `Source:` of a changed block at the new sha and commit the PRD, with no version bump and no section 14 row. The managed block carries a short clause (rendered worst case 1,481 of 1,536 bytes) | `dc81809` |

Each fix is pinned in `tests/test_context.py` or `tests/test_context_routing.py`. The suite is
552 tests; `change-uses-context-pack`, `changing-major-bump` and `changing-new-id-not-reused` stay
at 1.00 with the plugin (3 runs each).

## Re-run of step 5

A fresh build (steps 1 to 3 with the corrected commands below) gave the same outputs: lint exit 1
and three exit-2 refusals with the migration message, then after migration lint, trace and block
exit 0, and `prd.md` 3,284 to 3,238 bytes. The headless command, flags and prompt were the same.
The run took 75 seconds and 18 turns, exit 0.

The `--req E-001` decide pack is 2,379 bytes (ratio 0.62 to `prd.md` plus `features/notes.md`). It
holds `FR-002` (reached through `T-002.1`'s `known-failing`) and the whole `E-001` entry, and
counts 0 entries with no requirement.

`prd_context.py` runs:

| Call | Arguments | `prd-context-exit=` |
|---|---|---|
| 2 | `docs/prd/notes --area notes --req E-001` (decide), unfiltered | 0 |

Reads of PRD files by the session:

| Call | Tool and path | Classification |
|---|---|---|
| 2 | Bash, `prd_context.py` (the pack) | pack |
| 3 | Bash, `ls -R`; `cat` of `errors.md`, `test-cases/notes.yaml` and `prd.md` | allowed: files the change edited (all three edited in call 5) |
| 4 | Bash, `cat docs/prd/notes/features/notes.md` | **read outside the pack**: not edited, not a closing pointer; the pack already held the whole `FR-002` block |
| 21 | Bash, `grep` of `root\|conftest\|tests/` in `testing.md` | **read outside the pack**: quotes to dismiss two dry-run questions, which the dismissal rule requires |

The tester's own reads (Glob, then Read of `test-cases/notes.yaml`, `testing.md` and
`features/notes.md`) are its job and are not counted. Call 4 also grepped the format reference and
read `src/notes/app.py`, neither a PRD file.

Outcome: the PRD edits were the same as the first run's (1.0.2, `E-001` resolved, `known-failing`
removed, a section 14 row, status In review, lint exit 0). This time `prd-tester` raised three
questions. The session dismissed two with exact quotes from `testing.md` and could not dismiss the
third (AC-002.1 does not say what `search_notes` returns when no note matches), so the dry run
failed and the session stopped before approval, as the skill requires. Nothing was committed and
the code was not changed. Its final message planned the step 5 refresh ("then refresh FR-002's
`Source:` line").

| Check | Result |
|---|---|
| Pack ran before the first PRD edit | Yes: call 2, `--req E-001`; first edit call 5 |
| Unfiltered pack calls | Yes: the one call has no pipe; its exit is the script's |
| Reads outside the pack | 2: `features/notes.md` (call 4) and the `testing.md` quotes (call 21) |
| Sources current at the end | Yes, trivially: no code commit, and the implement pack exits 0. The G3 refresh did not run |

Verdict: G1 and G2 hold. The run is not a pass: two reads outside the pack remain, and G3 was not
exercised because the dry run stopped the change.

## Dispositions of the re-run

- **The `testing.md` read in call 21 was allowed.** It is a quote for a dry-run dismissal, which the
  dismissal rule requires. Rule 6 now carves it out: `7a91d19`.
- **The whole-file `cat` of `features/notes.md` in call 4 is a known limitation.** It happened in
  both runs. Rule 6 is enforced by text alone for the caller, and the text did not prevent it.
  See Later, item 5.
- **G3 is covered by its pin only.** The re-run stopped before the code commit, because the tester
  found a real PRD gap: AC-002.1 does not say what a search with no match returns, and the gap rule
  correctly stopped the change. See Later, item 6.

## Corrected brief commands

Step 1's export, which the plan file now carries:

```
git archive main prd-toolkit/evals/scaffolds prd-toolkit/tests/legacy.py prd-toolkit/tests/fixtures/legacy | tar -x -C <scratchpad>/proof-0.3/src
```

Step 5's headless form, prompt first:

```
claude -p "/prd-change fix E-001: search_notes must find notes containing the term regardless of letter case, so \"milk\" finds \"Buy Milk\". I approve the PRD change and the version bump you propose, and the code fix once the PRD is approved. Do not ask me questions." --plugin-dir <worktree>/prd-toolkit --model sonnet --output-format stream-json --verbose --allowedTools Read Glob Grep Write Edit Bash Agent Skill "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" > <scratchpad>/proof-0.3/fix-e001.jsonl
```

## Later

1. **Pack sizes on a large real area.** The ratios above come from a PRD of two requirements. The
   decide and implement packs must be measured on a large real area at the first real adoption,
   against the same rule (single-FR `decide` pack under 20,000 bytes and smaller than the PRD's
   files).
2. **The re-run's two reads outside the pack.** Decided: see "Dispositions of the re-run" and
   items 5 and 6.
3. **G3 in a live session.** The re-run stopped at a failed dry run, so the step 5 refresh is
   proven only by its pin. A run that reaches the code commit confirms it.
4. **The fixture's no-match gap.** AC-002.1 does not say what `search_notes` returns when no note
   matches; a tester may ask, and the change then cannot be approved.
5. **A caller-side guard hook.** Like the tester's, it blocks whole PRD-file reads outside rule 6's
   exceptions. Today rule 6 binds the caller by text alone, and the re-run read `features/notes.md`
   whole despite it.
6. **An eval that reaches the code commit.** Its scaffold has `Source:` lines, and its change goes
   through to the code commit, so the step 5 `Source:` refresh runs in a live session.
