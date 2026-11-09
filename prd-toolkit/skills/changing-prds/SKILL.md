---
name: changing-prds
description: Use when changing what a system does in a repo that has a docs/prd/ folder - a new feature, a changed rule or status code, a bug fix that alters behaviour, a removed requirement, switching an area or the PRD to another pack or output language (its Target: or Pack: line) - or when /prd-change runs, or when asked to change code and let the PRD follow, or when an agent hits something the PRD does not say, or when a reviewed PRD change waits for the owner's approval (its gate approval:<branch>, in the chat or the decision inbox, prd_gates.py) and someone asks to approve it; the PRD changes first, with new IDs and a version bump, before any code
---

# Changing PRDs

## Overview

**The PRD changes first.** `docs/prd/<slug>/` is the authority for what the system does. Code
implements it and never defines behaviour it lacks. A behaviour change is a PRD change, approved
by the user, before a line of code moves.

**Violating the letter of these rules is violating the spirit.** "Tiny", "one line", "just
reuse the number" and "the PRD can follow" change nothing below.

**Review mode.** `/prd-change --review <dir>` reviews a change and edits nothing. Read
`${CLAUDE_PLUGIN_ROOT}/skills/changing-prds/reviewing-a-change.md` whole and follow it instead of
the steps below.

Grammar (blocks, removed IDs, test cases): `${CLAUDE_PLUGIN_ROOT}/references/prd-format.md`.
Read it before editing. **Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: that is the copy its hooks and CI run. Otherwise `<scripts>` is the plugin's `scripts`
directory, written as a literal absolute path (in double quotes if it holds a space): the plugin
root is two directories above the skill's base directory (Claude Code shows it as "Base
directory for this skill" when the skill loads), and `<scripts>` is `<plugin root>/scripts`.
Glob for `.prd-toolkit/*.py` once to decide, and use the same `<scripts>` for every command.
A script that is not found is a tool error: report it, never guess another path.
When `.prd-toolkit/` exists but holds no `prd_error.py`, the vendored copy predates 0.6: stop, and
tell the user to run `prd_hooks.py install docs/prd/<slug>` from the plugin (the README's form)
and commit `.prd-toolkit/`. When `.prd-toolkit/` holds no `prd_change.py`, the vendored copy predates
0.8.1: stop, and tell the user the same.

Lint, the mechanical gate:

```bash
uv run --script <scripts>/prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"
```

The gate is the `prd-lint-exit=` value lint prints: `0` clean, `1` violations, `2` usage or internal error. Ignore the Bash call's own success; the trailing echo always succeeds. Use this form every time you run lint.

The bookkeeping, `prd_change.py`: the next free IDs, the version bump, the §14 and §11 rows and the
approval commit are the script's work, never yours. Each `prd_change.py` command below is its own
Bash call that ends `; echo "prd-change-exit=$?"`. Its own call holds that command and that echo
and nothing else: no `cd` or other command chained before it or after it, no state check or
cleanup folded in, no loop, no shell function and no variable in the path; the script path is typed out. The `prd-change-exit=` value is the gate: `0` done, `1` refused, `2` usage or internal error. On `1` the line after `refused:` names
what to fix; fix that and run the command again, never work around it. On `2` fix the command.
`record --change` takes one line with no `|`: it becomes a §14 table cell.

## The gap rule

Any agent (builder, tester, deployer, reviewer) that meets something the PRD does not say (a
missing error code, an unknown URL, an unspecified empty state) stops. It does not guess, and it
does not read the code to fill the gap. The gap is a change request: start step 1 here, with
the gap as the change.

## Packs and retargeting

An area's pack is its `Target:` line (`Target: pack <name> <X.Y.Z> (<source>)`), or §1's `Pack:`
line for an area with none, or `service` when there is neither. Before you say a pack is missing,
list the packs, its own Bash call:
`uv run --script <plugin scripts>/prd_lint.py --list-packs; echo "prd-list-packs-exit=$?"` (`<plugin scripts>` is the plugin's own `scripts` directory as a literal absolute path, even in a repository that has `.prd-toolkit/`: `--list-packs` lists what is on this machine and is not a gate, and a vendored copy lists only the packs it vendored). It prints
the built-ins and every installed plugin's packs, `<name> <version> (<source>) — <description>`; a
pack on that list exists, whatever a search of the repository found. So does a pack vendored in
`.prd-toolkit/packs/<name>/` (its `pack.yaml`), which lint reads before any other copy.

**A retarget of a built area is refused.** A change to the pack of an area that holds a block
`built`, `verified` or `live` (a `live (since X.Y.Z)` included) is not a PRD change: its
outputs, contracts and tests were built and checked under the old pack. Say, exactly:

`retargeting an area is a conversion, which a later prd-toolkit release brings`

and stop: no `/prd-change`, no version bump, no edit and no plan to move a status back to
`approved`. The same holds for §1's `Pack:` line when an area without its own `Target:` line
holds such a block. Name the block and its status that refuse it. The area stays as it is; a new
area under the other pack, for new outputs, is a separate change the user may ask for.

An output-language change, or a pack change on an area with no `built`, `verified` or `live` block
(every block `approved` or `as-built`), is a change like any other: the steps below, the version
by the table, and the area's contracts, Levels, Harness and test cases moved to the new pack.

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
7. **The script keeps the books.** Every new ID comes from `ids next`, the version, `updated`, the
   §14 row and the §11 rows from `bump` and `record`, and the approval commit from `approve`. Never
   count an ID, type a version or write one of those rows yourself, and never edit what `record`
   wrote: change the PRD and run `record` again.

## Version rule

| Level | When | Examples |
|---|---|---|
| **Major** | existing behaviour changes or is removed | getOrder answers 410 instead of 404 for a deleted order: 1.0.0 → **2.0.0**. Dropping the empty-file rule AC-001.3: major. |
| **Minor** | behaviour is added, nothing existing changes | admins can archive an order, a new FR-005: 2.0.0 → **2.1.0**. Accepting CSV files with a BOM: minor. |
| **Patch** | wording only; no AC, test expectation, contract or result changes. Two exceptions, below: a regression patch for an `errors.md` entry, and a test case or contract corrected to match its own unchanged AC | a typo, a clearer Flow line |

If any existing AC, test-case `expect`, error code, status code or response changes meaning or
disappears, it is major. Ask "can a test that passes today fail after this?" Yes means major,
except the two patches in the Patch row; any other changed `expect` is major.

**What `bump` applies.** `prd_change.py bump` (step 3) decides each changed item by this table, the
script's own (`change.BUMP_RULES`; a test holds the two equal, row for row):

| Item | Level |
|---|---|
| a new block or AC | minor |
| a new test case under a new AC | minor |
| a removed block or AC | major |
| a removed contract item | major |
| an AC whose text changed (not equal after lowercasing, removing punctuation and collapsing whitespace) | needs judgment |
| an AC whose text is equal after that normalization, a changed title, Flow, Edge cases or glossary meaning | patch |
| a changed test case or contract item under an unchanged AC | needs judgment |
| a changed test case under a changed AC | major |
| a new test case under an unchanged AC that cites an open errors.md entry | patch |
| any other new test case under an unchanged AC | needs judgment |
| a changed version on a `Pack:` or `Target: pack` line, the pack's name and source unchanged | patch |
| a moved block `Status:` value | patch |
| any other changed file in the PRD folder | needs judgment |

It ignores the frontmatter `version:`, `updated:` and `status:` lines, the §11 and §14 tables, block
`Source:` lines, a `Tests:` line that only follows its added or removed cases, and
`.prd-review.json`. The highest level wins, and one `needs judgment` item makes the result
`needs judgment`. **Only you decide a `needs judgment` item, by the Level table above, with its
reason:** an AC reworded with its meaning kept is patch, one that gains behaviour and changes
nothing existing is minor, and one whose meaning changes is major; a test case or contract
corrected to match its own unchanged AC is the patch below, and any other changed `expect` or
contract item is major; a new test case under an unchanged AC adds a test expectation, so minor,
unless it is a regression patch; any other file is decided by what its change does to behaviour.
Never hand the decision to the user, and never take `needs judgment` as leave to pick the lowest
level.

**A regression patch.** A change made for an `errors.md` entry (`prd-toolkit:handling-errors`)
that only adds its regression test is a patch: a new test case under an unchanged AC, or a
`known-failing: E-nnn` line added to an existing case, and the block, which returns to `approved` (its `Status:` line; `record` writes its §11 row) so `/prd-build <area> <IDs> --fixes E-nnn` can build the fix. Its §14
row names the entry (`record --change 'regression test for E-003'`), as `regression test for E-003`:
`| 1.0.1 | <date> | regression test for E-003; <dry-run record> | FR-001, T-001.3 |`. A unit-only change records `no dry run (unit only)`; a non-unit regression T-id, new or marked, is
dry-run as step 4 says. Its commits cite the entry: `Refs: FR-001, E-003`.

**A test case or contract corrected to match its AC.** A test case or a contract that contradicts
its own AC, while the AC and the code stand, is the fix of an `invalid requirement` entry
(`prd-toolkit:handling-errors`): revising the test case's `expect` or the contract to say what the
AC says is a patch when no AC or behaviour changes. The block returns to `approved` (its `Status:` line; `record` writes its §11 row), the §14 row
names the entry (`test case corrected for E-004`) with its dry-run record as above, and its commits
cite the entry: `Refs: FR-001, E-004`.

## ID rules

`ids next` (step 2) applies these rules; they say what it counts, so you can check its answer, never
so you count instead of it.

- **Next free UJ number** = the highest UJ number, removed ones included, + 1, written with two
  digits: after UJ-01, **UJ-02**.
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
| Index row (§11) | written by `record` from the block's `Status:` | written by `record`: status `removed` |
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
   `uv run --script <scripts>/prd_context.py docs/prd/<slug> --area <area> --req <IDs>; echo "prd-context-exit=$?"`.
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
2. **Edit the PRD.** New behaviour gets new IDs, each from `ids next`, its own Bash call:
   `uv run --script <scripts>/prd_change.py ids next docs/prd/<slug> <kind>; echo "prd-change-exit=$?"`,
   where `<kind>` is `FR`, `NFR`, `UJ`, `AC-<nnn>` (the next AC of block nnn) or `T-<nnn>` (the next
   T-id of requirement nnn). It prints the ID and reads the files on disk, so write each ID into the
   PRD before you ask for the next one of the same kind, and a new block's heading before its first
   `AC-<nnn>`. Use the ID it prints; never count one yourself, however obvious the next number looks:
   the count misses removed IDs and T-ids that survive only in §14. Changed and new requirements go to
   `approved` in the block's `Status:` line; `record` (step 3) writes the §11 index from it. Revise every test case whose AC changed and write one,
   with all seven elements, for every new AC. Revise `errors.yaml` (new code or changed
   `status`), `openapi.yaml` (responses, `x-error-codes`, `x-prd-ids`) and every other contract
   step 1 listed. If a block the change touches has a `Source:` line, run the pack again with
   `--for implement` (its own Bash call, the same gate), re-read each region it marks STALE, and
   rewrite that ref as `<path>:<current line> @<HEAD short sha>`. A revised block keeps its
   `Source:` line: refresh a STALE one to the current line and sha, and never drop it, because the
   next implement pack reads FR code from it. Set the PRD status to `In review`.
   **Linked PRDs.** When `links.md` has Consumers, run, after the edits and as its own call,
   `uv run --script <scripts>/prd_links.py impact docs/prd/<slug>; echo "prd-links-exit=$?"`.
   `0`: no consumer cites a changed item; go on. `1` (a consumer cites a changed item) or `3` (a
   consumer was unreachable) stops this change: it crosses repositories, so hand it, the edits
   in the tree and nothing committed, to `/prd-change-set` (skill `prd-toolkit:coordinating-prds`);
   that is the only route for an edit to a cited item. Never skip a consumer the output names,
   cloned or not. `2` is a usage error: fix the command. A repository whose `.prd-toolkit/` holds
   no `prd_links.py` predates 0.7: stop, and tell the user to re-run `prd_hooks.py install
   docs/prd/<slug>` from the plugin and commit `.prd-toolkit/`. When this change already runs
   inside `/prd-change-set`, hand nothing back to it: before the record exists, its step 1 reads
   this `impact` itself. Inside a change set (its `cs-<nnn>-<slug>` branch, with a record whose
   rows name this PRD), exit `1` is expected when every consumer it names is a member, and `3`
   when each unreachable one is a consumer the record's Log leaves out: go on, and step 5's
   approval is the change set's (`running-a-change-set.md` step 3), its commit adding
   `-m "Change-set: <start-prd>/CS-<nnn>"`.
   **A new link.** When this change adds a link, `prd_links.py add` writes the upstream's
   `links.md` Consumers row, uncommitted, in the upstream repository. That row needs its own
   `/prd-change` there (a patch bump); until it lands, `check` reports `missing row`.
3. **Bump the version** with the script, never by hand. First, its own call:
   `uv run --script <scripts>/prd_change.py bump docs/prd/<slug> --base HEAD; echo "prd-change-exit=$?"`.
   The base is `HEAD` because the change stays uncommitted until step 5. It prints one line per
   changed item, `<level> <ID> <file>:<line> <reason>`, and `level <level>` last. Decide each
   `needs judgment` item by the Version rule, with its reason, and carry each decision to step 5.
   The level is the highest of all the items, the decided ones included. Then, its own call:
   `uv run --script <scripts>/prd_change.py record docs/prd/<slug> --base HEAD --bump <level> --change '<the change, one line>'; echo "prd-change-exit=$?"`.
   `--bump` is `patch`, `minor` or `major`. `record` writes the version, `updated` (today), the §14
   row `| <version> | <date> | <change>; pending | <IDs> |` and the §11 rows: the added, retitled
   and removed blocks, and every §11 row's status from its block's `Status:` line. `refused: the diff needs major, not minor` means your level is below what
   the diff needs: record at the level it names. `refused: a needs-judgment bump must be decided first`
   means you passed the judgment as a level: decide it. The IDs cell lists every new, changed and
   removed ID, T-ids included, and the requirement each AC and T-id belongs to; it is the only
   record of a deleted test case. When it leaves out a UJ, FR, NFR, AC or T-id step 1 listed, the edit is incomplete: fix the PRD and run `record` again, which replaces its own `pending` row. After any later edit, run `bump` and `record`
   again; never edit the version, `updated` or a row `record` wrote. `pending` holds the place of
   the dry-run record step 4 makes: `dry run T-002.3, T-003.3, 0 open questions, 1 dismissed by quote`,
   `no dry run (removal only)`, `no dry run (unit only)` or `no dry run (wording only)`. Step 5's
   `approve` writes it there.
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
   **The verdict.** Once the `prd-lint-exit=` value is `0` and the dry run passed (or its record
   says why there is none), write `docs/prd/<slug>/.prd-review.json`, the file `approve` checks,
   in the shape **The verdict** of `${CLAUDE_PLUGIN_ROOT}/skills/changing-prds/reviewing-a-change.md`
   gives, filled from steps 1 to 4: `head` from `git rev-parse HEAD` and `digest` from
   `uv run --script <scripts>/prd_change.py digest docs/prd/<slug>; echo "prd-change-exit=$?"`, each
   its own call, `ready` `true` and `blockers` `[]`, and `"base": "<sha>"`, the full SHA from
   `git rev-parse HEAD` (its own Bash call), the base step 3's `bump --base HEAD` reads, so the
   inbox's approval card shows the owner the uncommitted change. For a change made for an
   `errors.md` entry, add `"refs": "<changed IDs>, E-nnn"` to the verdict: the inbox's approval
   passes it to `approve` as `--refs`. Leave `refs` out for any other change. Write it only
   then: anything that would make `ready` false sends you back to the step whose gate is open. It
   is never committed (`approve` leaves it out and deletes it). Inside a change set (step 2),
   write no `.prd-review.json`: the change set's one approval (`running-a-change-set.md` step 3)
   is the only approval, and this step's dry-run record goes to it in the report.
5. **Approval, then commit.** First check what this conversation holds. If it does not hold a
   passing dry-run report, or the recorded reason there is none, for the current files, run
   step 4 now. `In review` and a clean lint are not evidence that it ran; a new session starts
   with neither. Then show the user the restatement, the changes by ID, the new version and why
   that level (each `needs judgment` decision with its reason), the decisions from step 1, the
   lint result and the dry-run report. Ask through **The decision inbox** below, with the gate
   `approval:<branch>` (`<branch>` from `git branch --show-current`, its own call), or headless or
   in the chat as follows. An outcome `approve`: the inbox already ran `prd_change.py approve` with
   the owner's reply, step 4's record and the verdict's `refs` (step 4 sets it for a change made for
   an `errors.md` entry: `'<changed IDs>, E-nnn'`), and made the approval commit. Never run `approve` again:
   grep the plans as below, then go on from "Only now may code change". An outcome `changes`: its
   reply is the change request, an edit, so back to step 2; the revision answers that reply as it
   stands, and step 4's new verdict raises the gate again. Inside a change set (step 2) there is no
   gate: the change set's one approval is the approval. The chat route: wait for explicit approval.
   A reply that does not approve (a question, "maybe", a change request) is not one: answer it,
   and a requested change is an edit, so back to step 2. Your own text, the request that started
   the change and "go ahead and finish it" given before the user saw step 5 are never a reply. Then grep
   `docs/superpowers/plans/` for every changed ID and list each plan file that cites one as
   needing an update, and approve, its own call, with the user's words verbatim as `--reply`
   (writing each `'` as `'\''`) and step 4's record as `--dry-run`:

   ```bash
   uv run --script <scripts>/prd_change.py approve docs/prd/<slug> --reply '<the reply, verbatim>' --dry-run '<the dry-run record>'; echo "prd-change-exit=$?"
   ```

   `approve` runs every check before it writes (the verdict and its digest, lint, the dry-run
   record, the `pending` row), then writes the record in place of `pending`, sets the status
   `Approved`, runs `prd_block.py` and commits `docs(prd): approve <slug> <version>` with the reply
   in its body. Never set the status, run `prd_block.py` or commit the PRD folder and CLAUDE.md with the trailer
   `Refs: none (no behaviour change)` by hand: `approve` does all three, and stages
   `docs/prd/README.md` when it exists with the folder (a change made for an
   `errors.md` entry uses `Refs: <changed IDs>, E-nnn` on that commit instead: add
   `--refs '<changed IDs>, E-nnn'`). A refusal names what to fix; `the PRD changed after its
   review` means the files moved since step 4: run step 4 again for them. **Inside a change
   set** (step 2) `approve` is not run, since its commit carries no `Change-set:` trailer: write
   the dry-run record in place of the row's `pending` (the one hand edit of a row `record` wrote),
   set the status `Approved`, check the
   `prd-lint-exit=` value is `0`, rerun `uv run --script <scripts>/prd_block.py docs/prd/<slug>`,
   delete any stale `.prd-review.json` and make the commit `running-a-change-set.md` step 3 gives,
   which stages `docs/prd/README.md` when it exists with the folder and CLAUDE.md.
   Only now may code change, and each
   behaviour commit cites its IDs (`Refs: FR-005`). Hand off with only the UJ, FR and NFR IDs
   (map an AC, test case or error code to its requirement): hand off
   `/prd-build <area> <IDs> --fixes E-nnn` when the change was made for a confirmed entry whose
   route builds code (`code bug`, `spec gap`, `invalid requirement`, or `standard` when code must
   follow, as `prd-toolkit:handling-errors` routes them); otherwise build with
   `/prd-build <area> <changed IDs>`. Its close writes the status
   moves and each `Source:` line, so there is no refresh to do. Code written outside `/prd-build`
   is written from `/prd-context <area> <changed IDs> implement`. After the code commit, run the
   implement pack again (its own Bash call, the same gate), then
   rewrite each STALE `Source:` of a changed block as `<path>:<line> @<new short sha>` and commit
   the PRD. A `Source:` refresh is provenance, not behaviour: it takes no version bump and no
   §14 row, and the status stays Approved with no re-approval.
   Close: when the change touched `testing.md` or `operations.md`, a generated CI include is stale (a new level, an
   environment, a `tests` step or a Drift row changes it). If `.gitlab/prd-toolkit.yml` or
   `.github/workflows/prd-toolkit.yml` exists, regenerate each one present, one command per Bash call, and commit the file:
   `uv run --script .prd-toolkit/prd_hooks.py ci --<forge> --force docs/prd/<slug>`. Then confirm with
   `uv run --script .prd-toolkit/prd_hooks.py check --ci docs/prd/<slug>` (it prints nothing when the files are
   current). The merge gate's generated job runs that same `check --ci`, so a change merged with the old CI fails there. A change made for an `errors.md`
   entry cites it in `Refs:` beside the requirement it touches (`Refs: FR-002, E-003`).

## The decision inbox

The owner answers a gate in a local page, the decision inbox, unless nobody can open it. The step
that asks names the gate; `<gate id>` below is its id. One command per Bash call, with literal
paths, written with the skill's `<scripts>` path, never `${CLAUDE_PLUGIN_ROOT}`.

- **`wait`, first.** Start it with the Bash tool's `run_in_background`, before the owner sees any
  URL, so no answer can come before it is watching:
  `uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>`
- **The URL.** Then start, also with `run_in_background`,
  `uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>`
  and re-read its output until its first line appears:
  - `url=<url>`: give the owner that URL as a clickable link, beside what the step shows in the
    chat.
  - `prd_gates: an inbox is already serving at <url>`: the inbox that
    `<git common dir>/prd-inbox-<slug>.json` names is live and lists this gate too. Give the owner
    `<url>#gate=<gate id>`. Leave that `serve` running: it stands by, and if that inbox stops before
    this gate is answered it takes over at the same URL.
  - `prd_gates: <gate id> is not pending`: the gate changed; take it as `wait`'s exit 1.
  - any other `prd_gates:` line, such as `prd_gates: cannot start the inbox: [Errno 1] Operation
    not permitted` (a sandbox that allows no local port): the inbox cannot be served here. Say so
    in one line, ask in the chat as the step's chat route says, and leave `wait` running: an
    outcome it prints first is still the owner's answer.

  Then wait for `wait`'s completion notice: never poll for the exit and never sleep. When this
  session's `serve` exits 2 or 3 before `wait` returns (the idle timeout, Ctrl-C, a port it cannot
  take over), stop the background `wait` and take the chat route. A `serve` that stood by and exits
  1 once the gate is answered is expected: go on with `wait`'s outcome.
