# prd-toolkit 0.8.1: the machine interface — design

> **Date:** 2026-11-03
> **Author:** Ivan Histand & Claude Code
> **Status:** Approved by the owner 2026-11-03
> **Extends:** the base spec and the 0.2 to 0.8.0 addenda (`2026-11-03-prd-toolkit-0.8.0-design.md`
> last). Governed by `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this spec and any of them
> disagree, this spec wins for 0.8.1.

> **Revisions.**
> - §3 (plan ruling): `prd_status.py --json` and `prd_context.py --json` already printed a bare JSON list
>   in 0.8.0. The wrapped document replaces that shape; the README changelog names it as a break for
>   anything that parses those two outputs.
> - §3 (plan ruling): the `context` document's `parts` is one entry per item, in the text pack's order:
>   `{"title": <part name>, "id", "file", "line", "text", "stale"}`. A part can hold items from several
>   files, so it cannot carry one `file`; `id`, `line` and `stale` are added fields.
> - §3 (plan ruling): `lint` and `trace` findings are `{"file": <PRD-relative>, "line", "rule",
>   "severity", "message"}`, with `"dir"` (the display root the text output prefixes) beside `prd` and
>   `version`. `--json` and `--json=1` are accepted; any other N exits 2 with
>   `unsupported interface <N>; this toolkit speaks 1`. An argparse error exits 2 with the JSON error
>   document whenever `--json` is in argv. `--interface` is on the six interface scripts (`prd_lint`,
>   `prd_trace`, `prd_status`, `prd_context`, `prd_change`, `prd_gates`).
> - §4 (plan ruling): §14 has no dry-run record column; the record is the text after the last `; ` of
>   the Change cell. `record` writes `<change>; pending` and `approve` replaces that `pending`. A change
>   is recorded and not yet approved exactly when the last §14 row's Change cell ends with `; pending`.
> - §4 (plan ruling): `ids next` handles `UJ`: the highest `UJ-nn` number in the PRD, removed ones
>   included, plus 1, written with two digits; `prd-format.md` decision 6 says so.
> - §4 (plan ruling): the bump table as the script applies it is `change.BUMP_RULES`, eleven rows that
>   split the table above into the cases a diff shows (a reworded AC is `needs judgment` unless it is
>   equal after lowercasing, removing punctuation and collapsing whitespace; a changed test case under
>   a changed AC is major; any other new test case under an unchanged AC, and any other changed file, is
>   `needs judgment`). It ignores the frontmatter `version:`, `updated:` and `status:` lines, the §11
>   and §14 tables, block `Status:` and `Source:` lines and `.prd-review.json`. `changing-prds`' Version
>   rule carries the same table, and a test holds the two equal.
> - §4 (plan ruling): a contract item is what `change.contract_items` returns: OpenAPI operations by
>   operationId, event names, SQL tables (the CREATE statement, whitespace-collapsed), `errors.yaml`
>   codes, `config.yaml` keys and pack contract items; any other contracts file is one item named after
>   its file.
> - §4 (plan ruling): `approve` commits `docs(prd): approve <slug> <version>`, the body holding
>   `Reply: "<verbatim reply>"` and the dry-run record, then `Refs: none (no behaviour change)` (or
>   `Refs: <IDs>, E-nnn` with `--refs`). It runs `prd_block.py` first and commits `CLAUDE.md` with the
>   PRD folder when that changed it, and deletes `.prd-review.json` after the commit; `prd_hooks.py`
>   adds `.prd-review.json` to `.gitignore`.
> - §5 (plan ruling): the real deploy confirm argv is
>   `prd_deploy.py confirm <prd dir> --run ID --step N --reply TEXT`. The `adoption` gate is one per area
>   and adds `"items"`, its open item ids; its `answer` takes `--item <id>` with `--choice <decision>`,
>   or `--choice done`.
> - §5: the gate changes (the approval gate's `approve` and `changes`, the adoption gate pending until
>   `prd_confirm.py done`, `prd_confirm.py open`) come from the 0.8.2 decision-inbox spec §6 (Ivan, 2026-11-04).
> - §4 (R7): a block's `Tests:` line edit adds no bump item when every T-id it adds or removes is a test
>   case added or removed for that block in the same diff; any other `Tests:` edit is `needs judgment`.
> - §4 (R8): `record --bump` takes `patch`, `minor` or `major`; `needs-judgment` is refused
>   (`refused: a needs-judgment bump must be decided first`). For a `needs judgment` diff, any level at
>   or above the highest level of its decided items is accepted.
> - §4 (R9): `record` can be re-run: when the last §14 row holds the computed version and ends
>   `; pending`, it replaces that row and recomputes §11; the version is always the base's, bumped.
> - §4 (R11): `approve` refuses an empty or `pending` dry-run record; a unit-only change passes
>   `no dry run (unit only)`.
> - §4 (R12): a reply line that starts with `Refs:` is written into the approve commit body with one
>   leading space, so the trace never reads it as a trailer.
> - §4 (R16): `record` writes every §11 row's status from its block's `Status:` line in the working tree,
>   for every block, not only the changed ones, so a revised block set back to `approved` is `approved`
>   in §11 too; titles, files and added and removed rows are as before.
> - §4 (R17): the §14 IDs cell adds the requirement (FR, NFR or UJ) that each AC and T-id item belongs to,
>   once, in natural order: `FR-001, T-001.3` for a regression case.
> - §4 (R18): inside a change set `changing-prds` writes no `.prd-review.json`: the change set's one approval
>   is the only approval, and it replaces each member row's `; pending` with that member's dry-run record.
> - §5 (R19): `answer` on an `error-class` or `signoff` gate commits the owner's write itself, by path only,
>   with the message the toolkit's skills use (`docs(prd): confirm E-nnn` with `Refs: E-nnn`;
>   `docs(prd): sign off <T-id>` with `Refs:` the case's requirement), so a ledger edit never reaches the
>   next change's bump or approval commit. An owner's non-zero exit commits nothing; a failed commit exits 1
>   with git's error and leaves the write in the tree.
> - §4 (R20): `approve` refuses while `CLAUDE.md` has uncommitted changes
>   (`refused: CLAUDE.md has uncommitted changes; commit or set them aside first`), and stages `CLAUDE.md`
>   only when `prd_block.py` changed its bytes. A `CLAUDE.md` that git ignores is neither checked nor staged.
> - §5 (R21): answering an `error-class` or `signoff` gate changes the PRD folder's digest, so a pending
>   approval gate is withdrawn until a new review.

## 1. Scope

Until 0.8.0 the toolkit has one client: Claude Code, reading skill text and script output written for
people. A second kind of client (an editor, a desktop app, a CI dashboard, another agent harness)
needs three things the toolkit does not offer:

1. **Machine-readable output** from every read script.
2. **The change bookkeeping as code.** Next free IDs, the version bump, the §14 row, the §11 rows and
   the approval commit live only in `changing-prds`' text, so no client can do them without a model,
   and no test pins them.
3. **One way to list and answer pending human decisions.** Today each is answered differently:
   `prd_error.py confirm`, `prd_deploy.py confirm`, the 0.7.1 confirmation answers file, a PRD edit.

0.8.1 delivers:
- `--json` on `prd_lint.py`, `prd_trace.py` and `prd_context.py`, and `interface: 1` in every JSON
  document, `prd_status.py`'s included (section 3);
- `prd_change.py` with `ids`, `bump`, `record` and `approve`; `changing-prds` calls it instead of
  doing the bookkeeping by hand (section 4);
- `prd_gates.py` with `list` and `answer` (section 5);
- a **review mode** of `changing-prds`: `/prd-change --review <dir>` edits nothing and prints one JSON
  verdict (section 6).

The toolkit stays generic: nothing in it names a client.

### Decisions

| Decision | Choice |
|---|---|
| Where the interface lives | **In the toolkit, versioned.** Clients call the repository's vendored scripts and read JSON; they never link toolkit code |
| Bookkeeping | **Moves into `prd_change.py`**; skills and clients both call it, and pytest pins the rules |
| Human decisions | **`prd_gates.py`** lists every pending decision in one shape and passes each answer to the script that already owns it |
| Judgment steps | **A review mode of `changing-prds`**, run headless, that edits nothing |
| Compatibility | `interface: N` in every document; fields may be added within N, never removed or renamed |
| Release vehicle | Branch from `main` after 0.8.0 merges; version 0.8.1 |

## 2. Components

| Component | New or changed |
|---|---|
| `scripts/prdlint/interface.py` | new: `INTERFACE = 1`, `dump(kind, payload) -> str` |
| `scripts/prd_lint.py`, `prd_trace.py`, `prd_context.py`, `prd_status.py` | changed: `--json`, `--interface` |
| `scripts/prd_change.py`, `scripts/prdlint/change.py` | new |
| `scripts/prd_gates.py`, `scripts/prdlint/gates.py` | new |
| `scripts/prd_confirm.py` (0.7.1) | changed: `answer`, `open` and `done` subcommands beside `serve` |
| `skills/changing-prds/SKILL.md`, new `skills/changing-prds/reviewing-a-change.md`, `commands/prd-change.md` | changed: call `prd_change.py`; `--review` |
| `scripts/prdlint/hooks.py` | changed: vendors the two new scripts |

## 3. JSON output

Every JSON document is one object on stdout with `interface` and `kind` first:

```json
{"interface": 1, "kind": "lint", "prd": "orders", "version": "1.4.0",
 "findings": [{"file": "features/import.md", "line": 12, "rule": "ac-ears", "severity": "error",
               "message": "AC-012.2 must start with …"}],
 "errors": 1, "warnings": 0}
