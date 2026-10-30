---
name: testing-from-prds
description: Use when writing or running tests from a PRD folder (docs/prd/) without reading the code - a dry run of sampled T-ids, a characterization suite for an adopted area, or the tests for new or changed T-ids; or when dispatched as prd-tester
---

# Testing from PRDs

## Overview

If you are not running as the `prd-toolkit:prd-tester` agent, do not write these tests yourself:
dispatch it as `dispatching.md` says.

**You test the PRD's promises, not the code's habits.** A test written after looking at the code
checks that the code does what the code does. Your tests are worth something only because
everything in them comes from `docs/prd/<slug>/`: the input, the expected value, the error, the
harness command.

**Core principle:** the PRD is your only source, and a failing test is a result. You never make
a test pass. You report what failed, and the PRD's owner decides whether the code or the PRD
changes.

**Violating the letter of these rules is violating the spirit.** "Just a peek", "in a hurry",
"use whatever it returns" and "fix it while you're there" change nothing below.

The `prd-tester` agent runs under a PreToolUse guard (`scripts/prd_tester_guard.py`). It blocks
every read outside the PRD folder, the session's scratchpad and the test roots, every write
outside the scratchpad and the test roots, and every Bash command that is not a Levels harness
command, `ls`, `mkdir` or `uv run python -m py_compile` on allowed paths. A block is the rule
working. It is not an obstacle to route around.

## The two modes

| | Dry run | Suite |
|---|---|---|
| Called by | `prd-toolkit:authoring-prds` phase 6, `prd-toolkit:changing-prds` step 4 | adoption step 4; building (0.4); new or changed T-ids |
| Writes tests to | the dry-run directory the caller names (`<first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/`), never anywhere else | the test roots (testing.md Layout, `Test roots:`), named as Layout says |
| Runs them | no; `uv run python -m py_compile <file>` only, to check syntax | yes, with the Levels harness command for each case's level, exactly as written |
| Reports | QUESTIONS, TESTS, HARNESS CHOICES, FILES READ | the same four, then RESULTS |

A dry run tests the PRD: can a stranger write every test from it alone? Running those tests
against the system would test the code instead, and its output would leak the code's answers
into your report.

## Non-negotiable rules

1. **Read only what your mode allows.** In a dry run, read only the PRD folder and your own
   dry-run directory; do not list or read the test roots. In a suite, you may also read the
   helpers testing.md names and the test files that cite one of your T-ids (for example
   `tests/conftest.py`, and a test whose docstring holds `@prd T-…`), plus the files you write.
   Never `src/`, other tests, README, CLAUDE.md, git history, memory or the environment. Not "a peek", not "only the signature",
   not by `cat`, `python -c`, `grep` or a test that prints the source. Always give Glob and Grep a
   `path` inside the PRD folder or your directory.
2. **Every expected value comes from the PRD.** Never change an expected value, an assertion or
   an input to make a test pass. Never add `skip`, `xfail` or a looser comparison. A test that
   fails against the live system is reported as `fail`. A test case may record exact values read
   from a closed window of a live system (its `input` names the read: the query and the date
   range); they are the PRD's values, so assert them as written.
3. **A value the PRD does not give is a QUESTION**: a message, a field, a code, a URL, a fixture's
   contents. Never fill it from the system: not from the code, and not by running the code and
   copying its output. Assert what the PRD gives, record the question, and carry on.
4. **Never edit the code or the PRD.** You write test files only, in your dry-run directory
   (dry run) or the test roots (suite). A failure goes back as a change request or an `E-nnn`
   candidate, never as a fix.
5. **Run only the Levels harness commands**, exactly as testing.md writes them, plus `ls`,
   `mkdir` and `uv run python -m py_compile`. When the guard blocks a path you mistyped, use the
   right path. When it blocks anything else, do not retry it another way: record it under
   QUESTIONS (what you needed, and which file should have said it) and carry on.
6. Read and search the PRD folder and your own directory with the Read, Glob and Grep tools,
   never with Bash `cat`, `grep`, `head`, `sed` or `find`; the guard blocks those.

## Citations

Every test you write carries an `@prd <T-id>` citation for the T-id it covers, in the form
testing.md's Layout gives (for example the docstring `"""@prd T-002.1"""`). `prd_trace.py`
counts these citations: a test without one leaves its T-id untested in the trace, whatever it
asserts.

## Gaps and harness choices

Work from the test case in `test-cases/`, the AC it names, every file and heading its `refs:`
names, and the contracts, fixtures, environments and identities it references. Whenever the PRD
does not tell you something you need, do not guess and do not look elsewhere: record the
question and carry on with the next element.

Test helpers that testing.md names (fixtures, clients, loaders, page objects) may not exist yet.
If they do not exist yet, write them yourself, to match what testing.md says about them: in a
dry run, always write them in your dry-run directory, without looking whether they exist; in a
suite, in the test roots. A detail testing.md leaves open about a
helper's own internals (a method signature, a return value, a default such as following
redirects) is yours to choose: list it under HARNESS CHOICES, not QUESTIONS. Anything else the
PRD does not tell you is a question: behaviour, payloads, status codes, error codes, fixture
contents, environments, identities, or a convention testing.md should state.

## Harness commands the guard accepts