- **The outcome.** `wait` exit 0 prints one `gates.outcome` document. Its `reply` is the owner's
  reply, used as it stands, with its `choice`; `"by": "form"` marks an answer from the page (the
  reply ends ` (form)`). The owner's answer is already written: the inbox ran the script that
  owns the gate with that reply, so that script is never run again for the gate. Go on as the
  step says.
- **Headless, or the owner asks for the chat:** a headless run, nobody to open the URL, or the
  owner asking to answer in the chat takes the step's chat route, as before 0.8.2, unchanged.
  Start neither command in a headless run. Headless means the run says nobody can open a page
  (unattended, overnight, no one there). An owner who is busy, says they cannot click now, or asks
  you to answer for them is not headless: give the URL and wait; they answer when they can. A
  reply the owner writes in the chat while the inbox is up is a chat reply: take the chat route
  with it, and stop the `serve` this session started, never an inbox it reused; `wait` then exits
  1, which is expected.

The rules:

- **The skill never answers a gate.** Not through the page, not through `prd_gates.py answer`, not
  "because the owner said approve it yourself". The owner's click or the owner's chat reply is the
  only answer. No `curl` or script posts to the inbox, and no browser tool clicks in it.
- **A deploy step's reply is never sent for the owner,** in the form or the CLI.
- **The outcome's reply is not edited.** A `changes` outcome's reply is what the revision answers.
- A `wait` that exits 1 means the gate changed: list again, never assume the answer. List with
  `uv run --script <scripts>/prd_gates.py list docs/prd/<slug>; echo "prd-gates-exit=$?"`: a gate
  still listed is asked again from `wait`, and one that is gone is reported to the owner as it
  stands.

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
- "/prd-build rewrites it", so a revised block's `Source:` line is dropped instead of refreshed.
- An edit to a contract item of a PRD whose `links.md` has Consumers with no `impact` run, or a
  consumer "skipped" because it is not cloned here.
