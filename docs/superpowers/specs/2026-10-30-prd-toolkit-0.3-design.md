# prd-toolkit 0.3: tasks and context packs — design

> **Date:** 2026-10-30
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and
> `2026-10-29-prd-toolkit-0.2-design.md`. Where this addendum and either of them disagree, this
> addendum wins for 0.3.

## 1. Scope

A PRD exists so that an agent reads less code and less prose to do a task correctly. 0.2 gives
the agent the whole PRD folder and leaves the reading to it. 0.3 makes each task carry **a
focused subset**: the requirements the task touches and the things they cite, and, when the task
writes code, the code lines they were read from. Nothing else.

0.3 delivers:
- the **Tasks** paragraph in `prd-format.md`, saying where a sub-project and a change live;
- `prd_context.py` and the `/prd-context` command, which print a task's context pack;
- the adoption map moved out of `prd.md` into `adoption.md`;
- `Touches:` as an optional, linted field of `errors.md` entries;
- skill and managed-block wording that routes every task through the pack.

It is **proven by** migrating the Looker PRD adopted in 0.2 and making one real change to it
through the pack (section 8).

### Decisions

| Decision | Choice |
|---|---|
| Where a sub-project's PRD lives | Inside the repo's one PRD, as an area. No nested or per-feature PRDs |
| Where a change lives | As a delta to the living PRD, through changing-prds. No per-change PRD |
| How a task gets its context | A deterministic script prints it; skills tell the agent to work from it |
| Adoption map | Moves to `adoption.md`; §8 keeps its heading and a one-line body |
| Per-change and per-ticket records | Not in core. A downstream wrapper plugin builds them on `/prd-context` |
| Token budget | Reported, never enforced; the pack is never truncated |
| Milestone numbering | This is 0.3. Base spec section 9's 0.3 (building, deploying, hooks, CI, drift) becomes 0.4, and its 0.4 (error handling) becomes 0.5. The 0.2 spec's "building in 0.3" now reads 0.4 |
| Release vehicle | Branch `feat/prd-toolkit-0.3`, cut from `feat/prd-toolkit-0.2` and rebased onto `main` once the 0.2 PR merges |

Renumbering is deliberate: building-from-prds and `prd-builder` should take an `implement` pack
as their input, so packs come first.

## 2. Tasks

`prd-format.md` gains a section `## Tasks`, after `## Folder`:

> A repo has one PRD, `docs/prd/<project>/`. A sub-project of the repo (a dashboard, a service,
> a feature family) is an **area** of that PRD, never a PRD of its own. A task is one unit of
> work against the PRD:
>
> | Task | Edits in the PRD | Context pack |
> |---|---|---|
> | New sub-project | a new area: `features/<area>.md`, `test-cases/<area>.yaml`, a row in `adoption.md` when the project is adopted | `/prd-context` without an area |
> | Addition | new FR or UJ blocks in an existing area | `decide`, then `implement` |
> | Update | changed blocks and a version bump | `decide`, then `implement` |
> | Bug fix | the `E-nnn` entry resolved; its `known-failing` case passes | `decide`, then `implement`, for the IDs the entry touches |
>
> Every task adds a §14 row. The PRD always describes the system as it is now; git history and
> §14 record how it got there.

## 3. `prd_context.py`

```
prd_context.py <prd-folder> [--area <slug>] [--req <ID>[,<ID>…]] [--for decide|implement]
               [--context N] [--json]
```

`--for` defaults to `decide`; `--context` defaults to 20. The script follows `prd_lint.py`'s
conventions: a `uv run --script` header, the shared `prdlint` model and parsers, and a gate line
`; echo "prd-context-exit=$?"`.

**Exit codes.**

| Exit | Meaning |
|---|---|
| 0 | Pack printed; every cited source is current (always 0 for `decide`) |
| 1 | Pack printed; at least one `Source:` is stale (`implement` only) |
| 2 | Usage or tool error: unknown area or ID, unparseable PRD, `--req` or `implement` without `--area`, `implement` outside a git work tree. Nothing on stdout; the reason on stderr |

**Selection.**
- With `--area` and no `--req`: every UJ and FR block in `features/<area>.md`.
- With `--req`: only those blocks (UJ, FR or NFR IDs), plus every UJ their `Traces:` lines
  name. An ID outside the area is allowed and is labelled `(area: <other>)`. A removed block is
  included with its removed marker, never silently dropped.
- Without `--area`: the **repo pack**: the header, §1, §4, and one line per area (slug, state,
  Boundary) from `adoption.md`, or the list of `features/*.md` slugs for a project with no
  adoption map. `--req` is not allowed here.

