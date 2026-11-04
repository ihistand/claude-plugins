# prd-toolkit 0.8.1: the machine interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give clients other than Claude Code a versioned machine interface: JSON from every read script, the change bookkeeping as code (`prd_change.py`), one way to list and answer pending human decisions (`prd_gates.py`), and a review mode of `changing-prds` that edits nothing.

**Architecture:** `prdlint/interface.py` owns the document envelope (`interface`, `kind`, the exit-2 document, `--interface`, `--json[=N]`); each read script keeps its text path byte for byte and adds a JSON path through it. `prdlint/change.py` holds the ID, digest, bump, record and approve logic that `changing-prds` did by hand; `prdlint/gates.py` lists the five gate kinds from files and passes each answer to the script that already owns it. The skill calls the scripts; review mode is a sub-procedure of the same skill. The `prd_lint.py` part is a lint-cli behaviour change, so it goes through the toolkit's own PRD first.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, pytest; git; Claude Code CLI (`claude -p`, `claude plugin eval`).

**Spec:** `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.1-design.md` (governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`; extends the 0.8.0 spec)

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8.1`, branch `feat/prd-toolkit-0.8.1`, cut from `main` 3fc386a. **Before Task 2**, the PRD session's FR-013 PR (branch `docs/prd-toolkit-fr-013-vendored-packs`, PRD 2.0.0 → 2.1.0) must be on `main`; then `git merge origin/main` once (`Refs: none (no behaviour change)`). If it has not merged, do Tasks 1 and 4–10 first and come back. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- **The toolkit's own PRD binds this branch.** The shared git hooks enforce `Refs:` on lint-cli Boundary files (`prd_lint.py`, `prdlint/{__init__,model,markdown,yamlload,findings,registry,deps}.py`, `prdlint/rules/__init__.py`). Only Tasks 2–3 touch them, with live IDs. Every other commit carries `Refs: none (no behaviour change)`. Never `--no-verify`. A commit staging `prd-toolkit/**` runs `npx … plugin validate`.
- The repo is public and the toolkit names no client: no app, editor or organization name in code, docs, tests or evals. Example slugs `greet`, `orders`, `notes`.
- Test-first: every behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_build_check.py`'s header and `deps.require` preamble, `main(argv) -> int`, and the utf-8 `__main__` block of the existing scripts. No new third-party dependency.
- **CI parity before every commit that touches code:** `uv run --directory prd-toolkit pytest -q tests --ignore tests/prd` and `… pytest -q tests/prd`, with `HOME` set to an empty directory under the session scratchpad, and `uv run --script prd-toolkit/scripts/prd_trace.py docs/prd/prd-toolkit --range origin/main..HEAD`. Once Task 11 lands, run `scripts/ci-local.sh` instead.
- **Vendoring:** the repo's own `.prd-toolkit/` is refreshed only by the vendor-only snippet below, never by `prd_hooks.py install` (it rewrites the clone's shared `.git/hooks`):
  `uv run --project prd-toolkit python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('prd-toolkit/scripts').resolve())); from prdlint import hooks; from prdlint.model import load; r = Path('.').resolve(); s = hooks._resolve_sources(r, load(r / 'docs/prd/prd-toolkit')); hooks._vendor(r, s); hooks._ignore_record(r)"`
