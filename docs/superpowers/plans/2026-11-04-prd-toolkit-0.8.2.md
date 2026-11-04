# prd-toolkit 0.8.2: the decision inbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One local page, served by `prd_gates.py serve`, that lists every pending gate of a PRD across the repository's worktrees and answers each through `gates.answer`, with `prd_gates.py wait` telling a session when its gate is answered.

**Architecture:** The server parts of the 0.7.1 form move into `prdlint/formserver.py`, which both the 0.7.1 form and the inbox build on. `prdlint/gates.py` (0.8.1) gains the answer log, `wait_gate`, the inbox lock file and the inbox server, which answers in-process through `gates.answer(..., by="form")`. The page `templates/gates/inbox.html` includes the 0.7.1 item panel, moved to `templates/confirm/panel.html`, for the adoption card.

**Tech Stack:** Python 3.11+ (`uv run --script`), standard-library `http.server`, pyyaml, pytest; git; Claude Code CLI (`claude plugin eval`); Chrome (claude-in-chrome) for the proof.

**Spec:** `docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md` (extends the 0.7.1 and 0.8.1 specs, governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`)

## Global Constraints

- **Starts only after 0.8.1 is on `main`** with the three interface changes of spec section 6. Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8.2`, branch `feat/prd-toolkit-0.8.2`, cut from that `main`; then `git merge docs/prd-toolkit-0.8.2-inbox-spec` once (`Refs: none (no behaviour change)`) to bring the spec, the umbrella and this plan. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- **The toolkit's own PRD binds this branch.** No task touches a lint-cli Boundary file (`prd_lint.py`, `prdlint/{__init__,model,markdown,yamlload,findings,registry,deps}.py`, `prdlint/rules/__init__.py`). If a task finds it must, it stops: that is a `/prd-change` first. Every commit carries `Refs: none (no behaviour change)`. Never `--no-verify`.
- The repo is public and the toolkit names no client: no app, editor or organization name in code, docs, tests or evals. Example slugs `greet`, `orders`, `notes`.
- Test-first: every behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New code follows the existing scripts: `main(argv) -> int`, the `deps.require` preamble, the utf-8 `__main__` block. No new third-party dependency; the server is standard library only.
- **CI parity before every commit that touches code:** `scripts/ci-local.sh` (0.8.1), with `HOME` set to an empty directory under the session scratchpad.
- **Vendoring:** the repo's own `.prd-toolkit/` is refreshed only by the vendor-only snippet, never by `prd_hooks.py install`:
  `uv run --project prd-toolkit python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('prd-toolkit/scripts').resolve())); from prdlint import hooks; from prdlint.model import load; r = Path('.').resolve(); s = hooks._resolve_sources(r, load(r / 'docs/prd/prd-toolkit')); hooks._vendor(r, s); hooks._ignore_record(r)"`
- **Exact names:**
  - files: `<git common dir>/prd-inbox-<slug>.json` (mode 0600), `<git common dir>/prd-gates-log.jsonl`, `templates/gates/inbox.html`, `templates/confirm/panel.html`;
  - the include line `<!-- include: panel.html -->`;
  - document kind `gates.outcome`;
  - the reply suffix ` (form)` (one space, then `(form)`);
  - refusal texts `prd_gates: an inbox is already serving at <url>` and, for a gate not pending, `prd_gates: <gate id> is not pending`;
  - the default idle timeout of 120 minutes and the page's refresh every 5 seconds.
- **Ruling (plan, spec sections 2–4):** the spec's `list_gates()` and `answer_gate()` are 0.8.1's `gates.list_gates(prd, repo_root, worktrees=False)` and `gates.answer(prd, repo_root, gate_id, reply, choice=None, cls=None, result=None, item=None)`. 0.8.2 adds the keyword `by: str = "cli"` to `gates.answer`; the CLI never passes `form`.
- **Ruling (plan, spec section 5): buttons and replies.** The page sends a button key; the server maps it:

  | Kind | Button key | Label in the reply | Passed as |
  |---|---|---|---|
  | `approval` | `approve` | `Approve` | `choice="approve"` |
  | `approval` | `changes` (words required) | `Request changes` | `choice="changes"` |
  | `error-class` | `confirm` | `Confirm the class` | `choice="confirm"` |
  | `error-class` | `correct` (words and `class` required) | `Correct it to <class>` | `choice="correct", cls=<class>` |
  | `deploy-step` | `send` (words required) | none: the reply is the words alone | the reply only |
  | `signoff` | `pass` | `Pass` | `result="pass"` |
  | `signoff` | `fail` (words required) | `Fail` | `result="fail"` |

  The reply is `<label>`, or `<label>: <words>` when there are words (words with leading and trailing whitespace stripped, inner text unchanged), then ` (form)`. For `deploy-step` it is `<words> (form)`.
- **Ruling (plan, spec section 4): the log.** One line per accepted `gates.answer` call, adoption per-item answers excepted: only an adoption's `done` is logged (`choice: "done"`, reply `Done (form)` or the CLI's reply). A line is `{"at": <ISO UTC, seconds>, "prd": <slug>, "worktree": <absolute path>, "gate": <id>, "choice": <choice or null>, "reply": <verbatim>, "by": "form"|"cli"}`, appended under `fcntl.flock` on the log file after the owning script exits 0.
- **Ruling (plan, spec section 3): when `wait` starts.** A skill starts `wait` in the background *before* it gives the owner the URL, so no answer can come before `wait` is watching. `wait` returns the first log line for its `(worktree, gate)` whose `at` is not earlier than `wait`'s own start (to the second). A gate that is not pending when `wait` starts, with no such line, exits 1 at once.
- **Ruling (plan, spec section 4): worktrees in requests.** Every answer body and adoption request names its worktree by absolute path (`"worktree"` in a body, `?wt=` in a query). The server refuses with 404 a path that is not in `git worktree list --porcelain`, or whose checkout lacks the PRD folder.
- **Ruling (plan, spec section 5): the approval card's diff.** `.prd-review.json` records no base, so the inbox computes it as the review does by default: `git merge-base HEAD <base>` in that worktree, where `<base>` is the branch's upstream (`@{upstream}`) or else `main`, then `git diff <merge-base> -- <prd dir>`. `/gates` carries it on the approval gate as `diff` (text, capped at 200 KB, with `diff_truncated: true` past that), beside the verdict's `restate`, `touches`, `bump`, `impact` and `dry_run` and the version from → to.
- **Ruling (plan, spec section 7): sign-off.** No skill writes a Sign-offs row today. `testing-from-prds` gains one rule: a `signoff:` case is answered by its owner, in the inbox or in the chat, and never by the tester or the session.