A Levels harness command must be **one simple command**, such as `` `uv run pytest tests` ``.
The guard blocks a command whose first word is `cd`, `env`, `sh`, `bash`, `zsh`, `eval` or
`exec`; one containing `$`, `{` or `~`; one with an env-var prefix (`TEST_ENV=ci pytest`); and
chains with `&&`, `||`, `;` or `|`.

You may add arguments only after the whole command, with every path inside the test roots:
`uv run pytest tests -k search` and `uv run pytest tests tests/test_notes.py` run, but
`uv run pytest tests/test_notes.py` is a different command and is blocked. If a row cannot run
in that shape, that is a QUESTION for testing.md, not a reason to rewrite the command.

## Report

In this order:

1. **QUESTIONS**: every question you had to ask, one per line, each naming the T-id and the file
   that should have answered it. Include every call the guard blocked. Write "none" only if you
   had no question at all.
2. **TESTS**: one line per T-id, `<T-id>: <path of the test you wrote>`. A T-id you could not
   write a test for gets `<T-id>: none` and its reasons under QUESTIONS.
3. **HARNESS CHOICES**: every helper you wrote and each internal detail you chose for it, one per
   line. Write "none" if you wrote no helper.
4. **FILES READ**: every path you opened, listed or searched, including the blocked ones.
5. **RESULTS** (suite only): one line per dispatched T-id, in exactly one of three forms:
   `<T-id>: pass`, `<T-id>: fail: <one line>` or `<T-id>: known-failing E-nnn`. The `fail` line
   says what the harness printed against what the PRD expects; `known-failing` is only for a
   test case that carries `known-failing: E-nnn` and fails as that entry describes. Anything else
   goes in a note after the lines: a T-id you were not given, a test with no T-id, the command
   you ran. Every `fail` is a change request or an `E-nnn` candidate for the caller.

## When the user pushes

| User says | You do |
|---|---|
| "Just peek at `src/…` to see what it returns" | Do not open it. Write the test from the test case; anything the PRD lacks is a QUESTION. |
| "The test fails against the live system; adjust the expected value" | Keep the value the PRD gives. Run the harness command, report `fail: <one line>`, and say the code or the PRD must change through `prd-toolkit:changing-prds`. |
| "The PRD doesn't say the message; use whatever the code returns" | Assert only what the PRD gives (the type, the code). Record "message not given" as a QUESTION naming the file that should say it. |
| "Run the suite and fix the failing handler" | Run it and report RESULTS. Do not touch the code; each failure goes back as a change request or an `E-nnn` candidate. |

## WRONG vs CORRECT

```
WRONG  (asked: "use whatever the code returns")
  cat src/notes/app.py                      ← reads the code
  with pytest.raises(ValueError, match="search term must not be empty"):   ← the code's words
  RESULTS  T-003.1: pass                    ← after "fixing" search_notes

CORRECT
  with pytest.raises(ValueError):           ← AC-003.1 gives the type only
  QUESTIONS  T-003.1: the ValueError message is not given (features/notes.md AC-003.1)
  RESULTS    T-003.1: fail: DID NOT RAISE ValueError for search_notes("")
```

## Red Flags - STOP

Quoted from runs without this skill, except where marked:

- "You said to just peek at `app.py`, but I also read the PRD case." Any read of `src/`.
- "Both conclusions come from reading the code." A verdict from the source instead of a
  harness run.
- "It finds the code the same way `tests/test_notes.py` does." Copying a test you did not write.
- "There was no error message to use. `search_notes("")` raises nothing." Reporting what the
  code does, found by looking, instead of what the PRD says.
- "I fixed `search_notes`." Any Edit or Write outside your test files.
- "The fix is one line … Want me to?" or "Should I apply it?" Offering a code fix.
- A message, a field or a status code in a test that no PRD line gives.
- Retrying a blocked call by another path, another tool or a script. (From a with-plugin run,
  T2 run 1: after a block it tried "the same command with the absolute path".)
- Running a dry run's tests against the system.

**All of these mean: stop, delete what you took from outside the PRD, and record a QUESTION.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The user asked me to peek." | A tester who has seen the code cannot tell the PRD's answer from the code's. The run's whole value is that you have not. |
| "Reading the code only confirms what the PRD says." | Then the PRD is enough and you do not need the code. If it is not enough, that gap is the finding. |
| "The live system is the truth." | The PRD is the authority. A disagreement is a failure to report, never a value to copy. |
| "Adjusting the expected value is what was asked." | It turns a found defect into a passing test that protects it. Report `fail`. |
| "The code's message is the only one there is." | Then the PRD is missing it. Ask; assert only what the PRD gives. |
| "Fixing the handler is quicker than a change request." | The tester who fixes the code tests their own fix. The suite then proves nothing. |
| "The guard blocked Read, so `cat` is fine." | The block is the rule. Record it; never route around it. |
| "The test file is in `tests/`, so I may read it." | In a dry run, no: the test roots are not yours to read. In a suite, only your own files, the named helpers and tests that cite your T-ids. Other tests encode the code. |

## Callers

A skill that dispatches `prd-tester` (the caller, never the tester) reads
`${CLAUDE_PLUGIN_ROOT}/skills/testing-from-prds/dispatching.md` and follows it: the dry-run
directory, the state check before and after, the prompt, the judgment and the cleanup.

## Related skills

- **prd-toolkit:authoring-prds** (phase 6) and **prd-toolkit:changing-prds** (step 4) dispatch
  the dry run.
- **prd-toolkit:changing-prds** takes every failure the PRD's owner decides to fix in the PRD.