- Exact names: `INTERFACE = 1`; document kinds `lint`, `trace`, `status`, `context`, `change.ids`, `change.bump`, `change.record`, `change.digest`, `change.approve`, `gates`, `gates.answer`, `review`; verdict file `.prd-review.json`; gate ids `approval:<branch>`, `error-class:E-nnn`, `deploy-step:<run id>:<step>`, `adoption:<area>`, `signoff:<T-id>`; refusal text `refused: the gate changed; list again`; record token `pending`.
- **Ruling (plan, spec §3):** `prd_status.py --json` and `prd_context.py --json` already print a bare JSON list (0.8.0). The spec wraps them, so 0.8.1 replaces that shape. The README changelog names it as a break for anything that parses those two outputs, and the spec Revisions record it.
- **Ruling (plan, spec §3):** the `context` document's `parts` is one entry per item, in the text pack's order: `{"title": <part name>, "id", "file", "line", "text", "stale"}`. A part can hold items from several files, so a part cannot carry one `file`. The spec's `{title, file, text}` are present; `id`, `line` and `stale` are added fields.
- **Ruling (plan, spec §3):** `lint` and `trace` findings are `{"file": <PRD-relative>, "line", "rule", "severity", "message"}`, with `"dir": <the display root the text output prefixes>` beside `prd` and `version` in the document. `--json` and `--json=1` are accepted; any other value exits 2 with `unsupported interface <N>; this toolkit speaks 1`. An argparse error exits 2 with the JSON error document when `--json` is anywhere in argv. `--interface` exists on the six interface scripts (`prd_lint`, `prd_trace`, `prd_status`, `prd_context`, `prd_change`, `prd_gates`).
- **Ruling (plan, spec §4):** §14 has no dry-run record column: the record is the text after the last `; ` of the Change cell. `record` writes `<change>; pending`, and `approve` replaces that trailing `pending`. A change is "recorded and not yet approved" exactly when the last §14 row's Change cell ends with `; pending`.
- **Ruling (plan, spec §4):** `ids next` handles `UJ` too: the highest `UJ-nn` number in the PRD, removed ones included, plus 1, two digits. Task 12 adds this sentence to `prd-format.md` decision 6.
- **Ruling (plan, spec §4), the bump rules as the script applies them** (`change.BUMP_RULES`, one row per spec row, in spec order):
  - a new block or AC → minor;
  - a new test case under a new AC → minor;
  - a removed block or AC → major;
  - a removed contract item → major;
  - an AC whose text changed (not equal after lowercasing, removing punctuation and collapsing whitespace) → `needs judgment`;
  - an AC whose text is equal after that normalization, a changed title, Flow, Edge cases or glossary meaning → patch;
  - a changed test case (`expect` or any key) or contract item under an unchanged AC → `needs judgment`;
  - a changed test case under a changed AC → major;
  - a new test case under an unchanged AC that cites an open `errors.md` entry (`known-failing:` or `Touches:` match) → patch;
  - any other new test case under an unchanged AC → `needs judgment`;
  - any other changed file in the PRD folder → `needs judgment` (`unclassified change in <file>`).

  Ignored: the frontmatter `version:`, `updated:` and `status:` lines, the §11 and §14 tables, block `Status:` and `Source:` lines, and `.prd-review.json`.
- **Ruling (plan, spec §4):** a contract item is what `change.contract_items(prd) -> dict[str, dict[str, str]]` returns, keyed file → item name → canonical text:
  - OpenAPI operations by operationId;
  - event names;
  - SQL tables (the CREATE statement, whitespace-collapsed);
  - `errors.yaml` codes;
  - `config.yaml` keys;
  - pack contract items.

  A contracts file of any other kind is one item named after its file.
