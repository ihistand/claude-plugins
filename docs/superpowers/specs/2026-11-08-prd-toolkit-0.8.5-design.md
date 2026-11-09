# prd-toolkit 0.8.5: deploy, pack and check fixes from the first private-pack loop — design

> **Date:** 2026-11-08
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, every section approved by the owner in the brainstorm of 2026-11-08; the
> written text awaiting review
> **Extends:** `2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md` and the specs it extends, under
> `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this addendum and any of them disagree, this
> addendum wins for 0.8.5.
> **Needs:** 0.8.4 merged (PR #21, `3a27030`).
>
> **Revisions.**
> - Written (owner, 2026-11-08): the backlog `2026-11-07-prd-toolkit-0.8.5-deploy-and-packs-design.md`
>   becomes this design, under this name. Its eleven items keep their numbers (section 1), and two
>   bookkeeping gaps found since join them as items A and B. The 0.8.4 deferred minors stay parked,
>   except those inside code an item already changes (section 15).
> - Backlog history kept here: items 1 to 6 were the 0.8.4 spec's section 16 (PR #19), recorded on
>   2026-11-05 for 0.8.3, then moved here on 2026-11-07; items 7 and 8 are later-release candidates
>   from the same loop; items 9 and 10 joined on 2026-11-08 from the 0.8.4 proof and final review;
>   item 9's third way and item 11 joined on 2026-11-08 (PR #22).

## 1. Scope

0.8.5 takes the deploy and pack friction of the first full change, build and deploy loop on a private
pack, where a service's own UI does part of each deploy, plus the check, publishing, guard and CI
items that joined the backlog since. Success: the next deploy of that loop runs without its
workarounds (a `--timeout` on every run, three round-trips for three human steps done in one UI
session, a second push after the close, Checks that fall back to the exit code alone), and an adopting
repository takes a pack release without editing its PRD by hand.

| Item | What | Section |
|---|---|---|
| 1 | Several consecutive human steps confirmed by one reply | 5.1 |
| 2 | An `errors.md` entry recorded while a run is stopped | 5.2 |
| 3 | A `tests` step's own timeout | 5.3 |
| 4 | A close on another branch than the environment's | 5.4 |
| 5 | A Check that matches a line by pattern | 5.5 |
| 6 | A pack release without a hand-made PRD patch | 6 |
| 7 | STALE judged by the cited line, the exit scoped to `--req` | 8 |
| 8 | SOURCES lines checked against the round's hunks | 9 |
| 9 | The published page draws its mermaid diagrams | 10 |
| 10 | The tester guard checks every harness argument | 11 |
| 11 | Parallel tests for the toolkit's own suite | 12 |
| A | A moved `Status:` line named in §14's IDs cell | 7.1 |
| B | A new or removed block's ACs and T-ids named in §14's IDs cell | 7.2 |

The facts each design starts from (file and line, on `main` at `a9a520e`) were gathered before the
brainstorm; the plan's Task 0 re-reads them.

## 2. Decisions

| Item | Chosen | Rejected, and why |
|---|---|---|
| 1 | Repeated `--step N --reply TEXT` pairs, one record per step | One reply for a range: the log would no longer hold each step's own reply |
| 2 | An uncommitted entry naming this run is allowed past `resume`; the close commits it | Committing the entry at once: the run's recorded head and the close range would have to follow it |
| 3 | An optional `Timeout` column in Levels, with a pack default; `--timeout` still wins | A runbook-step label: one value for every level the step names |
| 4 | An optional `Branch` column in Environments and a warning | A refusal to start on another branch: it blocks a loop that deploys from a work branch |
| 5 | `matches` with a Python regular expression | A prefix form: it cannot say what follows the prefix |
| 6 | `prd_change.py pack`, a scripted patch the owner approves | A compatible range in `pack.yaml`: an area would run under a pack version nobody checked it against |
| 7 | Judge by the cited line's text; exit 1 only for the blocks asked for | Either half alone |
| 8 | The file must be in the round's diff and the line inside a changed hunk | The file alone: a SOURCES line could point anywhere in a long file |
| 9 | Inline SVG from a pinned Python renderer, each diagram falling back to its source | Embedding the mermaid library (about 3 MB of script on a page that loads nothing); a reimplementation such as `mmd` (not mermaid's own code, so diagrams can differ) |
| 10 | Every argument checked; a short list of options refused | An allowlist of pytest options: a PRD whose harness uses another option breaks |
| 11 | `pytest-xdist` for the toolkit's own suite | A path filter in the generated CI: a skipped job can leave a required check pending, and a wrong filter lets a broken build merge |
| A | A `patch` bump item per moved `Status:` line | An IDs-cell entry with no bump item: the bump output would not show it |
| Approach | The toolkit's own PRD first (one `lint-cli` `/prd-change`), then one release and one PR | Parsing the new fields outside `model.py` (two parsers, no lint); two releases (another renumbering) |

## 3. Components

| File | Change | Items |
|---|---|---|
| `scripts/prdlint/model.py` | Levels `Timeout` column, Environments `Branch` column, a Check's `matches` (a `lint-cli` Boundary file: section 4) | 3, 4, 5 |
| `scripts/prdlint/rules/registries.py` | The findings for those three fields | 3, 4, 5 |
| `scripts/prdlint/deploy.py`, `scripts/prd_deploy.py` | Multi-step confirm, the tracked-tree exception, per-level timeouts, the branch note, `matches` | 1 to 5 |
| `scripts/prdlint/gates.py` | A step confirmed ahead is never a pending gate | 1 |
| `scripts/prdlint/packs.py`, `scripts/prdlint/hooks.py` | A level's `timeout` key; install's pack-bump hint | 3, 6 |
| `scripts/prdlint/change.py`, `scripts/prdlint/change_approve.py`, `scripts/prd_change.py` | `pack`; Status items; full IDs cells; the approval commit carries a re-vendored pack | 6, A, B |
| `scripts/prdlint/context.py`, `scripts/prd_context.py` | Line-text STALE, MOVED, the scoped exit | 7 |
| `scripts/prdlint/buildcheck.py`, `scripts/prd_build_check.py` | `--sources` | 8 |
| `scripts/prdlint/publish.py`, `scripts/prd_publish.py` | Inline SVG with fallback; the renderer in the dependency header | 9 |
| `scripts/prd_tester_guard.py` | Every harness argument checked | 10 |
| `prd-toolkit/pyproject.toml`, `uv.lock` | `pytest-xdist` in the dev group | 11 |
| `references/prd-format.md`, `references/contract-types.md` | The new columns, `matches`, a level's `timeout` | 3, 4, 5 |
| Skills, agents and the README | Section 13 | all |
| `.prd-toolkit/` | Refreshed with `prd_hooks.py vendor` in every task that changes a vendored file | all |

## 4. The toolkit's own PRD changes first

`prdlint/model.py` is in the adopted `lint-cli` area's Boundary, and the commit hook refuses a change
to it without a requirement ID. The release begins with one `/prd-change` on the toolkit's own PRD,
as 0.8.4 began with FR-015:

- **New `lint-cli` requirements**, their IDs from `prd_change.py ids next`, each with one AC and one
  integration test case on a fixture PRD:
  1. lint reports a Levels `Timeout` cell that is not a whole number of seconds of at least 1; a blank
     cell, or no `Timeout` column, is no timeout and no finding;
  2. lint reports an Environments `Branch` cell that `git check-ref-format --branch` refuses; a blank
     cell, or no `Branch` column, is no finding;
  3. lint reports a Check whose `matches` pattern does not compile as a Python regular expression, and
     a Check that has both `prints` and `matches`.

  The rule each finding belongs to (an existing one such as `runbook-steps`, or a new one) and the
  exact message text are settled in the change itself; the change's dry run checks them.
- **testing.md:** the `unit` and `integration` Harness commands gain `-n auto` (item 11, section 12).
- **Version:** minor, 5.1.0 → 5.2.0 (new requirements; the harness edit decided as a patch item).

Then the dry run, the owner's approval through the decision inbox, and `/prd-build lint-cli <IDs>`
with the builder on a round branch and without worktree isolation, as in 0.8.4. That build adds the
parsing to `model.py` and the findings to the rules; the deploy side that uses the parsed fields is
built in the later plan tasks, which cite no `lint-cli` ID and touch no Boundary file.

## 5. The deploy runner

### 5.1 Several human steps in one reply (item 1)

Today `confirm --run ID --step N --reply TEXT` takes one step, and each confirm needs its own
`resume`, so three human steps done in one UI session cost three replies and three resumes.

- `prd_deploy.py confirm` takes the pair `--step N --reply TEXT` one or more times, in order.
- The first `N` must be the human step the run stopped at (the rule of today). Each later `N` must
  be the next step number of the runbook, a `human` step, not past the run's `--until` environment;
  the list ends at the first `agent` step. Each reply must be non-empty.
- All pairs are checked before any is written, under `run_lock`; one bad pair refuses the whole call
  (exit 2, the message naming the pair), and nothing is appended.
- Each step gets its own `{"kind":"confirm","step":N,"reply":...,"at":...}` record; a step after the
  stopped one also carries `"ahead": true`.
- On `resume`, `run_steps` treats a human step that has an ahead confirm as answered: it appends the
  step's `step` record with `"result":"human"` and `"confirmed_ahead": true` and goes on to the next
  step without stopping. `finished_envs` counts such a step as confirmed and resumed.
- The decision inbox is unchanged: it shows a card for the one step the run stopped at, and
  answering it confirms that one step. A step confirmed ahead is never listed as a pending gate.
- **The skill** (`deploying-from-prds`) passes a later step only when the owner's own reply names it,
  by number or by its title, and it passes the owner's words for each step. It never asks whether
  later steps are done.

### 5.2 An error entry during a stopped run (item 2)

Today `_moved` refuses `resume` and `rollback` when HEAD moved, the PRD version changed, the runbook
changed, or the tracked tree has any change. `errors.md` is tracked, so an entry recorded while the
run is stopped, committed or not, blocks the run until the close.

- `_moved`'s tracked-tree check accepts one kind of change: `errors.md`, differing from the run's
  head only by added entries, each `open`, `Classification: unclassified`, and with a `Detected:`
  line that names this run's ID and a step, as the close check's failure entry already must. Any
  other change, to `errors.md` or to another tracked file, is refused as today.
- `prd_error.py new` writes such an entry unchanged; nothing commits it.
- The close check (`close_findings`) allows these entries on every run, not only a failed one, so
  the close commit carries them with the Deployed rows. A failed run's own entry is one of them.
- **The skill** says: record the entry with `prd_error.py new`, do not commit it, then resume; the
  close commits it, and its diagnosis follows through `/prd-error` after the close.

### 5.3 A tests step's own timeout (item 3)

Today one `--timeout` value (default 600 s) covers every command, check and level of a call, so a
suite that takes 609 s needs `--timeout` on every `run` and `resume`.

- testing.md's Levels table gains an optional `Timeout` column, found by its header name as the
  `Environment` column is: whole seconds, at least 1. A blank cell or no column is the default.
- A pack's `pack.yaml` level may carry `timeout: <seconds>`. Where the skills copy a pack's levels
  into testing.md (authoring phase 2, the adoption bootstrap), they copy it into the `Timeout` cell.
- At `/prd-deploy`, each level a `tests` step runs gets its own Timeout; `Run:` and `Check:` commands
  keep the default. A `--timeout` given on the command line overrides every one of them (its argparse
  default becomes "not given", so the script can tell).
- The timeout message names the value that applied: `timed out after <N> s (the <level> level's
  Timeout)`, or `(--timeout)`, or `(the default)`.
- Lint: section 4, requirement 1.

### 5.4 The close on another branch (item 4)

Today the close commit lands on whatever branch ran the deploy. Where deploying means merging to an
environment's branch and promoting in a UI, the close still needs a second push, and nothing says so.

- operations.md's Environments table gains an optional `Branch` column: the branch that environment
  deploys from.
- When a run finishes (or a resume finishes) having reached an environment whose row names a branch
  other than `git branch --show-current`, `prd_deploy.py` prints on stderr
  `prd_deploy: the close is on <current>, not <branch>; push the close commit to <branch> too`
  (`a detached HEAD` for `<current>` when there is no branch). It is a note: the exit code does not
  change, and the run is never refused.
- `prd_deploy.py check` (the close check) prints the same line as a note, never a finding.
- **The skill**'s close step tells the owner to push the close to that branch, and never pushes it
  itself.
- Lint: section 4, requirement 2.

### 5.5 A Check that matches by pattern (item 5)

Today `prints` passes only when a whole stdout line, stripped, equals the text, so a Check whose
output carries a commit SHA or another changing value can use only its exit code.

- A runbook Check may be written `` Check: `<command>` matches `<pattern>` ``. It passes when the
  command exits 0 and at least one stdout line, stripped, satisfies `re.fullmatch(<pattern>, line)`.
- A mismatch prints `no stdout line matches '<pattern>'` on stderr, as a `prints` mismatch prints
  `no stdout line equals '<text>'`.
- `prints` keeps its exact meaning. A Check has `prints`, `matches` or neither, never both.
- The pattern sits between backticks, so it cannot hold a backtick; `prd-format.md` says so.
- Lint: section 4, requirement 3.

## 6. A pack release without a hand-made patch (item 6)

Today a PRD names an exact pack version (§1's `Pack:` line, an area's `Target:` line), and
`prd_hooks.py install` resolves it from the plugin: a plugin that now holds another version gives
`install refused: pack <name> <ver> (<source>) not found; … (holds <have>)`, exit 2, and nothing is
vendored. Every pack release, even one that changes nothing an area relies on, needs a `/prd-change`
whose only edit is a version number.

- **A new command**, `prd_change.py pack <prd> <name> <X.Y.Z>`, its own Bash call like every
  `prd_change.py` command, ending `; echo "prd-change-exit=$?"`:
  - it rewrites the version on every `Pack:` and `Target: pack` line that names `<name>`, keeping the
    source and the rest of each line;
  - it then does what `bump` and `record` do for a patch: the PRD version, `updated`, and the §14
    row `| <version> | <date> | pack <name> <old> → <new>; no dry run (pack version only) | - |`;
  - it refuses (exit 1, `refused: …`) when no line names `<name>`, when the named source does not
    hold `<name> <X.Y.Z>`, or when the PRD folder already has uncommitted changes, so it never mixes
    into another change; a usage error is exit 2.
- **A new bump rule:** a changed version on a `Pack:` or `Target: pack` line, the pack's name and
  source unchanged, is `patch`. `changing-prds`' "What `bump` applies" table gains the row, and the
  test that holds the table equal to `BUMP_RULES` checks it.
- **Install's hint:** when the source holds another version, the refusal ends
  `; to move the PRD to <name> <have>, run prd_change.py pack <prd> <name> <have>`.
- **The flow** (`changing-prds`): `prd_change.py pack`; then `prd_hooks.py install` from the plugin,
  which now resolves and re-vendors the pack; then the owner's approval as for any patch. `approve`
  stages `.prd-toolkit/packs/<name>/` and `.prd-toolkit/pack-sources.json` in the approval commit
  when the change moved a pack version, so lint is never red between the two.
- A new pack version that changes something the PRD relies on (a contract type, a level, a harness
  slot) fails lint or the next build, and that failure is a real change through `/prd-change`.
- A change of a pack's **name** on an area with a built block stays refused, as conversion work
  (0.8.7); only the version moves here.

## 7. The change bookkeeping

### 7.1 A moved Status line (item A)

Today `bump` ignores `Status:` lines, so a change whose only block edit is a status move (a
`live` block back to `approved` for a regression fix) records `-` in §14's IDs cell.

- A block whose `Status:` value differs from the base becomes the bump item
  `patch <ID> <file>:<line> status <old> → <new>`, so `record` names the block.
- It never raises the level on its own: a status move changes no behaviour.
- Only `/prd-change` runs `bump`; the statuses a build close or a deploy close writes are unaffected.
- `changing-prds`' list of what `bump` ignores drops block `Status:` lines.

### 7.2 Complete IDs cells (item B)

Today a new block records only its own ID: `_diff_blocks` skips its ACs and `_diff_cases` skips the
test cases under them, so a new FR-012 with AC-012.1 and T-012.1 records `FR-012`. `ids next` reads
§14's IDs cells so that a deleted T-id is never handed out again, so such a T-id, deleted later,
leaves no record.

- A new block records its ID, each of its ACs and each T-id of its test cases.
- A removed block (`Status: removed`, or a block gone from the file) does the same, so its deleted
  test cases survive in §14.
- The levels do not change: those items are already minor or major through their block.
- The 0.8.4 deferred test for the removal direction is written here.

## 8. STALE judged by the cited line (item 7)

Today `prd_context.py --for implement` marks a `Source: <path>:<L> @<sha>` region STALE whenever the
file changed since `<sha>` (or has uncommitted changes), and never compares the cited line; with
`--req`, a stale block pulled in only through `Traces:` also gives exit 1.

- The pack reads line L of `<path>` at `<sha>` and compares its text, whitespace stripped, with the
  file as it is now, uncommitted changes included:
  - the same text at line L: current, whatever else changed in the file;
  - the text at exactly one other line M: `MOVED: line L is now line M`, not stale; the build close
    and `changing-prds` step 2 refresh the `Source:` line from it;
  - the text gone, or on more than one line: `STALE: the cited line's text is gone` or
    `STALE: the cited line's text appears <N> times`;
  - a blank cited line: judged as today, by the whole file;
  - an unknown commit, a missing file, or a `Source:` that is not in the `<path>:<line> @<sha>` form:
    STALE as today.