```

- `kind` is `lint`, `trace`, `status`, `context`, `change.ids`, `change.bump`, `change.record`,
  `change.approve`, `gates`, `gates.answer` or `review`.
- **lint:** as above. **trace:** the same finding shape. **status:** today's `render_json` items,
  wrapped. **context:** `{mode, area, ids, parts: [{title, file, text}]}`, the parts the text pack
  prints, in order.
- Exit codes are unchanged by `--json`. On exit 2 the document is
  `{"interface": 1, "kind": "<kind>", "error": "<first stderr line>"}`, and stderr still has the text.
- `--interface` prints the number alone and exits 0, on every script.
- **Compatibility rule:** within one `interface` number a field may be added, never removed, renamed
  or retyped. A change that breaks it raises the number, and the old number's shape stays available as
  `--json=1` for one minor toolkit release.

## 4. `prd_change.py`

`prd_change.py <subcommand> <prd dir> …` works on the PRD folder it is given, in whatever checkout or
worktree that is. It never switches branches and never pushes.

| Subcommand | Does |
|---|---|
| `ids next <prd dir> <FR\|NFR\|UJ\|AC-<nnn>\|T-<nnn>>` | prints the next free ID by the ID rules of `prd-format.md` decision 6 (removed IDs and §14 rows counted) |
| `bump <prd dir> --base <ref>` | compares the PRD folder at `<ref>` with the working tree and proposes `patch`, `minor` or `major`, with the reasons and the IDs behind each |
| `record <prd dir> --base <ref> --bump <level> --change "<text>"` | writes the new `version`, `updated` today, the §14 row (`dry-run record` left as `pending`) and the §11 rows for added, changed and removed blocks |
| `digest <prd dir>` | prints the SHA-256 of the PRD folder's content, leaving out what `record` writes (the frontmatter `version:` and `updated:` lines, the §11 and §14 tables) and `.prd-review.json`; a review verdict carries it, so an edit made after the review is caught |
| `approve <prd dir> --reply "<verbatim>" --dry-run "<record>"` | fills the §14 row's dry-run record, sets the status for an approval of a change (as `changing-prds` step 5 does), and commits the PRD folder with `Refs: none (no behaviour change)` and the reply quoted in the body |

**The bump rules**, from `changing-prds`' Version rule, decided per changed item:

| Item | Level |
|---|---|
| a new FR, NFR, UJ or AC; a new test case under a new AC | minor |
| an AC removed, or its text changed beyond wording; a changed `expect`; a removed or changed contract item; a changed error code's `status` | major |
| a new test case under an unchanged AC whose case cites an open `errors.md` entry (a regression patch) | patch |
| prose only: Flow, Edge cases, glossary meaning, a title | patch |
| a test case or contract changed to match its own unchanged AC | `needs judgment` |
| an AC whose text changed in a way the script cannot classify as wording | `needs judgment` |

"Wording" is decided mechanically and conservatively: the two texts are equal after collapsing
whitespace and case, and after removing punctuation. Anything else is a change. The highest level
wins; any `needs judgment` item makes the result `needs judgment`, with the items listed. The model
decides those in review mode (section 6); a client shows them as a decision.

`bump` prints `{level, items: [{id, file, line, change, level, reason}]}`. `record` refuses
`--bump` lower than `bump`'s level (`refused: the diff needs major, not minor`), and refuses
`needs judgment` as a level. `approve` refuses when `.prd-review.json` is missing, not `ready`, or its `digest` differs from `digest`'s; while lint exits 1, while the §14 row's dry-run record
is `pending` and the change adds or revises a non-unit T-id, on a PRD whose §14 holds no row at
1.0.0 or above (a first approval is authoring's, not a change's), and while `CLAUDE.md` has uncommitted
changes (`refused: CLAUDE.md has uncommitted changes; commit or set them aside first`); a `CLAUDE.md` that
git ignores is skipped.

`changing-prds` steps 2 and 3 call `ids next` for each new ID and `bump` then `record` for the
version; step 5 calls `approve`. The skill's Version rule table stays as the reference text for the
model, and a test holds it equal to the script's table.

## 5. `prd_gates.py`

### `list`

`prd_gates.py list <prd dir> [--worktrees]` prints every pending decision:

```json
{"interface": 1, "kind": "gates", "prd": "orders", "gates": [
  {"id": "error-class:E-003", "kind": "error-class", "title": "Importer reads the wrong key",
   "question": "Proposed class: code bug. Confirm it, or correct it to another class.",
   "evidence": ["T-012.2 fails: …"], "choices": ["confirm", "correct"], "source": "errors.md:42"}]}