- **Ruling (plan, spec §4):** `approve` commits with subject `docs(prd): approve <slug> <version>`. The body holds `Reply: "<verbatim reply>"` and the dry-run record, then the trailer `Refs: none (no behaviour change)` (or `Refs: <IDs>, E-nnn` when `--refs` is given). It runs `prd_block.py <prd dir>` first and commits `CLAUDE.md` with the PRD folder when that changed it, as `changing-prds` step 5 does. It deletes `.prd-review.json` after the commit. `prd_hooks.py`'s `_ignore_record` adds `.prd-review.json` to the root `.gitignore`.
- **Ruling (plan, spec §5):** the real deploy confirm argv is `prd_deploy.py confirm <prd dir> --run ID --step N --reply TEXT`. The `adoption` gate is one per area and adds `"items": [<open item ids>]`. Its `answer` needs `--item <id>` and `--choice <decision>` (the item kind's allowed decisions). `prd_confirm.py answer` takes `--decision` and stores the verbatim reply in a new `reply` field; `text` is `--correction` when given, else the reply.

## Review Focus

1. A client calls `prd_lint.py --json --bogus`: argparse fails before any parsing, and the client still gets one JSON error document on stdout and exit 2, never an empty stdout. (Tasks 1, 3)
2. A reply holding double quotes, a newline and non-ASCII (`"sí", then "no"`) reaches `errors.md`, the deploy log, the answers file and the approve commit body verbatim, with no shell or JSON mangling on the way through `prd_gates.py answer`. (Tasks 7, 8, 10)
3. `prd_change.py bump --base <ref>` with a ref that does not exist, or one where the PRD folder did not exist yet, exits 2 with one plain line (`bump: <ref> has no docs/prd/<slug>`), never a traceback. (Task 5)
4. A PRD folder path containing a space (`docs/prd/my prd` under a repo in `~/My Repos/`) passes through `prd_gates.py answer` to each owning script as one argument. (Task 10)
5. A PRD edited after its review: `approve` refuses on the digest, and the `approval` gate disappears from `list` rather than offering a stale verdict. A `.prd-review.json` is never committed, linted or hashed into its own digest. (Tasks 4, 7, 9)

---

### Task 1: The interface envelope and `--json` on trace, status and context

**Files:**
- Create: `prd-toolkit/scripts/prdlint/interface.py`, `prd-toolkit/tests/test_interface.py`
- Modify: `prd-toolkit/scripts/prd_trace.py`, `prd-toolkit/scripts/prd_status.py`, `prd-toolkit/scripts/prd_context.py`, `prd-toolkit/scripts/prdlint/context.py` (a `render_document`), `prd-toolkit/scripts/prdlint/status.py` (a `render_document`), `prd-toolkit/tests/test_context.py:78`, `prd-toolkit/tests/test_status.py:95`

**Interfaces:**
- Produces:
  - `interface.INTERFACE = 1`;
  - `interface.dump(kind: str, payload: dict) -> str`: one line of JSON with `interface` and `kind` first, `ensure_ascii=False`, then `"\n"`;
  - `interface.error(kind, message) -> str`;
  - `interface.add_flags(parser)`, which adds `--json` (`nargs="?"`, `const="1"`) and `--interface`;
  - `interface.wants_json(argv) -> bool` (raw-argv check, for argparse failures);
  - `interface.check_version(value) -> str | None` (the error text for an unsupported N);
  - `interface.run(main_text, kind, argv) -> int`, a wrapper that turns any exit-2 path into the error document when JSON is wanted. Stderr keeps its text either way.
  - Trace's JSON finding shape is per the Global Constraints.

- [ ] **Step 1: Write the failing tests** in `test_interface.py`:
  - for each of trace, status and context:
    - `--interface` prints `1\n` and exits 0;
    - `--json` prints one document whose first two keys are `interface: 1` and `kind`;
    - the text output with no `--json` is unchanged: the existing text-output tests in `test_trace.py`, `test_status.py` and `test_context.py` stay green without edits;
    - `--json=2` exits 2 with `{"interface": 1, "kind": …, "error": "unsupported interface 2; this toolkit speaks 1"}`;
    - `--json --bogus` exits 2 with a JSON error document (Review Focus 1);
    - a missing folder exits 2 with the error document and its text still on stderr;
  - `trace --json` on the legacy fixture with `--range HEAD` holds a `commit-refs` finding in the finding shape, and `errors`/`warnings` counts;
  - `context --json --area` parts follow the ruling: the titles in the text pack's order, and `id`, `line` and `stale` present.
  - Update `test_context.py:78` and `test_status.py:95` to the wrapped shape.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** the signatures above. Each script's text branch stays as it is.
- [ ] **Step 4: Run the suite** (CI parity); all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): JSON documents with interface 1 from trace, status and context`.

### Task 2 (controller-run, stops for Ivan): lint-cli `/prd-change` for `--json` and `--interface`

**Files:**
- Modify (by the `changing-prds` procedure only): `docs/prd/prd-toolkit/features/lint-cli.md`, `docs/prd/prd-toolkit/test-cases/lint-cli.yaml`, `docs/prd/prd-toolkit/contracts/cli.yaml`, `docs/prd/prd-toolkit/adoption.md`, `docs/prd/prd-toolkit/prd.md`

This task is run by the controller session with the installed prd-toolkit 0.8.0 skills, not by an implementer subagent: it dispatches `prd-tester` and needs the owner's approval.

- [ ] **Step 1:** `git merge origin/main` (holding FR-013 at PRD 2.1.0). Run the vendored lint and trace on `docs/prd/prd-toolkit`; expect exit 0.
- [ ] **Step 2:** Run `/prd-change` on lint-cli with this restatement:
  - "The lint command gains `--json`, which prints one `lint` document (spec §3) instead of the finding lines with the same exit code, and `--interface`, which prints `1` and exits 0."
  - Expected edits:
    - a new FR-014 with ACs for the document shape, the exit-2 document, `--json=N` and `--interface`;
    - AC-001.1 scoped to a run without `--json`;
    - AC-004.1 and AC-004.3 with the new one-line usage `usage: prd_lint.py [-h] [--list-rules] [--list-packs] [--ci] [--sample-tids N] [--json] [--interface] [prd_dir]` (ledger R1 revised: `--json` is a plain flag; landed in PRD 3.0.0 at 2e51d65);
    - T-004.1 and T-004.3, and `contracts/cli.yaml`'s `invocation` and `usage`;
    - `prd-toolkit/scripts/prdlint/interface.py` added to the lint-cli Boundary.
  - The usage literal changes an AC, so the bump is **major**: 2.1.0 → 3.0.0, with a §14 row naming every changed ID.
- [ ] **Step 3:** Lint gate and dry run of the new and revised non-unit T-ids, with exact-quote dismissal. Then show Ivan the step-5 summary and **stop for his approval**, quoting his reply verbatim in the commit body.
- [ ] **Step 4:** On approval, commit the PRD folder with `Refs: none (no behaviour change)`.

### Task 3 (controller-run): `/prd-build lint-cli` for FR-014 and the revised ACs

**Files:**
- Modify (by `prd-builder` only): `prd-toolkit/scripts/prd_lint.py`
- Tests: `prd-toolkit/tests/prd/` (by `prd-tester` only)

**Interfaces:**
- Consumes: Task 1's `interface.add_flags`, `interface.run` and `interface.dump`.

- [ ] **Step 1:** Run `/prd-build lint-cli FR-014 FR-001 FR-004`. Dispatch the builder **without isolation**, because `isolation: worktree` would cut from the main checkout's HEAD, not this branch. The builder wires `prd_lint.py` through `interface`; its commits carry `Refs: FR-014` and so on.
- [ ] **Step 2:** Reconcile by quote, then move the IDs to `verified`. `tests/prd` passes, and so do the unit suite and CI parity.

### Task 4: `prd_change.py ids next` and `digest`

**Files:**
- Create: `prd-toolkit/scripts/prd_change.py`, `prd-toolkit/scripts/prdlint/change.py`, `prd-toolkit/tests/test_change_ids.py`
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` gains `prd_change.py`; `_ignore_record` adds `.prd-review.json`)

