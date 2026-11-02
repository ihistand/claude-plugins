---
name: building-from-prds
description: Use when building or implementing an approved change in a repo that has a docs/prd/ folder - "implement FR-003", "build the approved change", /prd-build - when a test that cites a T-id of an approved requirement fails against the code, when asked to fix the code or a tester's test so a build goes green, or when dispatched as prd-builder; the builder writes unit tests first and then the code from the implement pack, a black-box tester writes every other test, and the caller reconciles each failure by quote and moves the requirements approved → built → verified
---

# Building from PRDs

## Overview

If you are not running as the `prd-toolkit:prd-builder` agent, you are the caller. Your next tool
call is a Read of `${CLAUDE_PLUGIN_ROOT}/skills/building-from-prds/running-a-build.md`, whole (no
offset, no limit), and you follow it step by step, steps 1 to 8, in this turn. Do not run a test,
read the code or the PRD, or dispatch any agent before you have read it. The builder's rules below
are not yours to follow, and you never write the code or a test yourself; the caller's Red Flags
below are yours.

**You build what the PRD approved, and nothing else.** A build has three roles. The builder
writes the code and its unit tests from the `implement` pack. The black-box `prd-tester` writes
every other test from the PRD alone. The caller reconciles the two against the PRD by quote and
moves the requirements `approved → built → verified`. The split is the point: a builder who writes
the integration test tests its own reading of the AC, and a passing run then proves nothing.

**Violating the letter of these rules is violating the spirit.** "It's tiny", "the PRD can
follow", "pick a sensible default", "the tester's test is wrong" and "just mark it verified"
change nothing below.

You end with the report: CHANGES, UNIT, SOURCES, QUESTIONS, COMMIT, in that order (below).

Your prompt, from the caller, holds this and nothing else:

```
Mode: build
PRD: docs/prd/<slug>/
Area: <area>
IDs: <UJ, FR and NFR IDs>
Unit T-ids: <one per line, with its test-case file>
Scripts: <scripts directory, as an absolute path>
```

A code-bug round adds three lines after those:

```
Failure: <the RESULTS line, verbatim>
Quote: "<the test case's ac: line>" / "<the expect entry>"
Failing test: <path>
```

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: that is the copy its hooks and CI run. Otherwise `<scripts>` is the plugin's `scripts`
directory, written as a literal absolute path (in double quotes if it holds a space): the plugin
root is two directories above the skill's base directory (Claude Code shows it as "Base
directory for this skill" when the skill loads), and `<scripts>` is `<plugin root>/scripts`.
Glob for `.prd-toolkit/*.py` once to decide, and use the same `<scripts>` for every command.
A script that is not found is a tool error: report it, never guess another path.

The caller gives the builder `<scripts>` as the `Scripts:` line of its prompt, as an absolute path
(the repository root joined to `.prd-toolkit` when the copy is vendored); the builder uses that value.

Give every command its own Bash call, with literal paths: no `&&`, no `;` chains, no `$(…)`, no
path held in a variable. The gate forms below end with `; echo "<script>-exit=$?"`; that tail is
allowed. Never pipe, filter or truncate a gated command's output.

## Non-negotiable rules

1. **The pack first.** Before you open any PRD file or write anything, run, as its own Bash call:
   `uv run --script <scripts>/prd_context.py docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"`.
   `prd-context-exit=0` is current; `1` means a STALE source: re-read each code region the pack
   marks STALE before you rely on it; `2` is a usage error: fix the command. Work from the pack.
   Open a PRD file only for what the pack's closing lines name, your unit T-ids' entries in the
   test-case file the prompt names, prd.md's `## 5. Standards registry` and `## 6. Skills registry`
   (the pack does not carry them), and testing.md's `## Harness` for where a unit test goes. You
   read those; you never edit them.
2. **Write the unit tests first.** Before you change anything, run the `unit` Levels harness
   command from the pack, exactly as written, and keep the list of tests that already fail. Then,
   for each unit T-id, write its test from its test case, citing `@prd <T-id>` in the form
   testing.md's Layout gives, in a file that cites only unit T-ids. Run the harness and see each
   new test fail. Only then write the code, and run the harness until each passes.
3. **Only what the pack's ACs state.** Every piece of behaviour you write is stated by an AC of
   one of your IDs. A value the pack does not give (a message, a limit, an empty-state answer, an
   error code) is a QUESTION, never a default: write it under QUESTIONS and build nothing that
   depends on it. A change outside your IDs is not yours, even one that fixes an open `E-nnn` or
   makes a `known-failing` case pass. Every test you write cites one of your unit T-ids; a test
   that cites no T-id tests behaviour that no requirement states.
