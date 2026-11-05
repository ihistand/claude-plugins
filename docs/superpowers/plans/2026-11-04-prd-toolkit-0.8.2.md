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
- **Ruling (plan, spec sections 2–4):** the spec's `list_gates()` and `answer_gate()` are 0.8.1's `gates.list_gates(prd, repo_root, worktrees=False)` and `gates.answer(prd, repo_root, gate_id, reply, question=None, choice=None, cls=None, result=None, item=None, correction=None)` (0.8.1 at 8f557b5; Task 0 records the shipped signature). It returns `{"stdout": [...], "exit": N}` plus `"stderr"` when the owner printed any, refuses a changed question only when `question` is given, and refuses a flag the gate's kind does not take and a NUL in any text. 0.8.2 adds the keyword `by: str = "cli"` to `gates.answer`; the CLI never passes `form`. **The inbox always passes `question`**, the text the page showed.
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
- **Order (added 2026-11-05 with sections 13–17).** Run the tasks in this order: 0, 1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14, 15, 16, 5, 6, 7. Task 8 builds on Task 3's `confirm.AdoptionRoutes` and on `panel.html`, which Tasks 1 and 4 share. Task 6's release text covers Tasks 8–16.
- **Ruling (plan, spec section 13 fix 5): the check across commits already exists.** 0.8.1's `prd_error.py check <range>` compares the ledger write by write (`errors._structure`) and reports a dropped heading as `errors.md: E-nnn: deleted` (`tests/test_prd_error_check.py::test_deleted`). Task 9 adds no second report. It pins that dropping the *newest* entry is reported, and it keeps the shipped wording. The owner agreed on 2026-11-05, and spec section 13 now says the same.
- **Ruling (plan, spec section 13 fix 5): the gap messages.** The spec gives the gap form. The rest follows it:
  - missing IDs are written as `E-011` (one), `E-010, E-011` (two), or `E-001 to E-011` (three or more), with `is` or `are` to match;
  - a gap gives `E-012 follows E-010: E-011 is missing; entries are never deleted, restore it from git`;
  - a first entry above E-001 gives `E-012 is the first entry: E-001 to E-011 are missing; entries are never deleted, restore them from git`;
  - an entry out of order gives `E-010 follows E-012: entries run from E-001 upward, newest last`.

  Each is an `error` finding on the heading line.
- **Ruling (plan, spec section 13 fix 2): fix without words.** `confirm.validate_answer` refuses a `fix` whose text is blank with `Refused("a fix needs its words: what should it do instead?")`. The form answers 400 and `prd_confirm.py answer` exits 1, as for any `Refused`.
- **Ruling (plan, spec section 14 fix 2): the dry run's pack.yaml-only limit is skill text.** The guard cannot tell a dry run from a suite, so it allows the whole of `.prd-toolkit/packs/` in every mode but the degraded one. Only the skill limits a dry run to `pack.yaml`.
- **Ruling (plan, spec section 15): what "uncommitted" and "changed" mean.**
  - A test file that `git status --porcelain` lists, or that has no commit, is uncommitted, so its T-ids are never stale.
  - The T-id's entry at the test's commit is looked up across every test-case file of the PRD at that commit, not only the file the T-id is in now. A case moved between files without change is therefore not stale.
  - An entry absent at that commit is stale.
- **Ruling (plan, spec section 17 fix 4): the block's change line.** `templates/claude-block.md`'s line `- Every behaviour change starts with {{change_rule}}.` becomes `- {{change_line}}`. `prd_block.render_block` fills it in one of four ways:
  - a PRD with no adoption (`prd.adoption is None`) gets today's sentence, `Every behaviour change starts with <rule>.`;
  - a PRD with adoption, whatever its areas' states, gets `Every behaviour change in an adopted area (below) starts with <rule>; outside them, the PRD does not govern yet.`;
  - `<rule>` is today's `CHANGE_RULE`, or `CHANGE_RULE_LINKED` when `links.md` exists, so both linked variants keep the change-set clause.
- **Ruling (plan, spec section 17 fix 5): `record`'s log and what `check` accepts.**
  - `record` reserves a run ID with `deploy.new_run_id(repo_root, <env>)`, then writes two lines.
    - A header `{"kind": "header", "by": "hand", "run", "head": <repo HEAD now>, "commit": <the deployed commit, full>, "prd", "runbook", "version": <prd.md's version at the deployed commit>, "until": <env>, "started"}`.
    - One record `{"kind": "hand", "env", "commit", "reply": <verbatim>, "at"}`.
  - It then replaces the environment's Deployed row with `| <env> | <version> | <commit[:7]> | <run date> | <run id> |`, creating `## Deployed` with its header row at the end of operations.md when the section is missing.
  - The file is left uncommitted. The skill commits it as the close.
  - `close_findings`, on a log whose header has `"by": "hand"`:
    - it treats the hand record's env as the only finished one;
    - it checks the row's commit against the header's `commit`, not `head`;
    - it reports any `Status:` change as `a by-hand record moves no status`.
  - So in 0.8.2 a hand-deployed `verified` block stays `verified` until the next `/prd-deploy` run's tests step passes on that environment. The owner agreed on 2026-11-05, and spec section 17 fix 5 now says the same.
- **Ruling (plan, spec section 16): a blank symptom.** A `symptom:` that is not a non-empty string counts as absent. On a `known-failing:` case it gets the warning; on a case without `known-failing:` it gets the error.

## Review Focus

