# prd-toolkit 0.7.1: a confirmation form for adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace adoption step 3's long markdown checklist with a local form that shows one item at a time, saves each answer as it is given and tells the session when the owner is done.

**Architecture:** `prdlint/confirm.py` builds an area's items from the loaded PRD, validates the summaries file, fingerprints each item, keeps the answers file and runs a standard-library HTTP server bound to `127.0.0.1` with a token; `prd_confirm.py` is its thin CLI. The page `templates/confirm/form.html` is one self-contained file that talks to the server's four JSON requests. The adopting-prds skill runs `serve` in the background and applies the answers file under step 3's existing rules.

**Tech Stack:** Python 3.11+ (`uv run --script`), the standard library's `http.server`, `secrets`, `hashlib`, `json`; pyyaml (already a dependency); pytest; plain HTML, CSS and JavaScript with no library.

**Spec:** `docs/superpowers/specs/2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md`

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-confirm`, branch `feat/prd-toolkit-confirm-form`. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and carries `Refs: none`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- The repo is public and the toolkit platform-neutral: no organization names, hosts, users or people in code, tests, evals or docs, in any form.
- Test-first: every behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_build_check.py`'s header and `deps.require` preamble. Exit codes, exactly: 0 Done (every item answered, none changed since answered); 2 usage or tool error with nothing on stdout; 3 stopped without Done (Ctrl-C or the idle timeout). Refusals print `prd_confirm: <why>` on stderr.
- The server binds `127.0.0.1` only. Every request carries `token=<token>` (query string for `GET /`, query string or `X-Prd-Token` header for the JSON requests); without it: 403 and no change. The first stdout line of `serve` is exactly `url=http://127.0.0.1:<port>/?token=<token>`.
- The answers file is `.prd-confirm-<area>.json` at the repository root, rewritten whole through a temporary file in the same folder and `os.replace` on every change; its shape and `decision` values are spec §5's, exactly: `confirm`, `correct`, `bug`, `ask`, `intended`, `answer`, `fix`.
- `serve` adds the line `/.prd-confirm-*.json` to `.git/info/exclude` once (at the common git dir), never twice.
- Summaries: a JSON object mapping item ID to text; refused (exit 2) when a key is not an item (`summary for <ID> names no item of <area>`), when the text does not contain its own key (`summary for <ID> does not mention <ID>`), or when it is over 400 characters (`summary for <ID> is over 400 characters`).
- Code excerpts: the `Source:` line's file at its commit through `git show <commit>:<file>`, the cited line and ten lines either side, each line prefixed with its number.
- The page loads nothing: no `<script src`, `<link`, `@import` or `url(`; all item text is set with `textContent` (or `createTextNode`), never `innerHTML` with item data.
- `--idle-minutes` defaults to 120; the server exits 3 after that long without a request.
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.

## Review Focus

1. Item text holding HTML or script (`<script>`, `</div>`, quotes, a backslash) in an AC, a title or a code excerpt: it shows as literal text on the card and runs nothing. (Task 4)
2. Two `serve` runs at once on the same area, or the browser posting while a write is in progress: the answers file is always valid JSON with every answer the server accepted, never a half-written file. (Task 2)
3. An area whose `Source:` line names a commit or a file git no longer has: that item's excerpt reads `(code not available at <commit>)` and the item is still served and answerable. (Task 1)
4. A port the owner gives with `--port` that is in use: exit 2 with `prd_confirm: port <N> is in use`, nothing served; with no `--port`, a free port is always found. (Task 3)
5. A saved answer whose item text changed between two `serve` runs: the item shows "changed since you answered", counts as open, and Done is refused until it is answered again. (Task 2)

---

### Task 1: Items, summaries and fingerprints

**Files:**
- Create: `prd-toolkit/scripts/prdlint/confirm.py`
- Create: `prd-toolkit/tests/confirm_fixture.py` (helper), `prd-toolkit/tests/test_confirm_items.py`