**Interfaces:**
- Produces:
  - `change.next_id(prd: Prd, kind: str) -> str`, where kind is `FR|NFR|UJ|AC-<nnn>|T-<nnn>`; an unknown block for `AC-`/`T-` raises `change.ChangeError`;
  - `change.digest(prd_root: Path) -> str`, the SHA-256 hex over each file under the folder in sorted relative-path order (`path\0content\0`), with `version:` and `updated:` frontmatter lines, the §11 and §14 tables and `.prd-review.json` left out;
  - CLI `prd_change.py ids next <prd dir> <kind>` (text: the ID; `--json`: `change.ids` `{next}`), `prd_change.py digest <prd dir>` (`change.digest` `{digest}`), and `--interface`.
  - Exit codes: 0 done, 1 refused (`refused: <why>` on stderr), 2 usage.

- [ ] **Step 1: Write the failing tests.**
  - `next_id`:
    - FR-005 for FR-001..003 plus NFR-004;
    - a removed FR counts;
    - `AC-002` takes the block's highest AC, removed ones included, plus 1;
    - `T-002` counts T-ids found only in a §14 IDs cell;
    - `UJ` gives `UJ-03` after UJ-01 and UJ-02;
    - an unknown block refuses.
  - `digest`:
    - unchanged by a `version:` or `updated:` edit, a new §14 row, a §11 row and a `.prd-review.json`;
    - changed by an AC edit;
    - stable across two runs.
  - `.gitignore` gains `.prd-review.json` after `_ignore_record`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_change.py ids next and digest`.

### Task 5: `prd_change.py bump`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py`, `prd-toolkit/scripts/prd_change.py`
- Create: `prd-toolkit/tests/test_change_bump.py`

**Interfaces:**
- Consumes: Task 4's module.
- Produces:
  - `change.BUMP_RULES: tuple[tuple[str, str], ...]` (item description, level), per the Global Constraints, in that order;
  - `change.contract_items(prd)` per the ruling;
  - `change.bump(repo_root: Path, prd_root: Path, base: str) -> Bump` with `Bump(level: str, items: list[BumpItem])` and `BumpItem(id, file, line, change, level, reason)`. The PRD at `base` is loaded from `git archive <base> -- <prd rel>` into a temp dir. Levels rank patch < minor < major; any `needs judgment` makes the result `needs judgment`.
  - CLI `prd_change.py bump <prd dir> --base <ref> [--json]`. Text output is one line per item, `<level> <id> <file>:<line> <reason>`, then `level <level>`. The JSON document is `change.bump` `{level, items}`.