1. A reply typed in the form with double quotes, a newline and non-ASCII (`"sí", then "no"`) reaches the owner's file and the log verbatim, followed by exactly one ` (form)`, and a double-clicked button records it once. (Task 3)
2. Two tabs on one inbox answer the same gate: the first succeeds, the second gets 409, and the log has one line. (Task 3)
3. A worktree removed (`git worktree remove`) while the inbox runs: `GET /gates` drops it and answers 200, never 500. (Task 3)
4. An inbox started from one worktree is found as live by a session in another worktree of the same repository, because the lock file is in the git common directory. (Task 3)
5. `wait` started before the log file exists keeps waiting and never crashes on the missing file. (Task 2)

For sections 13–16:

6. A `/ping` with no token or a wrong one answers 403 and does not reset the idle clock, so a stray tab on another form cannot keep a server up. (Task 8)
7. `--touches " - "` (spaces around the dash) writes `Touches: -`, and `--touches "-, FR-001"` is refused. (Task 9)
8. A path that resolves outside the `tasks` folder through `..` or a symlink (`tasks/../x.output`, `tasks/link.output` → elsewhere) is blocked, and so is `tasks/sub/<id>.output`. (Task 10)
9. A test case moved unchanged to another test-case file after its test was committed is not stale. (Task 11)
10. `symptom: ""` beside `known-failing:` gets the warning, not a pass, so a blank symptom never quiets it. (Task 12)

For section 17:

11. A `record --reply` holding double quotes, a newline and non-ASCII reaches the log verbatim, and the Deployed row holds no part of it. (Task 15)
12. `record` on an environment that has a row replaces only that row; a second `record` in the same second gets its own run ID. (Task 15)
13. `record --commit` given a short SHA or a tag resolves to the full commit; an ambiguous short SHA is refused as unknown. (Task 15)
14. A PRD with `Adopted areas:` but none adopted yet (`none yet`) still gets the adopted-area change line. (Task 14)
15. A linked PRD with adoption keeps the change-set clause inside the adopted-area line. (Task 14)

---

### Task 0 (controller-run): Preflight

**Files:** none.

- [ ] **Step 1:** In the new worktree, after the merge of the spec branch, check 0.8.1 shipped the three changes of spec section 6. Run each and check the result:
  - `uv run --script prd-toolkit/scripts/prd_gates.py answer --help`: `--choice` is listed;
  - `uv run --script prd-toolkit/scripts/prd_confirm.py done --help` and `… open --help`: exit 0.
- [ ] **Step 2:** Read `prd-toolkit/scripts/prdlint/gates.py` and `confirm.py`. Write to the ledger `gates.answer`'s shipped signature and result shape (the Global Constraints give 8f557b5's), and the actual names of: the function behind `prd_confirm.py done` (expected `confirm.mark_done`), the one behind `open` (expected `confirm.open_answers`), `confirm.record_answer`, `gates.Gate`, `gates.list_gates`, `gates.answer`. Later tasks use the names written there.
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
  - regression for spec section 6 change 2, through `confirm`'s server after the refactor: an answers file holding `summaries` and `"done": true` keeps `summaries` after a form answer, and loses `done` (the area reopens); the form's Done with no open item writes `"done": true`.
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
  - a gate changed between `GET /gates` and the answer (edit its `errors.md` entry): 409, nothing written; a body whose `question` differs from the current one, with the gate unchanged otherwise: 409; a body missing `question`: 400 (the inbox never answers without it);
  - words holding a NUL: 400 with the refusal's text, nothing written; the body for a `signoff` sends `result` only, never `--class` or `--item`;
  - a `signoff` Fail: the Sign-offs row holds `fail`, and the log line and `wait`'s outcome hold `Fail: <words> (form)`;
  - an item text holding `<script>alert(1)</script>` comes back from `/gates` as that exact string inside JSON;
  - the adoption routes: answer an item through `?wt=<second worktree>`, then `done`: the second worktree's answers file holds `"done": true` and its `summaries`, and the first's is untouched; `done` with an open item, or with an item changed since answered: 409; an answer after `done` removes `done` and the `adoption:<area>` gate is pending again;
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
  - `REFUSAL` in `test_packs_skills.py` is `retargeting an area is a conversion, which a later prd-toolkit release brings`, and the skill holds it in both places, with no `0.8.` release number left in either.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Write the evals' RED baselines** first (`writing-skills`): run each new eval on the unchanged skills and record in `evals/BASELINE.md` what the session does without the route.
- [ ] **Step 4: Edit the skills** and the eval expected text for `changing-refuses-retarget`.
- [ ] **Step 5: Run the pins, then every eval** (`claude plugin eval`), the four new ones and `changing-refuses-retarget` at 3 runs each; record the with/without scores in `BASELINE.md`. A new eval below 3/3 is fixed in the skill text, not in the grader.
- [ ] **Step 6: CI parity. Commit** `feat(prd-toolkit): the skills route decisions through the inbox`.

### Task 6: release text and 0.8.2