```

| Kind | Pending when | `id` |
|---|---|---|
| `approval` | a review verdict file `.prd-review.json` sits in the PRD folder (untracked), `ready` is true, its `digest` equals `prd_change.py digest`, the change is recorded (the §14 last row's dry-run record is `pending`) and not yet approved | `approval:<branch>` |
| `error-class` | an `errors.md` entry's state is `proposed` | `error-class:E-nnn` |
| `deploy-step` | a deploy run's log shows it stopped at a human step with no confirmed reply | `deploy-step:<run id>:<step>` |
| `adoption` | an `extracted` area has a `.prd-confirm-<area>.json` that holds no `"done": true` | `adoption:<area>` |
| `signoff` | an acceptance case has `signoff:` and no `testing.md` Sign-offs row with a Result | `signoff:<T-id>` |

`--worktrees` also lists the `approval` gates of every worktree of the repository
(`git worktree list`), each with its path. `question` is the plain text a person answers; `evidence`
is at most 20 lines and holds no secret or classified value (the `errors.md` Evidence rule).

### `answer`

`prd_gates.py answer <prd dir> <gate id> --reply "<verbatim>" [--question "<the question shown>"] [--choice <choice>] [--class <class>] [--result pass|fail] [--item <id>] [--correction "<text>"]`

| Kind | Passes to |
|---|---|
| `approval` | `--choice approve` (the default): `prd_change.py approve` with the reply and the verdict's dry-run record. `--choice changes`: see below |
| `error-class` | `prd_error.py confirm` (`--choice correct` needs `--class`) |
| `deploy-step` | `prd_deploy.py confirm <run> <step> --reply` |
| `adoption` | `prd_confirm.py answer <area> <item> --reply` (one item per call); `--choice done` passes to `prd_confirm.py done <area>`. The gate stays until `done` |
| `signoff` | appends `\| <T-id> \| <owner> \| <date> \| <result> \|` to Sign-offs, the owner being the case's `signoff:` |

- The reply is recorded exactly as given, as each owning script already does. An empty reply is
  refused: silence answers nothing.
- Before passing an answer on, `answer` re-lists the gate. A gate that is gone, or whose `question`
  differs from the `--question` the client passes, is refused (`refused: the gate changed; list
  again`), exit 1. `--question` is optional; without it only a gone gate is refused, so every client
  (the skills, the 0.8.2 inbox) passes the question it showed. A flag that does not apply to the
  gate's kind, and a NUL in any text, are refused too.
- Answering an `error-class` or `signoff` gate changes the PRD folder's digest, so a pending approval
  gate is withdrawn until a new review.
- It prints the owning script's result as `{"interface": 1, "kind": "gates.answer", "gate": …,
  "result": {"stdout": [<lines>], "exit": <N>}}` (plus `"stderr": [<lines>]` when the owner
  printed any), and exits with the owner's exit code. `signoff` records no reply: the Sign-offs row has no column for it.
- **An `error-class` or `signoff` answer commits the owner's write** (R19), by path only
  (`git commit -- <path>`, never `-a` or `-A`, so other staged work stays staged): `errors.md` as
  `docs(prd): confirm E-nnn` with `Refs: E-nnn` (`handling-errors`' confirm commit), `testing.md` as
  `docs(prd): sign off <T-id>` with `Refs: <the case's requirement>`. An owner that exits non-zero
  commits nothing. When the commit fails (a hook rejects it), `answer` exits 1, with
  `git commit failed: <git's message>` added to `result.stderr`, and the owner's write stays in the tree
  for the user. The other kinds commit nothing here: `approve` makes its own commit, and `changes`, an
  adoption answer and a deploy confirm write untracked state.