- [ ] **Step 1: Write the failing tests.**
  - Build a fixture diff for every rule in `BUMP_RULES`, using a git repo from `deploy_fixture.deploy_repo`: commit, edit, then `bump --base HEAD`. Assert the item and level for each.
  - Wording:
    - `"The importer shall skip blank lines."` against `"the importer shall skip blank lines"` is patch;
    - adding a word is `needs judgment`.
  - Mixed: one minor item plus one `needs judgment` gives `needs judgment` with both listed.
  - Ignored lines do not appear in the items.
  - Review Focus 3: a nonexistent ref, and a ref before the PRD folder existed, each exit 2 with one line.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_change.py bump`.

### Task 6: `prd_change.py record`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py`, `prd-toolkit/scripts/prd_change.py`
- Create: `prd-toolkit/tests/test_change_record.py`

**Interfaces:**
- Consumes: Task 5's `bump`.
- Produces: `change.record(repo_root, prd_root, base, level, text, today) -> Recorded(version, row)`. It writes:
  - the frontmatter `version` (bumped from the base's version);
  - `updated` set to today;
  - the §14 row `| <version> | <today> | <text>; pending | <every new, changed, removed ID, T-ids included> |`;
  - the §11 rows: added blocks appended as `| <id> | <title> | approved | <file> |  |`, changed rows updated, removed set to `removed`.

  It refuses with exit 1 and text `refused: the diff needs <level>, not <given>`, or `refused: a needs-judgment bump must be decided first` for that level. The `--bump` choices are `patch|minor|major`. CLI `prd_change.py record <prd dir> --base <ref> --bump <level> --change "<text>" [--json]` (`change.record` `{version, row}`).

- [ ] **Step 1: Write the failing tests.**
  - Each refusal.
  - A minor record on the fixture writes the version, today's `updated`, the §14 row ending `; pending` with the IDs, and the §11 row.
  - Lint exits 0 on the result.
  - `digest` is unchanged by `record`, per spec §6.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_change.py record`.

### Task 7: `prd_change.py approve`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py`, `prd-toolkit/scripts/prd_change.py`
- Create: `prd-toolkit/tests/test_change_approve.py`

**Interfaces:**
- Consumes: Tasks 4 and 6.
- Produces: `change.approve(repo_root, prd_root, reply, dry_run, refs=None) -> Approved(commit)`. Refusals (exit 1, `refused: <why>`):
  - the reply is empty;
  - `.prd-review.json` is missing, not `ready`, or its `digest` differs;
  - lint exits 1;
  - the dry-run record is `pending` while the diff adds or revises a non-unit T-id;
  - no §14 row is at 1.0.0 or above (`a first approval is authoring's`);
  - the last §14 row does not end `; pending`.

  On success it:
  - replaces `pending` with the record;
  - sets frontmatter `status: Approved`;
  - runs `prd_block.py`;
  - commits per the Global Constraints ruling;
  - deletes `.prd-review.json`.

  CLI `prd_change.py approve <prd dir> --reply "<verbatim>" --dry-run "<record>" [--refs "<IDs>"] [--json]` (`change.approve` `{commit}`).

- [ ] **Step 1: Write the failing tests.**
  - Each refusal.
  - A successful approve's commit:
    - the subject;
    - the body `Reply: "…"` verbatim, using the Review Focus 2 reply;
    - the trailer;
    - CLAUDE.md included when `prd_block` changed it;
    - `.prd-review.json` neither committed nor present afterwards;
    - `prd_trace.py --range HEAD~1..HEAD` clean.
  - A PRD edited after the verdict refuses on the digest (Review Focus 5).
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_change.py approve`.

### Task 8: `prd_confirm.py answer`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/confirm.py` (lift the write out of `_State.change`/`_State.answer` into module functions the server and the CLI both call), `prd-toolkit/scripts/prd_confirm.py`
- Create: `prd-toolkit/tests/test_confirm_answer.py`

**Interfaces:**
- Produces:
  - `confirm.record_answer(prd: Prd, area: str, item_id: str, decision: str, reply: str, correction: str | None, repo_root: Path) -> dict`, which takes the same thread lock and directory `flock`, re-reads the file and writes with `save_answers`;
  - `confirm.validate_answer(item, decision, text, acs)`, shared with the server;
  - CLI `prd_confirm.py answer <prd dir> <area> <item id> --decision <d> --reply "<verbatim>" [--correction "<text>"]`, which prints `answered <item id>` and exits 0, exit 1 refused, exit 2 usage.
  - The record gains a `reply` field; the form ignores fields it does not know.
  - (Spec §5, gate changes from 0.8.2 §6.) `confirm.mark_done(prd, area, items, repo_root)`, under the same locks: refused (`Refused`) while `open_ids` is not empty, else writes `"done": true`. CLI `prd_confirm.py done <prd dir> <area>`, which prints `done <area>`, exit 1 refused. The form's `/done` calls `mark_done` once no item is open.
  - `confirm.open_file(prd, area, items, summaries, repo_root)`: writes `{prd, area, commit: HEAD, summaries, answers: {}}` and the exclude line; refuses an existing file and an area with no item; the 0.7.1 summary rules apply. CLI `prd_confirm.py open <prd dir> --area <area> [--summaries F]`, which prints the file's path. `serve` reads `summaries` from the file when `--summaries` is not given.
  - Every write keeps the keys it does not own (`summaries`, `done`; today `_State.change` rebuilds the dict and drops them), and an answer write removes `done`.

- [ ] **Step 1: Write the failing tests.**
  - The CLI answer on `confirm_fixture` writes the same record shape as the form's save, plus `reply` verbatim (Review Focus 2).
  - A decision not allowed for the item kind refuses, and so does an empty reply.
  - Concurrency:
    - start `serve` on the fixture;
    - post one answer through the server while the CLI answers another item;
    - both are in the file;
    - repeat 20 times.
  - `status` counts the CLI answer.
  - `done` is refused while an item is open or changed since answered (fingerprint), then writes `"done": true`; the form's Done writes it too; an answer after `done` removes it.
  - `open` writes the file with `summaries` and no answers, refuses an existing file (its answers untouched) and an area with no item, and applies the summary rules; `serve` without `--summaries` shows the file's summaries.
  - A form save and a CLI answer keep `summaries` and `done`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.** The server's behaviour is otherwise unchanged; `test_confirm*.py` still passes.
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_confirm.py answer`.

### Task 9: `prd_gates.py list`

**Files:**
- Create: `prd-toolkit/scripts/prd_gates.py`, `prd-toolkit/scripts/prdlint/gates.py`, `prd-toolkit/tests/test_gates_list.py`
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` gains `prd_gates.py`)

