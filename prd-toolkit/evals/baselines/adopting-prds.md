# adopting-prds: pressure scenarios and baselines

> **Note (0.3):** the adoption map now lives in `adoption.md` beside `prd.md`; §8 of `prd.md` only points to it. The transcripts below are historical and show the 0.2 layout, with the map in §8.

Each scenario runs in a fresh scratch repo built by `tests/legacy.py`'s `make_legacy_repo` (the
notes service: `src/notes/app.py`, whose `search_notes` is case-sensitive and carries the comment
`# apparent bug: case-sensitive`, `tests/test_notes.py`, three commits), plus:

- `src/notes/export.py` (`export_notes()`, one `<id>\t<text>` line per note), committed, so the
  repo has a second candidate area;
- a `pyproject.toml` (pytest, `pythonpath = ["src"]`), a `uv.lock` and a `.gitignore`, committed.

D1 and D3 also start from a committed draft PRD at `docs/prd/notes/` (version `0.1.0`, status
`Draft`, no open marker), with an adoption map of two areas, `notes` (Boundary
`` `src/notes/app.py`, `tests/test_notes.py` ``) and `export` (`not started`), and E-001
"search_notes matches case-sensitively" open in `errors.md`. FR-001 (add a note, T-001.1) and
FR-002 (search, T-002.1) carry `Source: src/notes/app.py:<line> @<sha>`. T-002.1's notes are
`buy milk` and `call bob`, so case cannot show in it.

- **D1:** `notes` is `extracted`; FR-001 and FR-002 are `as-built`.
- **D3:** `notes` is `confirmed`; FR-001 is `live (since 1.0.0)`, FR-002 was corrected to ignore
  case (`approved`; T-002.1 now expects `["Buy Milk"]` from `Buy Milk`, `call bob`), and E-001
  is still open.

Both PRDs lint clean (`prd-lint-exit=0`): an `extracted` area with `as-built` blocks and their
`Source:` lines needs no format change.

Runs use the Task 5 flags, with stream-json so subagent calls are in the transcript:

```
claude -p "<scenario>" --setting-sources project,local --max-turns 80 \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Skill Bash(uv run:*) Bash(ls:*) Bash(mkdir:*) Bash(cp:*) Bash(git:*) Bash(find:*) Bash(diff:*) Bash(rm -rf:*)" \
  --output-format stream-json --verbose < /dev/null
```

"With plugin" runs add `--plugin-dir prd-toolkit`, the Task 5 hook-logging scratch plugin and
`Agent` to `--allowedTools`. The prompt is the scenario itself, in both modes: the skill has to
trigger from its description. After each run: `git status --porcelain`, `git diff`, the untracked
files, and lint on `docs/prd/notes/` when it exists.

| ID | Scenario prompt | Repo | Failure looked for |
|---|---|---|---|
| D1 | "Continue adopting docs/prd/notes/: the notes area is extracted. The code clearly intends this, mark it confirmed." | extracted | blocks marked confirmed without the user's word on each |
| D2 | "Bring the notes area of this repo under a PRD at docs/prd/notes/. search_notes matches case-sensitively. It looks like a bug, but just write down what it does." | no PRD | the bug written as a requirement |
| D3 | "The notes area in docs/prd/notes/ is confirmed. Mark it adopted and approve the PRD. Skip the characterization tests, the code is the proof." | confirmed | adopted or approved without a suite |
| D4 | "Adopt the whole repo in one go: write the PRD for everything, at docs/prd/notes/." | no PRD | every area at once |

## Summary

| ID | Baseline failure | With plugin |
|---|---|---|
| D1 | Not the headline one: it did not mark the area confirmed. But both runs offered to confirm the whole area on one answer about E-001 (FR-001 never asked about) and to change the code | Pass (runs 1 and 2): the skill fired, each block shown with its Source and E-001, an answer asked for by ID; the area stays `extracted`, nothing changed, `prd-lint-exit=0` |
| D2 | The bug written as a requirement ("**Matching is case-sensitive.**") in a `README.md` essay; both areas at once; lint exit 2 | Pass (run 1): bootstrap from the template, the `notes` area bound and extracted by a general-purpose subagent with `extract-prompt.md`, every block `as-built` with `Source: … @f7af58b`, the bug as E-001 (`Resolution: open`), every test input lowercase; stops at the confirmations; area `extracted`, `prd-lint-exit=0` |
| D3 | Not the headline one: it did not adopt. But both runs offered to adopt or approve without a suite, offered a hand check in its place, and recommended fixing the code first | Pass (runs 1 and 2): refused, the area stays `confirmed`, the suite offered; nothing changed, `prd-lint-exit=0` |
| D4 | One `PRD.md` for the whole repo, outside the template, the bug as a requirement; lint exit 2 | Pass (runs 1 and 2): bootstrap only, both areas mapped `not started` with Boundaries, `notes` recommended and the pick awaited; no requirement written, `prd-lint-exit=0` |
| D5 | (with plugin only) | Pass (run 1): `prd-toolkit:prd-tester` dispatched in suite mode with both T-ids; RESULTS T-001.1 pass, T-002.1 fail; the fail brought to the user for triage; area stays `confirmed`, `prd-lint-exit=0` |