**Interfaces:**
- Consumes: `model.load(prd_dir)`; `Prd.blocks` (`ReqBlock.id`, `title`, `file`, `status`, `acs`, `source`, `lines`), `Prd.errors_ledger` (`ErrorEntry.id`, `title`, `open`, `touches`, `detected`, `diagnosis`), `Prd.sections` (§13 by `number == 13`), `Prd.adoption`, `Prd.yaml`, `Prd.test_cases`; `model.repo_root(path)`.
- Produces:
  - `@dataclass Item(id: str, kind: str, title: str, text: str, acs: list[tuple[str, str]], excerpts: list[str], fingerprint: str, where: str)` — `kind` in `requirement`, `bug`, `question`, `marker`; `where` the source location shown on the card (`prd-toolkit/scripts/prd_lint.py:65`, `errors.md`, `prd.md §13`, `contracts/config.yaml PRD_LINT_CI.owner`).
  - `build_items(prd: Prd, area: str) -> list[Item]` in spec §3's order; raises `Refused(<why>)` for an unknown area (`area <area> is not in adoption.md`) or none (`area <area> has no item to confirm`).
  - `load_summaries(path: Path, items: list[Item], area: str) -> dict[str, str]` raising `Refused` per the Global Constraints messages.
  - `class Refused(Exception)`.
- `tests/confirm_fixture.py`: `make_confirm_repo(tmp_path) -> tuple[Path, Path]` — a git repository holding a small `src/notes/app.py` and a PRD `docs/prd/notes` with an `adoption.md` area `notes` (`extracted`), two `as-built` FR blocks whose `Source:` lines cite that file at the repo's commit, one `approved` FR block (not an item), an open E-001 touching one FR, a resolved E-002, a §13 bullet naming one FR and one naming no FR of the area, and a `contracts/config.yaml` setting whose `owner` is a `[NEEDS CLARIFICATION: …]` marker named on one block's `Traces:` line. Returns (repo root, PRD folder).

- [ ] **Step 1: Write the failing tests** in `tests/test_confirm_items.py`:

```python
def test_items_in_order(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    assert [(i.id, i.kind) for i in items] == [("FR-001", "requirement"), ("FR-002", "requirement"),
                                               ("E-001", "bug"), ("Q-01", "question"),
                                               ("config.yaml:NOTES_LIMIT.owner", "marker")]

def test_requirement_item_carries_acs_and_excerpt(tmp_path): ...   # acs == [(AC id, text), ...]; excerpts[0] holds "  13 | " numbered lines from git show at the Source commit
def test_missing_commit_or_file(tmp_path): ...                      # Review Focus 3: a Source @deadbee → excerpt "(code not available at deadbee)", item still built
def test_not_as_built_and_resolved_are_not_items(tmp_path): ...     # FR-003 approved and E-002 resolved are absent
def test_unknown_or_empty_area(tmp_path): ...                       # Refused("area x is not in adoption.md"); an area with no as-built block and nothing else → "has no item to confirm"
def test_fingerprint_changes_with_text(tmp_path): ...               # editing FR-001's AC text changes FR-001's fingerprint only
def test_summaries_rules(tmp_path): ...                             # the three refusals, exact messages; a good file returns the mapping
```

- [ ] **Step 2: Run them to see them fail** (`ModuleNotFoundError: prdlint.confirm`).
- [ ] **Step 3: Implement `confirm.py`'s items part.** A marker item's ID is `<contract file name>:<key path>`; the fingerprint is `hashlib.sha256` of the item's served text (block lines, entry lines, bullet, marker line) as UTF-8, hex.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): confirmation items, summaries and fingerprints`.

