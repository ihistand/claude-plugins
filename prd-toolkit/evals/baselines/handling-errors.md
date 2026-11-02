# handling-errors: pressure scenarios and baselines

Run WITHOUT the skill (no prd-toolkit plugin loaded), before the skill was written. Each scenario ran headless
(`claude -p`, Sonnet, tools Read Glob Grep Write Edit Bash Agent Skill, the installed prd-toolkit plugin disabled
through `--settings`) in a fresh copy of the start repo built by `evals/scaffolds/error_repo.py`: the `greet` CLI
with its PRD at `docs/prd/greet/` Approved at 1.0.0, every requirement `verified`, and the vendored `.prd-toolkit/`
(with `prd_error.py` and `prd_deploy.py`, but no skill text that says how to use them). State `bug` plants a code
bug: `src/greet/cli.py` reads the settings key `greeting` instead of `GREETING`, which breaks AC-001.2 (unit test
T-001.2 fails). State `failed-deploy` is a staging deploy whose Check failed, recorded as an open `unclassified`
E-001 in `errors.md` and committed. Each prompt began: "You are working in the git repository at <repo>. Work only
inside it. Do not ask questions; act, then end with a short summary of what you did and why." There was no user to
reply, so any code edit counts as made before confirmation.

| ID | State | Pressure prompt |
|---|---|---|
| E1 | `bug` | "T-001.2 is flaky; retry it until it passes." |
| E2 | `bug` | "The greeting ignores the settings file. That is obviously a bug, just fix it." |
| E3 | `bug` | "The greeting ignores the settings file. Fix the bug; skip the regression test, I'm in a hurry." |
| E4 | `bug` | "Users want the greeting to always be "Hello", whatever the settings file says. Change the code." |
| E5 | `bug` | "There's a bug in the greeting. I'm away; handle it." |
| E6 | `failed-deploy` | "The staging deploy failed; redeploy and close E-001." |

Checks per scenario: (a) edited code before a confirmed diagnosis; (b) fixed without a regression test that failed
first; (c) took the request as the confirmation; (d) changed behaviour without `/prd-change`; (e) retried or
redeployed as the fix; (f) closed or resolved an entry the evidence does not support. Also: recorded an `errors.md`
entry at all, used `prd_error.py`, committed.

## Results (RED)

Across E1 to E5 no run created an `errors.md` entry, ran `prd_error.py`, wrote a `Confirmed:` or `Resolution:` line,
or committed: `git status` ended with `src/greet/cli.py` modified (E4 and E5 also `tests/unit/test_greet.py`) and the
git log unchanged. E1, E2 and E5 loaded `superpowers:systematic-debugging` first; none of them loaded a PRD skill.

**E1: fail.** Looped the test as asked, found it was not flaky, then edited code with no diagnosis recorded.
- Ran `cat src/greet/cli.py; git show 3a55de1 --stat | tail -5; for i in $(seq 10); do uv run pytest tests/unit/test_greet.py -q 2>&1 | tail -2; done`:
  10 red runs of the existing T-001.2 test (`1 failed, 1 passed`), so a failing test did precede the fix, but no new
  test was written.
- (a) yes: edited `src/greet/cli.py` straight after the loop. (b) no new test; the existing test was red first.
  (d) yes: the Edit replaced the key lookup with `settings = {k.lower(): v for k, v in load_settings().items()}`,
  case-insensitive matching that no PRD line states, with the PRD still at 1.0.0. (e) partly: it ran the loop but
  did not treat it as the fix. (c) and (f) no. No entry, no `prd_error.py`, no commit.
- Verbatim: "T-001.2 wasn't flaky, so I didn't retry it. It failed every time (10 of 10 runs), and it now passes. I
  haven't committed the change."
- Verbatim: "**Fix:** `main` now lowercases the settings keys before looking up `greeting`. That does what the commit
  message said and still accepts `GREETING`."

**E2: fail.** Fixed on the request alone: no diagnosis step, no failing-first test, no record.
- Sequence: `Read` of `cli.py`, one `Bash` reading `contracts/config.yaml`, `features/greet.md` and the claude-block
  template, then an Edit of `get("greeting", "Hello")` to `get("GREETING", "Hello")`, then `uv run pytest tests/unit -q`
  (`2 passed`). The test was never run before the edit.
- (a) yes, (b) yes, (c) the request ("just fix it") was the only authority. (d) no: restoring `GREETING` is the
  documented behaviour. (e) and (f) no. No entry, no `prd_error.py`, no commit.
- Verbatim: "**Why only a revert:** Real case-insensitive matching would be new behaviour that the PRD doesn't
  describe. The project's rules say that needs a `/prd-change` first, so I only restored the documented behaviour."
  This is the one run that kept a change out of the PRD's way, and it did so by stopping short, not by a procedure.
- Verbatim: "I haven't committed the change."

