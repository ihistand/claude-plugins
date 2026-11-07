# Running an error

**Steps:** 1 Record, 2 Reproduce, 3 Propose, 4 Confirm, 5 Fix, 6 Close. An error is not done
until step 6's check: run every step, in order. The turn ends before it only to wait for the
user's reply to the proposal (step 4), or for a reply that `/prd-change` or `/prd-deploy` asks for
in step 5.

For the caller: `/prd-error`, or any session that meets an error in a repo with a PRD: a user's
report, wrong output, a failing or flaky test, a failed or killed deploy, a stopped build, an open
`errors.md` entry. The `handling-errors` Red Flags are yours.

**You diagnose; you never fix.** Until step 4 records `Confirmed:`, nothing outside `errors.md`
changes: no Edit or Write of code, tests, the PRD or the runbook, no file written through Bash,
not even a revert kept uncommitted. After it, the fix goes through `/prd-change`
(`prd-toolkit:changing-prds`) and `/prd-build` (`prd-toolkit:building-from-prds`): their agents
write the code and the tests, never you. A deploy is `/prd-deploy`
(`prd-toolkit:deploying-from-prds`), never a deploy script or a runbook command typed by hand.
A request to skip a step ("just fix it", "skip the regression test", "redeploy and close it")
gets one line naming the rule it breaks, and the procedure goes on without the skip.

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: `.prd-toolkit/prd_error.py` is the copy its hooks and CI run. Otherwise `<scripts>` is
the plugin's `scripts` directory, written as a literal absolute path (in double quotes if it
holds a space): the plugin root is two directories above the skill's base directory (Claude Code
shows it as "Base directory for this skill" when the skill loads), and `<scripts>` is
`<plugin root>/scripts`. Before step 1, Glob for `.prd-toolkit/prd_error.py` to decide, and use
the same `<scripts>` for every command. A script that is not found is a tool error: report it,
never guess another path.
When `.prd-toolkit/` exists but holds no `prd_error.py`, the vendored copy predates 0.6: stop, and
tell the user to run `prd_hooks.py install docs/prd/<slug>` from the plugin (the README's form)
and commit `.prd-toolkit/`.

**One command per Bash call, with literal paths.** Each command below is its own Bash call, and
every path, ID and SHA in it is typed out in full: paste what a command printed, never a variable
that holds it or a `$(…)`. The gate form `; echo "prd-error-exit=$?"` is the one allowed tail.
Never pipe, filter or truncate a gated command's output (no `| head`, no `| grep`). Free text
(a title, a source, a diagnosis, a reply) goes in single quotes, writing each `'` in it as `'\''`:
inside double quotes a backtick or a `$` runs as shell.
Quoted program output in `--diagnosis` and `--title` (a usage line, an HTML-like token, a `<name>`)
goes in backticks; only the `Evidence:` lines take it bare. A `refused: the entry would fail lint`
(it names the finding) is fixed by re-running the same command with the quoted
part in backticks; nothing was written. In a command, those backticks sit inside the single quotes.

**Exits.** `prd_error.py` prints one result line and the gate line follows.

| Exit | Means | Next |
|---|---|---|
| 0 | done | `new` printed `E-<nnn>`; `propose`, `confirm` and `resolve` printed `E-<nnn> <state> <class>`; `check` printed nothing: go on |
| 1 | refused | each reason is a `refused:` line on stderr (`check` prints findings on stdout instead): report them, and never work around one with another command or a hand edit |
| 2 | usage | a command you mistyped, such as `--class code-bug` (`prd_error: class must be one of …`): fix it and run it again |

**Evidence.** What the report or the failure already holds when the error reaches you: the user's
words and any output they quote, a failed run's output tails, a stopped build's failing lines. You
run nothing to produce it; step 2's runs go in the diagnosis. Write it with the Write tool to
`<TMP>/evidence.txt`, outside the repository: run `mktemp -d` as its own call and paste the path it
prints wherever `<TMP>` appears. It holds at most 20 lines; never a secret value, a token, a
password or a value classified `confidential` or `pii` (write `<redacted>` in its place); and
never a code fence (a line that starts with three backticks or tildes): a fence ends the ledger's
parse and hides the entries after it, so `new` refuses one.

**Where to enter.** Find the one `docs/prd/<slug>/prd.md` (ask which when there is more than one),
then run, as its own call:

```bash
uv run --script <scripts>/prd_error.py list docs/prd/<slug> --open; echo "prd-error-exit=$?"
```

Each line is `E-<nnn> <state> <class> <Touches> <title>`; the second word is the state. A new error
enters at step 1. An open entry resumes at the step its state names: `unclassified` at step 2,
`proposed` at step 4, `confirmed` at step 5. A resolved entry has nothing left but step 6's check.
For an entry recorded before this session (a failed deploy and a stopped build record their own),
`<start>` is the commit before the one that added it: run, as its own call,

```bash
git log --reverse --format=%P -G "^### <E-nnn> " -- docs/prd/<slug>/errors.md
```

and paste the first line wherever `<start>` appears: its first SHA when it holds two (a merge).

1. **Record.** With no entry yet, run `git rev-parse HEAD` as its own call and paste the SHA as
   `<start>`: the commit before step 1, where step 6's check begins. Write the evidence file from
   what the report or the failure already holds (**Evidence**). Run nothing to produce it: step 2
   runs the test or the command. With nothing to quote, leave out `--evidence-file`. Then:

   ```bash
   uv run --script <scripts>/prd_error.py new docs/prd/<slug> --title '<the error in one line>' --source '<where it came from>' --touches <IDs> --evidence-file <TMP>/evidence.txt; echo "prd-error-exit=$?"
   ```

   `--source` says where it came from: `user report (/prd-error)`, `failing test T-001.2`.
   `--touches` takes the requirement IDs the error concerns, as `FR-001,FR-002`; leave it out when
   none is known yet. It prints the new `E-<nnn>`. Never write an entry or one of its lines by
   hand: every ledger write is a `prd_error.py` command (the one exception is step 6's fix of a
   `Resolution:` line that `check` reports wrong). Then, each its own call:

   ```bash
   git add docs/prd/<slug>/errors.md
   git commit -m "docs(prd): record <E-nnn>" -m "Refs: <E-nnn>"
   ```

   The commit holds `errors.md` alone. A failed deploy or a stopped build has already recorded its
   entry and committed it: start at step 2 with that entry.
2. **Reproduce.** Run the evidence and find the root cause, with `superpowers:systematic-debugging`
   when it is in your skills list. You may read the code and its history (`git log`, `git show`):
   you are not the black-box tester. Nothing is fixed here.
   - **A failing test, or one called flaky.** Run its level's harness command from `testing.md`
     Levels, narrowed to the test's file, as its own call: at most twice, never in a loop (no
     `for`, `while`, `seq`, `--count` or rerun plugin). "At most twice" counts every run of the
     harness in this loop, a whole-suite run included. A test that fails twice is failing, not
     flaky. One that passes once and fails once is nondeterministic, which is an error too. The
     runs and their results go in the `--diagnosis` of step 3: the evidence is already written. A
     missing test tool is reported, never a reason to edit untested.
   - **A deploy run.** Run `git rev-parse --git-common-dir` from the repository root as its own
     call and Read `<that dir>/prd-toolkit/deploys/<run id>.jsonl`: the failed step's command,
     exit and output tails. You never rerun a deploy, a runbook command or the deploy script. A
     step with a `start` record and no result (a killed run) ends only through
     `prd_deploy.py recover`, on the user's words, as `running-a-deploy.md` step 2 says.
   - **A stopped build.** Its evidence holds the failing lines; read the round records it names.
   - **A user's report.** Run the command it names once, as its own call, when that command
     changes nothing (never a deploy, a migration or a runbook step).

   An error that does not reproduce still goes to step 3, with a diagnosis that starts
   `not reproduced:` and says what was tried; the entry then waits for the user.