### Task 2: The answers file and the server

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/confirm.py`
- Test: `prd-toolkit/tests/test_confirm_server.py`

**Interfaces:**
- Consumes: Task 1's `Item`, `build_items`.
- Produces:
  - `answers_path(repo_root: Path, area: str) -> Path`; `load_answers(path: Path) -> dict`; `save_answers(path: Path, data: dict) -> None` (atomic, Global Constraints).
  - `REQUIRES_TEXT = {"correct", "bug", "ask", "answer"}` — `correct` is satisfied by text or by a non-empty `acs`.
  - `open_ids(items: list[Item], answers: dict) -> list[str]` — items with no answer or whose answer's fingerprint differs.
  - `make_server(prd: Prd, area: str, items: list[Item], summaries: dict, page: str, port: int = 0, idle_minutes: int = 120) -> tuple[ThreadingHTTPServer, str]` returning the server and its token; `run(server) -> int` returning 0 on Done and 3 on Ctrl-C or idle.
  - Requests per spec §5: `GET /` (the page, `text/html`), `GET /items` (JSON: `{"area", "items": [...], "answers": {...}, "open": [...]}`), `POST /answer` (`{"id","decision","text"?,"acs"?}` → 200 with the new `open`; 400 `{"error": "<why>"}` for an unknown ID, an unknown decision, a decision not allowed for the item's kind, or missing required text), `POST /undo` (`{"id"}`), `POST /done` (200 and stop when `open` is empty; 409 `{"open": [...]}` otherwise).
  - Allowed decisions by kind: requirement `confirm`, `correct`, `bug`, `ask`; bug `bug`, `intended`, `ask`; question `intended`, `fix`, `answer`; marker `answer`.
  - `ensure_excluded(repo_root: Path) -> None` (the `.git/info/exclude` line, once).

- [ ] **Step 1: Write the failing tests**, a real server on port 0 in a thread, driven with `urllib.request`:

```python
def test_no_token_is_403_and_writes_nothing(tmp_path): ...
def test_answer_written_atomically_and_reloaded(tmp_path): ...      # POST /answer confirm FR-001 → file holds it with fingerprint and ISO "at"; a new server shows it in GET /items
def test_required_text(tmp_path): ...                               # correct with neither text nor acs → 400; with acs only → 200; ask with "" → 400
def test_decision_not_allowed_for_kind(tmp_path): ...               # "intended" on a requirement → 400
def test_undo(tmp_path): ...
def test_done_refused_then_accepted(tmp_path): ...                  # 409 with open ids; after answering all → 200 and run() returns 0
def test_idle_timeout_returns_3(tmp_path): ...                      # idle_minutes small (allow a float, e.g. 0.01) → run() returns 3
def test_changed_since_answered_counts_open(tmp_path): ...          # Review Focus 5: answer FR-001, edit its AC, rebuild items → FR-001 in open; done refused
def test_concurrent_posts_keep_valid_json(tmp_path): ...            # Review Focus 2: 20 threads posting answers → the file parses and holds every accepted answer
def test_exclude_line_once(tmp_path): ...
```

- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.** One lock around every read-modify-write of the answers; the server stops itself (`shutdown` from a thread) on Done and on idle; `run` maps the three ends to 0 and 3.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): confirmation answers file and local server`.

### Task 3: `prd_confirm.py` and vendoring

**Files:**
- Create: `prd-toolkit/scripts/prd_confirm.py`
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` gains `prd_confirm.py`; `_source_files` vendors `templates/confirm/form.html` as `confirm/form.html`, as it does the block template)
- Test: `prd-toolkit/tests/test_confirm_cli.py`, and the existing vendoring tests (`tests/test_hooks_install.py`)

**Interfaces:**
- Consumes: Tasks 1–2.
- Produces: `prd_confirm.py serve <PRD> --area <area> [--summaries F] [--port N] [--no-open] [--idle-minutes N]` and `prd_confirm.py status <PRD> --area <area>`; the page path `confirm.page_path() -> Path` (the plugin's `templates/confirm/form.html`, or the vendored `<.prd-toolkit>/confirm/form.html`, chosen as `hooks._template_dir` chooses). `serve` opens the browser with `webbrowser.open` unless `--no-open`; a failure to open prints nothing extra and keeps serving.

- [ ] **Step 1: Write the failing tests:** `serve --no-open` on the fixture prints `url=http://127.0.0.1:<port>/?token=<64 hex>` first and serves; `status` prints `2/5` and one `open <ID>` line per open item; an unknown area, a bad summaries file and (Review Focus 4) a `--port` already bound each exit 2 with the `prd_confirm: …` message and print nothing on stdout; Ctrl-C (send SIGINT to the subprocess) exits 3; the vendored file list includes `prd_confirm.py` and `confirm/form.html`.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.** (Task 4 writes the real page; until then a placeholder `form.html` with `<title>` is enough for these tests.)
- [ ] **Step 3: Commit** `feat(prd-toolkit): prd_confirm.py serve and status`.

### Task 4: The page

