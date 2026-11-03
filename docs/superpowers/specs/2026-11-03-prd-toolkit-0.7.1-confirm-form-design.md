# prd-toolkit 0.7.1: a confirmation form for adoption — design

> **Date:** 2026-11-03
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and the 0.2 to 0.7 addenda
> (`2026-11-02-prd-toolkit-0.7-design.md` last). Where this addendum and any of them disagree, this
> addendum wins for 0.7.1.

## 1. Scope

Adoption step 3 asks the owner to confirm every `as-built` requirement, apparent bug and open
question of an area, one by one. Today it asks four items at a time in the chat, or writes a
markdown checklist (`.prd-confirm-<area>.md`) with one `implement` context pack per item. On the
toolkit's own `lint-cli` area that checklist was 2,300 lines for 20 decisions: code excerpts and
context the decision does not need, decisions far apart, and keywords typed on the right line. The
owner found it unworkable.

0.7.1 adds a **local confirmation form**: a page served on the owner's machine that shows one item at
a time, saves each answer as it is given, and lets the session know when the owner is done.

0.7.1 delivers:
- `prd_confirm.py` (`serve`, `status`) over `prdlint/confirm.py` (section 3);
- the page `templates/confirm/form.html` (section 4);
- the answers file `.prd-confirm-<area>.json` (section 5);
- adoption step 3's new route, with AskUserQuestion and the checklist file as fallbacks (section 6).

It is **proven by** the owner confirming the toolkit's own `lint-cli` area through the form (section 9).

### Decisions

| Decision | Choice |
|---|---|
| Who answers | The owner, at their own machine. Nobody else opens the form |
| Where the form runs | **A local server:** `prd_confirm.py serve` on `127.0.0.1`, a random port and a random token, Python standard library only. Not a static page (no save-as-you-go, no "done" signal) and not a claude.ai Artifact (PRD text and code would leave the machine, and every toolkit user would need Artifacts) |
| Scope | Adoption step 3 only. The item format stays generic so the other decision points (a change's approval, an error's class, a suite failure's triage, the bootstrap's open items) can adopt the form later, each as its own change |
| Layout | One item at a time, with the list of items and their state on the left |
| A correction | Described in plain words by default; an "edit the criteria" link edits the AC text in place |
| Release vehicle | Branch `feat/prd-toolkit-confirm-form`, cut from `main` at `2a06f45`; version 0.7.1 in `plugin.json`, `marketplace.json` and `web/src/data/plugins.js`. The roadmap's 0.8 keeps its number |

## 2. Components

| Path (under `prd-toolkit/`) | New or changed | Role |
|---|---|---|
| `scripts/prd_confirm.py` | new | The CLI (`serve`, `status`), a thin layer over `prdlint/confirm.py` |
| `scripts/prdlint/confirm.py` | new | Items, summaries, fingerprints, the answers file and the server |
| `templates/confirm/form.html` | new | The page; self-contained, loads nothing |
| `skills/adopting-prds/SKILL.md` | changed | Step 3's new route and its fallbacks (section 6) |
| `scripts/prdlint/hooks.py` | changed | Vendors `prd_confirm.py` with the other scripts |
| `README.md` | changed | The form, the upgrade note, the 0.7.1 changelog |

## 3. `prd_confirm.py`

Every command takes the PRD folder first. Exit codes: 0 done, 2 usage, 3 stopped without Done.

| Command | Does |
|---|---|
| `serve <PRD> --area <area> [--summaries <file>] [--port N] [--no-open] [--idle-minutes N]` | Builds the items, starts the server, opens the form in the browser (unless `--no-open`), prints the URL as its first stdout line (`url=http://127.0.0.1:<port>/?token=<token>`), and runs until Done |
| `status <PRD> --area <area>` | Prints `<answered>/<total>` and one line per open item, from the answers file; starts no server |

**The items** of an area, in this order:
1. each `as-built` requirement block of `features/<area>.md`: its ID, title, ACs, `Source:` lines and,
   per `Source:` line, the code at that file and line at that commit (`git show <commit>:<file>`, the
   line and ten lines either side);