3. **Propose.** Settle the class against the PRD, never against what the code does:

   | Class | When |
   |---|---|
   | code bug | the code does not do what an AC says |
   | spec gap | the PRD says nothing about what happened: no AC, contract or test case covers it |
   | invalid requirement | the code does what an AC says, and the AC is wrong; or a test case or a contract that contradicts its own AC (the AC stands, the PRD's test case or contract is wrong) |
   | environment | the code and the PRD agree; an environment, its config or the runbook is wrong |
   | standard | the code or the PRD breaks a standard in the PRD's registries |

   When the system does what the PRD says and the PRD is right, keep the class the report claims
   and start the diagnosis with `not a defect:`. Look for a recurrence among every entry, resolved
   ones included:

   ```bash
   uv run --script <scripts>/prd_error.py list docs/prd/<slug>; echo "prd-error-exit=$?"
   ```

   An entry with the same `Touches:` and the same symptom is its `--recurrence`. Then:

   ```bash
   uv run --script <scripts>/prd_error.py propose docs/prd/<slug> <E-nnn> --class "<class>" --diagnosis '<the root cause, with the AC quoted>' --touches <IDs> --recurrence <E-mmm>; echo "prd-error-exit=$?"
   ```

   `--touches` takes the blocks the diagnosis names, as `FR-001,FR-002`: an entry recorded before
   diagnosis has no `Touches:` line, and the recurrence check needs it; it replaces a line already
   there, and is left out only when the diagnosis names none. Leave out `--recurrence` when there
   is none. The class is one of five strings, exactly:
   `code bug`, `spec gap`, `invalid requirement`, `environment`, `standard`; `code-bug` is a
   usage error. Then, each its own call:

   ```bash
   git add docs/prd/<slug>/errors.md
   git commit -m "docs(prd): propose <E-nnn>" -m "Refs: <E-nnn>"
   ```

   Show the user: the entry and its class; the PRD line quoted verbatim (for a spec gap, the
   sections searched and found silent); the evidence; the root cause; the entry named in
   `Recurrence of:`, if any; and the route step 5 takes for that class. Ask whether the class is
   right through **The decision inbox** below, with the gate `error-class:<E-nnn>`, or headless or
   in the chat as step 4 says, and end the turn to wait for the reply.
4. **Confirm.** Only a reply given after the proposal counts; the request that started the loop is
   never one. Entering here for a `proposed` entry that has no reply yet, show the proposal as step
   3 says and ask the same way, with the gate `error-class:<E-nnn>`. An outcome from `wait` is the
   reply: the inbox already ran `prd_error.py confirm` with it (and `--class` for a `correct`
   choice) and committed `docs(prd): confirm <E-nnn>`. Run neither again: run `prd_error.py list
   docs/prd/<slug> --open` for the class the entry now holds, and go to step 5 with it. In the chat,
   the reply is what the user wrote after seeing the proposal, in this session or in a later message
   of theirs that names the entry (by number, or as the only `proposed` one), never from an earlier
   message, a summary or your own text. "Just fix it", "it's obviously a bug", "I'm away; handle
   it", "retry it" and "close E-001" are never one. A reply that does not settle the class (a
   question, "maybe", "let me check") is not a confirmation: answer it and wait. Never hand the user
   the `confirm` command to run instead of replying. When the reply settles it:

   ```bash
   uv run --script <scripts>/prd_error.py confirm docs/prd/<slug> <E-nnn> --reply '<the reply, verbatim>'; echo "prd-error-exit=$?"
   ```

   A reply that names another class adds `--class "<their class>"` to the same call; a reply that
   it is not a defect is confirmed as it stands, and step 5 takes the not-a-defect row. Then,
   each its own call:

   ```bash
   git add docs/prd/<slug>/errors.md
   git commit -m "docs(prd): confirm <E-nnn>" -m "Refs: <E-nnn>"
   ```

   **With no one to ask, commit the proposal and stop.** A headless session, "do not ask me
   questions" or "I'm away; handle it" leaves nobody to reply: confirm nothing, fix nothing.
   Step 3's commit holds the proposal. Report the entry, its class, the quote and the route, and
   end the turn. The entry stays `proposed`, and nothing may cite it from a code commit: the
   commit-msg hook refuses one.