**Files:**
- Create (or replace Task 3's placeholder): `prd-toolkit/templates/confirm/form.html`
- Test: `prd-toolkit/tests/test_confirm_page.py`

**Interfaces:**
- Consumes: the JSON requests of Task 2.
- Produces the page of spec §4: the left list grouped Requirements, Bugs, Questions, Settings, with states open, ✓ confirmed, ✎ corrected, 🐞 bug, ? someone else, ⟳ changed since answered, and the progress bar `<answered> of <total>`; one card with the ID, kind, `where`, the summary, the ACs (requirement), the text (bug, question, marker) and the excerpts under a `<details>` "Show the code"; the buttons per kind (spec §4 table) with their labels; "Correct…" opens a "What should it do instead?" box plus an "edit the criteria" link that shows one box per AC and marks changed ones; a refused save shows the server's `error`; Done disabled while `open` is non-empty; keys C, R, B, S, ←, →. It reads the token from its own URL and sends it on every request.

- [ ] **Step 1: Write the failing tests (static, no browser):** the page has no `<script src`, `<link`, `@import` or `url(`; it never assigns `innerHTML` from data (a regex over the script finds `innerHTML` only with literal strings); it names every request path (`/items`, `/answer`, `/undo`, `/done`) and every decision value of Task 2; and (Review Focus 1) a served `GET /` from Task 2's server returns this file unchanged, while `GET /items` returns an AC holding `<script>alert(1)</script>` as JSON text, so no server-side HTML building exists.
- [ ] **Step 2: Run them to see them fail; write the page; run the suite.**
- [ ] **Step 3: A manual check:** `uv run --script prd-toolkit/scripts/prd_confirm.py serve <fixture PRD> --area notes` against a fixture built in a scratch folder (never in the repo), click through every kind and the edit link, and record in the task report what you checked.
- [ ] **Step 4: Commit** `feat(prd-toolkit): the confirmation form page`.

### Task 5: Adoption step 3 and the eval

**Files:**
- Modify: `prd-toolkit/skills/adopting-prds/SKILL.md` (step 3)
- Create: `prd-toolkit/evals/adopting-confirm-headless-fallback/` (`case.yaml`, `prompt.md`, `scaffold.sh`, `graders/`)
- Test: the skill-text pins (`tests/test_adopting_skill.py` or the file that pins adopting-prds; add `tests/test_adopting_confirm.py` if none fits)

- [ ] **Step 1: Write the failing pins:** step 3 says to write the summaries file outside the PRD folder and the test roots; to run `prd_confirm.py serve docs/prd/<slug> --area <area> --summaries <file>` in the background (one command per Bash call, the vendored `.prd-toolkit/` copy or the literal plugin path, never `${CLAUDE_PLUGIN_ROOT}`) and give the owner the URL; on exit 0 to read the answers file, re-check each fingerprint (a mismatch is no answer) and apply each decision with the mapping of spec §6, then delete the answers and summaries files; on exit 3 to run `status` and leave the area `extracted`; the fallbacks (AskUserQuestion, the checklist file) kept, a headless run stopping with the area `extracted`. The skill's size pins still pass.
- [ ] **Step 2: Run them to see them fail; write the text; run the suite.**
- [ ] **Step 3: The eval case** (model it on an existing adoption case with a scaffold; the scaffold builds an `extracted` area): in a headless run asked to confirm the area, graders: no Edit/Write sets a block `live`; the area row stays `extracted`; the skill fired. Run it: `claude plugin eval ./prd-toolkit --case 'adopting-confirm-headless-fallback' --runs 1 --model sonnet --no-publish --scaffold --trust-plugin --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" --threshold 0` and record with / without in `prd-toolkit/evals/baselines/adopting-prds.md`.
- [ ] **Step 4: Commit** `feat(prd-toolkit): adoption step 3 confirms through the form`.

### Task 6: Release text and version 0.7.1

**Files:**
- Modify: `prd-toolkit/README.md` (the form under Adoption, `prd_confirm.py`'s commands and exit codes, the upgrade note of spec §10, a 0.7.1 changelog entry), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js`, `web/src/data/plugins.test.js` (0.7.1), `prd-toolkit/tests/test_manifests.py`
- Create: `prd-toolkit/tests/test_release_0_7_1.py`

- [ ] **Step 1: Write the failing pins** (0.7.1 in the three manifests; README names `prd_confirm.py serve` and `status`, exit codes 0/2/3 and the upgrade line); generalise any earlier release test that hardcodes 0.7.0 to a version regex, never delete it.
- [ ] **Step 2: Run them to see them fail; write the text; run pytest, `cd web && npm test`, `claude plugin validate ./prd-toolkit`.**
- [ ] **Step 3: Commit** `chore(prd-toolkit): 0.7.1 release text and versions`.

### After merge: the proof (spec §9)

Not a branch task. Once 0.7.1 is merged and installed, the owner confirms `lint-cli`'s items through the form on branch `feat/prd-toolkit-prd`, and the record `docs/superpowers/plans/2026-11-03-prd-toolkit-0.7.1-acceptance.md` is committed there with the pass line of spec §9 and the owner's notes.