## Review Focus

1. A reply typed in the form with double quotes, a newline and non-ASCII (`"sí", then "no"`) reaches the owner's file and the log verbatim, followed by exactly one ` (form)`, and a double-clicked button records it once. (Task 3)
2. Two tabs on one inbox answer the same gate: the first succeeds, the second gets 409, and the log has one line. (Task 3)
3. A worktree removed (`git worktree remove`) while the inbox runs: `GET /gates` drops it and answers 200, never 500. (Task 3)
4. An inbox started from one worktree is found as live by a session in another worktree of the same repository, because the lock file is in the git common directory. (Task 3)
5. `wait` started before the log file exists keeps waiting and never crashes on the missing file. (Task 2)

---

### Task 0 (controller-run): Preflight

**Files:** none.

- [ ] **Step 1:** In the new worktree, after the merge of the spec branch, check 0.8.1 shipped the three changes of spec section 6. Run each and check the result:
  - `uv run --script prd-toolkit/scripts/prd_gates.py answer --help`: `--choice` is listed;
  - `uv run --script prd-toolkit/scripts/prd_confirm.py done --help` and `… open --help`: exit 0.
- [ ] **Step 2:** Read `prd-toolkit/scripts/prdlint/gates.py` and `confirm.py`. Write to the ledger the actual names of: the function behind `prd_confirm.py done` (expected `confirm.mark_done`), the one behind `open` (expected `confirm.open_answers`), `confirm.record_answer`, `gates.Gate`, `gates.list_gates`, `gates.answer`. Later tasks use the names written there.
- [ ] **Step 3:** If any of the three changes is missing, stop and tell Ivan: the plan cannot start.

### Task 1: `formserver.py`, the shared page assembly, and `panel.html`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/formserver.py`, `prd-toolkit/templates/confirm/panel.html`, `prd-toolkit/tests/test_formserver.py`
- Modify: `prd-toolkit/scripts/prdlint/confirm.py`, `prd-toolkit/templates/confirm/form.html`, `prd-toolkit/tests/test_confirm_page.py` (it reads the assembled page)