- **The exit** counts only the blocks asked for: the `--req` blocks, or with no `--req` every block
  of the area. A block selected only because another one traces it still prints its STALE line,
  ending `(pulled in; not counted)`.
- `building-from-prds` rule 1 and `changing-prds` step 2 describe MOVED and the new STALE reasons.

## 9. SOURCES lines inside the round's hunks (item 8)

Today the builder's report gives one SOURCES line per block, `<ID>: <path>:<line>`, which the caller
writes into the PRD's `Source:` line at the close, and no script checks it.

- `prd_build_check.py --diff <base>..<head>` takes an optional `--sources <file>`, a file of SOURCES
  lines. `running-a-build.md` step 4 has the caller write the report's SOURCES field to a file
  outside the PRD folder and pass it.
- Each line must name a file the round added or changed (`git diff --name-status`), at a line inside
  one of that file's hunks on the head side (`git diff -U0`, the `+c,d` ranges). A hunk that only
  deletes lines (`d` is 0) counts at its deletion point, line `c` or `c + 1`.
- Anything else is a finding, and `--diff` exits 1 as for its other findings:
  - `sources: <ID>: <path> is not changed in <base>..<head>`
  - `sources: <ID>: <path>:<line> is outside the round's changes (hunks <a>-<b>, …)`
  - `sources: line <n> is not '<ID>: <path>:<line>'`