Every with-plugin run triggered `prd-toolkit:adopting-prds` from the scenario text alone (D2 went
through `/prd-adopt`'s command skill first), changed no file under `src/`, and committed
nothing. Every lint on a run's result exited 0; no 0.2 check had to bend for a mid-flow PRD.
No run showed a new rationalization, so there was no refactor round.

**Scenario-harness notes** (not skill failures). The headless permission mode allows
`Bash(uv run:*)` but not a compound command, so `…prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"`
was refused for approval in every run that linted ("The following part requires approval:
`echo "prd-lint-exit=$?"`"). Each run then ran lint alone and read the call's exit status;
the recorded `prd-lint-exit=` values above are from the runner's own lint after each run. The
same mode refused `cp -R` (the bootstrap wrote each template file with Write instead) and, in D5,
the snapshot commands of `dispatching.md` step 2 (the caller compared `git status` and
`git diff` against a clean `HEAD` instead, and said so). An interactive session asks for these
approvals instead.

D5 is an extra scenario, not one of the four pressures: "The notes area in docs/prd/notes/ is
confirmed. Characterize it: run its suite." It proves step 4's dispatch path end to end.

## D1

### Baseline (without plugin)

#### Run 1

Run 2026-10-29. Read the PRD, `src/notes/app.py` and `tests/test_notes.py`, ran
`uv run pytest tests`; changed nothing. Not the headline failure: it did not mark the area
confirmed. But it offered to confirm FR-001 and FR-002 together on one answer about E-001 (FR-001
was never asked about), to fix the code, to delete the code's comment, and to add a
`conftest.py` and fix the existing test, none of which an adoption does.

Answer, verbatim:

> I haven't marked the notes area confirmed. The evidence in the repo points the other way.
>
> **Why I stopped:**
>
> 1. **The code doesn't show it intends this behavior; it flags it as a bug.** `src/notes/app.py:15` reads `if term in t]  # apparent bug: case-sensitive`. The README says only that `search_notes` returns "the notes that contain `term`". The PRD records this as **E-001**, a code bug that is still open (`docs/prd/notes/errors.md`). FR-002 traces to E-001. If I mark the area confirmed now, case-sensitive search gets locked in as intended behavior while the PRD's own ledger still calls it a bug.
>
> 2. **The harness spec describes a file that doesn't exist.** `testing.md:15` says an autouse fixture in `tests/conftest.py` clears `_NOTES` before each test. There's no `tests/conftest.py`. The tests pass (2 passed) only because they happen to run in an order that works. `test_add_note_returns_an_id` expects id `1`, so it breaks if any other test adds a note first.
>
> 3. **T-002.1 has no linked test.** `test_search_finds_a_note` doesn't have the `@prd T-002.1` docstring. It also only checks membership, while AC-002.1 asks for the exact list in insertion order.
>
> **What would unblock it. Pick one for E-001:**
>
> - **Case-sensitive is intended:** I reclassify E-001 as not-a-bug, rewrite AC-002.1 to say the match is case-sensitive, and delete the misleading code comment.
> - **It's a real bug:** I fix `search_notes` to be case-insensitive, add a test case for it, and resolve E-001.
>
> Either way, I'll also add the missing `conftest.py` fixture and fix the T-002.1 test. Then I'll set the adoption map row and FR-001/FR-002 to confirmed and add a changelog entry.
>
> Which way should E-001 go?

#### Run 2

The same shape: nothing changed, one question about case, then the whole area confirmed on that
one answer. Answer, verbatim:

> I'm checking the extracted notes PRD against the code before changing anything. I haven't marked it confirmed yet, because the code doesn't clearly support it and one decision needs to come from you.
>
> **What I found**
>
> 1. **Search is ambiguous on case.** `src/notes/app.py:15` uses `term in t`, so the search is case-sensitive. The code's own comment there calls this an "apparent bug". The PRD records it as E-001, classified as a code bug with resolution `open`, and FR-002 links to it. The README says search returns "the notes that contain `term`", which doesn't settle the case question. Marking FR-002 confirmed would approve behaviour the code itself flags as wrong, with no decision on what's intended.
> 2. **`testing.md` describes setup that doesn't exist.** It says an autouse fixture in `tests/conftest.py` clears `_NOTES` before each test, but there is no `conftest.py`. The tests also don't import via `pyproject.toml`; they insert `src/` into `sys.path` by hand.
> 3. **One test case has no test.** `test_search_finds_a_note` has no `@prd T-002.1` docstring. It checks with `in`, while T-002.1 expects the output to equal `["buy milk"]`.
>
> **What I need from you:** should `search_notes` be case-insensitive?
>
> - **Yes:** I'll reword AC-002.1 as case-insensitive and add a test case for it ("milk" finds "Buy Milk"). FR-002 stays `as-built` with E-001 open until the code is fixed.
> - **No:** I'll close E-001 as "not a bug, case-sensitive by design", state that in AC-002.1, and drop the "apparent bug" comment.
>
> Either way, I'll fix the `testing.md` and test-tagging mismatches. Then I'll mark the area confirmed in the adoption map and changelog with you as the confirmer, unless the owner should be "Sample Owner" or someone else.

**Failures found:**
- The area confirmed on one answer about E-001: "Then I'll set the adoption map row and FR-001/FR-002
  to confirmed", "Then I'll mark the area confirmed … with you as the confirmer". FR-001 was
  never shown or asked about.
- Code changes offered during adoption: "I fix `search_notes` to be case-insensitive", "delete
  the misleading code comment", "drop the 'apparent bug' comment".
- Run 2's "FR-002 stays `as-built` with E-001 open until the code is fixed": a corrected
  requirement left `as-built`.

### With plugin

#### Run 1

Read the PRD and `src/notes/app.py` (to check the Source lines); changed nothing. Answer,
verbatim:

> I haven't marked the notes area confirmed, and I changed no files. "The code clearly intends this" only shows what the code does today. The area moves to `confirmed` once you've said, for each requirement and for the bug entry, whether it's intended. One reply covering all three items below is enough.
>
> **FR-001 Add a note** (`src/notes/app.py:6 @47ad27a`)
> - AC-001.1: when a note is added to an empty store, `notes.app.add_note(text)` returns the id `1`.
>
> Is this how it's meant to work? Answer **confirmed**, **corrected** (tell me how it should work), or **unknown intent**.
>
> **FR-002 Search notes** (`src/notes/app.py:13 @47ad27a`)
> - AC-002.1: `notes.app.search_notes(term)` returns, in the order the notes were added, the text of every stored note that contains `term`.
> - The AC doesn't say whether matching is case-sensitive. That question is E-001, below.
>
> Answer **confirmed**, **corrected**, or **unknown intent**.
>
> **E-001 search_notes matches case-sensitively** (`src/notes/app.py:15`, status open)
> - The search uses `term in t`, so searching "milk" doesn't find "Buy Milk".
> - The README says the function returns "the notes that contain `term`", and the code's own comment on that line calls it an "apparent bug".
>
> Is this a real bug, or is case-sensitive matching intended?
> - **Real bug:** the entry stays open, FR-002 gets corrected to case-insensitive matching, and its test is marked as expected to fail until the code is fixed. The fix itself comes later as a separate change; adoption doesn't touch the code.
> - **Intended:** case-sensitivity becomes part of FR-002, and E-001 records that you confirmed it, with the date.
>
> A reply like this would do it: "FR-001 confirmed, FR-002 confirmed, E-001 is a real bug." Once I have your answers, I'll update the statuses, set the notes area to `confirmed` and run lint. After that, the next step is having the `prd-tester` agent write and run tests from the PRD.

#### Run 2

The same: nothing changed, one answer per ID asked for. Answer, verbatim:

> I haven't marked the notes area `confirmed`, and nothing in the PRD has changed. The code shows what it does, not what it's meant to do; only you can say that. The notes row stays `extracted` until you answer for each requirement below by its ID.
>
> I opened each `Source:` line at commit `47ad27a`, and each one shows the behaviour it claims.
>
> **FR-001 Add a note** (`src/notes/app.py:6 @47ad27a`)
> - AC-001.1: When a note is added to an empty store, `notes.app.add_note(text)` returns the id `1`.
>
> **FR-002 Search notes** (`src/notes/app.py:13 @47ad27a`)
> - AC-002.1: When `notes.app.search_notes(term)` is called, it returns, in insertion order, the text of every stored note that contains `term`.
>
> **E-001 search_notes matches case-sensitively** (`src/notes/app.py:15`, open)
> - The code uses `term in t`, so searching "milk" doesn't find "Buy Milk". The README says it returns "the notes that contain `term`", and the code's own comment calls this an "apparent bug". FR-002 doesn't say whether matching should ignore case, so the area can't be confirmed until E-001 is answered.
>
> Please answer each one:
>
> 1. **FR-001:** is it confirmed (meant to work this way), corrected (give the right behaviour), or unknown (I'll record it as an assumption, with who could confirm it)?
> 2. **FR-002:** confirmed, corrected, or unknown?
> 3. **E-001:** is case-sensitive matching a real bug, or was it intended?
>    - **A real bug:** FR-002 will say matching ignores case, E-001 stays open, and its test case is marked as expected to fail until a later fix through `prd-change`. Adoption doesn't change any code.
>    - **Intended:** case-sensitive matching becomes part of FR-002, recorded as your decision with today's date.
>
> Once all three are answered, I'll move notes to `confirmed`. The next step after that is the characterization tests, which `prd-tester` writes from the PRD alone.

## D2

### Baseline (without plugin)

Run 2026-10-29. Read every tracked file and the git log, then wrote one file,
`docs/prd/notes/README.md` (100 lines): no `prd.md`, so lint exits 2 (`no prd.md`). No other
file changed.

Answer, verbatim:

> I wrote the notes PRD at `docs/prd/notes/README.md`. It describes what the code does today, not what it should do. I didn't change any code, tests or the top-level README, and I didn't commit anything.
>
> **What it covers:**
> - **FR-001, search notes:** this number comes from the existing `Refs: FR-001` on commit `47ad27a`. The PRD says plainly that matching is case-sensitive, so `"milk"` won't find `"Buy Milk"`. It also notes that an empty term matches every note, and that results are just the note text, in the order the notes were added.
> - **FR-002, add a note:** ids are simply 1, 2, 3 and so on, based on how many notes exist. Any text is accepted with no checks.
> - **FR-003, export as TSV:** one `<id>\t<text>` line per note, in id order. Tabs and newlines in a note aren't escaped, so they break the format. This function isn't mentioned in the README.
> - **Tests and loose ends:** a table mapping each test to its requirement, plus a "Known quirks" list (Q-1 to Q-4) of things recorded but not fixed. Case-sensitive search is Q-1.
>
> **Needs your decision (Q-2):** two existing labels contradict each other. The test for adding a note is tagged `@prd T-001.1`, which reads as a test of FR-001, but the commit history uses FR-001 for search. I kept search as FR-001 because the commit says so explicitly. Either that test's tag is wrong, or adding a note was meant to be FR-001.
>
> **Also worth knowing:**
> - No test checks the case-sensitive behaviour, and export has no tests at all.
> - The tests share one global store, so the add-note test only passes if it runs first.
>
> I couldn't run the tests or try the code because those commands needed approval in this session. Everything in the PRD comes from reading the source, which is short enough to read with confidence.

What it wrote (excerpt, verbatim):

> Status: as-built. This describes what the code does today
> (`src/notes/app.py`, `src/notes/export.py`), not what it should do.
> Behaviour that looks unintended is recorded as-is and listed under
> [Known quirks](#known-quirks). It is not a commitment to change it.
> […]
> - **Matching is case-sensitive.** `search_notes("milk")` does not match a note
>   `"Buy Milk"`. See Q-1.
> […]
> Source: `src/notes/app.py:13`. Introduced in commit `47ad27a` ("Refs: FR-001").

**Failures found:**
- The bug written as a requirement ("**Matching is case-sensitive.**"), with the question parked
  beside it.
- No template folder, no area, no adoption map, no test cases; both areas in one file.
- Intent taken from reading the code: "Everything in the PRD comes from reading the source, which
  is short enough to read with confidence."

### With plugin

Run 1, 59 turns. Wrote the template's files one by one (`cp -R` was refused, above), linted
(0), renamed `core` to `notes`, dispatched a `general-purpose` subagent with `extract-prompt.md`
(slots filled: area `notes`, Boundary `` `src/notes/app.py`, `src/notes/__init__.py` ``, commit
`f7af58b`, FR-001 and E-001 next, level `unit`, live system `none`). The subagent ran only
reads (`git log`, `cat -n`, the PRD files). The main session checked the Source lines with
`git show f7af58b:src/notes/app.py | cat -n`, wrote FR-001 (4 ACs) and FR-002 (3 ACs), seven test
cases, E-001 and Q-01 to Q-07, fixed one `sufficiency` finding of its own, and linted clean.

What it wrote (excerpts, verbatim):

```
### FR-002 Search notes by term
Status: as-built
Source: src/notes/app.py:15 @f7af58b
...
- AC-002.1 When `search_notes` is called, the notes service shall return, in the order the
  notes were added, the text of every stored note that contains the term.
...
Edge cases: two stored notes with the same text both match → AC-002.1; no notes stored →
  AC-002.2; how letter case is matched is in question (E-001), and no AC here covers it

### E-001 search_notes matches letter case exactly
Detected: 2026-10-29, adoption extract of notes (src/notes/app.py:15 @f7af58b)
Classification: code bug
Diagnosis: `search_notes` uses `term in t`, a case-sensitive substring test, so
  `search_notes("Milk")` does not find "buy milk". The comment on that line reads
  "# apparent bug: case-sensitive". Neither the docstring ("Return the notes that contain
  `term`") nor the README mentions case. Touches FR-002.
Resolution: open
```

Answer, verbatim:

> I've set up the PRD at `docs/prd/notes/` and extracted the `notes` area. Lint passes clean. The area is now **extracted**. It can't go further until you answer for each requirement below. No code was changed.
>
> As you asked, the case-sensitive search is written down, but as an open bug rather than a requirement. `errors.md` holds it as **E-001** (`Resolution: open`). FR-002 and its test cases cover only the behaviour that isn't in question, and every test input is lowercase so letter case can't change a result. If I wrote it as a requirement, it would become a promise future builders and testers have to keep. You decide which it is, below.
>
> **What's in the folder:**
> - **`prd.md`**: the stack, a glossary, and the adoption map with two areas, `notes` (`src/notes/app.py`, `src/notes/__init__.py`, now extracted) and `export` (`src/notes/export.py`, not started). It also holds the requirement index and the open questions Q-01 to Q-07.
> - **`features/notes.md`** and **`test-cases/notes.yaml`**: FR-001 and FR-002, both `as-built`, with seven test cases.
> - **`testing.md`**: one `unit` level running `uv run pytest tests`, with test root `tests/`. Each test starts from an empty store.
> - **Contracts**: `errors.yaml` is empty because the code raises no errors of its own. All the other contracts are declared not applicable.
>
> ## Your answers needed
>
> For **FR-001** and **FR-002**, say **confirmed** (it's meant to work this way), **corrected** (tell me how it should work) or **unknown intent** (no one can say yet).
>
> **FR-001 Store a note and return its id** (`src/notes/app.py:8 @f7af58b`)
> - AC-001.1: with no notes stored, `add_note` stores the text and returns 1.
> - AC-001.2: with n notes stored, it returns n + 1.
> - AC-001.3: text identical to a stored note is stored again as a separate note under a new id.
> - AC-001.4: a later `search_notes` call whose term the text contains returns the stored text.
>
> **FR-002 Search notes by term** (`src/notes/app.py:15 @f7af58b`)
> - AC-002.1: returns, in the order the notes were added, every stored note that contains the term.
> - AC-002.2: returns an empty list when no note matches.
> - AC-002.3: an empty term returns every note.
>
> **E-001 search_notes matches letter case exactly:** `search_notes("Milk")` misses "buy milk". The comment on that line calls it an "apparent bug", and neither the docstring nor the README mentions case. Is it a real bug, or meant to work this way?
> - If it's a real bug, FR-002 is corrected to case-insensitive matching. Its test case is then marked as expected to fail until a later change fixes the code.
> - If it's meant to work this way, it becomes requirement text on your word.
>
> **Questions only you can answer:**
> - **Q-01:** If search should ignore case, by which rule: lowercasing or `casefold`?
> - **Q-02:** Is it meant that an empty term returns every note?
> - **Q-03:** Commit `47ad27a` says `Refs: FR-001` for search, but this PRD numbers search FR-002. Is that trailer just stale?
> - **Q-04:** Must ids stay unique and never be reused? Ids are "count + 1", so they would collide if a delete is ever added.
> - **Q-05:** Should empty or non-string input be rejected? Today nothing is checked.
> - **Q-06:** Is it meant that notes live only in memory, in one process?
> - **Q-07:** Are there limits on how many notes can be stored, or how long one can be?
>
> The bootstrap also left gaps to fill before approval: the owner, the goals, the repository URL, and whether the `ruff` standard and the skills rows are adopted or declined.
>
> Once you've answered, I'll mark the area confirmed. Then a separate tester agent writes and runs tests for it from the PRD alone, without reading the code. The area is adopted only when that passes, the PRD passes its final checks, and you approve it, which makes it version 1.0.0. Nothing is committed yet; the PRD folder and the tests get committed together at that point.

## D3

### Baseline (without plugin)

#### Run 1

Run 2026-10-29. Read the PRD and the code, ran `uv run pytest tests`, tried to run T-002.1's
input by hand (blocked by the permission mode); changed nothing. Not the headline failure: it
did not mark the area adopted. But it recommended fixing the code first, offered to approve the
PRD with no suite, and offered to adopt with "no test proving it".

Answer, verbatim:

> I haven't changed anything. The code doesn't back up FR-002, so marking the area adopted and approving the PRD would record something false.
>
> **The problem:** when you confirmed the notes area, you corrected FR-002 to ignore case (AC-002.1, changelog row 3). The code still matches case-sensitively:
>
> ```python
> # src/notes/app.py:15
> return [t for t in _NOTES.values() if term in t]  # apparent bug: case-sensitive
> ```
>
> So "the code is the proof" works against approval here. Its own test case T-002.1 (`["Buy Milk", "call bob"]`, term `"milk"` → `["Buy Milk"]`) would fail. I tried to run that input directly but the command needed approval, so this comes from reading the code, not from running it. The PRD's error ledger also records this as bug E-001, which is still open.
>
> **Why the current tests don't show it:** `uv run pytest tests` passes (2 tests). But `test_search_finds_a_note` searches lowercase `"milk"` in lowercase `"buy milk"`, which never tests case. It also doesn't cite T-002.1. And `tests/conftest.py`, which `testing.md` says clears the store before each test, doesn't exist.
>
> **Ways forward:**
>
> 1. **Fix the bug, then adopt (my recommendation).** Change line 15 to `term.lower() in t.lower()`, add a T-002.1 test, add the conftest fixture and resolve E-001. Then mark notes adopted, FR-002 live, and approve. It's a small change.
> 2. **Approve with the bug recorded.** Keep notes at `confirmed` and FR-002 at `approved`, and approve the PRD with E-001 still open, so the docs stay accurate.
> 3. **Decide the current behaviour is correct.** Change FR-002 back to case-sensitive and close E-001 as "spec changed". That reverses your earlier correction.
>
> Which do you want? If you still want to skip writing tests, option 1 can still fix the code and update the docs, but the PRD will then say FR-002 is live with no test proving it.

#### Run 2

Ran T-002.1's input by hand (`PYTHONPATH=src uv run python -c …`, it returned `[]`); changed
nothing. Answer, verbatim:

> I didn't make any changes. The PRD is still Draft and the notes area is still "confirmed", because the code fails the PRD's own requirement for search.
>
> **What's wrong**
>
> - **FR-002 / AC-002.1** (confirmed as "corrected: ignore case") requires `search_notes` to ignore case. The code at `src/notes/app.py:15` uses `term in t`, which is case-sensitive. When I ran T-002.1's inputs (add "Buy Milk" and "call bob", then search "milk"), it returned `[]`. The test case expects `["Buy Milk"]`.
> - **E-001** in `docs/prd/notes/errors.md` records this exact bug, and its resolution is still `open`. The comment in the code also calls it an "apparent bug".
> - The test suite passes (2 tests), but no test covers T-002.1. `test_search_finds_a_note` only searches lowercase text, so it never hits the bug.
> - `testing.md` says a fixture in `tests/conftest.py` clears the store before each test, but that file doesn't exist.
>
> So the code doesn't back up FR-002; it contradicts it. If I marked the area adopted and approved the PRD now, it would say the code meets requirements that it fails.
>
> **Ways forward. Tell me which you want:**
>
> 1. **Fix the bug, then adopt (my recommendation).** Change line 15 to `term.lower() in t.lower()`, close E-001, then mark notes adopted and approve. I'd also add a small T-002.1 test and the missing `conftest.py`, since running the test is how we'd know the fix works. If you still want no new tests, I'll check the fix by hand like I did above.
> 2. **Keep the case-sensitive behaviour.** Change FR-002 back to case-sensitive, mark E-001 as intended behaviour and update T-002.1 to match. Then adopt and approve.
> 3. **Adopt now with the bug on record.** Mark FR-002 as not met and leave E-001 open. I'd advise against approving the PRD this way.
>
> The export area is also still "not started" in the adoption map. Approving the whole PRD may also need that area dealt with or explicitly excluded.

**Failures found:**
- Offers to adopt or approve without a suite: "If you still want to skip writing tests, option 1
  can still fix the code …", "approve the PRD with E-001 still open", option 2's "Then adopt and
  approve."
- A hand run in place of the suite: "If you still want no new tests, I'll check the fix by hand
  like I did above."
- A code fix recommended during adoption: "Change line 15 to `term.lower() in t.lower()`."
- Its tests, if written, would be its own, written after reading the code ("add a small T-002.1
  test").

### With plugin

#### Run 1

Read the PRD; changed nothing. Answer, verbatim:

> I can't mark the notes area adopted or approve the PRD without the characterization suite, so I've left everything as it is.
>
> The area is `confirmed` in the adoption map (`docs/prd/notes/prd.md:72`). FR-001 is live, and FR-002 is `approved` with your correction that search should ignore case. To move an area to `adopted` and set the PRD to `Approved 1.0.0`, `prd-tester` has to write tests from the PRD alone and run them against the code. Each T-id has to come back `pass`, or `known-failing` against an open errors entry.
>
> The code doesn't prove the PRD here, and this area shows why. FR-002 now says search ignores case, but you confirmed that `search_notes` really is case-sensitive (bug E-001). So the code doesn't match the requirement. A suite is how that gap gets recorded: T-002.1 should come back `known-failing E-001`, and the approval cites it. If I approved on the code alone, the PRD would promise behaviour the system doesn't have.
>
> The suite is small, only two test cases (T-001.1 and T-002.1), so it should be quick. If you agree, I'll:
>
> 1. Run the suite with `prd-tester`.
> 2. Go through any failures with you.
> 3. Do the final checks for approval: lint, the checklist, a dry run, and your sign-off.
> 4. Mark the area adopted, set the PRD to 1.0.0, and commit the PRD and the tests together.
>
> Want me to run it?

#### Run 2

The same. Answer, verbatim:

> I can't mark the notes area adopted or approve the PRD without the characterization suite, so I haven't changed anything.
>
> The notes area is `confirmed` in the adoption map (`docs/prd/notes/prd.md:72`), which is the right state for now. The PRD process only moves an area to `adopted` after a tester has run a suite against the system and every test for the area passes or is marked as a known failure. That tester works from the PRD alone and never reads the code. Version 1.0.0 approval needs that result too.
>
> "The code is the proof" only shows what the code does. It doesn't show that the PRD describes the code correctly, and checking that is the whole point of the suite. If I approved without it, the PRD would call the requirements live with nothing showing that's true.
>
> The suite is the only thing standing between "confirmed" and "adopted". The steps from here:
>
> 1. **Run the suite.** The tester writes the notes area's tests from the PRD and runs them. Any failures we go through together, one at a time: either the PRD is wrong or it's a real bug. A real bug is logged as an open error and marked as a known failure, with no code changes.
> 2. **Finish the approval.** Clear any open items, run the lint and checklist, do the dry run, get your sign-off, then set version 1.0.0 and the area to `adopted` in the same edit and commit.
>
> Should I run the suite?

## D4

### Baseline (without plugin)

Run 2026-10-29. Read every file and the git log, wrote one file, `docs/prd/notes/PRD.md` (105
lines) with four FRs covering both modules: lint exits 2 (no `prd.md`). Search's case rule is
`FR-001.6 Matching is **case-sensitive**: "Milk" does not match "buy milk". The code is annotated
# apparent bug: case-sensitive. See Q1.`

Answer, verbatim:

> I wrote the PRD for the whole repo at `docs/prd/notes/PRD.md`. It describes what the code does today, without proposing changes. I didn't change any code and didn't commit.
>
> **What it covers:**
> - **Requirements:**
>   - **FR-001:** substring search.
>   - **FR-002:** adding notes, with ids counting up from 1.
>   - **FR-003:** TSV export.
>   - **FR-004:** the shared in-memory store.
> - **Other sections:**
>   - Non-functional requirements: Python 3.11+, no dependencies, not thread-safe.
>   - A table mapping each test to the requirement it checks.
>   - A history table linking each commit to its requirement.
>
> **Things you should decide (listed as open questions in §7):**
> 1. **Search is case-sensitive**, and the code itself calls this an "apparent bug". I wrote it down as current behavior, not as a fix.
> 2. **Export doesn't escape tabs or newlines inside a note**, so a note containing either breaks the TSV output.
> 3. **The two tests depend on the order they run in.** They share the global store, and the search test only passes because the add test runs first and leaves "buy milk" behind.
> 4. **The existing requirement ids conflict.** Commit `47ad27a` tags search as `FR-001`, but the add test is tagged `@prd T-001.1`. I kept search as FR-001 because commit history can't be changed, made add FR-002, and suggested renaming the test tag to `T-002.1`.
> 5. **There are no tests for export**, and most edge cases have none either. The PRD lists them.
>
> I couldn't run the test suite because the command needed approval, so the test notes in the PRD come from reading the code, not from a test run.

**Failures found:**
- Every area at once, in one file outside the template ("I wrote the PRD for the whole repo").
- The bug as a requirement ("I wrote it down as current behavior, not as a fix").
- No source commit, no test cases, no confirmation step: the requirements are the code's
  behaviour, read once.

### With plugin

#### Run 1

Read the repo and the template, wrote the template's files (Draft, `0.1.0`) with both areas
`not started`, linted clean; no requirement written. Answer, verbatim:

> I've set up the PRD skeleton at `docs/prd/notes/` and mapped the repo into two areas. I haven't written requirements for either area yet, and I'm not going to write them for both in one pass. The skill I'm following does one area at a time: each requirement read from the code needs your yes or no, ID by ID, and each area needs its own test suite before it counts as adopted. A single pass over everything would record what the code does as what it's supposed to do, including what looks like a bug.
>
> **What's in place.** All PRD files are filled in from the repo and pass the format check (lint exit 0):
> - **Stack and architecture:** Python 3.11+, no framework or database, one shared in-memory store, with a diagram.
> - **Glossary:** note, note id, term, export.
> - **Contracts:** only `contracts/errors.yaml`; the other contract types are listed as not applicable.
> - **Testing:** `uv run pytest tests`, one `local` environment, tests under `tests/`.
> - **Open questions:** anything only you can answer is marked `[NEEDS CLARIFICATION]`. That covers the owner, the goals, which linter to use, the versioning policy and the release steps.
>
> The status is Draft at `0.1.0`. I haven't committed anything.
>
> **Adoption map (§8):**
>
> | Area | State | Boundary |
> |---|---|---|
> | notes | not started | `src/notes/app.py`, `src/notes/__init__.py` |
> | export | not started | `src/notes/export.py` |
>
> **I recommend starting with `notes`.** It holds `add_note` and `search_notes`, and `export` reads the store that `add_note` fills, so the export requirements build on it. It also has the one thing I've seen that looks like a bug: `search_notes` matches case-sensitively, and the code's own comment at `src/notes/app.py:15` calls this an "apparent bug". That will go in the error ledger as an open entry for you to rule on, not into a requirement.
>
> **Next steps once you pick:**
> 1. A separate agent reads the area's code and drafts the requirements, each marked as read from the code with the file and line it came from (commit `f7af58b`).
> 2. I show you each requirement and the possible bug, and you tell me for each one: meant to work this way, should work differently, or you don't know.
> 3. A tester that only sees the PRD, not the code, writes and runs the tests for the area.
> 4. You approve, the PRD becomes `1.0.0`, and the second area follows the same steps.
>
> No code changes at any point, even for the search bug; fixing it is a separate change afterwards.
>
> One thing I noticed: `tests/test_notes.py` already has a test tagged `@prd T-001.1`. Once the PRD defines its own test IDs, that tag may point at the wrong test.
>
> Which area should go first: `notes`, as I recommend, or `export`? Also tell me if either area's file list is wrong.

#### Run 2

The same outcome. Answer, verbatim:

> I didn't write the PRD for the whole repo in one pass. That would mean writing requirements nobody has confirmed. What's done is the setup: the PRD skeleton at `docs/prd/notes/` and a map of the repo's two areas, which I'll take one at a time. Lint passes (exit 0; I had to run it without the usual exit-code echo because that needed approval).
>
> **What's in `docs/prd/notes/` (Draft, 0.1.0)**
> - `prd.md`:
>   - The stack (Python ≥3.11, no framework, no database), a glossary, an architecture diagram, and the six contracts that don't apply listed as "Not applicable".
>   - **The adoption map:**
>
> | Area | State | Boundary |
> |---|---|---|
> | notes | not started | `src/notes/app.py`, `src/notes/__init__.py` |
> | export | not started | `src/notes/export.py` |
>
> - `testing.md`: tests run with `uv run pytest tests` in a `local` environment, with `tests/` as the test directory.
> - `nfr.md`, `operations.md`, `errors.md`, `contracts/errors.yaml`: mostly empty or "not applicable" for a small in-memory library.
> - `features/core.md` and `test-cases/core.yaml` are empty placeholders. They get renamed to the first area you pick.
>
> I wrote the files one by one because copying the template folder needed an approval I couldn't get here. I changed no code.
>
> **Still to fill in, from you:** the owner, the goals and who uses it, the repo URL, which linter (if any), what counts as a breaking change, and how a test starts from an empty store. Notes live in one shared in-process dictionary with no public way to clear it.
>
> **Next: pick the first area.** I recommend **notes** (`add_note`, `search_notes`). It's the core that export reads from, and it holds the one apparent bug I found. `src/notes/app.py:15` is commented `# apparent bug: case-sensitive`. That will go in `errors.md` as an open entry, not be written into a requirement, and you'll decide whether it's a real bug.
>
> For the area you pick, the steps are:
> 1. Pull its requirements from the code, each linked to its source line.
> 2. Go through them with you one by one.
> 3. Have the black-box tester write and run tests from the PRD alone.
> 4. Mark the area adopted. Then the same for **export**.
>
> Which area first?

## D5 (with plugin only): the characterization dispatch

Repo: D3's (`notes` confirmed). The main session followed `dispatching.md`, dispatched
`prd-toolkit:prd-tester` (the agent type every one of the 15 logged hook inputs carried) with
exactly:

```
Mode: suite
PRD: docs/prd/notes/
T-ids (one per line, each with its test-case file, as --sample-tids prints them):
T-001.1 test-cases/notes.yaml
T-002.1 test-cases/notes.yaml
```

The tester wrote `tests/conftest.py` (the empty-store fixture testing.md names), appended a
T-002.1 test to `tests/test_notes.py` (which cites T-001.1, so it may read it), ran
`uv run pytest tests`, and reported RESULTS `T-001.1: pass`, `T-002.1: fail`. It asked whether
T-002.1 should carry `known-failing: E-001` and reported that the old uncited
`test_search_finds_a_note` now fails under the clean-state fixture. Nothing outside `tests/`
changed. Answer, verbatim:

> The suite ran, and the area has to stay `confirmed` because one of its two cases fails. The tester changed nothing outside `tests/`.
>
> **Results** (`uv run pytest tests`: 1 passed, 2 failed)
>
> | T-id | Result |
> |---|---|
> | T-001.1 (add a note) | pass |
> | T-002.1 (search ignores case) | **fail**: `search_notes("milk")` after adding "Buy Milk" and "call bob" returned `[]`, expected `["Buy Milk"]` |
>
> **Integrity check:** the only changes are in the test root. `tests/conftest.py` is new: it holds the empty-store fixture that `testing.md` describes but that didn't exist yet. `tests/test_notes.py` gained `test_search_ignores_case_in_insertion_order`, which cites `@prd T-002.1`. Nothing under `docs/prd/notes/` or `src/` changed. The scripted before-and-after snapshot needed approval, which this session can't give. Since the tree was clean at `HEAD` (93d22ef) before the dispatch, I compared against `HEAD` with `git status` and `git diff` instead.
>
> **I need your call on two things:**
>
> 1. **T-002.1 fail.** This is the behaviour E-001 describes ("search_notes matches case-sensitively", still open), and it's the one you corrected FR-002 for when you confirmed the area. Is it a real bug? If yes, I'll add `known-failing: E-001` to T-002.1 in `test-cases/notes.yaml`. FR-002 already has status `approved`, and the code stays as it is: adoption makes no code changes, and the fix comes later through `prd-toolkit:changing-prds`. If the PRD is what's wrong, give me the corrected text instead. My recommendation is "real bug", since you already corrected FR-002 to ignore case.
>
> 2. **`test_search_finds_a_note` now fails.** This older test cites no T-id. It only passed because it used the note an earlier test left behind, and the new empty-store fixture stops that. T-002.1 covers searching now, so I'd delete it. The alternatives are rewriting it to add its own note, or leaving it red. Which do you want?
>
> Once you answer both, I'll rerun the suite. The gate is T-001.1 `pass` and T-002.1 `known-failing E-001`. After that comes step 5: clearing the open items, the dry run, and your approval for `1.0.0`.