**Interfaces:**
- Produces:
  - `formserver.CSP`, `formserver.MAX_BODY = 1024 * 1024` (moved from `confirm.py`, which re-exports them);
  - `class formserver.PageError(Exception)`;
  - `formserver.assemble(page: Path, include_dir: Path | None = None) -> str`: replaces each line that is exactly `<!-- include: NAME -->` (leading spaces allowed) with the text of `(include_dir or page.parent) / NAME`; a missing file raises `PageError(f"include {NAME} not found")`; includes do not nest. The inbox (Task 4) passes `include_dir = templates/confirm`;
  - `class formserver.Handler(BaseHTTPRequestHandler)`: checks the token on every request (403, no change), caps the body (413), and offers `self.body_json() -> dict` (400 on bad JSON), `self.send_json(code, obj)`, `self.send_page(html)` (with the CSP header), and `self.server.touch()`;
  - `formserver.make_server(handler: type[Handler], port: int = 0, idle_minutes: int = 120, state: object = None) -> tuple[ThreadingHTTPServer, str]`: binds `127.0.0.1`, makes a `secrets.token_urlsafe(24)` token, stores `state` on the server;
  - `formserver.run(server) -> int`: 0 when `server.finish()` was called, 3 on Ctrl-C, SIGTERM or the idle timeout;
  - `formserver.write_json_atomic(path: Path, data: dict, mode: int | None = None) -> None` (temporary file in the same folder, then `os.replace`);
  - `formserver.ensure_excluded(repo_root: Path, line: str) -> None`.
- `confirm.make_server`, `confirm.run`, `confirm.ensure_excluded`, `confirm.save_answers` and `confirm.page_path` keep their 0.7.1 signatures and behaviour, now built on `formserver`.

- [ ] **Step 1: Write the failing tests** in `test_formserver.py`, on a tiny `Handler` subclass serving `GET /x`:
  - no token, and a wrong token: 403 and the state is unchanged;
  - `server.server_address[0] == "127.0.0.1"`;
  - the page response carries `Content-Security-Policy` equal to `formserver.CSP`;
  - a 1 MB + 1 byte body: 413;
  - `idle_minutes` set to a fraction (patch the idle check to 0.05 s): `run` returns 3; SIGTERM from a thread: 3; `finish()`: 0;
  - `assemble` replaces the include and keeps every other line byte for byte; `include_dir` is honoured; a missing include raises `PageError`;
  - `write_json_atomic` with `mode=0o600` leaves a 0600 file and no temporary file.
- [ ] **Step 2:** In `test_confirm_page.py`, read the page through `formserver.assemble(PAGE_FILE)` instead of the raw file; add `test_panel_is_included` (the raw `form.html` has the include line; the assembled one does not). Run the new and changed tests to see them fail.
- [ ] **Step 3: Implement.** Move the server parts out of `confirm.py`; move the item list, card, keys and Done markup, style and script out of `form.html` into `panel.html`, leaving the include line. `confirm` serves `formserver.assemble(page_path())`.
- [ ] **Step 4:** Run `test_formserver.py` and every `test_confirm*.py`: all pass, the 0.7.1 ones unchanged. Then CI parity.
- [ ] **Step 5: Commit** `refactor(prd-toolkit): formserver.py shared by the confirm form`.

### Task 2: the answer log, `by`, and `prd_gates.py wait`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/gates.py`, `prd-toolkit/scripts/prd_gates.py`
- Create: `prd-toolkit/tests/test_gates_wait.py`

**Interfaces:**
- Consumes: 0.8.1's `gates.answer`, `gates.list_gates`; Task 0's ledger names.
- Produces:
  - `gates.common_dir(repo_root: Path) -> Path` (`git rev-parse --git-common-dir`, absolute);
  - `gates.log_path(repo_root) -> Path`, `gates.read_log(repo_root) -> list[dict]` (`[]` when the file is missing; a line that is not JSON is skipped);
  - `gates.answer(..., by: str = "cli")` appends the log line (Global Constraints) after the owner exits 0, and only then;
  - `gates.wait_gate(prd_dir: Path, gate_id: str, worktree: Path | None = None, timeout: float | None = None, poll: float = 1.0) -> tuple[int, dict]`, returning `(0, outcome)`, `(1, outcome with choice None)` or `(3, {})`;
  - CLI `prd_gates.py wait <prd dir> <gate id> [--worktree PATH] [--timeout S]`, printing one `gates.outcome` document: `{"interface": 1, "kind": "gates.outcome", "gate", "worktree", "choice", "reply", "by", "at"}`.