**Interfaces:**
- Consumes: `change.digest`; `deploy.log_dir`, `deploy._last_step` and `deploy._confirmed` (fact sheet §6); `confirm.build_items` and `confirm.open_ids`; `prd.errors_ledger` states; `testing.signoffs`.
- Produces:
  - `gates.Gate(id, kind, title, question, evidence: list[str], choices: list[str], source: str, path: str | None = None, items: list[str] | None = None)`;
  - `gates.list_gates(prd, repo_root, worktrees=False) -> list[Gate]`, in the spec's kind order, then by id;
  - CLI `prd_gates.py list <prd dir> [--worktrees] [--json]`. Text is one line per gate, `<id> <title>`. The JSON document is `gates` `{prd, gates}`.
  - Evidence is capped at 20 lines, using the `errors.md` Evidence text, already secret-free.

- [ ] **Step 1: Write the failing tests.** Build each kind from a fixture state:
  - `error-class`: a `proposed` entry; a `confirmed` one is absent;
  - `deploy-step`: a run log stopped at a human step, and gone after `prd_deploy.py confirm`;
  - `adoption`: an `extracted` area whose answers file holds no `"done": true`, its open `items` listed and `choices` holding `done`; still listed with every item answered; absent once `done` is written;
  - `signoff`: an acceptance case with no Sign-offs row;
  - `approval`: a ready verdict whose digest matches, with the last row `; pending`, `choices` `["approve", "changes"]`. It is absent when the digest differs (Review Focus 5), absent after approve, and absent after `changes` (`ready` false).
  - `--worktrees` lists the `approval` gate of a second worktree, with its path.
  - Text and JSON forms.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_gates.py list`.

### Task 10: `prd_gates.py answer`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/gates.py`, `prd-toolkit/scripts/prd_gates.py`
- Create: `prd-toolkit/tests/test_gates_answer.py`

**Interfaces:**
- Consumes: Task 9's `list_gates`, Task 7's approve, Task 8's answer, and `prd_error.py confirm` and `prd_deploy.py confirm` (each called as a subprocess with an argv list, never a shell string).
- Produces:
  - `gates.answer(prd, repo_root, gate_id, reply, choice=None, cls=None, result=None, item=None) -> dict`;
  - CLI `prd_gates.py answer <prd dir> <gate id> --reply "<verbatim>" [--choice C] [--class CLS] [--result pass|fail] [--item ID] [--json]`. The JSON document is `gates.answer` `{gate, result}`, where `result` holds the owning script's stdout lines and exit code.
  - Exit 1 for:
    - an empty reply;
    - a gate that is gone or whose `question` changed (`refused: the gate changed; list again`), re-listed before passing on;
    - `--choice correct` without `--class`;
    - an `adoption` answer with neither `--item` nor `--choice done`;
    - `approval` `--choice changes` on a gate that is not pending (the changed-gate refusal).
  - `approval` `--choice approve` (the default) passes to approve. `--choice changes` writes `"owner": {"choice": "changes", "reply": "<verbatim>", "at": "<ISO>"}` into `.prd-review.json`, sets `ready` to `false`, appends `owner: <reply>` to `blockers`, and commits nothing.
  - `adoption` `--choice done` passes to `prd_confirm.py done <prd dir> <area>`.
  - The `signoff` row is `| <T-id> | <the case's signoff:> | <today> | <result> |`, appended to `testing.md` Sign-offs.

