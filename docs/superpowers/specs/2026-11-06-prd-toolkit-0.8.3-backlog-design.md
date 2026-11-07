# prd-toolkit 0.8.3: fixes from the 0.8.2 proof — design

> **Date:** 2026-11-06
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md` and the specs it extends, under
> `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this addendum and any of them disagree, this addendum
> wins for 0.8.3.
> **Needs:** 0.8.2 on `main` (PR #16, `f7462ef`).
>
> **Inserted (owner, 2026-11-06).** 0.8.3 was the PRD READMEs. This release takes its place; the READMEs
> become 0.8.4 (`2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md`, content unchanged), best practices
> 0.8.5 and conversion 0.8.6. The umbrella's §4 records the move.

## 1. Scope

0.8.2 was proven on 2026-11-06 in two worktrees of this repository, on proof branches that stayed
local. The proof, and the reviews before it, left a backlog: a build that cannot finish in this
repository, two `prd_change.py record` bugs, seven confirmed `prd_build_check.py` bugs, and eight small
inbox and gate residuals. 0.8.3 fixes all of them and adds no feature.

**Governance.** The toolkit's own PRD (`docs/prd/prd-toolkit`, 4.0.0) has one adopted area,
`lint-cli`. Every item here except E-007 lies in an area that is `not started`, or, for
`prd_gates.py`, `prdlint/gates.py` and `prdlint/change.py`, in no area's Boundary. So 0.8.3 is built
from this spec through a plan, as 0.8.2 was, and writes no `errors.md` entry. E-007, a `lint-cli` bug,
goes through the real PRD after 0.8.3 merges, and is the proof (section 9).

The E-numbers below are the proof branch's (`proof/prd-toolkit-0.8.2-error`, deleted; the entries are
quoted from its `errors.md` at `bcc5373`). They name backlog items in this spec only; the real PRD
numbers its own entries.

0.8.3 delivers:
- a build in this repository that refreshes `.prd-toolkit/` through a new `prd_hooks.py vendor`, which
  `prd_build_check.py --diff` accepts when the refresh is exact (section 2);
- the standby promise made only when the vendored copy has a standby (section 3);
- `prd_change.py record` writing each live block's Since, and the IDs a changed contract item cites
  (section 4);
- seven `prd_build_check.py` fixes (section 5);
- eight inbox and gate fixes (section 6);
- a README note on namespaced commands (section 7).

## 2. A build in the toolkit's own repository (E-008)

**The failure.** `tests/test_vendored_copy.py` asserts that `prd_hooks.py check docs/prd/prd-toolkit`
exits 0: this repository's `.prd-toolkit/` must be the plugin's bytes. A builder's fix to a script that
`.prd-toolkit/` vendors (the E-007 round changed `prdlint/model.py`) breaks that unit test. The builder
must fix a test its change broke (building-from-prds rule 8), and `prd_build_check.py --diff` refuses
every builder edit under `.prd-toolkit/` (`the builder may not edit the vendored .prd-toolkit/ copy`).
No step of the build refreshes the copy, so the round cannot pass. The proof's builder refreshed it
with a hand-run snippet and the check refused the round (E-007 round 1, `dde9113`).

This happens only in a repository that holds the plugin. Elsewhere a builder never changes the scripts
that `.prd-toolkit/` vendors, and the refusal stands as it is.

### 2.1 `prd_hooks.py vendor <prd>`

A new subcommand writes `.prd-toolkit/` exactly as `install` does (`hooks._vendor`, with the packs the
PRD names) and nothing else: no git hook, no `CLAUDE.md` block, no CI file. It prints
`vendored the toolkit into .prd-toolkit/ (version <X.Y.Z>)` and exits 0.

- It runs only from the plugin (`hooks.is_plugin()`). Run from a vendored copy it prints
  `prd_hooks: vendor runs from the plugin, not from .prd-toolkit/` and exits 2.
- A PRD whose pack cannot be resolved is the same error `install` gives, exit 2.
- `prd_hooks.py --help` lists it beside `install`, `check` and `ci`.

### 2.2 `--diff` accepts an exact refresh

`prd_build_check.py --diff <base>..<head>` keeps its refusal for a path under `.prd-toolkit/`, with one
exception. The changed `.prd-toolkit/` paths pass when both hold at `<head>`:

1. **The repository holds the plugin:** a directory `<dir>` in `<head>`'s tree has
   `<dir>/.claude-plugin/plugin.json` whose `name` is `prd-toolkit`, and `<dir>/scripts/prd_hooks.py`.
   With more than one such directory, none counts and the refusal stands.