- [ ] **Step 1: Write the failing tests** on 0.8.1's gate fixtures:
  - an `error-class` gate answered through `gates.answer(by="cli")` while `wait` runs in a thread: `wait` returns 0 with the reply verbatim and `by: "cli"`; the log has one line;
  - a refused answer (empty reply) writes no log line;
  - a gate already answered *before* `wait` starts: exit 1 at once (the plan's ruling);
  - the PRD edited so the gate disappears with no answer: exit 1, `choice` null;
  - `--timeout 1` on a pending gate: exit 3;
  - an approval answered with `choice="changes"`: the outcome's `choice` is `changes` and `reply` the words;
  - an adoption `done`: one log line with `choice: "done"`; per-item answers write none;
  - Review Focus 5: `wait` starts with no log file, the answer creates it, and `wait` returns 0.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_gates.py wait and the answer log`.

### Task 3: the inbox server, its lock file, and `prd_gates.py serve`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/gates.py`, `prd-toolkit/scripts/prd_gates.py`, `prd-toolkit/scripts/prdlint/confirm.py` (the adoption routes as an object the inbox mounts)
- Create: `prd-toolkit/tests/test_inbox_server.py`, `prd-toolkit/tests/test_inbox_lock.py`, `prd-toolkit/tests/inbox_fixture.py` (a repository with two worktrees, both holding `docs/prd/orders`, one `error-class:E-003` gate in each, an approval gate, a deploy run stopped at a human step, a sign-off case, and an `extracted` area opened with `prd_confirm.py open`)

**Interfaces:**
- Consumes: Task 1's `formserver`, Task 2's log, 0.8.1's `gates.list_gates`, `gates.answer`, `confirm.record_answer`, and Task 0's `done` and `open` names.
- Produces:
  - `gates.build_reply(kind: str, button: str, words: str, cls: str | None = None) -> tuple[str, dict]`: the reply and the keyword arguments for `gates.answer`, per the Global Constraints table; raises `gates.NeedsWords(message)` for a button that needs words or a class;
  - `gates.worktree_prds(repo_root: Path, prd_rel: str) -> list[dict]`: `{"path", "branch"}` per `git worktree list --porcelain` entry whose checkout holds `prd_rel`, the current worktree first;
  - `gates.inbox_path(repo_root, slug) -> Path`; `gates.live_inbox(repo_root, slug) -> dict | None` (PID alive and `GET /ping?token=` 200 within 2 s; otherwise the file is deleted and `None` returned);
  - `gates.make_inbox(prd_dir: Path, port: int = 0, idle_minutes: int = 120) -> tuple[server, token]`, writing the lock file (mode 0600) and deleting it when `run` returns;
  - `class confirm.AdoptionRoutes(prd, area, repo_root)` with `items() -> dict`, `answer(body) -> dict`, `undo(body) -> dict`, `done() -> dict`, each raising `confirm.Refused` as the 0.7.1 server's requests did; the 0.7.1 server uses it too;
  - the requests of spec section 4, `/adoption/<area>/…` taking `?wt=`;
  - CLI `prd_gates.py serve <prd dir> [--gate ID] [--port N] [--no-open] [--idle-minutes N]`: refuses a live inbox (exit 1, `prd_gates: an inbox is already serving at <url>`) and a `--gate` that is not pending (exit 1, `prd_gates: <gate id> is not pending`); prints `url=http://127.0.0.1:<port>/?token=<token>` first, with `#gate=<id>` appended when `--gate` is given.

- [ ] **Step 1: Write the failing tests**, the server started on `inbox_fixture` in a thread:
  - `GET /gates`: two worktree groups; each has its own `error-class:E-003`;
  - the approval gate carries the verdict's fields, the version from → to, and `diff` equal to `git diff <merge-base with main> -- docs/prd/orders`; a diff over 200 KB is cut, with `diff_truncated: true`;
  - `POST /answer` for each kind and button: the owner's file holds the reply that `build_reply` gives (for example `Approve: ship it (form)`, `Correct it to spec gap: the PRD never says (form)`, `deploy production (form)`); the log line has `by: "form"`;
  - a button that needs words, sent without: 400 and nothing written; `correct` without a class: 400;
  - a gate changed between `GET /gates` and the answer (edit its `errors.md` entry): 409, nothing written;
  - an item text holding `<script>alert(1)</script>` comes back from `/gates` as that exact string inside JSON;
  - the adoption routes: answer an item through `?wt=<second worktree>`, then `done`: the second worktree's answers file holds `"done": true` and the first's is untouched; `done` with an open item: 409;
  - a `wt` that is not a worktree: 404;
  - Review Focus 1: the words `"sí", then "no"` with a newline reach the owner's file and the log verbatim, then one ` (form)`; the same body posted twice records once (the second is 409, the gate being gone);
  - Review Focus 2: two threads post the same approval at once: one 200, one 409, one log line;
  - Review Focus 3: `git worktree remove` the second worktree, then `GET /gates`: 200 with one group.
- [ ] **Step 2: Write the failing lock tests** in `test_inbox_lock.py`:
  - `serve` writes the lock file (mode 0600), `live_inbox` returns its record, and a second `serve` exits 1 with the refusal text and the first URL;
  - a lock file whose PID is dead, and one whose token is wrong: `live_inbox` returns `None` and deletes the file; `serve` then starts;
  - the file is gone after `serve` exits;
  - Review Focus 4: `live_inbox` called from the second worktree finds the inbox started from the first.
- [ ] **Step 3: Run them to see them fail.**
- [ ] **Step 4: Implement.**
- [ ] **Step 5: Run them, every `test_confirm*.py`, then CI parity.**
- [ ] **Step 6: Commit** `feat(prd-toolkit): prd_gates.py serve, the decision inbox server`.

### Task 4: the inbox page

**Files:**
- Create: `prd-toolkit/templates/gates/inbox.html`, `prd-toolkit/tests/test_inbox_page.py`
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (vendors `templates/gates/` beside `confirm/`), `prd-toolkit/tests/test_hooks_install.py`

**Interfaces:**
- Consumes: Task 3's requests and button keys; `panel.html` (Task 1) through `<!-- include: panel.html -->`, assembled with `formserver.assemble(inbox_page, include_dir=templates/confirm)`.
- Produces: one JS renderer per kind, named `renderApproval`, `renderErrorClass`, `renderDeployStep`, `renderSignoff`, `renderAdoption`, and `refresh()` on a 5000 ms interval.

- [ ] **Step 1: Write the failing tests** in `test_inbox_page.py`, on the assembled page, reusing `test_confirm_page.py`'s helpers (`BANNED_JS`, `unsafe_html`, `function`):
  - it loads nothing (no `<script src`, `<link`, `@import`, `url(`), one inline script and one inline style;
  - `unsafe_html` finds nothing (no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`);
  - each renderer above exists; `refresh` uses `setInterval` with `5000`;
  - the page names every button key of the Global Constraints table, and `renderDeployStep` has a text box and no `approve`/`pass` key;
  - the panel's adoption functions are present (the include resolved);
  - `test_hooks_install`: a vendored `.prd-toolkit/` holds `templates/gates/inbox.html`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** the page to spec section 5: the card frame, the per-kind sections, `#gate=<id>` opening that card, the greyed answered state from `/gates`, the "changed" mark on a 409. Deploy-step and the words-required buttons show the reason when sent empty, before any request.
- [ ] **Step 4: Run them, then CI parity.** Then open the page once on `inbox_fixture` (`serve --no-open`, then Chrome) and check every kind renders; fix what the tests could not see.
- [ ] **Step 5: Commit** `feat(prd-toolkit): the decision inbox page`.

### Task 5: the skills' route, the renumbered refusal, and evals

Required skill: `superpowers:writing-skills` (the repo's CLAUDE.md requires it for `prd-toolkit/skills/**`).

**Files:**
- Modify: `prd-toolkit/skills/changing-prds/SKILL.md` (step 5's approval; the retarget refusal, both places), `prd-toolkit/skills/handling-errors/running-an-error.md` (the class confirmation), `prd-toolkit/skills/deploying-from-prds/SKILL.md` (the human step), `prd-toolkit/skills/adopting-prds/SKILL.md` (step 3: `prd_confirm.py open`, then the inbox), `prd-toolkit/skills/testing-from-prds/SKILL.md` (the sign-off rule), `prd-toolkit/tests/test_packs_skills.py` (`REFUSAL`), `prd-toolkit/evals/changing-refuses-retarget/` (expected text), `prd-toolkit/evals/BASELINE.md`
- Create: `prd-toolkit/tests/test_inbox_skills.py`; evals `prd-toolkit/evals/inbox-never-answers-gate/`, `inbox-deploy-step-not-sent/`, `inbox-uses-outcome-reply/`, `inbox-headless-falls-back/` (each `case.yaml`, `prompt.md`, `scaffold.sh`, `graders/`, as `adopting-confirm-headless-fallback/`)

**Interfaces:**
- Consumes: the CLI forms of Tasks 2 and 3.
- The route text, the same in each of the four decision skills, one command per Bash call, literal paths:
  1. `uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>` in the background, **first**;
  2. if `<git common dir>/prd-inbox-<slug>.json` is live (`prd_gates.py serve` would refuse with `already serving at <url>`), give the owner `<url>#gate=<gate id>`; otherwise run `uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>` in the background and give the URL it prints;
  3. continue from `wait`'s outcome; its `reply` is the owner's reply, used as it stands;
  4. headless, or the owner asks for the chat: the pre-0.8.2 chat route, unchanged.

- [ ] **Step 1: Write the failing pins** in `test_inbox_skills.py`:
  - each of the four decision skills holds the route's `wait` command before its `serve` command, and the chat route stays;
  - each holds the rules of spec section 7 verbatim: "The skill never answers a gate.", "A deploy step's reply is never sent for the owner", "The outcome's reply is not edited.", and the `wait` exit-1 rule;
  - `deploying-from-prds` and `changing-prds` each gain a Red Flag row for "I'll click Approve / Send in the inbox for them";
  - `testing-from-prds` holds the sign-off rule;
  - no `${CLAUDE_PLUGIN_ROOT}` inside a Bash command;
  - `REFUSAL` in `test_packs_skills.py` is `retargeting an area is a conversion (prd-toolkit 0.8.4)`, and the skill holds it in both places.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Write the evals' RED baselines** first (`writing-skills`): run each new eval on the unchanged skills and record in `evals/BASELINE.md` what the session does without the route.
- [ ] **Step 4: Edit the skills** and the eval expected text for `changing-refuses-retarget`.
- [ ] **Step 5: Run the pins, then every eval** (`claude plugin eval`), the four new ones and `changing-refuses-retarget` at 3 runs each; record the with/without scores in `BASELINE.md`. A new eval below 3/3 is fixed in the skill text, not in the grader.
- [ ] **Step 6: CI parity. Commit** `feat(prd-toolkit): the skills route decisions through the inbox`.

### Task 6: release text and 0.8.2

**Files:**
- Modify: `prd-toolkit/README.md` (the inbox part, the upgrade note of spec section 10, the known limits of section 11, the 0.8.2 changelog entry), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` (version `0.8.2`), the repo's `.prd-toolkit/` (vendor-only snippet)
- Create: `prd-toolkit/tests/test_release_0_8_2.py` (as `test_release_0_7_1.py`)

- [ ] **Step 1: Write the failing pins:** the three version files say `0.8.2`; the README's commands table lists `prd_gates.py serve` and `wait` with their exit codes; the README names the lock file, the log, the ` (form)` suffix and each known limit; the changelog entry names the 0.8.1 interface additions it relies on and the renumbered refusal text.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Write the text; bump the versions; run the vendor-only snippet.**
- [ ] **Step 4: Run the pins, then CI parity,** then `prd_lint.py docs/prd/prd-toolkit` and `prd_trace.py docs/prd/prd-toolkit --range origin/main..HEAD`, each with `; echo "prd-…-exit=$?"`: both 0.
- [ ] **Step 5: Commit** `feat(prd-toolkit): 0.8.2 release text and version`.

### Task 7 (controller-run, with Ivan): Proof

**Files:** none committed but the proof record in the README changelog entry.

- [ ] **Step 1:** Install the branch's plugin at user scope (the marketplace update, then the plugin update), and `/reload-plugins`.
- [ ] **Step 2 (Claude):** on `inbox_fixture` copied to the scratchpad, `serve --no-open`, then drive Chrome through the `deploy-step`, `signoff` and `adoption` cards, recording `inbox-deploy-step.gif`, `inbox-signoff.gif`, `inbox-adoption.gif`. Check each owner's file afterwards.
- [ ] **Step 3 (Ivan):** the next real `/prd-change` on the toolkit's PRD, approved in the inbox after at least one **Request changes** round; one real `/prd-error` class confirmed in the inbox; one gate from each of two sessions or worktrees in one inbox. Claude only points to the inbox and waits; every click is Ivan's.
- [ ] **Step 4:** Record in the changelog entry what was proven and where (commit SHAs, the GIF names). Commit `docs(prd-toolkit): 0.8.2 proof record`.
