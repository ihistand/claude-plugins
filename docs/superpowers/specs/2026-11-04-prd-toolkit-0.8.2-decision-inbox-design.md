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
> - Sections 4 and 5 (2026-11-04, from 0.8.1's spec at 8f557b5): 0.8.1's `answer` refuses a changed
>   question only when given `--question`, so the inbox always sends the question it showed; its
>   other refusals are 400; a sign-off's reply lives only in the answer log.
> - Section 13 (owner, 2026-11-05): five fixes from the first real adoption through the 0.7.1 form (an
>   orders area of a private pack), added to 0.8.2 because four of them are in the code 0.8.2 already
>   changes. Sections 1, 2 and 8 name them.
> - Section 14 (owner, 2026-11-05): three fixes from that adoption's characterization suite, in what
>   the tester can read and what a pack states about its helpers.
> - Section 15 (owner, 2026-11-05): a suite rewrites a test whose test case changed after it was
>   written, from the same adoption.
> - Section 16 (owner, 2026-11-05): a known-failing case names the failure that counts, and the
>   checklist asks how each precondition is checked, from the same adoption's dry run.
> - Section 17 (owner, 2026-11-05): seven fixes from the same adoption's later dry runs, its
>   first fix build and its first deploy.
> - Section 13 fix 5 (owner, 2026-11-05): the check across commits is 0.8.1's existing `deleted`
>   finding of `prd_error.py check`, kept as it is, not a new message.

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
- the skills' new route: point to the inbox, wait, fall back to the chat (section 7);
- five fixes from the first real adoption: the form's idle timeout, the question choices, `status`
  after the answers file is gone, `prd_error.py new --touches -`, and a lost `errors.md` entry
  (section 13);
- three fixes from its characterization suite: a backgrounded run's output, the vendored pack's files,
  and a pack helper's stated shapes (section 14);
- a suite that rewrites a test whose test case changed since the test was written (section 15);
- a known-failing case that names its symptom, and a checklist item for how a precondition is
  checked (section 16);
- seven fixes from the same adoption's dry runs, its first fix build and its first deploy
  (section 17).

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
| `scripts/prdlint/confirm.py` | changed | Keeps the adoption items, summaries, fingerprints and answers file; builds its server on `formserver`. 0.7.1 behaviour is unchanged except section 13's fixes 1–3 |
| `scripts/prdlint/gates.py` (0.8.1) | changed | `answer_gate()` gains `by` (`form` or `cli`, default `cli`) and writes the answer log; new `serve_inbox()` and `wait_gate()` |
| `scripts/prd_gates.py` (0.8.1) | changed | New subcommands `serve` and `wait` |
| `templates/gates/inbox.html` | new | The inbox page |
| `templates/confirm/panel.html` | new | The 0.7.1 item panel (list, card, keys, Done), moved out of `form.html`, with section 13's question choices |
| `templates/confirm/form.html` | changed | Includes `panel.html`, and asks `/ping` while open (section 13, fix 1); otherwise the page the owner sees is unchanged |
| `scripts/prd_error.py`, `scripts/prdlint/errors.py`, `scripts/prdlint/rules/errors.py`, `references/prd-format.md` | changed | Section 13, fixes 4 and 5 |
| `skills/adopting-prds/SKILL.md` | changed | Section 13, fix 2: the new question choices, and a "change" whose words match the current behaviour |
| `scripts/prd_tester_guard.py`, `skills/testing-from-prds/SKILL.md`, `agents/prd-tester.md`, `references/contract-types.md` | changed | Section 14: background task output, the vendored packs folder, a shipped helper's stated shapes (with `prd-format.md`) |
| `scripts/prd_build_check.py`, `scripts/prdlint/buildcheck.py`, `skills/testing-from-prds/SKILL.md` and `dispatching.md`, `agents/prd-tester.md`, `skills/building-from-prds/running-a-build.md`, `skills/adopting-prds/SKILL.md` | changed | Section 15: `--stale` and the `Rewrite:` line |
| `references/prd-format.md`, `scripts/prdlint/rules/testcases.py`, `skills/testing-from-prds/SKILL.md`, `agents/prd-tester.md`, `skills/handling-errors/`, `skills/adopting-prds/SKILL.md`, `references/quality-checklist.md` | changed | Section 16: `symptom:` and the precondition checklist item |
| `skills/testing-from-prds/SKILL.md`, `skills/authoring-prds/dry-run-prompt.md`, `agents/prd-tester.md`, `templates/prd/testing.md`, `references/prd-format.md`, `references/quality-checklist.md` | changed | Section 17, fixes 1 and 2: a pack's helpers are imported, never copied; the Leaks slot's traceback rule |
| `skills/authoring-prds/SKILL.md`, `skills/adopting-prds/SKILL.md` | changed | Section 17, fix 3: a dry run failed only on harness conventions |
| `templates/claude-block.md`, `scripts/prd_block.py` | changed | Section 17, fix 4: the change rule names the adopted areas |
| `scripts/prd_deploy.py`, `scripts/prdlint/deploy.py`, `skills/deploying-from-prds/SKILL.md` | changed | Section 17, fix 5: `prd_deploy.py record` for a deploy done by hand |
| `skills/building-from-prds/running-a-build.md`, `skills/building-from-prds/SKILL.md` | changed | Section 17, fixes 6 and 7: a `verified` with no build-gate test, and the builder's isolation base |
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
| `POST /answer` | `{worktree, gate, question, choice, words, class?, result?}`, where `question` is the gate's `question` exactly as the page showed it: builds the reply (section 5), calls `answer_gate(…, question=<that text>, by="form")`, and returns its `result` (`{stdout, exit}`, and `stderr` when the owner printed any). 400 for required words missing, or for any other refusal (a NUL in the words, a flag the kind does not take), with the refusal's text; 409 for `refused: the gate changed; list again`, a changed or gone gate. The question is always sent, so a gate whose question changed while the owner read it is refused, never answered |
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
| `signoff` | The T-id, the case's title, `input` and `expect`, and "Signing as `<owner>`" from its `signoff:` | **Pass** · **Fail…** (words required) | The Sign-offs row, `--result pass\|fail`. The row has no reply column, so the reply, a Fail's words included, is kept only in the answer log and `wait`'s outcome, where the session reads why it failed |
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
- **The 0.7.1 form:** every existing `prd_confirm.py` test passes unchanged, except those section 13
  changes on purpose (the question labels, and `status` on a confirmed entry), which change with it.
  Section 13 lists its own tests. The page check (loads
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

## 13. Fixes from the first real adoption

The first owner adoption through the 0.7.1 form (an orders area of a private pack, 2026-11-05, 19
items) found five faults. The owner added them to 0.8.2 on 2026-11-05. Fixes 1–3 are in
`confirm.py` and the form, which 0.8.2 already moves onto `formserver`. Fixes 4 and 5 are in
`prd_error.py` and lint. None touches an adopted area of the toolkit's own PRD: `error-entries`
belongs to `lint-registries` (not started), and fix 5 adds no rule, so `lint-cli`'s `--list-rules`
list is unchanged and 0.8.2 still needs no `/prd-change` (section 9).

1. **An open form timed out while the owner was reading.** The first serve ended with exit 3 after
   120 minutes and no answer saved. The owner restarted it with `--idle-minutes 720`. The cause is
   that the page makes no request between answers, and only a request resets the idle clock.
   - **Fix.** The 0.7.1 page asks `GET /ping` (served by `formserver`, as for the inbox) every 60
     seconds while it is open. The idle timeout then counts from the last page closing, not from the
     last answer, and the default stays 120 minutes.
   - On the idle exit, `serve` prints to stderr
     `prd_confirm: stopped after <N> minutes with no page open; <a> of <t> answered, kept in <file>; serve again to go on`.
2. **The question choices read ambiguously.** The owner picked "No, fix it" on every question,
   including ones where the note answered the question or confirmed the current behaviour.
   - **Fix.** The three choices are renamed. The stored `decision` values and the answers file stay
     as they are:

     | `decision` | Old label | New label | Words |
     |---|---|---|---|
     | `intended` | Yes, intended | **Keep it as it is** | optional |
     | `fix` | No, fix it | **Change it…** | required ("What should it do instead?") |
     | `answer` | In my own words | **Answer in my own words** | required |

     Words on `fix` become required, so the skill no longer asks for them in the chat.
   - **The skill's rule** (`adopting-prds`, applying answers): a `fix` whose words describe the
     behaviour the item already states is not applied as a correction. The skill asks the owner in
     the chat, for that one item, whether they meant keep it. It never decides that itself.
   - The inbox's adoption panel (section 5) uses the same choices.
3. **`status` counts confirmed bugs as open.** The skill deletes the answers file once every answer
   is applied. Afterwards, `prd_confirm.py status` lists each bug item whose `errors.md` entry is
   confirmed but still open as `open` again: 0/5 on the orders area.
   - **Fix.** A `bug` item whose entry has a well-formed `Confirmed:` line (state `confirmed`) counts
     as answered, with or without the answers file. This holds in `open_ids`, and so in `status`,
     `done` and the adoption gate.
   - The form shows it answered with its `Confirmed:` reply. A change to it goes through
     `/prd-error`, not the form.
4. **`prd_error.py new --touches -` is refused** with `Touches: - is not defined in the PRD`, though
   `prd-format.md` says `-` means none. The session left out `--touches` and wrote `Touches: -` by
   hand.
   - **Fix.** On `new` and `propose`, `--touches -` writes `Touches: -`.
   - `-` together with an ID is refused: `Touches: - cannot be combined with IDs`.
   - Leaving out `--touches` writes no line, as now.
5. **Lint cannot see a lost `errors.md` entry that nothing cites.** A session's own write dropped
   E-001 to E-011. `prd_error.py` was not the cause: a scratch-copy run kept every entry. The
   entries were restored from HEAD. Entries are never deleted, and `prd_error.py new` numbers them
   from the highest + 1, so a gap or a missing heading is always a lost record.
   - **Fix, in the file.** `error-entries` also reports, on the heading line, an entry out of order
     or a gap in the numbers:
     `E-012 follows E-010: E-011 is missing; entries are never deleted, restore it from git`.
     The entries must run from E-001 upward with no gap and newest last.
   - **Across commits, already shipped.** A gap check cannot see the newest entries dropped.
     0.8.1's `prd_error.py check <range>` already covers that case. It compares the ledger write by
     write and reports a dropped heading as `errors.md: E-014: deleted`. 0.8.2 keeps that check and
     its wording, and adds only a test that dropping the newest entry is reported.
   - A PRD that already has a gap restores the entry from git. No migration row is needed.

**Tests** (with the rest of section 8):
- **Fix 1:** the page asks `/ping` while open (a page test on the assembled page); the server stays
  up past `--idle-minutes` while pings arrive and exits 3 once they stop; the stderr line.
- **Fix 2:** the labels on the page; `fix` with no words refused (400 from the form, exit 1 from
  `prd_confirm.py answer`); an eval in which a `fix` whose note restates the current behaviour gets a
  chat question, not a correction.
- **Fix 3:** `status` after the answers file is deleted counts a confirmed entry's item as answered,
  and a proposed one as open; `done` is not refused for a confirmed one.
- **Fix 4:** `--touches -` writes `Touches: -` on `new` and `propose`; `-,FR-001` is refused.
- **Fix 5:** a gap and an out-of-order heading each give the finding; a clean ledger gives none;
  `check` over a range that drops the newest entry reports it, and over one that only appends reports
  nothing.

## 14. Fixes from the same adoption's characterization suite

The suite run of the same adoption (2026-11-05) found three faults in what the tester can see. The
owner added them to 0.8.2 on 2026-11-05. All three are in `prd_tester_guard.py`, the tester's skill and
the references, none in an adopted area.

1. **A backgrounded harness run cannot be read.** The tester ran the suite with the Bash tool's
   `run_in_background`, and the guard then blocked the Read of the task's output file. That file is
   outside the read roots (PRD folders, scratchpad, test roots). The tester fell back to
   `--junitxml` inside a test root.
   - **Fix.** The guard allows `Read`, and only `Read`, of a file named `<id>.output` directly in the
     `tasks` folder beside the hook input's `scratchpad_dir`, where Claude Code writes background
     task output. `Glob`, `Grep`, `ls` and any write there stay blocked. When there is no
     `scratchpad_dir`, or the `tasks` folder is not its sibling, nothing more is allowed.
   - **The skill's rule** (`testing-from-prds`, suite mode): a harness run longer than the Bash
     tool's timeout runs in the background, and the tester reads its output file. It never reads
     any other task's output.
   - **Cost if wrong:** that folder also holds the caller's background tasks. A tester could read a
     caller's output by guessing its ID, but the IDs are random and the skill forbids it.
2. **The vendored pack's files cannot be listed.** The tester wanted to confirm that the helpers a
   pack ships exist, and the guard blocked `ls .prd-toolkit/packs/<name>/`.
   - **Fix.** The read roots gain the repository's `.prd-toolkit/packs/`, read-only: `Read`, `Glob`,
     `Grep` and `ls`. A pack is part of the PRD's harness, not the system under test.
   - The skill's rule 1 names it: in a write or a suite, the tester may read the vendored pack's
     files; in a dry run, only its `pack.yaml`.
3. **A pack's shipped helpers had no stated shapes.** The tester asked again and again for the
   fields of a helper's result and the type of a query helper's parameters. `prd-format.md` makes a
   helper's internals the tester's HARNESS CHOICES, but a helper the pack ships already exists, so
   its shapes are not the tester's to choose.
   - **Fix.** `prd-format.md` (Harness) and `contract-types.md` (the pack manifest) say that a helper a pack ships is stated, in
     the pack's `harness` (the Assertions or Fixtures slot), with its parameters, their types and
     the shape of its result. A helper a pack ships whose shapes are not stated is a dry-run
     question, not a HARNESS CHOICE.
   - The private pack in that adoption states its own helpers' shapes in its next release. That fix
     is not in this repository.

**Tests:**
- **Fix 1:** the guard allows a Read of `<scratchpad parent>/tasks/<id>.output`, and blocks a Glob,
  a Grep, an `ls`, a write there, a Read of any other file there, and the same Read when the
  scratchpad has no sibling `tasks` folder.
- **Fix 2:** the guard allows Read, Glob, Grep and `ls` under `.prd-toolkit/packs/`, and blocks a
  write there and a Read elsewhere in `.prd-toolkit/`.
- **Fix 3:** a pinned line in each of the two references; an eval in which a dry-run tester given a pack
  helper with no stated shape asks a question instead of choosing one.

## 15. A changed test case gets its test rewritten

In the same adoption, the owner corrected the SQL of two test cases (T-045.1, T-045.2) after their
tests were written. The next suite still ran the old tests, and they failed. A suite revises a test
only on a `Misread:` line, so only a test-misread round fixed them. The tester cannot notice on its
own: it never reads git history (rule 1), so it cannot tell that a case changed after its test.

- **`prd_build_check.py --stale <prd dir> --tids <T-ids>`.** For each dispatched T-id that a
  committed test file cites, it compares that T-id's test-case entry at two points: the last commit
  that changed the test file, and the working tree. The entries are compared as parsed YAML, so a
  change of layout alone is not stale.
  - It prints one line per T-id whose entry differs:
    `stale <T-id> <test path>: its test case changed after the test (last changed in <sha>)`.
  - It exits 0 when there is none, 1 when there is any, and 2 on a usage or tool error.
  - A T-id with no test, or whose test file is not committed yet, is never stale. A missing test is
    a write's job, and an uncommitted one is being written now.
- **The `Rewrite:` line.** A suite prompt gains one optional `Rewrite: <T-id>` line per stale T-id.
  - On it, the tester rewrites that one test from the test case as it now stands, then runs it.
    Every value still comes from the PRD. Rule 2's limits hold: no `skip`, no `xfail` and no looser
    comparison.
  - Unlike `Misread:`, it carries no quote: the whole current case is the brief.
- **The caller.** Before every suite dispatch, the caller runs `--stale` with the suite's T-ids, as
  its own Bash call, and adds a `Rewrite:` line for each stale one. This holds in
  `running-a-build.md` and in `adopting-prds` step 4, where the case above happened.
  - The suite round's state check then allows changes to those tests only, as it does for a
    misread round.
  - `--stale` exit 2 stops the dispatch. It is a tool error, never "nothing stale".
  - **The caller never edits a test** to bring it up to date, and never sends a `Misread:` line in
    place of a `Rewrite:` one. A misread is the tester's error, read against an unchanged case.
- **Why a script and not the tester.** The rule must not depend on the caller remembering which
  cases it edited, and the tester has no way to see it. `--stale` judges from git and the working
  tree alone.

None of this touches an adopted area of the toolkit's own PRD.

**Tests:**
- **`--stale`:** a case changed after its test's last commit is stale; one unchanged, or changed
  only in layout, is not; a T-id with no test or an uncommitted test is not; two test files citing
  one T-id are judged by the newer; exit codes 0, 1 and 2.
- **The skills:** pinned lines for the `Rewrite:` line in the tester's skill, the agent and
  `dispatching.md`, and for the caller's `--stale` step in `running-a-build.md` and `adopting-prds`.
- **Evals:** a caller that edited a case before the suite dispatches it with `Rewrite:`, not
  `Misread:`, and edits no test itself; a tester given `Rewrite:` rewrites that test from the
  current case and changes no other test.

## 16. A known-failing case names its failure

The same adoption's first dry run failed on two questions that the toolkit, not the PRD, should
have prevented.

1. **"Fails as its entry describes" had nothing to compare against.** A case marked
   `known-failing: E-nnn` counts as expected whenever its test fails, for any reason. So a test broken
   in some other way passes for the known bug. The session worked around it with a YAML comment on
   each such line: `# counts only when …; any other failure is a fail`.
   - **Fix: a `symptom:` key.** A test case may add `symptom: "<what the run shows while the bug is
     open>"` beside `known-failing:`. It is plain language, observable, and a single symptom.
   - A separate key, not text inside `known-failing:`, because lint, trace, the context pack,
     `prd_error.py` and `prd_change.py` all compare the `known-failing` value with an entry ID.
   - **Lint** (`test-refs`, no new rule):
     - `symptom:` without `known-failing:` is an error.
     - A `known-failing:` case with no `symptom:` gets a `warn` finding:
       `T-043.2: known-failing E-014 names no symptom; any failure would pass as it`.
     - It is a warning, not an error, so a PRD written before 0.8.2 still lints clean (the exit code
       counts errors only). It needs no edit and no migration row.
   - **The tester** (`testing-from-prds`, the agent): on a case with `symptom:`, the test treats only
     that symptom as the expected failure. It checks for the symptom and, when it sees it, raises
     the harness's own expected-failure exception.
     - The marker accepts only that exception: pytest `xfail(strict=True, raises=<it>)`, or the
       harness's equivalent, recorded under HARNESS CHOICES.
     - Any other failure reports `<T-id>: fail: not the known failure: <one line>`.
     - A case with no `symptom:` keeps today's rule.
   - **The writers.** Each skill that adds a `known-failing:` line also writes its `symptom:`, from
     the entry's Evidence or Diagnosis, never invented:
     - `handling-errors`, in a regression patch;
     - `adopting-prds`, for a confirmed bug's case.

     A symptom that the entry does not show is a question for the owner.
2. **A test case's precondition did not say how it is checked.** The private pack gives its cases a
   state, which its Harness says "is checked by the count or total it names", but a case's state named
   no count. The toolkit has the same gap for any precondition a test must confirm before it acts.
   - **Fix.** `quality-checklist.md` gains an item: every precondition or state a test case declares
     either names the check that confirms it, or the Harness (Clean state or Fixtures) says how such
     a precondition is confirmed.
   - The authoring and adopting skills run the checklist, so the gap is asked about before the dry
     run, not during it. This is a checklist line, not a lint rule, because a check's wording is not
     mechanical.

**Tests:**
- **Fix 1, lint:** `symptom:` without `known-failing:` is an error; a `known-failing:` case without
  `symptom:` is a warning, and the exit code stays 0 when it is the only finding; a case with both is
  clean.
- **Fix 1, skills:** pinned lines in the tester's skill, the agent, `handling-errors` and
  `adopting-prds`. In an eval, a suite tester on a case with `symptom:` writes a test whose marker
  accepts only that failure. In another, a test failing in another way is reported `fail: not the
  known failure`.
- **Fix 2:** the checklist line, pinned.

## 17. Fixes from the adoption's later dry runs, first fix and first deploy

The same adoption needed seven dry runs before one passed. Its first `--fixes` build and its first
production deploy followed. Every dry-run gap was a harness convention, none a behaviour. The owner
added these seven fixes to 0.8.2 on 2026-11-05. None touches an adopted area of the toolkit's own
PRD.

1. **The dry run copied the pack's helpers.** The testing skill tells a dry-run tester to write
   every helper testing.md names in its dry-run directory, "without looking whether they exist".
   For a helper the area's pack ships, that writes a copy, and the pack's Harness forbids copies.
   The tester followed the skill.
   - **Fix.** `testing-from-prds`, `dry-run-prompt.md` and the agent say that a helper the area's
     pack ships (stated in the pack's `harness`, section 14 fix 3) is never written. In every mode,
     a dry run included, the test imports it from the vendored pack, as the Harness says.
   - Only a helper testing.md names that no pack ships is written, as today.
   - Its shapes come from the pack's `harness`. An unstated shape is a question, as in section 14.
2. **A failure report printed classified values.** pytest's default long traceback prints the
   arguments of each frame, the one that raised included. A helper that held filter values and a
   query body printed them into the run's output.
   - **Fix.** The Leaks slot of `templates/prd/testing.md`, and its description in
     `prd-format.md` (Harness), require a harness to say how a failure report avoids printing the
     values a test passes:
     - for pytest, the harness commands carry `--tb=short`, or each helper that takes a value sets
       `__tracebackhide__ = True`;
     - another harness names its own equivalent.
   - `quality-checklist.md` gains the matching item: the Leaks slot says how a failure's
     traceback is kept free of test values.
   - This is a template and checklist line, not a lint rule: a harness's flags are not mechanical
     to judge.
3. **A dry run failed only on harness conventions, and still took the full loop.** Each failed
   run went back to `Draft`, through clarify, the mechanical gate and a fresh sample.
   - **Fix: a harness-only round.** In `authoring-prds` phase 6 and the adoption's dry run, a
     failed dry run counts as harness-only when every question's answer is an edit to
     testing.md's `## Harness` and to no other PRD file. A harness-only round goes like this:
     - the status stays `In review`, with no return to `Draft` and phase 3;
     - the questions go to the owner in one batch;
     - the answers are written into the Harness;
     - lint runs;
     - phase 6 runs again on a fresh sample, as today.
   - Any answer that touches another file (an AC, a test case, a contract), or a question the
     owner answers with a behaviour, makes it a full round, unchanged.
   - The fresh sample stays. It is the only evidence that the gaps are closed.
4. **The change rule did not fit a partly adopted PRD.** The CLAUDE.md block says "Every
   behaviour change starts with `/prd-change`". On a PRD that lists adopted areas, a session read
   it as covering changes outside them too, where the PRD holds nothing yet.
   - **Fix.** When the PRD has `Adopted areas:`, `templates/claude-block.md` renders the rule as
     `Every behaviour change in an adopted area (below) starts with <change rule>; outside them,
     the PRD does not govern yet`.
   - A PRD with no adoption keeps today's line.
   - `prd_block.py` writes it. A repository picks it up on its next `prd_block.py` run, and the
     release notes say so.
5. **A deploy done by hand left no record.** The owner promoted the release through the
   service's own UI, not `/prd-deploy`, so the PRD has no Deployed row for it.
   - **Fix: `prd_deploy.py record <prd dir> --env <env> --commit <sha> --reply "<owner's words>"`.**
     - It writes a run log marked `by hand`, holding the commit and the owner's words, and
       replaces that environment's Deployed row. The Run column names the run log.
     - It refuses an environment that is not in both Environments tables, and a commit that is
       not in the repository.
     - It runs nothing and moves no status. It exits 0, 1 on a refusal, or 2 on usage.
   - `prd_deploy.py check` accepts a close commit that writes only what that log records.
   - **The skill** (`deploying-from-prds`): when the owner deployed by hand, record it with
     `record`, and never write a Deployed row directly. `verified → live` still needs that
     environment's deploy-gate tests to pass in a suite run after the record. Without one, the
     row is written and every status stays.
6. **`verified` with no test of the change.** When every T-id of a block is deploy-gate, the
   build closes it `verified` without running anything that touches the change. The
   `built → verified` conditions hold vacuously, as `running-a-build.md` says.
   - **Fix.** The close report names each such block:
     `<ID>: verified with no build-gate test; its proof is the deploy gate at /prd-deploy`.
   - The status rule is unchanged, so areas tested only live still close.
7. **The isolated builder started from the wrong commit.** The Agent tool's `isolation: worktree`
   cuts the builder's worktree from the main checkout's HEAD, not from the build branch. A
   builder dispatched on a side branch (a `--fixes` branch, a feature branch) starts without the
   branch's PRD changes.
   - **Fix.** `running-a-build.md` step 3 says it: when the build branch is not the main
     checkout's HEAD, dispatch the builder without isolation, and take the no-isolation path.
   - The builder prompt gains a `Base: <sha>` line: the build branch's HEAD at dispatch. The
     builder's skill gains a first check, `git merge-base --is-ancestor <sha> HEAD`. When it
     fails, the builder stops with `QUESTIONS: worktree is not on the build branch`.

**Tests:**
- **Fix 1:** pinned lines in the three texts. In an eval, a dry-run tester on a case using a
  pack-shipped helper writes no file that defines that helper.
- **Fix 2:** the template's Leaks slot and the checklist item, pinned.
- **Fix 3:** pinned lines in `authoring-prds` and `adopting-prds`. In an eval, a dry run whose
  questions are all Harness conventions keeps the status `In review` and samples afresh.
- **Fix 4:** `prd_block.py` on a PRD with `Adopted areas:` renders the new line, and on one
  without renders today's.
- **Fix 5:** `record` writes the run log and the Deployed row, and replaces an earlier row. It
  refuses an unknown environment and an unknown commit, and `check` accepts its close commit.
  The skill's rule, pinned.
- **Fix 6:** the report line, pinned in `running-a-build.md`.
- **Fix 7:** the step 3 line and the builder's check, pinned. In an eval, a builder whose
  worktree lacks the base commit stops with the question.