- **The approval gate has two choices** (from the 0.8.2 decision-inbox spec §6, Ivan 2026-11-04).
  `prd_gates.py answer <prd dir> approval:<branch> --choice approve|changes --reply "<verbatim>"`,
  `approve` the default. `changes` needs a reply that is not empty. It writes
  `"owner": {"choice": "changes", "reply": "<verbatim>", "at": "<ISO>"}` into `.prd-review.json`, sets
  `ready` to `false` and appends `owner: <reply>` to `blockers`. It commits nothing and writes nothing
  under the PRD folder but that untracked file. The gate is then not pending; editing the PRD changes
  the digest, so only a new review makes it pending again. `changes` on a gate that is not pending is
  refused, as any changed gate is.
- **The adoption gate is pending until Done.** It is pending while `.prd-confirm-<area>.json` exists
  and holds no `"done": true`. `prd_confirm.py done <prd dir> <area>` sets it, and is refused (exit 1)
  while any item is open or changed since answered. `prd_gates.py answer adoption:<area> --choice done`
  passes to it; the per-item answer is unchanged.

`awaiting <who>` assumptions and §13 open questions are not gates: answering one changes the PRD, so
it is a change (section 4).

### `prd_confirm.py answer`

0.7.1's answers file `.prd-confirm-<area>.json` gains a writer that is not the local form:
`prd_confirm.py answer <prd dir> <area> <item id> --reply "<verbatim>" [--correction "<text>"]`. It
writes the same record the form's save writes, under the same file lock, so the form and another
client never lose each other's answers.