- The caller sends the report back to the builder with the finding; the round is not failed for it.
- Without `--sources`, `--diff` is unchanged.

## 10. The published page draws its diagrams (item 9)

Today a mermaid fence renders as `<pre class="mermaid">` holding the escaped source. The 0.8.4 proof
showed the source, and the 2026-11-08 probe found why: an Artifact draws `pre.mermaid` blocks only on
its own main page, and the proof had published the page as a file inside another Artifact. Published
as its own Artifact, the unchanged page draws both its diagrams (the Overview's, and the Technical
tab's, whose panel was hidden at load). A plain browser still shows the source.

- **The renderer.** The plan's first task renders the toolkit's own §4 diagram and a sequence-diagram
  sample with each candidate that runs mermaid's own code in an embedded JavaScript engine,
  `mermaidx` and `mmdc` (PyPI), keeps the one that draws them correctly, and pins its exact version
  in `prd_publish.py`'s dependency header. If neither does, the fallback below is the whole of item 9
  and the owner is asked before the plan goes on.
- **A diagram that renders** becomes an inline `<svg>` inside `<figure class="diagram">`, followed by
  a closed `<details>` whose summary is `Diagram source` and which holds the source in
  `<pre class="mermaid-source">`. The source never carries the class `mermaid`, which an Artifact
  would draw a second time. The figure has a light background in both themes, because the SVG's
  colours are fixed.
- **A diagram that does not**, or a renderer that cannot load, stays today's `<pre class="mermaid">`,
  which an Artifact still draws. Each fallback prints one stderr line,
  `prd_publish: diagram at <file>:<line> shown as source: <reason>`, and the render still exits 0.
- **The page still loads nothing.** Labels render as SVG text, not HTML inside the SVG. Before it is
  inserted, the SVG is checked: no `<script`, no `on…=` attribute, no `href` that is not `#…`, no
  `<foreignObject`, and no `url(` other than `url(#…)`. Any of those sends that diagram back to its
  source. Diagram IDs are numbered in order (`diagram-1`, …), so a render is the same every time.
- **Tests.** `test_loads_nothing` gains a rendered-SVG case. The golden page test runs with the
  renderer stubbed, so it stays deterministic. A separate test renders the toolkit's own diagram for
  real and asserts `<svg` and no `pre.mermaid`; it is never skipped, since `uv` installs the pinned
  renderer from the dependency header.
- **Text.** `publishing-prds` rule 5: publish the page as its own Artifact, never as a file inside
  another one. The README's Known limits and the 0.8.4 spec's section 8 say where a diagram draws
  (everywhere when rendered; as source, inside an Artifact only), and `test_release_0_6`'s pinned
  README sentence changes with the text.

## 11. The tester guard checks every harness argument (item 10)

Today the guard checks a harness command's extra arguments only when they look like paths (they hold
`/` or end in `.py`), so `--doctest-modules scripts`, `..`, `--pyargs <module>` or an unquoted
`-k s*` can reach the code. The 0.8.4 final review asked for this first.

