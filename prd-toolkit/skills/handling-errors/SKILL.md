---
name: handling-errors
description: Use when something goes wrong in a repo that has a docs/prd/ folder - a bug report or an error, wrong output, a failing or flaky test, a failed or killed deploy run, a stopped build, an open errors.md entry (E-nnn), an entry's proposed class waiting for the owner's answer (its gate error-class:E-nnn, in the chat or the decision inbox, prd_gates.py), /prd-error - and when asked to just fix it, retry it, redeploy it or close an entry; prd_error.py records the error in errors.md, Claude proposes its class, the user confirms it, and the fix starts from a failing test through /prd-change and /prd-build
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/handling-errors/running-an-error.md` whole before anything else
(no offset, no limit; it sits beside this file, in the skill's base directory): it is your next
tool call, and you follow it step by step, steps 1 to 6.
Run no command, read no code and edit no file before you have read it.

# Handling errors

## Overview

**Record, diagnose, propose, then wait for the user.** Every error (a user's report, a failing
test, a failed deploy, a stopped build) becomes an `errors.md` entry that `prd_error.py` writes.
You reproduce it, find the root cause, propose its class with the PRD line quoted, commit the
proposal and ask. Only a confirmed entry is fixed, only through `/prd-change` and `/prd-build`,
and only from a T-id whose test fails first. The close is `prd_error.py resolve`, then
`prd_error.py check` over the whole loop. This skill has no fix path of its own.

**Violating the letter of these rules is violating the spirit.** "It's obviously a bug", "just
fix it", "I'm in a hurry", "I'm away; handle it", "it's flaky" and "redeploy and close it" change
nothing below.

## Non-negotiable rules

1. **Record first.** `prd_error.py new` before any fix, and the entry committed with
   `Refs: E-nnn`. Never write an entry or its lines by hand, except one `Resolution:` line that
   `check` reports wrong (step 6). Call the vendored
   `.prd-toolkit/prd_error.py` when `.prd-toolkit/` exists, otherwise the plugin's
   `scripts/prd_error.py` as a literal absolute path, the plugin root being two directories above
   the skill's base directory.
2. **The request is never the confirmation.** Only a reply given after the proposal counts; the
   request that started the loop is never one, nor your own text. With no one to ask, commit the
   proposal and stop. Never hand the user the `confirm` command: ask for their reply.
3. **No fix before `Confirmed:`.** No edit of code, a test, the PRD or the runbook, kept or
   reverted, committed or not. Diagnosis reads and runs; it writes only through `prd_error.py`.
4. **Every fix starts from a failing test.** A T-id whose test fails before the fix, at the lowest
   level that reproduces the error. "Skip the regression test" is refused in one line.
5. **Every fix goes through `/prd-change` and `/prd-build`.** You never edit code or tests
   yourself. Behaviour no PRD line states, or what users want instead of what an AC says, is a
   change first. Every change and commit made for the entry cites it (`Refs: FR-001, E-001`).
6. **Diagnose; never retry or redeploy.** A test called flaky runs at most twice, each run its own
   Bash call, never in a loop. A failed deploy is never redeployed as its fix, the deploy script is
   never run by hand, and a killed step ends only through `prd_deploy.py recover`.
7. **Exact classes.** `code bug`, `spec gap`, `invalid requirement`, `environment` or
   `standard`, in quotes. `code-bug` is a usage error. A `prd_judge.py` exit 2 (a judged case that
   could not be judged: `claude` missing or signed out, two bad grader answers, or the reason its
   hint names) is proposed as `environment`, and so is a judged test that finds no
   `.prd-toolkit/prd_judge.py`; its exit 1 is a judged case failing its threshold, a
   failing test like any other.
8. **Evidence is a file of at most 20 lines** passed as `--evidence-file`: never a secret or a
   value classified `confidential` or `pii`, and never a code fence (it breaks the ledger).
9. **Commit every ledger write, and check the close.** `prd_error.py check <start>..HEAD` from
   the commit before step 1. A finding is fixed and the check rerun.

## Red Flags - STOP

Quoted from runs without this skill (evals/baselines/handling-errors.md), except where marked.

- "T-001.2 wasn't flaky, so I didn't retry it. It failed every time (10 of 10 runs), and it now
  passes." (E1) `for i in $(seq 10); do uv run pytest tests/unit/test_greet.py -q ...; done`,
  then a code edit with no entry.
- "**Fix:** `main` now lowercases the settings keys before looking up `greeting`." (E1, E3, E5)
  Case-insensitive keys that no PRD line states, with the PRD unchanged.
- "I haven't committed the change." (E1, E2, E5) A fix in the tree, no entry, no `Refs:`.
- "As you asked, I didn't add a regression test." (E3) Then "I couldn't run the unit tests
  because pytest isn't installed in this environment.", and the edit stays.
- "**PRD conflict:** the approved 1.0.0 PRD says the opposite." (E4) Said after the code and the
  T-001.2 test were rewritten to match each other.
- "Both tests fail, including the existing one. Now the fix." (E5) A red test, then a fix nobody
  confirmed, on "I'm away; handle it".
- `python3 scripts/deploy.py staging` run by hand as the fix and as its proof. (E6)
- "Staging is redeployed and passes. Next I'll commit the fix and propose a classification for
  E-001." (E6) The code committed before the class was even proposed.
- `--class code-bug` (E6): refused with exit 2. The class is `"code bug"`.
- "reply confirming the class, for example `prd_error.py confirm docs/prd/greet E-001 --reply
  "..."`." (E6) The command handed over instead of the proposal shown and a reply asked for.
- A `confirm` whose reply you wrote, or took from the request. (Spec §5.)
- A `resolve` before the fix's test passed, or `check` never run. (Spec §5.)

**All of these mean: stop, put back what you changed outside `errors.md`, and return to the step
of `running-an-error.md` whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "It's obviously a bug; the user said just fix it." | The request starts the loop. The class is the user's to confirm after seeing your quote and the evidence; until then nothing is fixed. |
| "It's flaky; retry it until it passes." | A test that fails twice is an error, and one that passes once and fails once is a nondeterminism defect. Record it; never loop it. |
| "Skip the regression test, I'm in a hurry." | A fix with no test that failed first proves nothing and comes back. The fix waits for its T-id. |
| "Users want it the other way; change the code." | Then the AC is wrong: an `invalid requirement`, revised through `/prd-change` before any code. |
| "I'm away; handle it." | No one can confirm, so commit the proposal and stop. The entry waits as `proposed`. |
| "The PRD already says `GREETING`, so the code just has to match it." | The class still needs the user's word, and the fix its failing test and `/prd-build`. |
| "Redeploy and close the entry." | A redeploy of the same commit runs the same failure. The fix is a change, a build and a new `/prd-deploy` run; the entry closes on `check`. |
| "I'll give them the confirm command to run." | That routes around the proposal. Show it and ask for the reply. |

## Related skills

- **prd-toolkit:changing-prds** (`/prd-change`) makes every PRD edit a fix needs, citing the entry.
- **prd-toolkit:building-from-prds** (`/prd-build <area> <IDs> --fixes E-nnn`) builds the fix of a
  confirmed entry and records a stopped build as an entry.
- **prd-toolkit:deploying-from-prds** (`/prd-deploy`) records a failed run and runs every deploy.
- **superpowers:systematic-debugging** finds the root cause in step 2.