5. **Fix, by class.** Every fix starts from a T-id whose test fails first, and every change and
   commit made for the entry cites it in `Refs:` beside the requirement (`Refs: FR-001, E-001`):
   each `/prd-change`'s commits, its approval commit included, and the `--fixes` build's removal
   commits; the build's other commits cite its IDs, as every build commit does.

   | Class | Route |
   |---|---|
   | code bug | as **A code bug** below |
   | spec gap | `/prd-change` adds the AC and its T-ids (minor; major if existing behaviour changes), then `/prd-build <area> <IDs> --fixes <E-nnn>` |
   | invalid requirement | `/prd-change` revises the AC and its test cases (major when existing behaviour changes), or, when a test case or a contract contradicts its own AC, revises the test case or contract (a patch when no AC or behaviour changes: see the version rules in `prd-toolkit:changing-prds`), and the block returns to `approved`; then `/prd-build <area> <IDs> --fixes <E-nnn>` |
   | environment | `/prd-change` on `operations.md` or `contracts/config.yaml` when the PRD holds what is wrong, then a new `/prd-deploy` run: never a deploy by hand |
   | standard | the user chooses the side that changes, the registry row or the PRD, through `/prd-change`; then `/prd-build <area> <IDs> --fixes <E-nnn>` when code must follow |
   | not a defect | nothing changes |

   **An environment.** A new `/prd-deploy` run without a PRD change follows only the user's word on
   what they fixed in the environment (a host restarted, a secret set); a request to "redeploy" is
   not that word. The entry still closes only by `resolve --run` and `check`.

   **A code bug.** First a patch `/prd-change` (**A regression patch** in
   `prd-toolkit:changing-prds`: its version, §14 row and dry-run record) adds a regression T-id
   under the quoted AC, at the lowest level that reproduces the error (a patch: the AC is
   unchanged, and the T-id tests what it already says). When an existing T-id under that AC
   already fails on the error at that level (step 2 ran it red), it is the regression T-id, and
   the change adds none. Prefer a build-gate level whenever one can reproduce the error, and
   take the lowest level that reproduces it: a deploy-gate regression T-id's test runs only at
   `/prd-deploy`, so the fix is proven only there. A non-unit regression
   T-id's case carries `known-failing: <E-nnn>`; a unit one is written failing by the builder in
   the `--fixes` build, as always. Write the case's `symptom:` from the entry's Evidence or
   Diagnosis, never invented; a symptom the entry does not show is a question for the owner. As
   with any change, the block returns to `approved`. When the
   regression T-id's case already carries `known-failing: <E-nnn>` and its block is `approved` (an
   entry from 0.5, or from adoption), the PRD already says it all: skip the patch, and the
   tester-only round below marks and tags its test.
   For a non-unit regression T-id, a tester-only round comes next: dispatch `prd-toolkit:prd-tester`
   alone, as `testing-from-prds/dispatching.md` says (snapshot, dispatch, state check), with
   `Mode: suite` and only the regression T-ids (`Mode: write` for a deploy-gate level, whose red
   proof is the failed run in the evidence). Its test is a strict expected failure cited
   `@prd <T-id> known-failing <E-nnn>`, and its RESULTS line `<T-id>: known-failing <E-nnn>` is the
   red proof; `fail: unexpected pass` means the T-id does not reproduce the error, so it goes back
   to `/prd-change`. The failing test is committed, each its own call:

   ```bash
   git add <tester path>
   git commit -m "test(<area>): <T-id> known-failing <E-nnn>" -m "Refs: <IDs>, <E-nnn>"
   ```

   Then `/prd-build <area> <IDs> --fixes <E-nnn>`: it un-marks the regression tests, the builder
   fixes the code, the build removes their `known-failing:` lines before its full run (a
   deploy-gate one's once the un-mark is committed, a build-gate one's once it passes), and the
   close takes the block to `verified`; a later `/prd-deploy` takes it to `live`.