**A `decide` pack holds, in this order, each part under a `## <part>` heading:**
1. **Header**: PRD path, version, mode, area, its state and Boundary, and the size line.
2. **Stack**: `prd.md` §1 Metadata & stack and §4 Architecture, whole.
3. **Glossary**: the §3 rows whose Term occurs (case-insensitive, whole word) in a selected
   block.
4. **Requirements**: the selected blocks, verbatim, in file order.
5. **Cited**: NFR blocks a selected block names by ID; each `Errors:` code with its
   `contracts/errors.yaml` entry; each `<type>:<name>` item with its contract entry, resolved
   exactly as lint's `contracts-valid` resolves it; each `[ASSUMPTION A-nn …]` marker in a
   selected block with its §12 row.
6. **Known defects**: the open `errors.md` entries whose `Touches:` names a selected ID, whole.
   A closing line counts the open entries with no `Touches:`: `2 open errors.md entries name no
   requirement`.
7. **Open questions**: the §13 items that contain a selected ID, one of their AC IDs, or the
   area slug as a whole word. A closing line counts the rest: `14 other open questions in
   prd.md §13`.
8. **History**: the last three §14 rows that contain the area slug.

**An `implement` pack adds two parts after Requirements:**
- **Code**: for each `<path>:<line> @<sha>` in a selected block's `Source:` field (continuation
  lines included), lines `line − N` to `line + N` of the working-tree file, clamped to the file,
  each prefixed with its line number. Paths are relative to the git top level. A source is
  **stale** when `git log --format=%H <sha>..HEAD -- <path>` prints anything, when `<sha>` is
  not a commit, or when the file is missing; its excerpt is headed `STALE: <reason>; the cited
  line may have moved`, or replaced by that line when the file is missing.
- **Levels**: `testing.md`'s Levels table.

A stale source is a flag, not an error: the agent re-reads that region, and the task's
changing-prds edit refreshes the `Source:`.

**Size line.** `pack 18,402 bytes (~4.6k tokens, bytes / 4); prd.md 34,725; features/<area>.md
48,805`. The last field is omitted in the repo pack.

**`--json`.** A list of `{"part", "id", "file", "line", "text", "stale"}` objects, one per item
in the text pack, in the same order; `id` and `line` are `null` where they do not apply. It is
for wrapper plugins and tests.

**Determinism.** The same PRD, tree and arguments give byte-identical output.

**Known limit.** §13 is free text. A question that names no ID and no area slug is counted, not
included. A later release may require each question to cite an ID, an area or `all`; 0.3 adds
no rule.

## 4. `errors.md` `Touches:`

The entry grammar gains an optional line, after `Classification:`:

```
Touches: FR-012, NFR-03
```

It lists the requirement IDs the error concerns, comma-separated. `index-consistent` reports a
`Touches:` ID that no block defines. The pack's Known defects part reads it (section 3). The
adopting extract prompt writes it for each `E-nnn`, which makes the 0.2 extractor's habit
official.

## 5. `adoption.md`

`adoption.md` sits at the PRD folder root and holds only the `| Area | State | Boundary |` table
that §8 held in 0.2, with the same header, states and Boundary rules. It is optional in the
folder table: present for an adopted project, absent for a new one.

§8 keeps its heading, so section order is unchanged. Its body is exactly one line:
- `See adoption.md.` when `adoption.md` exists;
- `Not applicable: new project` when it does not.

**Lint.**
- `sections` checks the §8 body against the file's presence. A table still in §8 is reported
  as `section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there
  and leave "See adoption.md."`. The header and state checks move to `adoption.md`.
- `index-consistent` is unchanged: an area past `not started` must have `features/<area>.md`.
- `model.py`'s `_adoption()` reads `adoption.md`. `trace.py`, `prd_block.py` and
  `prd_context.py` read the adoption rows through the model and need no change of their own.

**Migration.** By hand, guided by the lint message; no script. A toolkit format migration is a
**patch** bump with a §14 row such as `format: adoption map moved to adoption.md (prd-toolkit
0.3)`. `prd-format.md` §9 gains that sentence.