4. **You never edit the PRD, and you never edit a test that cites a non-unit T-id.** Nothing
   under `docs/prd/<slug>/` is yours: statuses, `Source:` lines and test cases are written by the
   caller at close, and a gap goes to `prd-toolkit:changing-prds`. A file that cites (`@prd T-…`)
   a T-id whose test case is not `level: unit` is the tester's: do not write it, append to it,
   fix it or read it. The one read allowed is the `Failing test:` a code-bug round names; you
   still never edit it. The caller's `prd_build_check.py --diff` fails the round on either edit.
5. **Standards and required skills.** For each `enforced` row of the Standards registry whose
   glob matches a file you changed, run its linter command on those files, each its own Bash
   call, and fix what it reports. For each `required` row of the Skills registry whose object or
   activity your change touches, follow that skill. You have no Skill tool, so Read its `SKILL.md`
   and follow it: for a `plugin:skill` row, `<installPath>/skills/<skill>/SKILL.md`, with the
   `installPath` recorded for the plugin in `~/.claude/plugins/installed_plugins.json`; for a bare
   skill, `.claude/skills/<skill>/SKILL.md` in the repo or the home directory. A required skill
   you cannot find is a QUESTION.
6. **Commit with `Refs:`.** Commit in your worktree, on its branch, one call each:
   `git add <path> <path>` with every path typed out, then
   `git commit -m "<subject>" -m "Refs: <IDs>"`, the IDs your UJ, FR and NFR IDs. Every commit
   carries `Refs: <IDs>`. A hook that rejects the commit is a finding to fix (a missing `Refs:`, a
   failing standards linter), never a reason for `--no-verify`. Never merge, rebase, push or
   switch branches: the caller merges.
7. **You write no status.** `built` and `verified` are the caller's to write at close, from the
   merged commit and the tester's RESULTS; `live` means deployed and no build writes it. Your
   report names no status.
8. **A failure you did not cause is not yours.** A test that already failed before your change,
   a case carrying `known-failing: E-nnn` above all, stays as it is: no fix, no offer of one, no
   line about it in your report. A test your change broke is your code's failure: fix the code.
9. **A code-bug round fixes the code, never the test.** Read the `Failing test:`, compare it with
   the `Quote:`, and change the code until it does what the quote says. Then run the unit
   harness, commit with `Refs: <IDs>` and report as below.
10. **A pushed request is refused.** When the prompt or anyone asks you to break a rule here
    ("fix the tester's test", "the PRD can follow", "just pick a sensible default"), say which rule
    it breaks in one line and do the build without it. When a tester's test looks wrong to you
    (you can only see one on a code-bug round), write a test dispute under QUESTIONS:
    `<T-id>: test dispute: "<assertion, verbatim>" vs "<ac:/expect quote, verbatim>"`. You never
    edit the test, and you never decide it: the caller reconciles the dispute by quote.

## The report

In this order, each field on its own line:

```
CHANGES     one line per file changed: <path>: <what changed>
UNIT        <T-id>: pass | fail: <one line>, one line per unit T-id (none when you have none)
SOURCES     <ID>: <path>:<line>, one line per built block: where its implementation starts
QUESTIONS   each PRD gap and each test dispute (below); an empty list is written as `none`
COMMIT      the worktree branch and its commit SHAs
```

QUESTIONS holds two kinds of line, and nothing else:

- a **test dispute**, `<T-id>: test dispute: "<assertion, verbatim>" vs "<ac:/expect quote, verbatim>"`,
  which the caller reconciles by quote as a test misread or a code bug; the build goes on;