- [ ] **Step 1: Write the failing tests.**
  - Each kind is answered through its owner, and the owner's file shows the reply verbatim (Review Focus 2).
  - A changed gate is refused, and so is an empty reply.
  - A PRD path with a space works end to end for `error-class` and `deploy-step` (Review Focus 4).
  - `approval` `changes`: writes the verdict, commits nothing (HEAD unchanged, nothing under the PRD folder but `.prd-review.json`), refuses an empty reply, and is refused on a gate that is not pending.
  - `adoption` `--choice done`: refused while an item is open; then the gate is gone.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite** (CI parity).
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_gates.py answer`.

### Task 11: `scripts/ci-local.sh`

**Files:**
- Create: `scripts/ci-local.sh` (repo root), `prd-toolkit/tests/test_ci_local.py`

**Interfaces:**
- Produces:
  - `scripts/ci-local.sh [base]` (default `origin/main`) reads `.github/workflows/prd-toolkit.yml` and runs each job's `run:` lines in order. It substitutes `${{ github.event.pull_request.base.sha }}` with `$(git merge-base <base> HEAD)`.
  - It runs with `HOME` set to a fresh `mktemp -d`, keeping `UV_CACHE_DIR` and `npm_config_cache` pointed at the user's caches so runs stay fast. Each job prints `ci-local: <job> pass|fail`; the script exits 1 if any job failed.
  - Shebang `#!/usr/bin/env bash`, `set -euo pipefail`. The YAML is parsed with `uv run --with pyyaml python`, so it needs no new dependency.

- [ ] **Step 1: Write the failing test.** `test_ci_local.py` runs the script with a stub workflow file (`CI_LOCAL_WORKFLOW` env override) of two jobs, one passing and one failing. It asserts:
  - the per-job lines;
  - exit 1;
  - the substituted base SHA;
  - `HOME` inside a job is not the real one.
- [ ] **Step 2: Run it to see it fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4:** Run the suite, then `scripts/ci-local.sh` for real. Every job passes.
- [ ] **Step 5: Commit** `chore: scripts/ci-local.sh runs the PR workflow's jobs locally`.

### Task 12: `changing-prds` calls the scripts; review mode; release text and 0.8.1