2. **The refresh is exact:** `.prd-toolkit/` at `<head>` is byte-for-byte what `vendor` writes from
   `<dir>` at `<head>`, for every path `vendor` writes, and holds no path `vendor` would delete. The
   check builds that expected tree in a temporary directory from `<head>`'s files (never from the
   working tree, never from the installed plugin).

When condition 1 holds and condition 2 fails, each differing path is reported once, in path order:
`<path>: differs from the plugin; refresh it with prd_hooks.py vendor`, exit 1. When condition 1 fails,
the existing line is printed for each path, unchanged. A tool error building the expected tree (a git
command fails, the plugin's `prd_hooks.py` cannot run) is exit 2, `prd_build_check: <message>`.

### 2.3 The builder refreshes, the caller checks

- **building-from-prds**, rule 4 and the Red Flags; **agents/prd-builder.md**, the same rule: in a
  repository that holds the plugin (2.2, condition 1), a change to any plugin file that `vendor`
  copies (its scripts, templates, language tables and the packs the PRD names) is followed, before the
  commit, by
  `uv run --script <worktree>/<dir>/scripts/prd_hooks.py vendor docs/prd/<slug>` (its own Bash call,
  from the builder's own worktree, so it vendors the changed scripts), and the `.prd-toolkit/` changes
  are committed in the same commit as the change. Never an edit under `.prd-toolkit/` by hand, and
  never `prd_hooks.py install`.
- **running-a-build.md**, the round check: no new step. The caller's `--diff` check accepts an exact
  refresh and refuses anything else; a `differs from the plugin` line is a fail the caller routes to
  the builder like any other `--diff` finding.
- Backlog item (i) (who re-vendors) is this section.

## 3. The standby promise checks the vendored copy (k)

The four decision skills tell the user, after `serve --gate`, "Leave that `serve` running: it stands
by…" (adopting-prds, changing-prds, deploying-from-prds, handling-errors' running-an-error.md). The
proof's `-change` worktree ran a `.prd-toolkit/` vendored before 0.8.2's section 18: its `serve --gate`
exited 1 at once, and the skill's promise was false.

In each of the four, when `<scripts>` is `.prd-toolkit`, the skill reads `.prd-toolkit/VERSION` once
(a Read, before the first `serve`). When the file is missing or names a version below `0.8.2`, the
skill does not promise a standby and tells the user, in place of that sentence:
`This repository's .prd-toolkit/ is <version or "older than 0.6">, so the inbox closes with the session that started it; run prd_hooks.py install docs/prd/<slug> from the plugin to refresh it.`
It then goes on with the inbox as 0.8.2 says. When `<scripts>` is the plugin's own directory, nothing
changes.

## 4. `prd_change.py record` (E-016, j)

**E-016.** `record` writes an added block's §11 row with an empty Since, and copies only the status from
each block (`change._index_rows`). A block whose `Status:` is `live (since X)` then fails lint's
`index-consistent` (`FR-016 is live but the index has no Since`), and `approve` refuses. The proof hit
it adopting `build-check` with five `live` blocks.

Fix: for every row `record` writes, new or existing, the Since cell is the `since` the loader reads from
the block's `Status:` line (`live (since 5.1.0)` → `5.1.0`), and empty when the status has none. A row
whose block is unchanged keeps its cells as they were.

**(j).** When only a contract item changes, `record` writes `-` in the §14 IDs cell, though the item
cites its requirement and `bump` flagged it. `_record_ids` keeps only items whose id is a requirement
ID, and a contract item's id is its name.

Fix: for each added, changed or removed contract item, the IDs cell also lists the UJ, FR and NFR IDs
that item cites, each once, in the cell's existing order:
- an OpenAPI operation cites the IDs in its `x-prd-ids` list;
- every other item (an event, a table, an `errors.yaml` code, a `config.yaml` key, a custom or pack
  type's item, a whole-file item) cites each `UJ-nnn`, `FR-nnn` and `NFR-nnn` token in its text, as
  `contract_items` canonicalizes it. The proof's case: the `cli.yaml` item `prd_lint` names
  `(FR-009)` in its text.
- An `AC-nnn.n` among them adds its block, as `_record_ids` already maps an AC.

An added or changed item is read at the working tree, a removed one at the base. An ID that is not a
block in either PRD is not added. An item that cites nothing adds nothing; when the whole change names
no ID the cell stays `-`.

## 5. `prd_build_check.py` (E-009 to E-015)

Each was confirmed as a code bug against the behaviour the proof's `build-check` adoption extracted;
the AC quoted is that adoption's, and is the behaviour 0.8.3 builds.

| Item | Mode | Today | 0.8.3 |
|---|---|---|---|
| E-009 | `--stale` | A PRD folder outside any git working tree: `repo_root` falls back to the folder, no citation is found, nothing is printed, exit 0. | `prd_build_check: <prd> is not in a git working tree`, exit 2, before any T-id is read. |
| E-010 | `--results` | Blank lines are skipped anywhere after the heading, so a T-id line after a blank line that follows result lines is still read. | "skipping blank lines before the first result line, and shall stop at the first line after it that is blank or is not a result line, reading nothing after it." The docstring and the inline comment say the same. |
| E-011 | `--stale` | Test-case files parsed with `yaml.safe_load`, which keeps a repeated key's last value. | Parsed with the PRD loader's YAML reader (`prdlint.yamlload`): the first value wins, as the loader and the format reference say. |
| E-012 | `--stale` | At a commit, `git ls-tree -r` recurses into `test-cases/` subfolders; in the working tree, `glob("*.yaml")` does not. | Both ends read only files directly in `test-cases/` named `*.yaml`, as the loader does. |
| E-013 | `--stale` | A directory or broken symlink named `<name>.yaml` in `test-cases/` is read and raises: exit 2, internal error. | Skipped: only regular files are read. Lint reports such an entry (after E-007's fix). |
| E-014 | `--diff` | `CITE` runs over the whole file, so `@prd` at a line's end and a T-id on the next line count as a citation. | Citations are read line by line with the trace's scanner (`trace._scan`'s rule), so `--diff`, `--stale` and `prd_trace.py` agree on what a file cites. |
| E-015 | `--stale` | Only committed citing files are judged, and `git status` is run on the judged file alone, so an untracked test that also cites the T-id is ignored. | "If any file under the test roots that cites the T-id has an entry in `git status --porcelain` (untracked, or a working-tree or staged change: a test being written now), the build check shall print no line for the T-id, whatever the committed citing files show." |

Each fix gets a unit test that fails first (red, then green), named for its item in a comment, never
citing a T-id: build-check is not adopted, and the tests are the plugin's own suite.

## 6. The inbox and gates ((a) to (h))

**(a) and (e): the approval card diffs against the reviewed base.** Review mode
(`reviewing-a-change.md`) reads the change against `--base <ref>`, else the branch's upstream, else
`main`. The card's `_diff_base` uses `git merge-base HEAD` with the upstream, `origin/HEAD`,
`init.defaultBranch`, then `main`. The owner can approve a diff that is not the one reviewed.

- The verdict gains an optional key `base`: the full SHA review mode diffed against
  (`git rev-parse <base>`, its own call). `VERDICT_TYPES` gains `"base": str`. Review mode's step that
  writes `.prd-review.json` writes it; changing-prds' own verdict writer records `git rev-parse HEAD`, the
  base its `bump --base HEAD` reads.
- The card diffs, and reads the "from" version, against the verdict's `base` when it is present and
  `git cat-file -e <base>^{commit}` succeeds.
- Without it (a verdict written before 0.8.3, or a base no longer in the repository), the card uses
  review mode's rule: the branch's upstream (`git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`)
  when it has one, else `main`, else `HEAD`. `origin/HEAD`, `init.defaultBranch` and the merge-base go.

**(b): a corrupt deploy run log is a tool error.** `prd_deploy.py` reports a `ValueError` raised while
reading a run log as `prd_deploy: <message>`, exit 2, which the deploy-step route reads as the owner's
refusal (400). Fix, in two parts:
- `prd_deploy.py` reports a run log that does not parse as `prd_deploy: internal error: <type>: <message>`,
  exit 2. Its other `ValueError` messages (usage refusals) are unchanged.
- The deploy-step route classifies an exit-2 answer as a tool error (500) when the first stderr line
  starts with `prd_deploy: internal error:`, and as a refusal (400) otherwise. The substring test goes.

**(c): a multi-line `refs` fails the shape check.** `verdict_shape_ok` accepts a `refs` string with a
line break, and `prd_change.py approve` then fails with a 500. A `refs` holding `\n` or `\r` makes the
verdict the wrong shape: no gate, as invalid JSON is.

**(d): `beforeDone` is optional.** `templates/confirm/panel.html` awaits `HOST.beforeDone()` with no
check. It awaits it only when `HOST.beforeDone` is a function; with none, Done goes on as it does
without a host.

**(f): a PRD that vanishes during a takeover keeps the standby.** Between `_standby`'s `model.load` and
`make_inbox`'s own load, the PRD can disappear; `make_inbox` then fails in a way that reaches the
`OSError` branch and prints `cannot take over` (exit 2). A load failure inside `make_inbox` is told
apart from a bind failure (the bind's `OSError` alone is a port problem), and a load failure goes on
standing by.

**(g): an unexpected error during a takeover is said once.** The trailing `except Exception: continue`
hides a programming error until the idle bound. It prints
`prd_gates: standby: <type>: <message>` to stderr the first time each distinct `(type, message)` occurs,
then goes on standing by. An expected load failure (f) prints nothing.

**(h): not pending wins over idle.** When the idle bound and the gate leaving the list fall in the same
tick, the standby exits 3. It checks the gate first: not pending is exit 1 (after `STANDBY_LINGER`), and
only a still-pending gate past the bound is exit 3.

## 7. Documentation

- **README, testing locally:** under `claude --plugin-dir <path>`, the commands answer only to their
  namespaced form (`/prd-toolkit:prd-change`); the skills' bare `/prd-change` is the installed form.
- **README, 0.8.3 changelog entry:** each fix above, one line each; the upgrade (section 10).
- `prd_hooks.py vendor` in the README's script table and in the "Upgrading" notes, as the way this
  repository refreshes its own copy.

## 8. Testing the toolkit

- Unit tests, red first, for: `vendor` (writes exactly `install`'s `.prd-toolkit/`, writes no hook or
  block, refuses from a vendored copy); `--diff`'s exact-refresh acceptance (an exact refresh passes, a
  hand edit fails with the new line, a refresh in a repository without the plugin keeps the old line,
  two plugin directories keep the old line, a stale file `vendor` would delete fails); E-016 and (j)
  in `record`; each row of section 5; (a) to (h).
- `tests/test_inbox_skills.py` (or its neighbour) pins the section 3 sentence in all four skills, as
  0.8.2 pins the standby sentence.
- The skill changes in sections 2.3 and 3 follow `superpowers:writing-skills`: a baseline run without
  the change, then with it, for the builder's refresh rule (a builder whose fix breaks
  `test_vendored_copy.py` runs `vendor` and commits it, never hand-edits) and for the standby check.
- `scripts/ci-local.sh origin/main` with an empty `HOME` before any push; the inbox evals
  (`--case 'inbox-*'`) still pass.

## 9. Proof

After 0.8.3 merges and is installed, in this repository, on a branch of its own:

1. `/prd-error` records the `lint-cli` crash on a non-file `.yaml` in `test-cases/` or `contracts/`
   (the proof's E-007) in the real `errors.md`, and the owner confirms its class.
2. `/prd-change` revises what its class calls for (the proof found AC-006.3's scope wrong); the version
   level is the skill's to decide.
3. `/prd-build lint-cli FR-006 --fixes E-<n>`: the round's commit holds the `prdlint/model.py` fix and
   the `vendor` refresh of `.prd-toolkit/`; `prd_build_check.py --diff` exits 0; the build closes
   `verified`.

The proof passes when step 3 closes `verified` with no hand edit under `.prd-toolkit/`. It is recorded
in the 0.8.3 changelog entry.

## 10. Upgrade

No PRD needs an edit. A repository with `.prd-toolkit/` re-runs `prd_hooks.py install docs/prd/<slug>`
to vendor the fixed `prd_build_check.py`, `prd_change.py`, `prd_gates.py` and `prd_deploy.py`. A
verdict written before the upgrade still makes a gate; its card uses the section 6 fallback.

## 11. Release and renumbering

- `prd-toolkit/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`: `0.8.3`.
- Umbrella `2026-11-03-prd-toolkit-0.8-umbrella.md`: a §4 revision line (owner, 2026-11-06) and the
  table: 0.8.3 is this spec, the READMEs 0.8.4, best practices 0.8.5, conversion 0.8.6, with the
  dependency columns moved to match.
- The READMEs spec is renamed `2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md` (`git mv`); its
  title and its own version references change to 0.8.4, a revision line records the move, and its
  content does not change; its plan moves to `2026-11-04-prd-toolkit-0.8.4.md` the same way, with its
  worktree, branch and "starts after" line moved to 0.8.4 and 0.8.3. Revision notes in earlier specs
  (0.8.0, 0.8.2) are history and keep the paths and numbers they had.
- Shipped text names no release number for a later feature (0.8.2 made the retarget refusal say "a
  later prd-toolkit release"), so the renumbering changes no skill or script.

## 12. Out of scope, and not toolkit defects

- **Adding `prd_gates.py`, `prdlint/gates.py`, `prdlint/change.py`, `prd_change.py` and
  `prdlint/change_approve.py` to an area's Boundary** in the real adoption map. A PRD change, for a
  later release.
- **Adopting `build-check`.** The proof drafted it (5.1.0, uncommitted, archived outside the repository);
  it is not part of 0.8.3.
- **"changing-prds cuts its own worktree from main."** No toolkit text tells a session to make a
  worktree; the proof session made one from `main` on its own and so ran `main`'s vendored copy. Not a
  toolkit defect; nothing changes.