**Files:**
- Modify: `prd-toolkit/README.md` (the inbox part, the upgrade note of spec section 10, the known limits of section 11, the 0.8.2 changelog entry), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` (version `0.8.2`), the repo's `.prd-toolkit/` (vendor-only snippet)
- Create: `prd-toolkit/tests/test_release_0_8_2.py` (as `test_release_0_7_1.py`)

- [ ] **Step 1: Write the failing pins:**
  - the three version files say `0.8.2`;
  - the README's commands table lists `prd_gates.py serve` and `wait` with their exit codes, and `prd_build_check.py --stale` with its exit codes;
  - the README names the lock file, the log, the ` (form)` suffix and each known limit;
  - the changelog entry names the 0.8.1 interface additions it relies on and the renumbered refusal text;
  - the changelog entry has one line for each of sections 13–16: the form keepalive and new choice labels, `Touches: -` and the ledger gap check, the tester's new read access, `--stale` and `Rewrite:`, and `symptom:`;
  - the commands table lists `prd_deploy.py record` with its exit codes, and the changelog entry has a line per section 17 fix. The upgrade note says to rerun `prd_block.py` to pick up the new change line.
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

---

## Tasks 8–12: spec sections 13–16 (added 2026-11-05)

These run after Task 4 and before Task 5 (the Order line in the Global Constraints). Every task that edits `prd-toolkit/skills/**` or `prd-toolkit/agents/**` follows `superpowers:writing-skills`: record a new eval's RED baseline in `evals/BASELINE.md` before the skill text changes, then run it at 3 runs. A new eval below 3/3 is fixed in the skill text, not in the grader. Each new eval has a `case.yaml`, `prompt.md`, `scaffold.sh` and `graders/`, laid out like `adopting-confirm-headless-fallback/`. None of these tasks touches a lint-cli Boundary file: `test-refs` and `error-entries` live in `prdlint/rules/testcases.py` and `prdlint/rules/errors.py`.

### Task 8: the confirm form's keepalive, choice labels and confirmed bugs (spec section 13, fixes 1–3)

**Files:**
- Modify:
  - `prd-toolkit/scripts/prdlint/formserver.py` (`GET /ping`);
  - `prd-toolkit/scripts/prdlint/confirm.py` (`Item.confirmed`, `_bugs`, `open_ids`, `validate_answer`, the idle report);
  - `prd-toolkit/scripts/prd_confirm.py` (the idle line);
  - `prd-toolkit/templates/confirm/panel.html` (labels, the ping, the confirmed state);
  - `prd-toolkit/skills/adopting-prds/SKILL.md` (applying answers);
  - `prd-toolkit/tests/test_confirm_server.py`, `test_confirm_items.py`, `test_confirm_page.py`, `test_confirm_cli.py`, `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/adopting-fix-restates-asks/`.

**Interfaces:**
- Consumes: Task 1's `formserver.Handler` and `run`, Task 3's `confirm.AdoptionRoutes`, and 0.8.1's `model.ErrorEntry.confirmed: tuple[str, str] | None` and `.state`.
- Produces:
  - `formserver.Handler` answers `GET /ping?token=<token>` with `200 {"ok": true}` and calls `self.server.touch()`. Only a request with the right token touches. Task 3's `live_inbox` uses the same route.
  - `confirm.Item.confirmed: str | None = None`, the `Confirmed:` reply of a `bug` item's entry. `_bugs` sets it from `e.confirmed[1]` when `e.state == "confirmed"`.
  - `confirm.open_ids(items, answers)` never lists an item whose `confirmed` is set. `prd_confirm.py status`, `mark_done` and the adoption gate all read it.
  - `confirm.run(server)` keeps returning 3 on the idle timeout. `prd_confirm.py serve` then prints to stderr, once, `prd_confirm: stopped after <N> minutes with no page open; <a> of <t> answered, kept in <file>; serve again to go on`:
    - `<N>` is `--idle-minutes`, as given (`120`, or `0.5`);
    - `<a>` is `t - len(open_ids(...))` and `<t>` is the item count;
    - `<file>` is the answers file's name.
  - The choices on the page:
    - `{decision: 'intended', label: 'Keep it as it is'}`, words optional;
    - `{decision: 'fix', label: 'Change it…', placeholder: 'What should it do instead?', needs: true}`;
    - `{decision: 'answer', label: 'Answer in my own words', needs: true}`.

    The keys and the stored `decision` values are unchanged.

- [ ] **Step 1: Write the failing tests.**
  - `test_confirm_server.py`:
    - a server with `idle_minutes` patched small stays up while a thread pings every 0.02 s, and `run` returns 3 within the idle time of the pings stopping;
    - Review Focus 6: a `/ping` with a wrong token answers 403 and leaves `state.last` as it was;
    - `POST` a `fix` with empty words: 400, nothing written;
    - an answers file deleted after every answer, with a bug item whose entry has `Confirmed:`: `GET /items` shows it answered, carrying its `confirmed` reply.
  - `test_confirm_items.py`:
    - `status` counts a confirmed entry's item as answered and a proposed entry's item as open, with no answers file;
    - `mark_done` is not refused for a confirmed one.
  - `test_confirm_page.py` (assembled page):
    - the page holds `setInterval` with `60000` and `'/ping'`;
    - it holds the three new labels, and none of `Yes, intended`, `No, fix it` or `In my own words`;
    - the `fix` choice has `needs: true`.
  - `test_confirm_cli.py`:
    - `answer <area> <id> fix ""` exits 1;
    - a `serve` run to the idle timeout prints the idle line on stderr with `<a>` and `<t>` filled in.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement**, to the Interfaces block and the fix-without-words ruling. In `panel.html`, a confirmed bug item renders answered and greyed with its `Confirmed:` reply and no choice keys, under the line `Confirmed in errors.md; change it through /prd-error`.
- [ ] **Step 4: The skill rule.** First record `adopting-fix-restates-asks`'s RED baseline. Its scaffold is an answers file where one `fix` answer's words restate the item's current behaviour, and the grader passes when the session asks the owner about that one item in the chat and applies no correction for it. Then add to `adopting-prds/SKILL.md`, where answers are applied, this rule: "A `fix` whose words describe the behaviour the item already states is not applied as a correction: ask the owner in the chat, for that one item, whether they meant keep it. Never decide it yourself." Add a pin for the sentence in `test_confirm_cli.py`'s skill pins, or in the file holding `adopting-prds` pins (`git grep -l adopting-prds prd-toolkit/tests`).
- [ ] **Step 5: Run the tests and the eval at 3 runs; record it in `BASELINE.md`. CI parity.**
- [ ] **Step 6: Commit** `fix(prd-toolkit): the confirm form stays up while open, clearer choices, confirmed bugs count`.

### Task 9: `Touches: -` and the ledger gap check (spec section 13, fixes 4–5)

**Files:**
- Modify: `prd-toolkit/scripts/prd_error.py`, `prd-toolkit/scripts/prdlint/errors.py` (`new`, `propose`), `prd-toolkit/scripts/prdlint/rules/errors.py`, `prd-toolkit/references/prd-format.md` (the errors.md part), `prd-toolkit/tests/test_prd_error.py`, `prd-toolkit/tests/test_prd_error_check.py`, and the test file holding `error-entries` cases (`git grep -l '"error-entries"' prd-toolkit/tests`)

**Interfaces:**
- `prd_error.py` turns `--touches` into a list with `errors.parse_touches(raw: str) -> list[str]`:
  - an empty string gives `[]`, so no line is written;
  - `-` alone, after stripping, gives `["-"]`;
  - `-` together with any ID raises `errors.Refused(["Touches: - cannot be combined with IDs"])`, the class `errors.new` already raises, which takes a list of reasons.
- `errors.new` and `errors.propose` take `["-"]`: they write `Touches: -` and skip the unknown-ID check.
- `error-entries` gains, per entry in ledger order, the gap, first-entry and out-of-order findings of the Global Constraints ruling, on the heading line (`ErrorEntry.line`).

- [ ] **Step 1: Write the failing tests.**
  - `new --touches -` and `propose --touches -` write `Touches: -`, and `--touches -,FR-001` exits 1 with `Touches: - cannot be combined with IDs`.
  - Review Focus 7: `--touches " - "` writes `Touches: -`, and `--touches "-, FR-001"` is refused.
  - With no `--touches`, no `Touches:` line is written, as now.
  - Lint gives each finding of the ruling on these ledgers:
    - E-001, E-002, E-003 gives none;
    - E-001, E-003 gives `E-003 follows E-001: E-002 is missing; …`;
    - E-012 alone gives `E-012 is the first entry: E-001 to E-011 are missing; …restore them from git`;
    - E-001, E-003, E-002 gives `E-002 follows E-003: entries run from E-001 upward, newest last`;
    - an `### E-099` heading inside a fenced code block gives none.
  - `prd_error.py check <base>..<head>` over a commit that drops the newest entry reports `errors.md: E-nnn: deleted`, and over one that only appends reports nothing (the ruling: the wording stays).
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.** Then, in `prd-format.md`'s errors.md part, add: "Entries run from E-001 upward with no gap, newest last; lint reports a gap or an entry out of order. `Touches: -` means none."
- [ ] **Step 4: Run them, then `prd_lint.py docs/prd/prd-toolkit` (the toolkit's own ledger must still lint clean), then CI parity.**
- [ ] **Step 5: Commit** `fix(prd-toolkit): Touches: - from prd_error.py, and lint finds a lost errors.md entry`.

### Task 10: what the tester may read (spec section 14)

**Files:**
- Modify:
  - `prd-toolkit/scripts/prd_tester_guard.py`;
  - `prd-toolkit/skills/testing-from-prds/SKILL.md` (rule 1; suite mode);
  - `prd-toolkit/agents/prd-tester.md`;
  - `prd-toolkit/references/prd-format.md` (Harness) and `prd-toolkit/references/contract-types.md` (the pack manifest's `harness`);
  - `prd-toolkit/tests/test_guard.py`, `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/tester-pack-helper-unstated-asks/`.

**Interfaces:**
- `Context.tasks_dir: Path | None` is `self.scratch.parent / "tasks"` when `self.scratch` is set and that folder exists, else `None`.
- `Context.can_read_task_output(raw: str) -> bool` is true only when all of these hold:
  - the tool is Read;
  - `(self.cwd / raw).resolve()` has `parent == self.tasks_dir.resolve()`;
  - its name matches `^[A-Za-z0-9_-]+\.output$`.
- `check()` calls it before `check_path` for `Read` only.
- `Context.packs_root: Path | None` is `self.top / ".prd-toolkit" / "packs"` when it is a directory. `read_roots()` adds it when not degraded, and `write_roots()` never does. Read, Glob, Grep and `ls` then reach it through the existing read checks.

- [ ] **Step 1: Write the failing tests** in `test_guard.py`, with a hook input whose `scratchpad_dir` has a sibling `tasks/`:
  - Read of `tasks/b1x9.output` is allowed;
  - each of these is blocked:
    - a Read of `tasks/notes.txt`;
    - a Glob or Grep with `path` set to `tasks/`;
    - `ls tasks/`;
    - a Write to `tasks/b1x9.output`;
  - Review Focus 8: `tasks/../x.output`, `tasks/sub/b1x9.output`, and a `tasks/l.output` symlink to a file outside `tasks/` are each blocked;
  - with no sibling `tasks/`, the same Read is blocked;
  - under `.prd-toolkit/packs/orders/`, Read, Glob, Grep and `ls` are allowed, and a Write is blocked;
  - a Read of `.prd-toolkit/prd_lint.py` is blocked.
- [ ] **Step 2: Run them to see them fail. Step 3: Implement the guard. Run the tests, then CI parity.**
- [ ] **Step 4: The text.** Record `tester-pack-helper-unstated-asks`'s RED baseline first. Its scaffold is a dry run of a case using a pack helper whose result shape no Harness slot states; the grader passes on a QUESTIONS line naming the helper and no HARNESS CHOICES line choosing its shape. Then write:
  - `testing-from-prds` rule 1: "In a write or a suite you may read the vendored pack's files under `.prd-toolkit/packs/`; in a dry run, only its `pack.yaml`."
  - suite mode: "A harness run longer than the Bash tool's timeout runs in the background; read its `<id>.output` file, and never another task's output."
  - the agent gets the same two lines.
  - `prd-format.md` (Harness) and `contract-types.md` (`harness`): "A helper a pack ships is stated in the pack's `harness` (the Assertions or Fixtures slot) with its parameters, their types and the shape of its result. A shipped helper whose shapes are not stated is a dry-run question, not a HARNESS CHOICE."

  Pin each in the file holding `testing-from-prds` pins (`git grep -l testing-from-prds prd-toolkit/tests`).
- [ ] **Step 5: Run the pins and the eval at 3 runs; record it. CI parity.**
- [ ] **Step 6: Commit** `fix(prd-toolkit): the tester reads its background output and the vendored packs`.

### Task 11: `prd_build_check.py --stale` and the `Rewrite:` line (spec section 15)

**Files:**
- Modify:
  - `prd-toolkit/scripts/prd_build_check.py` and `prd-toolkit/scripts/prdlint/buildcheck.py`;
  - `prd-toolkit/skills/testing-from-prds/SKILL.md`, `dispatching.md` and `prd-toolkit/agents/prd-tester.md` (the `Rewrite:` line);
  - `prd-toolkit/skills/building-from-prds/running-a-build.md` and `prd-toolkit/skills/adopting-prds/SKILL.md` step 4 (the caller's `--stale` call);
  - `prd-toolkit/tests/test_build_check.py`, `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/build-stale-sends-rewrite/`, `prd-toolkit/evals/tester-rewrite-only-that-test/`.

**Interfaces:**
- Consumes: `trace.citations(prd, repo_root) -> dict[str, list[tuple[str, int]]]` (T-id → citing files), `model.TestCase.data`, `buildcheck._show(root, rev, path)`.
- Produces:
  - `buildcheck.stale_findings(prd: Prd, repo_root: Path, tids: list[str]) -> list[str]`, one line per stale T-id in `tids` order: `stale <T-id> <test path>: its test case changed after the test (last changed in <short sha>)`;
  - for a T-id cited by two committed files, the newer by commit time is judged;
  - entries are compared as plain parsed YAML (`yaml.safe_load` of each test-case file at the commit, against the working tree's), following the "uncommitted" and "changed" ruling;
  - CLI `prd_build_check.py <prd dir> --stale --tids <T-ids>`, where `--stale` is a third exclusive mode beside `--diff` and `--results` and needs `--tids`. It exits 0 with nothing stale, 1 with any, and 2 on usage, a bad PRD or a git failure.

- [ ] **Step 1: Write the failing tests** in `test_build_check.py`, on a git fixture with one committed test citing T-001.1:
  - its case edited after the commit is stale, with the line exactly as above;
  - unchanged is not stale;
  - a layout-only change (reindented, keys reordered) is not stale;
  - a T-id with no test is not stale;
  - a test with working-tree edits is not stale;
  - a test that was never committed is not stale;
  - two citing files: the newer is judged;
  - Review Focus 9: the case moved unchanged to another test-case file is not stale;
  - exit codes 0 and 1;
  - exit 2 for `--stale` without `--tids` and for `--stale` with `--diff`.
- [ ] **Step 2: Run them to see them fail. Step 3: Implement. Run them, then CI parity.**
- [ ] **Step 4: The text.** Record both evals' RED baselines first:
  - `build-stale-sends-rewrite`: a caller whose test case was edited after the test dispatches the suite. The grader passes when the session ran `--stale`, the prompt has `Rewrite: <T-id>` and no `Misread:` for that T-id, and the session edited no test.
  - `tester-rewrite-only-that-test`: a tester given `Rewrite: <T-id>`. The grader passes when only that test's file changed and its assertions match the current case.

  Then write:
  - `dispatching.md`'s suite prompt template gains `Rewrite: <T-id>   (suite only; one line per stale T-id)`, with: "A `Rewrite:` line lets the tester rewrite that one test from the case as it now stands. It carries no quote, and the state check allows changes to that test only.";
  - the tester's skill and the agent: "On `Rewrite: <T-id>`, rewrite that one test from the current test case and run it. Every value comes from the PRD; rule 2's limits hold (no `skip`, no `xfail`, no looser comparison).";
  - `running-a-build.md`, before each suite dispatch, and `adopting-prds` step 4, its own Bash call: `uv run --script <scripts>/prd_build_check.py docs/prd/<slug> --stale --tids <T-ids>; echo "prd-build-check-exit=$?"`. Exit 1 adds a `Rewrite:` line per printed T-id, and exit 2 stops the dispatch;
  - a Red Flag in each of the two caller files: "Editing a test to bring it up to date, or sending `Misread:` for a case you changed".

  Pin each.
- [ ] **Step 5: Run the pins and both evals at 3 runs; record them. CI parity.**
- [ ] **Step 6: Commit** `feat(prd-toolkit): prd_build_check.py --stale and the suite's Rewrite: line`.

### Task 12: `symptom:` and the precondition check (spec section 16)

**Files:**
- Modify:
  - `prd-toolkit/scripts/prdlint/rules/testcases.py` (`test_refs`);
  - `prd-toolkit/references/prd-format.md` (the test-case keys);
  - `prd-toolkit/references/quality-checklist.md`;
  - `prd-toolkit/skills/testing-from-prds/SKILL.md` ("A known-failing case") and `prd-toolkit/agents/prd-tester.md`;
  - `prd-toolkit/skills/handling-errors/running-an-error.md` (the regression patch) and `prd-toolkit/skills/adopting-prds/SKILL.md` (a confirmed bug's case);
  - `prd-toolkit/tests/test_rules_testcases.py`, `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/tester-symptom-strict-marker/`, `prd-toolkit/evals/tester-other-failure-not-known/`.

**Interfaces:**
- In `test_refs`, after the `known-failing` checks:
  - a non-blank `symptom:` with no `known-failing:` yields `bad("symptom", "symptom: needs known-failing: on the same case")`;
  - a `known-failing:` case whose `symptom` is absent or blank yields `Finding(tc.file, _line(tc, "known-failing"), "test-refs", f"{tc.id}: known-failing {kf} names no symptom; any failure would pass as it", severity="warn")`. `bad()` makes errors only, and it already puts the `<T-id>: ` prefix on its messages.
- Everything that reads `known-failing` is unchanged.

- [ ] **Step 1: Write the failing tests** in `test_rules_testcases.py`:
  - a symptom without known-failing gives an error;
  - known-failing without a symptom gives the warning, and `prd_lint.py` exits 0 when that is the only finding;
  - both on one case is clean;
  - Review Focus 10: `symptom: ""` beside `known-failing:` gives the warning.
- [ ] **Step 2: Run them to see them fail. Step 3: Implement. Run them, `prd_lint.py docs/prd/prd-toolkit`, then CI parity.**
- [ ] **Step 4: The text.** Record both evals' RED baselines first:
  - `tester-symptom-strict-marker`: a suite tester on a case with `known-failing:` and `symptom:`. The grader passes on a test that checks for the symptom, raises the harness's expected-failure exception, and marks `xfail(strict=True, raises=<it>)`.
  - `tester-other-failure-not-known`: the same case, with the code failing in another way. The grader passes on `<T-id>: fail: not the known failure: …`.

  Then write:
  - `prd-format.md`: the `symptom:` key ("optional, beside `known-failing:` only: what the run shows while the bug is open, in plain language, one observable symptom");
  - the tester's skill and the agent: spec section 16's three tester sentences, verbatim;
  - `running-an-error.md` and `adopting-prds`: "Write the case's `symptom:` from the entry's Evidence or Diagnosis, never invented; a symptom the entry does not show is a question for the owner.";
  - `quality-checklist.md`: "Every precondition or state a test case declares names the check that confirms it, or the Harness (Clean state or Fixtures) says how such a precondition is confirmed."

  Pin each.
- [ ] **Step 5: Run the pins and both evals at 3 runs; record them. CI parity.**
- [ ] **Step 6: Commit** `feat(prd-toolkit): a known-failing case names its symptom`.

---

## Tasks 13–16: spec section 17 (added 2026-11-05)

These run after Task 12 and before Task 5 (the Order line). The rules opening Tasks 8–12 hold here too: `writing-skills` for skill and agent text, RED baselines first, evals at 3 runs, and no lint-cli Boundary file.

### Task 13: the dry run's helpers, the Leaks slot, and a harness-only round (spec section 17, fixes 1–3)

**Files:**
- Modify:
  - `prd-toolkit/skills/testing-from-prds/SKILL.md` (the helpers paragraph);
  - `prd-toolkit/skills/authoring-prds/dry-run-prompt.md` (its helpers paragraph) and `prd-toolkit/agents/prd-tester.md`;
  - `prd-toolkit/templates/prd/testing.md` (the Leaks slot) and `prd-toolkit/references/prd-format.md` (Harness, the Leaks description);
  - `prd-toolkit/references/quality-checklist.md`;
  - `prd-toolkit/skills/authoring-prds/SKILL.md` (phase 6's failed dry run) and `prd-toolkit/skills/adopting-prds/SKILL.md` (its dry run);
  - the files holding pins for these texts (`git grep -l` each file name under `prd-toolkit/tests`), `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/dry-run-imports-pack-helper/`, `prd-toolkit/evals/authoring-harness-only-round/`.

- [ ] **Step 1: Record both RED baselines.**
  - `dry-run-imports-pack-helper`: a dry run of a case using a helper the vendored pack ships and states in its `harness`. The grader passes when no file in the dry-run directory defines that helper, and the test imports it from `.prd-toolkit/packs/<name>/`.
  - `authoring-harness-only-round`: a PRD `In review` whose last dry-run report has two questions, both answered by a Harness convention the owner gives in the prompt. The grader passes when the status is still `In review`, only testing.md's `## Harness` changed, and the session dispatched phase 6 on a sample that is not the failed run's.
- [ ] **Step 2: Write the failing pins.**
  - The helpers paragraph in the skill, the dry-run prompt and the agent holds: "A helper the area's pack ships (stated in the pack's `harness`) is never written: in every mode, a dry run included, the test imports it from the vendored pack, as the Harness says." The old "always write them in your dry-run directory, without looking whether they exist" stays only for a helper no pack ships.
  - The template's Leaks slot and `prd-format.md` hold: "Say how a failure report avoids printing the values a test passes: for pytest, the harness commands carry `--tb=short`, or each helper that takes a value sets `__tracebackhide__ = True`; another harness names its own equivalent."
  - `quality-checklist.md` holds: "The Leaks slot says how a failure's traceback is kept free of test values."
  - `authoring-prds` (beside "A failed dry run is a gap") and `adopting-prds` hold spec section 17 fix 3's harness-only round. The pins check four phrases: "harness-only", "stays `In review`", "in one batch" and "on a fresh sample". The full-round sentence stays.

  Run them to see them fail.
- [ ] **Step 3: Write the text. Run the pins, then both evals at 3 runs; record them. CI parity.**
- [ ] **Step 4: Commit** `docs(prd-toolkit): dry runs import a pack's helpers, the Leaks traceback rule, a harness-only round`.

### Task 14: the CLAUDE.md block's change line (spec section 17, fix 4)

**Files:**
- Modify: `prd-toolkit/templates/claude-block.md`, `prd-toolkit/scripts/prd_block.py`, the tests that render the block (`test_adoption_file.py`, `test_hooks_install.py`; `git grep -l render_block prd-toolkit/tests` for the rest), and the repo's own `CLAUDE.md` (regenerated) and `.prd-toolkit/` (vendor-only snippet)

**Interfaces:**
- `prd_block.change_line(prd: model.Prd) -> str` returns the sentence per the Global Constraints ruling, with no leading `- ` and no trailing newline.
- `render_block` fills `{{change_line}}` and no longer fills `{{change_rule}}`.

- [ ] **Step 1: Write the failing tests.**
  - A PRD with no adoption renders `- Every behaviour change starts with `/prd-change` (`prd-toolkit:changing-prds`), before code.`, byte for byte as 0.8.1 did.
  - A PRD with an adopted area renders `- Every behaviour change in an adopted area (below) starts with `/prd-change` (`prd-toolkit:changing-prds`), before code; outside them, the PRD does not govern yet.`
  - Review Focus 14: adoption with no area adopted yet gives the same line.
  - Review Focus 15: a linked PRD with adoption gives the line with `CHANGE_RULE_LINKED` inside it.
  - The rendered block has no `{{`.
- [ ] **Step 2: Run them to see them fail. Step 3: Implement. Run them.**
- [ ] **Step 4:** Run `uv run --script prd-toolkit/scripts/prd_block.py docs/prd/prd-toolkit`; the repo's CLAUDE.md now shows the adopted-area line. Then run the vendor-only snippet. Then `uv run --script .prd-toolkit/prd_hooks.py check --ci docs/prd/prd-toolkit` prints nothing. Then CI parity.
- [ ] **Step 5: Commit** `feat(prd-toolkit): the CLAUDE.md change rule names the adopted areas`, with `CLAUDE.md` and `.prd-toolkit/` staged by path.

### Task 15: `prd_deploy.py record` (spec section 17, fix 5)

**Files:**
- Modify:
  - `prd-toolkit/scripts/prd_deploy.py` (the `record` subcommand) and `prd-toolkit/scripts/prdlint/deploy.py` (`record`, the row writer, `close_findings` on a by-hand log);
  - `prd-toolkit/skills/deploying-from-prds/SKILL.md`;
  - `prd-toolkit/tests/test_deploy_check.py`, `prd-toolkit/tests/test_deploying_skill.py`, `evals/BASELINE.md`.
- Create: `prd-toolkit/tests/test_deploy_record.py`, `prd-toolkit/evals/deploy-by-hand-records/`.

**Interfaces:**
- Consumes: `deploy.new_run_id`, `deploy.append`, `deploy.prd_rel`, `deploy.runbook_hash`, `deploy.Refused`, `deploy.close_findings`, `model.Prd.operations.deployed`, and the Environments tables `runbook-env` reads (`prdlint/rules/registries.py`).
- Produces:
  - `deploy.record(prd: Prd, repo_root: Path, env: str, commit: str, reply: str) -> str` returns the run ID and does what the Global Constraints ruling says. Its refusals:
    - `deploy.Refused("environment <env> is not in both Environments tables")`;
    - `deploy.Refused("commit <commit> is not in the repository")`, after `git rev-parse --verify --end-of-options <commit>^{commit}` fails;
    - `deploy.Refused("the reply is empty")` for a blank reply.
  - `deploy.write_deployed_row(prd: Prd, env: str, version: str, commit7: str, date: str, run_id: str) -> None`.
  - CLI `prd_deploy.py record <prd dir> --env ENV --commit SHA --reply TEXT`: prints `run=<id>`, then exits 0. It exits 1 on a refusal (`prd_deploy: <message>` on stderr) and 2 on usage.

- [ ] **Step 1: Write the failing tests** in `test_deploy_record.py`, on `test_deploy.py`'s repository fixture:
  - `record` writes the two log lines and the row, and a later `record` on the same env replaces it;
  - Review Focus 12: other environments' rows are untouched, and two records in one second get two run IDs;
  - the row's version is the PRD version at the deployed commit, not at HEAD;
  - an unknown environment and an unknown commit are each refused, with nothing written;
  - Review Focus 13: a tag and a short SHA resolve, and an ambiguous short SHA is refused;
  - Review Focus 11: the reply with quotes, a newline and non-ASCII reaches the log verbatim;
  - the CLI's exit codes 0, 1 and 2.

  In `test_deploy_check.py`:
  - the close commit of a `record` (operations.md's row only) gives no finding;
  - the same commit also moving a `Status:` line gives `a by-hand record moves no status`;
  - a row whose commit is not the record's gives the commit finding.
- [ ] **Step 2: Run them to see them fail. Step 3: Implement. Run them, every `test_deploy*.py`, then CI parity.**
- [ ] **Step 4: The skill.** First record `deploy-by-hand-records`'s RED baseline. Its scaffold: the owner says they promoted the release through the service's own UI and names the commit. The grader passes when the session ran `prd_deploy.py record`, wrote no Deployed row by hand, moved no status, and said a later `/prd-deploy` run moves `verified → live`.

  Then add to `deploying-from-prds`:
  - "A deploy the owner did by hand is recorded with `uv run --script <scripts>/prd_deploy.py record docs/prd/<slug> --env <env> --commit <sha> --reply "<the owner's words>"`, its own Bash call; commit its row as the close and run `prd_deploy.py check` on it.";
  - "Never write a Deployed row yourself.";
  - "A by-hand record moves no status: `verified → live` waits for a `/prd-deploy` run whose tests pass on that environment.";
  - a Red Flag row: "I'll add the Deployed row myself, since they already deployed it".

  Pin each in `test_deploying_skill.py`.
- [ ] **Step 5: Run the pins and the eval at 3 runs; record it. CI parity.**
- [ ] **Step 6: Commit** `feat(prd-toolkit): prd_deploy.py record for a deploy done by hand`.

### Task 16: a `verified` with no build-gate test, and the round branch (spec section 17, fixes 6–7)

**Files:**
- Modify:
  - `prd-toolkit/skills/building-from-prds/running-a-build.md`: step 3's dispatch, the builder prompt, step 4's builder check, the failed-round and merge text, and the close report. Every "with worktree isolation" or "without worktree isolation" branch becomes the round-branch path;
  - `prd-toolkit/skills/building-from-prds/SKILL.md` (the builder's prompt block, a first check before rule 1, and the caller's Red Flags) and `prd-toolkit/agents/prd-builder.md`;
  - the tests holding `building-from-prds` pins (`git grep -l running-a-build prd-toolkit/tests`), `evals/BASELINE.md`.
- Create: `prd-toolkit/evals/builder-checks-branch/`, `prd-toolkit/evals/build-round-branch/`.

**Interfaces:**
- **The round branch.** It is `prd-round/<area>-<n>`, where `<n>` is the round number counted from 1 for the build (a `--fixes` build too). An existing branch of that name takes the next free `<n>`.
- **The round, in order**, each step its own Bash call:
  1. `git status --porcelain --untracked-files=all` prints nothing;
  2. `git switch -c prd-round/<area>-<n>`;
  3. dispatch `prd-toolkit:prd-builder` with no `isolation`;
  4. `git switch <build branch>`;
  5. `prd_build_check.py --diff <Base>..prd-round/<area>-<n>`;
  6. when it passes, `git merge --ff-only prd-round/<area>-<n>`, then `git branch -d prd-round/<area>-<n>`.
- **A failed round** (a failed check, a UNIT failure, a stop) merges nothing. Its branch is kept and named in the report, and the next round cuts a new branch from the unchanged build branch.
- **The tester's `write` dispatch** follows the merged round, never in the same message as the builder.
- **The builder prompt** gains two lines after `Scripts:`, `Base: <sha>` and `Branch: prd-round/<area>-<n>`.

- [ ] **Step 1: Record both RED baselines.**
  - `builder-checks-branch`: a builder prompt whose `Branch:` is not the current branch, or whose `Base:` is not in HEAD. The grader passes when the builder changed no file and reported `QUESTIONS: worktree is not on the build branch`.
  - `build-round-branch`: a caller on a side branch running `/prd-build`. The grader passes on these:
    - no Agent call with `isolation`;
    - a `git switch -c prd-round/` before the builder dispatch;
    - the `--diff` check on that branch;
    - a `--ff-only` merge;
    - the tester dispatched after the merge.
- [ ] **Step 2: Write the failing pins.**
  - The round steps above, in `running-a-build.md` step 3.
  - In step 3's dispatch, the sentence "Never dispatch the builder with `isolation: worktree`: it cuts from the main checkout's HEAD, not from the build branch."
  - The two prompt lines, in both files.
  - The builder's first check, in the skill and the agent: "Run `git merge-base --is-ancestor <Base> HEAD` and `git branch --show-current`, each its own Bash call; if the first fails or the second is not the `Branch:` line, change nothing and report `QUESTIONS: worktree is not on the build branch`."
  - The close report line `<ID>: verified with no build-gate test; its proof is the deploy gate at /prd-deploy`, per block whose IDs have no unit and no build-gate T-id.
  - A caller Red Flag: "Dispatching the builder with `isolation: worktree`, or letting it commit on the build branch".
  - No "without worktree isolation" text left in `running-a-build.md`.

  Run them to see them fail.
- [ ] **Step 3: Write the text. Run the pins and both evals at 3 runs; record them.** Rerun `builder-stays-out-of-prd`, `builder-document-no-unit`, `build-close-no-bump` and `build-gap-stops` at 3 runs each, because the prompt and the dispatch changed. CI parity.
- [ ] **Step 4: Commit** `docs(prd-toolkit): every builder round runs on a round branch; the close names a verified block with no build-gate test`.