6. **Close.** For a fix (code bug, spec gap, invalid requirement, standard), the rule is this.
   Resolve only when the `--fixes` build closed with every regression T-id `pass` (its suite
   RESULTS, or the builder's unit result) and the block `verified`; otherwise run `/prd-build <area>
   <IDs> --fixes <E-nnn>` again. A build-gate and a unit regression T-id are proven by that
   build. A deploy-gate regression T-id is not run in it (its `known-failing:` line came off once
   the tester's un-mark was committed), so a deploy-gate regression T-id's entry is resolved only
   after a `/prd-deploy` run whose `tests` step record passed that T-id's level: Read the run's log
   (`<that dir>/prd-toolkit/deploys/<run id>.jsonl`, as in the deploy skill) and check that the
   `tests` step record for that level is `pass` before resolving; with no such run, deploy first.
   The resolution keeps the code-bug form (T-id, level, version, fix commit). A unit regression
   T-id carries no marker to grep, so the build's
   close is its only proof. An environment fix resolves on the new run that finished; not a defect
   resolves at once. Before the resolve, Grep `known-failing: <E-nnn>` with the path
   `docs/prd/<slug>/test-cases/`, and `known-failing <E-nnn>` with each test root: a match means the
   `--fixes` build did not finish, so run it again (its un-mark is idempotent). Then resolve by the
   class's form, one of:

   ```bash
   uv run --script <scripts>/prd_error.py resolve docs/prd/<slug> <E-nnn> --t <T-id> --version <X.Y.Z> --commit <sha>; echo "prd-error-exit=$?"
   uv run --script <scripts>/prd_error.py resolve docs/prd/<slug> <E-nnn> --run <run id> --t <T-id> --version <X.Y.Z>; echo "prd-error-exit=$?"
   uv run --script <scripts>/prd_error.py resolve docs/prd/<slug> <E-nnn> --not-a-defect '<why>'; echo "prd-error-exit=$?"
   ```

   The first is a fix (code bug, spec gap, invalid requirement, standard): the regression T-id,
   the PRD `version:` after the change, and the commit of the `--fixes` build that fixed the code
   (its merge, or the builder's commit). The second is an environment fix: the new deploy run's id,
   with `--t` only when a deploy-gate T-id proves it. The third is not a defect, with the PRD line
   quoted. Then commit `errors.md` alone, each its own call:

   ```bash
   git add docs/prd/<slug>/errors.md
   git commit -m "docs(prd): resolve <E-nnn>" -m "Refs: <E-nnn>"
   ```

   Then, with `<start>` from step 1 or from **Where to enter**:

   ```bash
   uv run --script <scripts>/prd_error.py check docs/prd/<slug> <start>..HEAD; echo "prd-error-exit=$?"
   ```

   Exit 0 is clean. Exit 1 prints `errors.md: E-<nnn>: <finding>` lines. A finding is fixed and
   the check rerun on the same range; it is never left for the user, with one exception. A finding
   on the `Resolution:` line you wrote (its form, its T-id, its version, its commit) is fixed by an
   Edit of that one line, committed the same way as a new commit (never an amend). The exception:
   a finding on a commit already made (a code commit that cited the entry before `Confirmed:`, a
   changed `Detected:` line) cannot be fixed by an edit, and history is never rewritten, so report
   it with its commit. Exit 2 is a usage error: fix the command.

   **Report:** the entry and its class; the user's reply, quoted verbatim; each change, build and
   deploy made for it, with their commits; the resolution; and the check's result.

## The decision inbox

The owner answers a gate in a local page, the decision inbox, unless nobody can open it. The step
that asks names the gate; `<gate id>` below is its id. One command per Bash call, with literal
paths, written with the skill's `<scripts>` path, never `${CLAUDE_PLUGIN_ROOT}`.

- **`wait`, first.** Start it with the Bash tool's `run_in_background`, before the owner sees any
  URL, so no answer can come before it is watching:
  `uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>`
- **The URL.** When `<scripts>` is `.prd-toolkit` (not the plugin's own directory), Read
  `.prd-toolkit/VERSION` once first, before the first `serve`; a missing file or a version below
  `0.8.2` (compare the numbers part by part: `0.8.10` is above `0.8.2`) means that copy has no
  standby. Then tell the owner, in place of the standby promise below, and promise no standby:
  `This repository's .prd-toolkit/ is <version or "older than 0.6">, so the inbox closes with the
  session that started it; run prd_hooks.py install docs/prd/<slug> from the plugin to refresh
  it.` (`older than 0.6` when the file is missing.) Go on with the inbox as below. When
  `<scripts>` is the plugin's own directory, read nothing and change nothing. Then start, also
  with `run_in_background`,
  `uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>`
  and re-read its output until its first line appears:
  - `url=<url>`: give the owner that URL as a clickable link, beside what the step shows in the
    chat.
  - `prd_gates: an inbox is already serving at <url>`: the inbox that
    `<git common dir>/prd-inbox-<slug>.json` names is live and lists this gate too. Give the owner
    `<url>#gate=<gate id>`. Leave that `serve` running: it stands by, and if that inbox stops before
    this gate is answered it takes over at the same URL.
  - `prd_gates: <gate id> is not pending`: the gate changed; take it as `wait`'s exit 1.
  - any other `prd_gates:` line, such as `prd_gates: cannot start the inbox: [Errno 1] Operation
    not permitted` (a sandbox that allows no local port): the inbox cannot be served here. Say so
    in one line, ask in the chat as the step's chat route says, and leave `wait` running: an
    outcome it prints first is still the owner's answer.

  Then wait for `wait`'s completion notice: never poll for the exit and never sleep. When this
  session's `serve` exits 2 or 3 before `wait` returns (the idle timeout, Ctrl-C, a port it cannot
  take over), stop the background `wait` and take the chat route. A `serve` that stood by and exits
  1 once the gate is answered is expected: go on with `wait`'s outcome.
