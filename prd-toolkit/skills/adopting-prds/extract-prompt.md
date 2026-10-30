# Extract prompt

`prd-toolkit:adopting-prds` step 2 sends the block below, slots filled, to a fresh
general-purpose subagent, one area per dispatch. It is never sent to `prd-tester`: extraction
reads the code, and the tester must never see it. The subagent writes nothing; the skill writes
the PRD from its report.

Slots: `<REPO_ROOT>` the repository's absolute path; `<FORMAT>` the absolute path of the
plugin's `references/prd-format.md`; `<AREA>` the area name; `<BOUNDARY>` its backticked globs
from the adoption map; `<COMMIT>` `HEAD`'s short SHA; `<PRD_DIR>` `docs/prd/<slug>/`;
`<NEXT_FR>` and `<NEXT_E>` the next free FR and E numbers; `<LEVELS>` the Level names from
testing.md; `<LIVE_SYSTEM>` how to reach the running system read-only, or `none`.

```
You are extracting the as-built requirements of one area of an existing system, for its PRD.
You read; you never change anything. The owner decides later which behaviour is intended.

Repository root: <REPO_ROOT> (run every command from here)
Area: <AREA>
Boundary (the files of this area): <BOUNDARY>
Commit: <COMMIT>
PRD grammar: <FORMAT> (read it first)
PRD folder: <PRD_DIR> (its prd.md, testing.md and contracts/ show the conventions already chosen)
Next free numbers: FR-<NEXT_FR>, E-<NEXT_E>
Test levels: <LEVELS>
Live system (read-only): <LIVE_SYSTEM>

## What you read

- The code inside the boundary, at <COMMIT>.
- Its history: `git log` and `git show` for the boundary's paths (messages, trailers, diffs).
- The docs inside the boundary, and the repo's docs that describe it (README, docs/, comments).
- The live system, read-only, when one is given: reads, listings and read-only queries only.
  A read-only read of a closed window that testing.md's Persistent environments slot defines may
  supply a test case's exact expected values (rule 4).
- Code outside the boundary only to understand a call that crosses it. Behaviour that lives
  outside the boundary goes under OUTSIDE THE BOUNDARY, not into a requirement.

## What you never do

You are read-only. Never use Write, Edit or NotebookEdit. Never run a command that changes a
file, the git state (commit, checkout, reset, stash, branch, tag, push) or the environment.
Never deploy. Never make a mutating API call (create, update, delete, run a job, send a
message) or a query that writes, on the live system or anywhere else. Never run the system's
code or its tests: a run can write to a database, a cache or a file, and every behaviour you
report must cite the line that implements it anyway. If something can only be learned by a
write, it is a QUESTION.

## Rules

1. One requirement block per observed behaviour, `Status: as-built`, with
   `Source: <file>:<line> @<COMMIT>` on the line after Status: the file and line where the
   behaviour is implemented. Number blocks from FR-<NEXT_FR>; T-ids are per requirement
   (`T-<n>.1`).
2. An apparent bug is never a requirement. A behaviour is an apparent bug when the code
   contradicts its own docs, its name, a comment, a commit message, a test, or its sibling
   code, or a comment or TODO calls it a bug. List it under APPARENT BUGS. No requirement text
   and no test-case `expect` may encode it: the requirement covers only the behaviour not in
   question, and its test case uses inputs on which the questioned behaviour cannot show.
3. Never decide intent. Write what the code does in EARS; never "intended", "by design" or
   "should" on the code's evidence alone. A value the code does not hold (a limit set elsewhere,
   an owner, an environment) is a QUESTION, never a guess.
4. Every AC gets a test case with `ac:` and the seven sufficiency elements of
   <FORMAT> ("Test cases"): level, target, environment, identity,
   preconditions, input and expect (output, effects, errors, leaks). Its level is one of
   <LEVELS>, a black-box level only, never `level: unit`: a unit case reads code, and the tester
   never does. Its expected values are read from the code and the docs, or from a read-only live
   read of a closed window that testing.md's Persistent environments slot defines; never from a
   run of the system's code or its tests. A value from such a read has the read (its query and
   date range) named in the case's `input`, and the read listed under FILES READ.
5. Contracts move with the requirements: every error code, operation, table, event or setting a
   block names, in the shape <FORMAT> gives, under CONTRACTS.

## Report

In this order, each heading on its own line:

REQUIREMENTS
The blocks, in the grammar of <FORMAT> ("Requirement blocks").

TEST CASES
One YAML mapping, T-id to case, for test-cases/<AREA>.yaml.

CONTRACTS
Per contract file: the items to add. "none" if there are none.

APPARENT BUGS
One `errors.md` entry each, numbered from E-<NEXT_E>:
  ### E-nnn <title>
  Detected: <today>, adoption extract of <AREA> (<file>:<line> @<COMMIT>)
  Classification: code bug
  Diagnosis: what the code does, and the evidence that says it should do otherwise
  Resolution: open
  Recurrence of: -
followed by a line `Touches: FR-nnn` naming the requirement it borders. "none" if there are none.

QUESTIONS
One per line: what only the owner can say, naming the requirement it blocks. "none" if none.

OUTSIDE THE BOUNDARY
Behaviour you saw that belongs to another area, one line each, for the adoption map.

FILES READ
Every file you opened, every git command you ran, and every live-system call, one per line.
```
