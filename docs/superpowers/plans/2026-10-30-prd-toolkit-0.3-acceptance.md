# prd-toolkit 0.3 acceptance run

> **Date:** 2026-10-30
> **Plan:** `2026-10-30-prd-toolkit-0.3.md`, Task 8
> **Result:** pass on a small PRD, with 2 pack gaps and 2 other findings listed below. The run used
> a 0.2-format PRD (one area, two requirements, one open bug) in a scratch repo, outside this
> repo and never pushed. 0.3 refused it, the hand migration cleared the refusals, the packs met
> the size rule, and a headless `changing-prds` session fixed the open bug. No toolkit code or
> text was changed during the run.
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
| 1 | Read of `features/notes.md` head | The format of a features file when the change touches only the test case and the error entry | controller to decide |
| 2 | `grep E-001\|known` across the area's PRD files | A list of every place `E-001` and `known-failing` appear, so a fix can edit them without searching | controller to decide |

Other findings, neither a read gap:

| # | Finding | Disposition |
|---|---|---|
| 3 | The skill's pack call in the session ended `\| head -40; echo "prd-context-exit=$?"`, which reports `head`'s status. A STALE pack (exit 1) would show as 0 | controller to decide |
| 4 | The code fix changed a cited line, and the skill did not re-point `FR-002`'s `Source:` to the new sha, so the PRD is stale after a clean change | controller to decide |

Harness deviations, so the run can be repeated:

- The brief's `git archive` command omits `prd-toolkit/tests/fixtures/legacy`, which the scaffold
  copies from; the export needs that path too.
- Placing the prompt after the variadic `--allowedTools` makes `claude -p` read no prompt and exit 1
  ("Input must be provided"); the prompt went first on the command line.

## Later

1. **Pack sizes on a large real area.** The ratios above come from a PRD of two requirements. The
   decide and implement packs must be measured on a large real area at the first real adoption,
   against the same rule (single-FR `decide` pack under 20,000 bytes and smaller than the PRD's
   files).
2. **Dispositions for gaps 1 to 4**, once the controller has chosen: a test on this branch, or a
   later release.