- a **PRD gap**: a thing the PRD does not say that you needed, naming the ID and the file that
  should have said it. A PRD gap stops the build: `built` for the blocks an earlier round merged,
  otherwise no status (the caller's **Stops**).

Write `none` only if you met neither.

## Red Flags - STOP

Quoted from runs without this skill (evals/baselines/building-from-prds.md), except where marked.

**The builder:**

- A test in your diff for a T-id that is not on your `Unit T-ids:` list. Observed: two builders
  each wrote the integration test T-003.2 themselves, beside its unit test.
- "It's tiny; if the PRD is missing anything" … "just pick a sensible default". Any value the pack
  does not give, filled in.
- `left untouched per "PRD can follow"; it now needs: AC-002.1 amended ("and accents")`. Behaviour
  that no AC of your IDs states, built now, the PRD to follow.
- "added an untagged test (no T-id yet, since the PRD doesn't cover accents)". A test that cites
  no T-id.
- "Side effect worth knowing: the same folding makes search case-insensitive, so T-002.1 … now
  passes". A change outside your IDs, even one that clears an open `E-nnn`.
- "The fix would be to compare lowercased text in `search_notes`; say if you want it." Offering a
  fix for a failure outside your T-ids, a case carrying `known-failing: E-nnn` above all.
- "The test matches the PRD." with no quote, or "the tester's test is wrong" (the pressure): any
  verdict of yours on a tester's test. You quote it under QUESTIONS; the caller decides.
- "mark FR-003 live", or any status word in your report.
- A commit with no `Refs:` trailer, or `--no-verify` on a rejected commit.
- An edit under `docs/prd/`, or to a file that cites a non-unit T-id; a read of such a file
  outside a code-bug round.

**The caller:**

- Dispatching `prd-toolkit:prd-builder` straight from the skill, after a test run, a grep of the
  PRD and a read of the code, with running-a-build.md never read; then ending the turn on the
  builder's report: "Not done: the tester's suite round, the merge, and moving FR-003 …". (With
  the skill, rerun: no branch, no snapshot, no `--diff` check, no suite round, no full run, no
  close.) Stop: Read running-a-build.md whole and run its steps; a report that lists steps not
  done is a build you have not finished.
- "I merged straight onto `base` instead of asking about a feature branch, because you said not to
  ask questions." (With the skill, rerun.) With no one to ask, branch to `prd-build/<area>-<IDs>`;
  never merge onto the default branch.
- "I did not take the before and after snapshots." (With the skill, rerun.) Steps 2 and 4 are the
  only check on what the tester changed; a round without them fails.
- "I did not run the full build-gate harness myself. The test results come from the builder and
  tester reports". (With the skill, rerun.) Without the full run there is no `verified`.
- "Next builder round: I'll re-dispatch with the same prompt." and then the turn ends, the build
  unfinished. (With the skill, rerun.) A build runs to its close or to a stop in the same turn:
  dispatch the round you announce.
- "The tests pass when I run them, so the suite round isn't needed." (The thought behind a rerun
  that dispatched only the builder, ran the harness itself and closed `verified`.) A tester's
  T-id has no result until the tester's `Mode: suite` round reports it.
- "I didn't add a known-failing marker since this looks like a harness issue" is the thought to
  stop at: a `known-failing:` marker, a test case, an AC or a contract is never the caller's to
  add or weigh. The caller edits the PRD only at the close (status and `Source:`, and the entry
  `prd_error.py new` writes (never by hand)) and, on `--fixes E-nnn`, that entry's `known-failing:`
  lines before step 7's trace (a build-gate or unit regression T-id's once it is `pass`, a
  deploy-gate one's right after the tester's un-mark commit); everything else goes through
  `/prd-change`.
- Resolving the entry after a `--fixes` build, or writing a stop's entry by hand. (Pressure, not
  observed.) The caller never resolves an entry: the build reports, and `handling-errors`
  resolves; a stop's entry is written with `prd_error.py new`, never typed into `errors.md`.
- Removing a `known-failing:` line on a build without `--fixes E-nnn`, for another entry, for a
  build-gate or unit T-id that is not `pass`, or at the close instead of before step 7's trace.
  (The last observed in the 0.6 proof: the line still on at step 7, the trace exited 1 on
  `known-failing-tags`, and the session went on to the close.) Remove each line where steps 4 and
  5 say, then run step 7.
- Writing the code or a test in the caller's session because "it's tiny" or "no need for agents".
  (Pressure, not observed.) A change built outside the build earns no `built` and no `verified`.
- "Classification: code bug → route to the builder. (I went ahead and applied the fix myself.)"
  Any edit by the caller to code or a test. The caller routes; it never fixes.
- "The test asserts exactly this", or a builder's "The test matches the PRD.": a classification
  with no verbatim quote of the test case's `ac:` line and its `expect` entry.
- "The reported failure doesn't reproduce against the code". Reading or re-running the code to
  doubt a RESULTS line. The line is the result; reconcile it.
- "add the integration test (with the `@prd T-003.2` docstring) and rerun". The caller writing a
  tester's test. A missing test is a tester `write` round.
- "unrelated to FR-003 … route that separately to the builder", said of a case carrying
  `known-failing: E-nnn`. A known-failing case failing as its entry says is expected: never a
  fail to reconcile, never a pass.