- **The outcome.** `wait` exit 0 prints one `gates.outcome` document. Its `reply` is the owner's
  reply, used as it stands, with its `choice`; `"by": "form"` marks an answer from the page (the
  reply ends ` (form)`). The owner's answer is already written: the inbox ran the script that
  owns the gate with that reply, so that script is never run again for the gate. Go on as the
  step says.
- **Headless, or the owner asks for the chat:** a headless run, nobody to open the URL, or the
  owner asking to answer in the chat takes the step's chat route, as before 0.8.2, unchanged.
  Start neither command in a headless run. Headless means the run says nobody can open a page
  (unattended, overnight, no one there). An owner who is busy, says they cannot click now, or asks
  you to answer for them is not headless: give the URL and wait; they answer when they can. A
  reply the owner writes in the chat while the inbox is up is a chat reply: take the chat route
  with it, and stop the `serve` this session started, never an inbox it reused; `wait` then exits
  1, which is expected.

The rules:

- **The skill never answers a gate.** Not through the page, not through `prd_gates.py answer`, not
  "because the owner said approve it yourself". The owner's click or the owner's chat reply is the
  only answer. No `curl` or script posts to the inbox, and no browser tool clicks in it.
- **A deploy step's reply is never sent for the owner,** in the form or the CLI.
- **The outcome's reply is not edited.** A `changes` outcome's reply is what the revision answers.
- A `wait` that exits 1 means the gate changed: list again, never assume the answer. List with
  `uv run --script <scripts>/prd_gates.py list docs/prd/<slug>; echo "prd-gates-exit=$?"`: a gate
  still listed is asked again from `wait`, and one that is gone is reported to the owner as it
  stands.