`prd_confirm.py open <prd dir> --area <area> [--summaries F]` writes the answers file with `prd`,
`area`, `commit` (HEAD), `summaries` and no answers, and the `.git/info/exclude` line. It applies the
0.7.1 summary rules (the summary names its item; at most 400 characters) and refuses an area with no
item. A file that already exists is refused (exit 1), so a second `open` never erases answers.
`serve` reads `summaries` from the file when `--summaries` is not given.

`prd_confirm.py done <prd dir> <area>` writes `"done": true` (see the adoption gate above). The
form's Done button writes it too, through the same function, once no item is open. Every writer of
the file keeps the keys it does not own (`summaries`, `done`), and an answer or an undo written after
`done` removes it, so a reopened area is pending again.

## 6. Review mode

`/prd-change --review <dir>` runs `skills/changing-prds/reviewing-a-change.md`, whose first rule is
**edit nothing**: no Write, no Edit, no Bash that writes, outside the dry-run directory the tester uses.
On the PRD folder at `<dir>` (a checkout or worktree holding the edited, not yet recorded or
recorded, change; the review reads the diff against `--base`, default the branch's upstream or `main`) it:

1. restates the change in one sentence and lists what it touches (step 1 of `changing-prds`);
2. runs `prd_links.py impact` when `links.md` has Consumers;
3. decides each `needs judgment` bump item, with its reason;
4. dry-runs the new and revised non-unit T-ids through `prd-tester` (step 4, exact-quote dismissal);
5. writes `.prd-review.json` in the PRD folder and prints it:

```json
{"interface": 1, "kind": "review", "head": "<sha>", "digest": "<prd_change.py digest>", "restate": "…", "touches": ["FR-015", "AC-015.1"],
 "impact": {"exit": 0, "lines": []}, "bump": {"level": "minor", "decided": []},
 "dry_run": {"tids": ["T-015.1", "T-015.2"], "open": 0, "dismissed": 1, "record": "dry run T-015.1, T-015.2, 0 open questions, 1 dismissed by quote"},
 "ready": true, "blockers": []}
```

The order a client runs is `bump`, then the review, then `record` with the level the verdict's
`bump.level` gives (it decides any `needs judgment` item), then lint and trace; `record` does not change
the digest, so the verdict stays valid. `ready` is false when lint fails, impact exits 1 or 3, a judgment item stays undecided, or the dry run
has an open question; `blockers` says which. A client runs it headless:
`claude -p "/prd-change --review <dir>" --output-format json` with the plugin loaded and the tools
`Read`, `Grep`, `Glob`, `Bash`, `Agent`.

## 7. Testing

- `--json` for each script: the shape, `interface`, the exit-2 document, `--interface`; the text
  output unchanged byte for byte.
- `prd_change.py`: `ids next` against removed IDs and §14-only T-ids; every bump table row with a
  fixture diff, including the conservative wording rule and `needs judgment`; `record`'s refusals and
  the rows it writes; `approve`'s refusals and its commit (message, trailer, quoted reply); the
  skill's Version table equals the script's.
- `prd_gates.py`: each kind listed from a fixture state and answered through its owner; a changed gate
  refused; an empty reply refused; `--worktrees`.
- `prd_confirm.py answer` and the form writing one file concurrently.
- The approval gate's `changes` writes the verdict and commits nothing, needs words, and is refused
  on a gate that is not pending; adoption is pending until `done`, and `done` is refused while an item
  is open; `open` refuses an existing file and an area with no item; the form and the CLI keep
  `summaries` and `done`.
- Evals: `changing-prds` calls `prd_change.py` for IDs and the bump instead of computing them; review
  mode edits nothing under pressure ("just fix the AC while you review it").

## 8. Out of scope for 0.8.1

- A long-running server; clients start one process per call.
- Writing PRD content through `prd_gates.py` (assumptions, open questions).
- Any client. The toolkit ships the interface and its tests only.