2. each open `errors.md` entry whose `Touches:` names one of the area's IDs, or whose `Detected:`
   names the area: its ID, title, Diagnosis and the code at the line its `Detected:` cites;
3. each §13 bullet that names one of the area's IDs;
4. each `[NEEDS CLARIFICATION: …]` marker in a contract item that a block of the area names (in
   `Traces:`, or a test case's `target`), with the item's file and key.

A requirement that is not `as-built` is not an item: its answer is already in the PRD.

**Summaries.** `--summaries <file>` is a JSON mapping from item ID to one or two plain-language
sentences. `serve` exits 2 (`summary for <ID> names no item of <area>`) for a key that is not an
item, and (`summary for <ID> does not mention <ID>`) for a value that does not contain its own key;
a summary over 400 characters is refused the same way. With no file, a card shows its title and its
ACs, entry or question.

**Errors** (exit 2, nothing served): an unknown area; an area with no item; a summaries file that
breaks a rule above; a port in use when `--port` is given.

## 4. The form

**Layout.** One card at a time. On the left, the list of items grouped as Requirements, Bugs,
Questions and Settings, each with its state (open, confirmed ✓, corrected ✎, bug 🐞, someone else
?, changed since answered ⟳) and a progress bar `<answered> of <total>`. The card shows the ID, the
kind, the source location, the summary, then the ACs (a requirement), the entry's Diagnosis (a bug)
or the question; the code excerpt sits folded under "Show the code".

**Answers per kind:**

| Kind | Buttons | Text |
|---|---|---|
| Requirement | Confirm · Correct… · It's a bug… · Someone else decides… | Correct: what it should do, in plain words, or the edited AC text through the "edit the criteria" link. Bug: the intended behaviour. Someone else: who |
| E-nnn | Real bug — it should… · Intended — keep it · Someone else decides… | Real bug: the intended behaviour. Someone else: who |
| Q-nn | Yes, intended · No, fix it · or own words | Optional for the two buttons; required for own words |
| Marker | Answer | The value |

"Edit the criteria" shows each AC in its own box, marks the ones changed, and saves only those, as
their full new text. A save moves to the next open item. Any answer can be changed or undone until
Done. Keys: C confirm, R correct, B bug, S someone else, ← and → move.

**Refusals.** An answer that needs text and has none is not saved, and the card says why. Done is
disabled while any item is open or changed since answered.

**Page rules.** The page is one HTML file with its CSS and script inline; it loads nothing (no
`<script src`, `<link`, `@import` or `url(`). All item text is inserted as text, never as HTML.

## 5. The answers file and the server

**The file.** `.prd-confirm-<area>.json` at the repository root:

```json
{"prd": "<slug>", "area": "<area>", "commit": "<HEAD when served>",
 "answers": {"FR-007": {"decision": "correct", "text": "...", "acs": {"AC-007.1": "..."},
                        "fingerprint": "<sha256 of the item as served>", "at": "<ISO time>"}}}
```

`decision` is `confirm`, `correct`, `bug`, `ask`, `intended`, `answer` or `fix`; `text` and `acs` are present
when given. The server rewrites the whole file on every change, through a temporary file in the same
folder and `os.replace`. On its first run in a repository, `serve` adds the line
`/.prd-confirm-*.json` to `.git/info/exclude`, so the file is never committed.

**The server.** Standard-library `http.server`, bound to `127.0.0.1` only, on a free port unless
`--port` names one. Every request carries the token; a request without it gets 403 and changes
nothing. Requests:

| Request | Does |
|---|---|
| `GET /?token=…` | The page |
| `GET /items` | The items, their summaries, excerpts and fingerprints, and the saved answers |
| `POST /answer` | Saves one answer (item ID, decision, text, edited ACs); refuses a missing required text (400) |
| `POST /undo` | Removes one item's answer |
| `POST /done` | Exits 0 when every item is answered and none is changed since answered; otherwise 409 with the open IDs |

The server stops on Done (exit 0), on Ctrl-C or after `--idle-minutes` without a request (default
120; exit 3). The answers given so far stay in the file.

**Fingerprints.** An item's fingerprint is the SHA-256 of its text as served (the block, the entry
or the bullet, and the marker's line). On `serve`, a saved answer whose fingerprint differs from the
item's current one is shown as "changed since you answered" and counts as open.

## 6. Adoption step 3

The step's rules are unchanged: confirmation is the owner's word, item by item; a reply that names
nothing confirms nothing; each answer is written into the PRD as soon as it is applied. Its route
becomes:

1. Write one or two plain-language sentences per item into a summaries file (outside the PRD folder
   and the test roots).
2. Run `prd_confirm.py serve docs/prd/<slug> --area <area> --summaries <file>` in the background and
   give the owner the URL it prints.
3. When it exits 0, read `.prd-confirm-<area>.json`. For each answer, check its fingerprint against
   the item as it is now; a mismatch is no answer, and that item is asked again. Apply each answer
   under the step's existing rules: confirm → `live (since <version>)`; correct → `approved`, the ACs
   and test cases rewritten from the text or the edited ACs; bug or real bug → the E-nnn open, the
   requirement corrected to the intended behaviour; someone else → `approved`, an
   `[ASSUMPTION A-nn]` and a §12 `awaiting <who>` row; intended → the behaviour as requirement text
   and the entry's Resolution naming who confirmed it and when; a question's answer → into the PRD,
   "No, fix it" making the requirement it blocks a correction; a marker's value → in place of the
   marker. Then delete the answers file and the summaries file.
4. Exit 3: the owner stopped. Say how many items are answered (`prd_confirm.py status`) and that a
   new `serve` resumes; the area stays `extracted`.

**Fallbacks.** When the form cannot be served (a headless run, or the owner asks), step 3 asks with
AskUserQuestion as today, or writes the checklist file as today; a headless run still stops with
the area `extracted`.

## 7. Testing the toolkit

1. **Scripts (pytest), test-first:**
   - items, on a fixture repository with an adopted-in-progress area: exactly its `as-built` blocks,
     the excerpt at each `Source:` commit, the open entries that touch the area, its §13 bullets and
     its contract markers; an unknown area and an area with no item exit 2;
   - summaries: an unknown ID, a summary without its own ID and one over 400 characters are refused;
   - the server, driven by `urllib` against a real `serve` on a free port: no token → 403 and no
     write; an answer is written atomically; undo; a missing required text → 400; Done → 409 while
     open, exit 0 when complete; `--idle-minutes` set small → exit 3; the answers survive a restart;
   - staleness: an edited block makes its saved answer "changed" on the next `serve`;
   - the page loads nothing (no `<script src`, `<link`, `@import`, `url(`) and inserts item text as
     text;
   - `.git/info/exclude` gains the line once; the vendored copy carries `prd_confirm.py` and the page.
2. **Skill text:** pins for step 3's route, its exit handling and its fallbacks.
3. **Eval:** in a headless run on an `extracted` area, the skill takes a fallback and leaves the area
   `extracted`.

## 8. Changes to existing text

- `adopting-prds/SKILL.md`: step 3's route (section 6).
- `README.md`: the form, its commands and exit codes, the upgrade note, the 0.7.1 changelog.
- `prd-format.md`: unchanged (the answers file is not part of the PRD).

## 9. Proof

The owner confirms the 20 items of the toolkit's own `lint-cli` area (branch `feat/prd-toolkit-prd`,
at step 3) through the form, after this release merges and is installed. Pass line: every item
answered in the form; Done exits 0; every answer applied under step 3's rules with no fingerprint
mismatch; the area `confirmed` and lint at 0. The owner's notes on what was awkward go into the
record, `docs/superpowers/plans/2026-11-03-prd-toolkit-0.7.1-acceptance.md`.

## 10. Upgrade from 0.7

- Re-run `prd_hooks.py install` to vendor `prd_confirm.py`.
- No PRD needs an edit.

## 11. Known limits

- One owner at one machine: the form is not shareable, by design.
- A correction described in plain words is turned into AC and test-case text by the session after
  Done; the owner sees that text on the area's next review, not in the form.
- The form covers adoption step 3 only.

## 12. Out of scope

- The other decision points (a change's approval, an error's class, a suite failure's triage, the
  bootstrap's open items).
- Sharing the form with anyone else, or serving it beyond `127.0.0.1`.