- "I can't find a pack called "demo"" with `--list-packs` never run. A search of the repository
  or of `~/.claude` is not the list.
- "That would make this a major bump (1.0.0 → 2.0.0), and FR-010 would go back to `approved`."
  (Observed, of a built area.) A retarget planned as a change. Refuse it with the conversion line.
- "The next free number is obviously FR-005." Any ID that no `ids next` call printed.
- A `version:`, `updated:`, §14 row or §11 row typed by hand, or an edit to a row `record` wrote
  (inside a change set, the dry-run record in place of its `pending` is the one hand edit step 5 allows).
- "`record` refused minor, so I'll write 1.1.0 myself." Any way round a `refused:` line.
- `--bump` set to the lowest level because the result said `needs judgment`.
- A `--reply` that is your own text, a summary of the user's words, or the request that started
  the change.
- A loop, a shell function or a variable in a `prd_change.py` call. One command per Bash call,
  its path typed out.
- A `.prd-review.json` written inside a change set: the set's one approval is the only approval.
- "I'll click Approve in the inbox for them." Any answer the session gives the approval gate: in the
  page, through `prd_gates.py answer`, or by `prd_change.py approve` on an outcome already approved.

**All of these mean: stop, put the code back, and return to the step whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "Counting the next ID myself is quicker than a script call." | The count misses removed IDs and T-ids that survive only in §14. `ids next` reads them all, in one call. |
| "`record` refused, so I'll write the row myself." | The refusal is the version rule. Record at the level it names. |
| "`needs judgment` means any level will do." | It means you decide it by the Version rule, with the reason, and show the decision in step 5. |
| "The owner told me to click Approve in the inbox for them." | The click is the owner's answer. A session that clicks, or runs `prd_gates.py answer`, writes an approval nobody gave. Give the URL and wait for the outcome. |
| "The user approved in their first message." | A request is not an approval of a diff they have not seen. Step 5 shows it, then waits. |
| "A retarget is just a major change." | Its built outputs, contracts and tests belong to the old pack; moving them is a conversion. Refuse with `retargeting an area is a conversion, which a later prd-toolkit release brings`. |
| "The pack isn't in the repository, so it doesn't exist." | Packs live in installed plugins too. `--list-packs` is the list; run it before saying a pack is missing. |
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