After a harness command's own tokens, every remaining argument is classified:

- **A bare positional** (any argument not starting with `-`) is checked as a path, resolved from the
  harness's base (uv's `--directory`, else the working directory), and must lie under a test root.
  `tests/prd/test_x.py` and `tests` pass; `scripts`, `.`, `..` and a module name do not.
- **Refused outright:** `--pyargs`, `--doctest-modules`, `--doctest-glob`, `--rootdir`, `--confcutdir`,
  and `-p <plugin>`, except `-p no:<name>`, which only turns a plugin off.
- **Options that take a value** come from a fixed table, so a value is never read as a positional:
  path options (`-c`, `--basetemp`, `--junitxml`, an `-o` key holding `dir`, `path`, `file` or
  `cache_dir`) go through the test-root check; `-n` must be `auto` or a whole number; `-k` and `-m`
  expressions, and the values of `--tb`, `--maxfail`, `--durations` and the like, pass. An option
  not in the table is read as a plain flag, so a value it takes is checked as a positional, which
  errs toward refusing.
- **An unquoted glob character** (`*`, `?`, `[`, and zsh's `^` and `#`) in any harness argument is
  refused: the shell would expand it against the code before pytest sees it. A quoted
  `-k 'T-015*'` passes.
- **Messages:** `prd_tester_guard: <arg> is not under a test root`,
  `prd_tester_guard: <option> is refused after a harness command`,
  `prd_tester_guard: unquoted glob in <arg>`.
- **The 0.8.4 guard leftovers** come along: refusal tests for `grep -e x <outside>`,
  `--exclude-from=` and `--exclude-dir=`, and zsh's glob characters in grep arguments.
- **Tests:** every example above is refused; the toolkit's harness commands, and a harness using
  `-n auto`, `-p no:cacheprovider`, `--tb=short` and a quoted `-k`, still pass.
- `prd-tester`'s agent text and `testing-from-prds` list what the guard refuses.

## 12. Parallel tests for the toolkit's own suite (item 11)

Today every pull request waits about 21 minutes for `test-unit`: about 3,145 tests, run one at a
time, most starting a script as a subprocess, often in a fresh git repository.

- `prd-toolkit/pyproject.toml`'s dev group gains `pytest-xdist`, and `uv.lock` follows.
- The toolkit PRD's `unit` and `integration` Harness commands gain `-n auto` (section 4). The
  Harness's "nothing is shared between tests" rule allows it.
- Before the switch, one full run with `-n auto` finds tests that depend on order or on a shared
  cached module (the 0.8.4 ledger names one in the hooks tests), and they are fixed in the same task.
- `.github/workflows/prd-toolkit.yml` is regenerated with `prd_hooks.py ci --github --force`; the
  test jobs take their commands from Levels.
- The generated CI for adopting repositories changes only where their own Levels change. No path
  filter is added.
- The PR records the `test-unit` time before and after.

## 13. Skills, agents and the README

Every skill change follows `superpowers:writing-skills`; the two rules with the most behaviour, multi-step
confirm and publishing as its own Artifact, get evals.

| File | Change |
|---|---|
| `deploying-from-prds` (`SKILL.md`, `running-a-deploy.md`) | Items 1 to 5: confirming later steps only when the reply names them; an entry recorded mid-run and left uncommitted; Timeout and `--timeout`; the branch note and the second push; `matches` |
| `changing-prds` | Item 6's flow and bump row; item A's ignore list |
| `building-from-prds`, `running-a-build.md` | Item 7's MOVED and STALE reasons; item 8's `--sources` step |
| `publishing-prds` | Item 9's rule 5 |
| `testing-from-prds`, `agents/prd-tester.md` | Item 10's refused arguments |
| `authoring-prds`, `adopting-prds` | Copying a pack level's `timeout` into Levels |
| `references/prd-format.md`, `references/contract-types.md` | The `Timeout` and `Branch` columns, `matches`, a level's `timeout` |
| `README.md` | A 0.8.5 changelog entry; the Deploying, Packs, Publishing, and Hooks and CI sections; Known limits (0.8.5); an upgrade note |

The 0.8.4 changelog entry's proof record gains one line: fixes 2 and 3 were proven live after the
merge (2026-11-08), a real `prd-tester` on the installed 0.8.4 running `uv run --directory` and five
checked greps with no refusal.

**Upgrading from 0.8.4:** re-run `prd_hooks.py install docs/prd/<slug>` from the plugin, which vendors
the new scripts. Every new column and form is optional, so no PRD changes. A pack release now ends
with `prd_change.py pack` (section 6).

## 14. Testing

Each item's tests sit with its task, written first (`superpowers:test-driven-development`):

- **Deploy (5.1 to 5.5):** a scratch repository with a made-up runbook, as the existing deploy tests
  build: three consecutive human steps confirmed in one call and resumed once; a bad pair refusing
  the whole call; an uncommitted entry naming the run passing `resume` and one naming another run
  refused; a level Timeout of 2 s killing a sleeping level while another level passes and an explicit
  `--timeout` winning; the branch note present and absent; `matches` passing on a SHA line and failing
  with its message.
- **Packs and bookkeeping (6, 7):** `pack` on a scratch PRD with two naming lines; each refusal; the
  approval commit holding the re-vendored pack; install's hint; the bump table test; Status items;
  full IDs cells for a new and a removed block.
- **Context and build check (8, 9):** same line, moved line, gone, repeated and blank cited lines;
  the scoped exit; SOURCES in a hunk, outside a hunk, in an unchanged file, at a deletion point, and
  malformed.
- **Publishing (10):** section 10's tests.
- **Guard (11):** section 11's tests.
- **The toolkit's own PRD (4):** the new test cases, written by `prd-tester` from the PRD alone and
  run in the suite round of `/prd-build`.
- **CI parity** before every push: `scripts/ci-local.sh origin/main` with an empty HOME, now with
  `-n auto`.

## 15. Out of scope

- An inbox card that confirms several steps: the chat route does it (5.1).
- A path filter in the generated CI (section 2).
- A compatible-range declaration in `pack.yaml` (section 2).
- The other 0.8.4 deferred minors, parked in the 0.8.4 ledger archive: they are taken up when a
  release changes the code they sit in, or when one causes a failure.
- Adding `timeout` to a private pack's own levels: that pack's release, after 0.8.5 ships.

## 16. The proof

Before the merge:

1. A scratch repository's runbook with three human steps, a level with a 2 s Timeout, an Environments
   `Branch`, a `matches` Check and an error entry recorded mid-run: one run to its close, with each
   behaviour of section 5 seen in the log and the close check exiting 0.
2. `prd_change.py pack` moving a scratch PRD to a new pack version, approved, the vendored pack in the
   approval commit, and lint clean after it.
3. The toolkit's PRD published as its own Artifact with its diagram as inline SVG, checked in Chrome
   and in a plain browser opened on the file.
4. A live `prd-tester` refused on each example of section 11 and allowed on the PRD's own harness.
5. `test-unit`'s CI time on the PR, against the 21 minutes of PR #22.

After the merge: install 0.8.5 at user scope; the next deploy of the private-pack loop uses items 1
to 5 for real.