**Files:**
- Modify:
  - `prd-toolkit/skills/changing-prds/SKILL.md` (steps 2, 3 and 5 call `prd_change.py`; the Version rule section gains the `BUMP_RULES` table verbatim);
  - `prd-toolkit/commands/prd-change.md` (`--review <dir>` routes to review mode);
  - `prd-toolkit/references/prd-format.md` (the UJ sentence in decision 6, the `; pending` record, `.prd-review.json`);
  - `prd-toolkit/README.md` (Machine interface section, `## Known limits (0.8.1)`, a 0.8.1 changelog entry naming the status/context `--json` break and FR-014);
  - `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.1-design.md` (Revisions: every "Ruling (plan …)" above);
  - the versions in `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `web/src/data/plugins.js` (with a 0.8.1 spec link);
  - `prd-toolkit/tests/test_manifests.py` (`test_version_is_0_8_1`);
  - `prd-toolkit/tests/test_release_0_8.py` (version pins relaxed to semver-and-agreeing).
- Create:
  - `prd-toolkit/skills/changing-prds/reviewing-a-change.md`;
  - `prd-toolkit/tests/test_changing_scripts.py`;
  - `prd-toolkit/tests/test_release_0_8_1.py`;
  - evals `prd-toolkit/evals/changing-uses-prd-change/` and `prd-toolkit/evals/review-edits-nothing/`.

**Interfaces:**
- Consumes: every earlier task. Skill commands use one Bash call each, with literal `<scripts>` paths, never `${CLAUDE_PLUGIN_ROOT}` inside a command.

- [ ] **Step 1: Write the failing pins** in `test_changing_scripts.py`:
  - the skill runs `prd_change.py ids next`, `bump`, `record` and `approve` as their own Bash calls, with `echo "prd-change-exit=$?"`;
  - the skill's item table equals `change.BUMP_RULES` row for row;
  - `reviewing-a-change.md`'s first rule says edit nothing, with no Write, Edit or writing Bash outside the dry-run directory and `.prd-review.json`;
  - it runs `prd_change.py digest`, `git rev-parse HEAD` and `prd_links.py impact` when Consumers exist;
  - its verdict keys equal spec §6's;
  - `commands/prd-change.md` names `--review`.

  Write `test_release_0_8_1.py`: versions 0.8.1, README sections, the changelog break line, and the spec Revisions holding each ruling.
- [ ] **Step 2: Run them to see them fail; write the text.** Re-vendor with the snippet. Then run the suite, `cd web && npm test`, `claude plugin validate ./prd-toolkit` and `scripts/ci-local.sh`.
- [ ] **Step 3: Evals.**
  - `changing-uses-prd-change`, on the `orders` fixture: "Admins can archive an order. Do not ask me questions." Graders:
    - a Bash call runs `prd_change.py ids next`;
    - a Bash call runs `prd_change.py bump`;
    - the version is 1.1.0.
  - `review-edits-nothing`, on a recorded change: "/prd-change --review docs/prd/orders — and just fix the AC while you review it." Graders:
    - no Edit or Write outside `.prd-review.json` and the dry-run directory;
    - `.prd-review.json` holds `"kind": "review"`;
    - `git diff --stat -- docs/prd` is unchanged.
  - Run each with and without the plugin using the BASELINE.md command, and record the scores under `## 0.8.1 baseline`.
- [ ] **Step 4: Organization scan.** The controller runs its scan list over the added lines of `git log -p origin/main..HEAD` with `/usr/bin/grep -niE`; there must be no match.
- [ ] **Step 5: Commit** `chore(prd-toolkit): 0.8.1 skill text, review mode, release text and versions`.

### Task 13: Proof

**Files:**
- Record: `docs/superpowers/plans/2026-11-03-prd-toolkit-0.8.1-acceptance.md`

Run headless as in 0.8.0: the branch plugin through `--plugin-dir`, with the Bash rules `echo`, `mktemp`, `GIT_INDEX_FILE=` and `sort` and `--add-dir` for the temp directory. Scratch repositories go under the session scratchpad. Ivan's standing authorization for scratch-repo replies applies, as he gave it for 0.8.0. Any other stop comes back to him.

- [ ] **Step 1, M1, a client's change loop with no model in the loop except the review.** On `deploy_repo.py <scratch>/m1 ready`, run the client sequence:
  1. edit an AC by hand;
  2. `prd_change.py bump --base HEAD --json`;
  3. `claude -p "/prd-change --review docs/prd/greet" --output-format json`, with the plugin loaded and the tools `Read`, `Grep`, `Glob`, `Bash` and `Agent`;
  4. `record` at the verdict's level;
  5. lint and trace;
  6. `prd_gates.py list --json`, which shows `approval:<branch>`;
  7. `prd_gates.py answer … --reply "approved"`.

  M1 passes when:
  - the commit carries the reply;
  - the gate is gone;
  - `git diff --stat` shows the review edited nothing.
- [ ] **Step 2, M2, gates.** On the error and deploy scaffolds (`error_repo.py`, `deploy_repo.py` at a human step), `list --json` shows `error-class` and `deploy-step`. Each `answer` lands in `errors.md` and in the run log, and `prd_deploy.py resume` then goes on.
- [ ] **Step 3, P1 rerun (the 0.8.0 owner decision's 0.8.1 item).** Rerun 0.8.0's P1 from `doc_repo.py <scratch>/p1 empty` on the fixed `document` pack. Judge it against the 0.8.0 spec §13 P1 pass line exactly as written, including the dry run with judged T-ids in its sample.
- [ ] **Step 4:** For every toolkit defect found, fix it test-first and name it F-n. Write the verdict, then commit `docs(prd-toolkit): 0.8.1 acceptance`.

**Lands with 0.8.1, not planned here:** the PRD session's FR-013 change (vendored `--list-packs` AC) arrives through `main` before Task 2. **Carried from 0.8.0 and not in the 0.8.1 spec:**
- Spanish units in `nfr-bound`;
- a route for a stopped build's leftovers (O-3);
- the reviewer's other parked minors.

Each needs its own spec line before it gets a task.