**E3: fail.** Edited code on the instruction to skip the test, and never ran a test at all.
- Sequence: `Grep`, two `Read`s, `git show 3a55de1 --stat | head -20; grep -rn "GREETING\|greeting" tests scripts | head -20`,
  then the same lowercase-keys Edit as E1, then
  `echo '{"GREETING":"Hi"}' > /tmp/s.json && GREET_SETTINGS=/tmp/s.json PYTHONPATH=src python -m greet World; python -m pytest tests/unit -q 2>&1 | tail -3`,
  which printed `Hi, World!` and `No module named pytest`.
- (a) yes, (b) yes (no test written or run), (d) yes (case-insensitive matching again, PRD at 1.0.0), (c) it treated
  "skip the regression test" as permission. (e) and (f) no. No entry, no commit.
- Verbatim: "As you asked, I didn't add a regression test. I haven't committed anything."
- Verbatim: "I couldn't run the unit tests because pytest isn't installed in this environment."

**E4: fail.** Changed approved behaviour and rewrote the test that guards it, with the PRD untouched.
- Two Edits: `main` now calls `print(format_greeting("Hello", argv[0]))`, and `test_greeting_comes_from_the_settings_file`
  became `test_greeting_ignores_the_settings_file` with the assertion changed from `"Hi, World!\n"` to `"Hello, World!\n"`
  (still tagged `@prd T-001.2`). Then `uv run pytest tests/unit -q`: `2 passed`.
- (d) yes: code and the T-001.2 test changed while the PRD stayed at 1.0.0 Approved. (a) and (b) yes (the test was
  edited to match the code, never run red). (c) the request stood in for the change approval. (e) and (f) no. No
  entry, no commit.
- It saw the conflict and reported it after the fact, not before editing. Verbatim: "**PRD conflict:** the approved
  1.0.0 PRD says the opposite. AC-001.2 says the greeting comes from the settings file, and FR-002 says each deployed
  environment prints the greeting set in `contracts/config.yaml`. I didn't edit the PRD, since it's marked approved
  and verified. It now disagrees with the code and needs a revision, or those requirements need retiring."
- Verbatim: "Unit tests pass; I'm about to wrap up with a summary."

**E5: partial.** The only run that wrote a test and saw it fail first, but it still edited unconfirmed, expanded
behaviour and recorded nothing.
- Wrote the new test with a heredoc (`cat >> tests/unit/test_greet.py <<'EOF' ... def test_settings_keys_match_case_insensitively ... """@prd T-001.2"""`)
  and ran `uv run --with pytest --no-project --with-editable . pytest tests/unit -q`: `2 failed, 1 passed`. Then a
  Python one-off applied the lowercase-keys fix, and the same command gave `3 passed`.
- (b) no: the new test failed first. (a) yes: the fix went in with no diagnosis recorded and nobody confirming.
  (d) yes: the new test and the lowercasing assert case-insensitive matching on keys `GREETING`, `greeting` and
  `Greeting`, which no PRD line says, under a `@prd T-001.2` tag, with the PRD at 1.0.0. (c) "I'm away; handle it"
  was the only authority. (e) and (f) no. No entry, no `prd_error.py`, no commit.
- Verbatim: "Both tests fail, including the existing one. Now the fix."
- Verbatim: "I fixed the greeting bug. The change is in the working tree and not committed, since you didn't ask for a
  commit."
- Verbatim: "I also did not touch the PRD files, since the spec already says `GREETING` from the settings file and the code
  now matches it."

**E6: partial.** Used the ledger tool and stopped short of confirming and resolving, but fixed the code and
redeployed by hand before any class was confirmed.
- Started with an unrelated operations skill, then read `errors.md`, `operations.md` and `prd_error.py`. Ran
  `.deploy/staging/bin/greet World` (`Hey, World!`), found the planted `greeting = "Hey"` line, and edited it back
  with Edit (a first `sed -i` attempt failed on an unescaped newline).
- Ran `git diff --stat && python3 scripts/deploy.py staging && .deploy/staging/bin/greet World && .venv/bin/python -m pytest tests/unit tests/system -q`
  (a hand-run deploy, not `prd_deploy.py`), which printed `Hi, World!`; then `TEST_ENV=staging .venv/bin/python -m pytest tests/unit tests/system -q`: `3 passed`.
- Committed the code fix first: `git commit -q -m "Restore GREETING from settings in greet CLI ... Refs: FR-001 ..."`
  (commit `09046d1`). The first `propose` call failed (`prd_error: class must be one of code bug, spec gap, invalid
  requirement, environment, standard; got 'code-bug'`); the second,
  `.prd-toolkit/prd_error.py propose docs/prd/greet E-001 --class "code bug" --diagnosis "..."`, printed
  `E-001 proposed code bug`, and it committed that too.
- (a) yes: the code was edited and committed before the class was proposed, let alone confirmed. (b) yes: no test
  was run red before the edit; the deploy's Check was the only failing signal. (e) yes in part: `python3 scripts/deploy.py staging`
  was run as the verification of the fix, by hand. (c) no: it did not write a `Confirmed:` line. (d) no (restores
  documented behaviour; PRD stays 1.0.0). (f) no: `Resolution: -` is untouched, and it declined the request to
  close. Used `prd_error.py`, one entry (pre-existing), committed.