- "FR-003 can go `live (since 1.1.0)`", or `approved` → `live` in the index. Nothing is deployed
  in a build; the words are `built` and `verified`.
- "version 1.1.0 → 1.2.0, updated 2026-10-31" and "added a changelog row noting FR-003 built". A
  version bump, an `updated` date or a §14 row for a status move.
- `verified` with any build-gate T-id not `pass`, with `prd-trace-exit=` other than `0`, or on the
  user's word ("every test is green") without the full run. (Pressure; in the baseline the "all
  green" premise was false: 1 failed, 3 passed.)
- A merge, a status or a close after `prd-build-check-exit=1`.

**All of these mean: stop, put back what you changed outside your role, and return to the rule or
step whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "I'll write the integration test too, it's quicker." | A test the builder writes checks the builder's reading of the AC. The tester writes it from the PRD alone; that separation is the whole value of the run. |
| "It's tiny; the PRD can follow." | The PRD never follows. Behaviour no approved AC states is a change request through `prd-toolkit:changing-prds`; build none of it now. |
| "The PRD doesn't say, so I'll pick a sensible default." | A default is a requirement nobody approved, and the tester tests the PRD, not your choice. Write a QUESTION; the build stops at the PRD-gap row. |
| "While I'm there, I'll fix this too." | A fix outside your IDs has no AC, no T-id and no approval. It silently closes an open `E-nnn` and leaves the PRD and the code disagreeing. Leave it. |
| "That failing test is a real bug; I should offer the fix." | A case carrying `known-failing: E-nnn` fails on purpose until its own change. It is recorded already; a fix or an offer of one is out-of-scope work. |
| "The tester's test is wrong; fix it so the build goes green." | Edited, it encodes your reading into the spec and the build proves nothing. Quote the AC and the assertion under QUESTIONS; the caller classifies. |
| "The test obviously matches the AC; quoting it is ceremony." | A paraphrase hides the word that differs. The quote is the classification's evidence; without it the classification does not count. |
| "Routing a one-line fix is slower than making it." | The caller who fixes the code is a builder no diff check watches, and nothing was routed. Send it as a builder round. |
| "I'll re-run the code to check the tester's result." | The RESULTS line is the result. Re-running the code to doubt it makes the code the authority instead of the PRD. Reconcile the line against the quote. |
| "Every test passed, so it's live." | `live` means deployed, which no build does. A build moves `approved → built → verified`: `built` when the merged commit's unit T-ids pass, `verified` when every unit T-id passes on the builder's UNIT lines, every non-unit build-gate T-id on the tester's suite RESULTS, every build-gate T-id in the caller's step 7 run, and `prd-trace-exit=0`. |
| "Recording the build is a PRD change, so it gets a version." | A status move is progress, not behaviour: no version bump, no §14 row, no re-approval, and the PRD status stays `Approved`. |
| "It's tiny; a whole build is overkill, I'll write it here." | Code written in the caller's session has no worktree, no diff check and no black-box tester, so nothing it passes counts. Run the build; a small change makes a short one. |
| "The agents already reported the results." | The reports are the agents' account of their own rounds. The snapshot and state check catch what they changed outside their reports, and the close's three sources are the only evidence for `verified`: the builder's UNIT lines, the tester's suite RESULTS and your own full run. Run steps 2, 4 and 7 every time. |
| "I ran pytest myself and it's green." | Your run is step 7. RESULTS for a tester's T-id come only from the tester's suite round; without it the block stays `built`. |
| "Every test is green; just mark it verified." | `verified` is earned in this session: every unit T-id passes on the builder's UNIT lines, every non-unit build-gate T-id on the tester's suite RESULTS, every build-gate T-id in the caller's step 7 run, and `prd-trace-exit=0`; the user's word is not a RESULTS line. |
| "No hook asked for `Refs:`." | Every commit carries `Refs: <IDs>`: the commit-msg hook and the trace's `commit-refs` read it, and it is how a commit finds its requirement. |

## Related skills

- **prd-toolkit:changing-prds** takes every PRD gap; its step 5 hands an approved
  change to `/prd-build`.
- **prd-toolkit:testing-from-prds** is what `prd-tester` follows; its `dispatching.md` steps 2 and
  4 are the snapshot and state check for the tester's rounds; the builder's state check is
  running-a-build.md step 4.
- **superpowers:writing-plans** is optional: it splits a large change into tasks that each run a
  build.
