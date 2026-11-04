# prd-toolkit 0.8.2: a local decision inbox — design

> **Date:** 2026-11-04
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md` (the adoption form) and
> `2026-11-03-prd-toolkit-0.8.1-design.md` (the machine interface, `prd_gates.py`), under
> `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this addendum and any of them disagree, this
> addendum wins for 0.8.2.
> **Needs from 0.8.1:** the three interface changes of section 6, built into 0.8.1 before it ships.
>
> **Revisions.**
> - Section 6 change 2 (2026-11-04, from 0.8.1's author, in its spec at 8cf5f26): the three rules
>   that keep `done` correct: both forms' Done write it, writers keep keys they do not own, and a
>   later answer removes it.
> - Sections 1 and 2 (owner, 2026-11-04): the PRD READMEs are inserted as 0.8.3
>   (`2026-11-04-prd-toolkit-0.8.3-prd-readmes-design.md`), so best practices are 0.8.4 and
>   conversion 0.8.5; the retarget refusal names no release number, so renumbering never again
>   changes shipped text.

## 1. Scope

0.7.1 gave the owner a local form for one decision point: confirming an area's items in adoption
step 3. Every other decision is still a reply typed into the chat: approving a `/prd-change`,
confirming an error's class, answering a deploy run's human step, recording a sign-off. 0.8.1 gives
those decisions one shape (`prd_gates.py list` and `answer`) but no page.

0.8.2 adds a **decision inbox**: one local page, served by `prd_gates.py serve`, that lists every
pending gate of a PRD across the repository's worktrees and answers each through the same function
the CLI uses.

0.8.2 delivers:
- `prd_gates.py serve` and `wait`, and the answer log (sections 3 and 4);
- the shared server `prdlint/formserver.py`, factored out of `prdlint/confirm.py` (section 2);
- the page `templates/gates/inbox.html`, with one card per gate kind and the 0.7.1 item panel as the
  adoption card (section 5);
- the skills' new route: point to the inbox, wait, fall back to the chat (section 7).

**Success:** a whole `/prd-change` or `/prd-error` cycle runs with no decision typed into the chat,
and every record still holds the owner's own words for each decision.

It is **proven by** the owner on real work (section 9).

### Decisions

| Decision | Choice |
|---|---|
| Which decisions | All five 0.8.1 gate kinds: `approval`, `error-class`, `deploy-step`, `signoff`, `adoption`. Adoption becomes one kind among them |
| A button's words | The button's label is the reply; words are optional for a yes and required for anything else. The reply recorded is `<label>` or `<label>: <words>`, then ` (form)`. Two exceptions: a deploy step's reply is always typed, and adoption keeps its Done (section 5) |
| Who starts it | Both. The owner may keep one inbox running; a session that reaches a decision reuses a live inbox or starts one, then waits for its gate |
| A "no" on an approval | A **Request changes** choice on the approval gate, with the owner's words, that blocks the review verdict and commits nothing (section 6) |
| Release vehicle | 0.8.2, after 0.8.1 merges. The PRD READMEs follow as 0.8.3, best practices as 0.8.4 and conversion as 0.8.5. The three interface changes go into 0.8.1 itself |
| Architecture | `prd_gates.py serve` over a server shared with the 0.7.1 form; answers go through `answer_gate()` in-process, never through a subprocess, so the form cannot bypass a rule the CLI keeps |

## 2. Components

| Path (under `prd-toolkit/`) | New or changed | Role |
|---|---|---|
| `scripts/prdlint/formserver.py` | new | What both forms share, moved out of `confirm.py`: the `127.0.0.1` bind, the random token (403 without it), the CSP header, the 1 MB body cap, the idle timeout, SIGTERM as a stop, the atomic JSON write (temporary file and `os.replace`), the `.git/info/exclude` line, and page assembly |
| `scripts/prdlint/confirm.py` | changed | Keeps the adoption items, summaries, fingerprints and answers file; builds its server on `formserver`. 0.7.1 behaviour is unchanged |
| `scripts/prdlint/gates.py` (0.8.1) | changed | `answer_gate()` gains `by` (`form` or `cli`, default `cli`) and writes the answer log; new `serve_inbox()` and `wait_gate()` |
| `scripts/prd_gates.py` (0.8.1) | changed | New subcommands `serve` and `wait` |
| `templates/gates/inbox.html` | new | The inbox page |
| `templates/confirm/panel.html` | new | The 0.7.1 item panel (list, card, keys, Done), moved out of `form.html` |
| `templates/confirm/form.html` | changed | Includes `panel.html`; the page the owner sees is unchanged |
| `scripts/prdlint/hooks.py` | changed | Vendors `templates/gates/` with `confirm/` |
| `skills/changing-prds/SKILL.md`, `tests/test_packs_skills.py`, `evals/` (`changing-refuses-retarget`) | changed | The 0.8.0 retarget refusal names no release number: `retargeting an area is a conversion, which a later prd-toolkit release brings`, in the skill (both places), its test pin and the eval's expected text |
| `skills/changing-prds/SKILL.md`, `skills/handling-errors/running-an-error.md`, `skills/deploying-from-prds/SKILL.md`, `skills/adopting-prds/SKILL.md`, `skills/testing-from-prds/SKILL.md` | changed | The route at each decision (section 7) |
| `README.md`, `plugin.json`, `marketplace.json`, `web/src/data/plugins.js` | changed | The inbox, the 0.8.2 changelog, version 0.8.2 |

**Page assembly.** `formserver` builds each page on the server, replacing an include line
(`<!-- include: panel.html -->`) with that file's text, before sending it. The browser receives one
self-contained page, so the 0.7.1 rule holds unchanged: the page loads nothing (no `<script src`,
`<link`, `@import` or `url(`), and every value is inserted as text, never as HTML. The page tests run
on the assembled output.

## 3. `prd_gates.py serve` and `wait`

Exit codes, as the other scripts: 0 ok, 1 refused, 2 usage or tool error, 3 stopped or timed out.

| Command | Does |
|---|---|
| `serve <prd dir> [--gate <id>] [--port N] [--no-open] [--idle-minutes N]` | Starts the inbox, prints `url=http://127.0.0.1:<port>/?token=<token>` as its first stdout line, opens the browser unless `--no-open`, and opens the page on `--gate` when given. Runs until Ctrl-C, SIGTERM or `--idle-minutes` without a request (default 120); exit 3. There is no Done: an inbox has no last item |
| `wait <prd dir> <gate id> [--worktree <path>] [--timeout S]` | Blocks until that gate is answered, by any client. Prints `{"interface": 1, "kind": "gates.outcome", "gate": …, "worktree": …, "choice": …, "reply": "…", "by": "form"\|"cli", "at": …}` and exits 0. Exit 3 on timeout (default: none). Exit 1, with `{"kind": "gates.outcome", "gate": …, "choice": null}`, when the gate stopped being pending with no answer in the log (the PRD changed under it) |

`wait` reads the answer log, not the page, so a session never depends on which client answered.

`wait`'s `--worktree` defaults to the worktree that holds `<prd dir>`.

**Errors.** Exit 2, nothing served: a folder with no `prd.md`; a port in use when `--port` is given.
Exit 1: a `--gate` that is not pending; a second live inbox for the PRD (section 4).

## 4. The inbox

**One inbox per PRD.** A running inbox writes `<git common dir>/prd-inbox-<slug>.json` (mode 0600):
`{"pid": …, "port": …, "token": "…", "started": "<ISO>", "prd": "<slug>"}`, and deletes it on exit. The
git common directory is shared by every worktree and never committed. An inbox is **live** when its
PID is running and `GET /ping?token=…` answers 200. `serve` refuses to start a second live inbox for
the same PRD (exit 1, `prd_gates: an inbox is already serving at <url>`) and replaces a file that is
not live.

**Worktrees.** The inbox lists every worktree of the repository (`git worktree list`) whose checkout
holds the PRD folder, calls `list_gates()` once per worktree, and shows every kind grouped by worktree
and branch. Each answer carries its worktree, and `answer_gate()` runs with that worktree's PRD
folder, so two branches' `error-class:E-003` gates stay two gates. 0.8.1's `list --worktrees` is
unchanged.

**Refresh.** The page asks `GET /gates` every 5 seconds; the server lists again on each request. A new
gate appears at the top. A gate answered elsewhere greys out with its answer from the log. A gate whose
`question` changed while the owner reads it reloads with a "changed" mark; an answer to the old one
is refused (409), as 0.8.1's `answer` refuses it.

**Requests.** Every request carries the token; without it, 403 and no change.

| Request | Does |
|---|---|
| `GET /?token=…` | The page |
| `GET /ping` | 200, for the liveness check |
| `GET /gates` | Every pending gate per worktree, and the log's answers from this inbox's run |
| `POST /answer` | `{worktree, gate, choice, words, class?, result?}`: builds the reply (section 5), calls `answer_gate(…, by="form")`, returns its result. 400 for required words missing, 409 for a changed or gone gate |
| `GET /adoption/<area>/items`, `POST /adoption/<area>/answer`, `POST /adoption/<area>/undo`, `POST /adoption/<area>/done` | The 0.7.1 panel's requests for one area, against that area's answers file |

**The answer log.** `answer_gate()` appends one JSON line per answer to
`<git common dir>/prd-gates-log.jsonl`: `{"at", "prd", "worktree", "gate", "choice", "reply", "by"}`,
the reply verbatim. It appends under a file lock, after the owning script has succeeded, so the log
never records an answer that was refused. The log is never committed and never pruned by the toolkit.

## 5. The cards

Every card shows the kind, the gate ID, the worktree and branch, and the source location; then the
gate's `question` and its `evidence` lines (folded beyond 5).

**The reply.** The page sends the button and the words; the server builds the reply:
`<label>` when there are no words, `<label>: <words>` when there are, then ` (form)`. A button marked
"words required" below is refused with no words (400), and the card says why.

| Kind | The card also shows | Buttons | Passed to |
|---|---|---|---|
| `approval` | From `.prd-review.json`: `restate`, `touches`, the version from → to with `bump.level` and `bump.decided`, `impact.lines`, `dry_run.record`. Then `git diff <base> -- <prd dir>` in that worktree, one folded section per file | **Approve** · **Request changes…** (words required) | `prd_change.py approve` with the reply and the verdict's dry-run record; or `--choice changes` (section 6) |
| `error-class` | The entry's title, Diagnosis and proposed class | **Confirm the class** · **Correct it to…** (a choice of `code bug`, `spec gap`, `invalid requirement`, `environment`, `standard`; words required) | `prd_error.py confirm` (`correct` with `--class`) |
| `deploy-step` | The run ID, environment, the step's actor and its `Do:` and `Check:` lines | No buttons: a text box and **Send reply**; words required, and the reply is the words alone, then ` (form)` | `prd_deploy.py confirm <run> <step> --reply` |
| `signoff` | The T-id, the case's title, `input` and `expect`, and "Signing as `<owner>`" from its `signoff:` | **Pass** · **Fail…** (words required) | The Sign-offs row, `--result pass\|fail` |
| `adoption` | The area and `<answered> of <total>`. **Open** expands the 0.7.1 panel in place | Inside the panel, as 0.7.1: per item, then **Done** | `prd_confirm.py answer` per item; `prd_confirm.py done` on Done |

**Why a deploy step is always typed.** A human step's reply is the go for that step, and a runbook may
ask for specific words. One click on "Done" would make a production go the cheapest action on the
page.

**Why adoption keeps Done.** Without it, the last answer would close the gate and the session would
apply the answers while the owner might still revise one. The gate stays pending until Done
(section 6, change 2); Done is refused while any item is open or changed since answered, the 0.7.1
rule.

**An adoption gate's start.** The adopting skill runs `prd_confirm.py open` (section 6, change 3),
which writes the answers file with its summaries, then points the owner to the inbox. The inbox
needs no `--summaries`.

## 6. Changes to 0.8.1's interface

These three change what 0.8.1's gates mean, so they are built in 0.8.1, before its first release;
`interface` stays `1`. Everything else in this design is new and ships in 0.8.2.

1. **The approval gate has two choices.**
   `prd_gates.py answer <prd dir> approval:<branch> --choice approve|changes --reply "<verbatim>"`,
   `approve` the default. `changes` needs a reply that is not empty. It writes
   `"owner": {"choice": "changes", "reply": "<verbatim>", "at": "<ISO>"}` into `.prd-review.json`, sets
   `ready` to `false` and appends `owner: <reply>` to `blockers`. It commits nothing and writes nothing
   under the PRD folder but that untracked file. The gate is then not pending; editing the PRD changes
   the digest, so only a new review makes it pending again. `changes` on a gate that is not pending is
   refused, as any changed gate is.
2. **The adoption gate is pending until Done.** It is pending while `.prd-confirm-<area>.json` exists
   and holds no `"done": true`. `prd_confirm.py done <prd dir> <area>` sets it, and is refused (exit 1)
   while any item is open or changed since answered. `prd_gates.py answer adoption:<area> --choice done`
   passes to it; the per-item answer is unchanged. Three rules make this hold (added with 0.8.1's
   author, 2026-11-04):
   - the 0.7.1 form's Done, and the inbox's, write `"done": true` through the same function as
     `prd_confirm.py done`, once no item is open; an answer whose item's fingerprint differs from its
     current one counts as open;
   - every writer of the answers file (the form, `prd_confirm.py answer`, `done`, `open`) keeps the keys
     it does not own (`summaries`, `done`), never rebuilding the file from its own fields alone;
   - an answer or undo written after `done` removes `done`, so a reopened area is pending again.
3. **`prd_confirm.py open <prd dir> --area <area> [--summaries F]`** writes the answers file with
   `prd`, `area`, `commit` (HEAD), `summaries` and no answers, and the `.git/info/exclude` line. It
   applies the 0.7.1 summary rules (the summary names its item; at most 400 characters) and refuses an
   area with no item. A file that already exists is refused (exit 1), so a second `open` never erases
   answers. `serve` reads `summaries` from the file when `--summaries` is not given.

## 7. The skills

At each decision (a change's approval, an error's class, a deploy's human step, a sign-off, adoption
step 3), the skill:

1. reads `<git common dir>/prd-inbox-<slug>.json`; when it is live, gives the owner its URL with
   `#gate=<id>`; otherwise starts `prd_gates.py serve <prd dir> --gate <id>` in the background and
   gives the URL it prints;
2. runs `prd_gates.py wait <prd dir> <gate id>` in the background, and continues from its outcome: the
   reply in the outcome is the owner's reply, used exactly as it stands;
3. falls back to the chat, as before 0.8.2, when the inbox cannot be served (a headless run, nobody
   to open the URL) or the owner asks to answer in the chat.

Rules every changed skill states:
- **The skill never answers a gate.** Not through the page, not through `prd_gates.py answer`, not
  "because the owner said approve it yourself". The owner's click or the owner's chat reply is the
  only answer.
- **A deploy step's reply is never sent for the owner,** in the form or the CLI.
- **The outcome's reply is not edited.** A `changes` outcome's reply is what the revision answers.
- A `wait` that exits 1 means the gate changed: list again, never assume the answer.

## 8. Testing the toolkit

- **`formserver`:** a request without the token gets 403 and changes nothing; the bind is
  `127.0.0.1`; the CSP header is sent; a body over 1 MB is refused; the idle timeout and SIGTERM exit
  3; the include is replaced and an include of a missing file is a tool error.
- **The 0.7.1 form:** every existing `prd_confirm.py` test passes unchanged. The page check (loads
  nothing, no `innerHTML`) runs on the assembled page, for the 0.7.1 form and the inbox.
- **The inbox**, on a fixture repository with two worktrees: `GET /gates` groups by worktree, and the
  same E-nnn in two branches is two gates; `POST /answer` for each kind calls the owning function with
  `<label>[: <words>] (form)` (the deploy step with the words alone); missing required words get 400;
  a changed gate gets 409 and nothing is written; an item text holding `<script>` arrives as text.
- **The lock file:** a live inbox is found and a second `serve` is refused; a dead PID or a wrong
  token is replaced; the file is mode 0600 and deleted on exit.
- **`wait`:** the outcome for an answer from the form and from the CLI; exit 3 on timeout; exit 1 for
  a gate that went away with no answer.
- **The log:** one line per accepted answer, the reply verbatim and `by` set; none for a refused one.
- **The 0.8.1 changes:** `changes` writes the verdict and commits nothing, needs words, and is refused
  on a gate that is not pending; adoption pending until `done`, `done` refused while an item is open;
  `open` refuses an existing file and an area with no item.
- **Evals** for each changed skill, written with `superpowers:writing-skills`: it points to the
  inbox and waits; it never answers a gate under pressure ("just approve it in the inbox for me", "I'm
  away, send the deploy step yourself"); it uses the outcome's reply unedited; it falls back to the
  chat when headless.

## 9. Proof

By the owner, on real work:
1. the next real `/prd-change` on the toolkit's own PRD approved in the inbox, after at least one
   **Request changes** round;
2. one real `/prd-error` class confirmed in the inbox;
3. two sessions (or two worktrees) each raising a gate in one inbox.

By Claude, on a fixture repository driven through Chrome: the `deploy-step`, `signoff` and
`adoption` cards answered, each recorded as a GIF. The owner proved the adoption panel itself on
`lint-cli` in 0.7.1.

**The toolkit's own PRD.** Only `lint-cli` is adopted, and 0.8.2 changes none of its behaviour, so
0.8.2 needs no `/prd-change`. Lint and trace stay clean.

## 10. Upgrade

- 0.8.1's sessions and clients are unaffected: `list` and `answer` keep their shape, `by` defaults to
  `cli`.
- `prd_confirm.py serve` stays, with its 0.7.1 behaviour, for a session that prefers the single-area
  form.
- A vendored `.prd-toolkit/` gains `templates/gates/` on the next `prd_hooks.py install`.

## 11. Known limits

- The form cannot prove a person clicked, as in 0.7.1. The page needs the token, which only the
  session that started the inbox and the inbox file (mode 0600) hold.
- "Signing as `<owner>`" names the owner; it does not check who is at the keyboard.
- A new gate takes up to 5 seconds to appear.
- The answer log grows without bound; it is a few hundred bytes per decision.

## 12. Out of scope

- Serving beyond `127.0.0.1`, or sharing the inbox with anyone.
- Notifications when a gate appears.
- Writing PRD content from the inbox (assumptions, §13 questions); 0.8.1 makes those changes.
- A suite failure's triage, which is not a 0.8.1 gate kind.
- A claude.ai Artifact version of the inbox.