**Skills and template.** adopting-prds steps 0 and 5 and the extract prompt name "the area's
row in `adoption.md`" for §8. Step 0's bootstrap creates `adoption.md` and writes `See
adoption.md.` into §8. `templates/prd/prd.md`'s §8 marker lists the two allowed bodies; the
template ships no `adoption.md`. The eval scaffold and graders that read §8 follow.

## 6. Routing tasks through the pack

**`/prd-context <area> [IDs] [implement]`**, a new command, runs `prd_context.py` on the repo's
PRD with those arguments and prints the pack and its exit line. With no arguments it prints the
repo pack. It exists because the managed CLAUDE.md block cannot name the script's path;
`${CLAUDE_PLUGIN_ROOT}` resolves only inside the plugin.

**changing-prds.**
- Step 1 (Restate) runs `/prd-context <area> <IDs>` for the IDs the change touches, or with no
  area for a new sub-project, or with the `Touches:` IDs for a bug fix. A new non-negotiable
  rule: **read whole PRD files only to edit them**. Work from the pack; open another PRD file
  only for what the pack's closing lines say it left out.
- Step 5's hand-off, after approval: "write the code from `/prd-context <area> <changed IDs>
  implement`".

**adopting-prds step 3.** Each AskUserQuestion preview and each checklist item is the
`implement` pack for that one requirement (`--req FR-nnn`): the block and its fresh,
staleness-checked `Source:` excerpt.

**The managed CLAUDE.md block.** Its first bullet becomes:

> To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD
> files only to edit them. Before writing code for an approved change, run `/prd-context <area>
> <IDs> implement`. Code implements the PRD; it never defines behaviour the PRD lacks.

The other lines stay. The rendered block stays under 1,536 bytes.

**Unchanged.** testing-from-prds and `prd-tester`: the dispatch already scopes the tester by
area and T-ids, the tester needs the test cases the pack leaves out, and running the script
would widen the guard's Bash allow-list. authoring-prds: a new PRD has nothing to slice.

## 7. Testing the toolkit

Every rule and pin below is written test-first and fails before its change.

**`prd_context.py`.** The `orders` fixture gains a second area, an `adoption.md`, an open
`E-nnn` with `Touches:`, a resolved one, an open one with no `Touches:`, §13 questions with and
without IDs, assumption markers, contract references, `Source:` lines and §14 rows. Tests:
- Selection: area without `--req`; `--req` with traced UJs; a cross-area ID labelled; the repo
  pack; each exit-2 case prints nothing on stdout.
- Inclusion: every cited kind of section 3 appears.
- **Focus**: the pack does not contain the other area's blocks, an uncited NFR, an entry that
  touches another ID, a resolved entry, an unrelated question, an unused glossary term, or any
  `test-cases/` text. Each focus test is first run against a deliberately over-inclusive stub
  and must fail there.
- `implement`, in a temporary git repo: the window and its clamping; a file changed after its
  `@sha` gives `STALE` and exit 1; an unknown sha and a missing file are stale; untouched files
  give exit 0.
- `--json` lists the same `(part, id)` pairs as the text pack; the size line's numbers equal the
  real byte counts; two runs are byte-identical.

**Lint and model.** A table in §8, `See adoption.md.` with no file, `Not applicable: new project`
with the file, and a bad header or state in `adoption.md` are each a violation. A dangling
`Touches:` ID is an `index-consistent` violation. Existing fixtures migrate; trace and block
tests stay green with no logic change.

**Pins.** changing-prds step 1 names `/prd-context` and "read whole PRD files only to edit
them"; step 5 names the `implement` pack; adopting step 3 builds previews from it; the block's
new bullet; the rendered block under 1,536 bytes with 20 areas and a realistic skills list; the
`## Tasks` table in `prd-format.md`.

**Evals.** A new eval `change-uses-context-pack`: a scaffolded PRD with two areas and a change
request for area A. Graders: the transcript runs `/prd-context` or `prd_context.py` before its
first PRD edit, and never reads `features/<B>.md` or a `test-cases/` file. The adopting and
authoring baselines and the `notes_repo` scaffold follow the §8 move. Evals run before release
and are recorded in `BASELINE.md`.

**Verify.** `uv run --directory prd-toolkit pytest -q`, `cd web && npm test`, and `claude plugin
validate ./prd-toolkit`.

## 8. Proof: the Looker PRD

On the PRD adopted in 0.2, after its first area is approved:
1. Migrate §8 to `adoption.md` (a patch bump). Record `prd.md`'s size before and after; §8 was
   18,433 of 34,725 bytes.
2. Record the sizes of three packs for the adopted area: `decide` for the whole area, `decide`
   for one FR, and `implement` for one FR. Compare them with `prd.md` plus the area's features
   file. **Pass: the single-FR `decide` pack is under 20,000 bytes.**
3. Make one real, small change through changing-prds with the pack. **Pass: the session reads
   no PRD file beyond the pack and the files it edits.** Each extra read it needed is a **pack
   gap**, either fixed with a test or listed as a later item.

The acceptance note, `docs/superpowers/plans/2026-10-30-prd-toolkit-0.3-acceptance.md`, records
the numbers and the gaps. It names no hosts, users, platform objects or people.

## 9. Out of scope for 0.3

- Per-change or per-ticket records, and any commit-annotation link: a wrapper plugin's job.
- Parallel-team collisions on `prd.md`'s version and §14.
- Packs for `prd-tester`.
- A token budget that truncates or refuses a pack.
- A lint rule tying §13 questions to IDs or areas.
- Platform-specific `implement` content (related files beyond `Source:`): a wrapper plugin's job.