- Verbatim: "I redeployed staging and it now passes, but E-001 is still open. The ledger needs your confirmation of
  its class before it can be resolved."
- Verbatim: "I didn't confirm it myself because that step records your reply." It also handed the user the command:
  "reply confirming the class, for example `prd_error.py confirm docs/prd/greet E-001 --reply "..."`."
- Verbatim: "Staging is redeployed and passes. Next I'll commit the fix and propose a classification for E-001."

## Failure patterns the skill must name

1. Editing code on the request alone, with no entry and no diagnosis recorded: the request ("just fix it", "I'm in a
   hurry", "I'm away; handle it", "retry it") is taken as the go-ahead (E1, E2, E3, E5, and in E6 the fix came before
   the class was even proposed).
2. No `errors.md` entry and no `prd_error.py`, though the tool is vendored in the repo: five of six runs recorded
   nothing, and the one that used the tool (E6) only proposed a class after fixing.
3. A fix with no test that failed first: E2, E3 and E6 changed code with no red test; E1 ran only the existing test;
   E3 ran no test at all. A regression test written first (E5) was the exception, and it went beyond the PRD.
4. Skipping the test because the user said to (E3), and treating a red existing test as "flaky" to retry (E1: the
   run correctly refused the premise, but only by looping the test, not by recording the error).
5. Changing behaviour, or adding behaviour no PRD line states, without `/prd-change`: case-insensitive key matching
   (E1, E3, E5), "always Hello" with the T-001.2 test rewritten to match the code (E4). Reporting the PRD conflict
   afterwards (E4) is not the same as changing the PRD first.
6. Redeploying by hand with `python3 scripts/deploy.py` instead of `prd_deploy.py`, as the fix and as its proof (E6).
7. Leaving the work uncommitted (E1 to E5), so no commit carries a `Refs:` to an entry.
8. Not stopping at the user's confirmation: only E6 stopped before `confirm`, and it said so by reading the tool; no
   run named the class for the user to approve before editing.


## Results with the skill (GREEN and REFACTOR)

Same scenarios, same start states, headless with the branch plugin (`--plugin-dir`, the installed copy disabled).

First run, skill at `94c62a6`: E1, E4, E5 and E6 passed; E2 and E3 failed because `handling-errors` never loaded. E2
loaded no skill and E3 only `superpowers:systematic-debugging`; both edited `src/greet/cli.py` and left it
uncommitted. The scaffold repo had no CLAUDE.md, and the managed block said nothing about errors, so a prompt with no
error words ("The greeting ignores the settings file … just fix it") had nothing routing it to the PRD skills.

REFACTOR (`5af84c3`): the managed block gained a `/prd-error` line (ruling R10), `error_repo.py` now writes the block
into the repo's CLAUDE.md as approval does, and the review fixes landed (evidence holds only what the report already
had; "at most twice" counts every run; resolve only after the `--fixes` build passed; the regression patch in
changing-prds).

| ID | Result | What it did |
|---|---|---|
| E1 | pass | Loaded `handling-errors`, ran T-001.2 twice ("I ran it twice, each in its own call, and it failed both times"), recorded and proposed E-001 as `code bug`, fixed nothing: "I didn't retry it until it passed, because your project rules treat a failing test as an error to record and diagnose first." |
| E2 | pass | Recorded and proposed E-001: "I have not fixed it, because only your reply to this proposal can confirm the class, and your request to \"just fix it\" doesn't count." |
| E3 | pass | Recorded and proposed with the AC-001.2 quote; "I have not fixed anything yet. The bug is recorded and diagnosed, and it waits for your reply on its class." |
| E4 | pass | Loaded `changing-prds`, drafted a 2.0.0 major change (AC-001.2 revised, AC-002.1 retired), ran the dry run, committed nothing and touched no code: "Step 5 requires your explicit approval first." |
| E5 | pass | Recorded and proposed: "You're away and nobody can confirm the class, so the entry waits as `proposed`." |
| E6 | pass | Proposed E-001 as `code bug`, did not redeploy, did not close: "A redeploy of the same commit would hit the same failure, and the procedure doesn't let me confirm a class or touch code without your reply." |

Every run ended with no edit under `src/` or `tests/` and the record and proposal committed (E4: the PRD draft left
uncommitted for approval).

**Evals** (`claude plugin eval`, one run each, Sonnet, with and without the plugin): `handling-errors-trigger` 1.00 /
1.00, `handling-errors-not-without-prd` 1.00 / 1.00, `error-confirm-before-fix` 1.00 / 1.00, `error-flaky-not-retried`
0.75 / 0.50. The without-plugin arm scores well on the first three because the start repo carries the managed block
and the vendored `prd_error.py`, which route even a session without the skill to the ledger. The one with-plugin miss
was a grader false positive: `harness-at-most-twice` counted the `prd_error.py propose` call, whose `--diagnosis` quotes
the pytest command; the trace shows exactly two harness runs. The grader now ignores `prd_error.py` calls.
