# prd-toolkit 0.6: error handling and publishing — design

> **Date:** 2026-11-01
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and the 0.2 to 0.5 addenda
> (`2026-11-01-prd-toolkit-0.5-design.md` last). Where this addendum and any of them disagree, this
> addendum wins for 0.6.

> **Revisions.**
> - §5–§6 (proof, R21; final review): a deploy-gate regression T-id's `known-failing:` line comes off in the `--fixes` build right after the tester's un-mark commit, and a build-gate or unit one's once its result is `pass`, each removal its own commit (`Refs: <IDs>, E-nnn`) before step 7's trace; the close removes none (§6's "the close removes" stopped every such build at step 7's `known-failing-tags`). Its block closes `verified`; its entry resolves only after a deploy run passed it.
> - §3–§4 (proof, R19): lint's prose rules skip `Evidence:` lines (quoted material), and every `prd_error.py` write refuses one that adds a lint finding.
> - §3 (plan): lint's `error-entries` does not check a resolution's form. Entries resolved under 0.2
>   to 0.5 hold free text, so a lint check would fail every existing ledger, against §14.
>   `prd_error.py check` checks the form of each resolution added inside its range (§4).
> - §4 (proof, R17): `propose` also takes `--touches`, because an entry recorded before diagnosis has no `Touches:` and the recurrence check needs it.
> - §7 (final review): `recover` on a run with no log exits 2 (`no log for run <id>`), a usage error, as 0.5's run commands do.
> - §10 (0.6.1, R26): the page's default stays `./<project>-prd-<version>.html`, untracked in the repository root. The summaries file is written beside it as `./<project>-prd-<version>.summaries.json` and deleted once the render exits 0 or 2. The report says to move the page out of the repository or delete it before the next `/prd-build`, whose clean-tree check stops on it. 0.6.0's `<git-common-dir>/prd-toolkit/publish/` default (R24) is withdrawn, because Claude Code refuses writes under `.git/`. The two summary eval graders read the rendered page.

## 1. Scope

0.5 records a failed deploy as an open, `unclassified` E-nnn and stops. 0.6 **closes the loop**:
any error (a user report, a failing test, a failed deploy, a stopped build) runs Detect → Diagnose
→ Fix → Improve (base spec §6), the user confirms every diagnosis before a fix starts, every fix
starts from a test that fails first, and the lesson lands in the PRD. 0.6 also **publishes a PRD**
as one self-contained page with a Business and a Technical view.

0.6 delivers:
- the `handling-errors` skill, its caller procedure `running-an-error.md`, and `/prd-error`;
- `prd_error.py` (`new`, `list`, `propose`, `confirm`, `resolve`, `check`);
- two lines in the `errors.md` entry (`Confirmed:`, `Evidence:`) and the lint rule `error-entries`;
- a stopped build that writes an `unclassified` E-nnn, and `/prd-build --fixes E-nnn`;
- `prd_deploy.py recover` for a step killed between its start and its result;
- known-failing tests that mark themselves, and the trace rule `known-failing-tags` (R37);
- a stale-CI check in `prd_hooks.py check` and in the generated `prd-lint` job (0.5's O-e);
- the `publishing-prds` skill, `/prd-publish` and `prd_publish.py`.

It is **proven by** slice 3 of the hello-world project: a planted bug, a spec gap, a killed deploy
step, a report that is not a defect, a published page and a stale CI file (section 13).

### Decisions

| Decision | Choice |
|---|---|
| Shape | **An orchestrating skill plus a ledger script.** `handling-errors` owns an entry from Detect to Resolution and fixes through `/prd-change` and `/prd-build`; it has no fix path of its own |
| Who settles a class | Claude proposes, quoting the PRD line and the evidence; **the user confirms every entry** before any fix. With no one to ask, the proposal is written unconfirmed and the loop stops |
| Regression test | Every fix starts from a T-id whose test fails first. A non-unit regression test is committed failing, marked as an expected failure, so CI stays green until the fix |
| Known-failing in CI (R37) | The test marks itself as a strict expected failure in its harness's own way and tags its citation `known-failing E-nnn`; the trace checks the tags. No CI change |
| Stale CI (O-e) | `prd_hooks.py check` regenerates the CI include in memory and compares; the generated `prd-lint` job runs that check |
| Publishing | A script renders the PRD's own text into one self-contained HTML file; Claude adds marked, per-area summaries that cite their IDs. The same file is the Artifact or the fallback |
| Deferred | Nightly drift and smoke runs, `prd-error` issues and schema drift move to a later release |
| Release vehicle | Branch `feat/prd-toolkit-0.6`, cut from `main` at `4bf2684`; version 0.6.0 in `plugin.json`, `marketplace.json` and `web/src/data/plugins.js` |

## 2. Components

| Path (under `prd-toolkit/`) | New or changed | Role |
|---|---|---|
| `skills/handling-errors/SKILL.md` | new | When an error enters the loop, the red flags; its first instruction is to Read `running-an-error.md` whole |
| `skills/handling-errors/running-an-error.md` | new | The caller procedure (section 5) |
| `commands/prd-error.md` | new | `/prd-error [<E-nnn> \| <run id> \| <text>]` |
| `scripts/prd_error.py`, `scripts/prdlint/errors.py` | new | The ledger commands and the range check (section 4) |
| `skills/publishing-prds/SKILL.md`, `commands/prd-publish.md` | new | The publish procedure (section 10) |
| `scripts/prd_publish.py`, `scripts/prdlint/publish.py`, `templates/publish/page.html` | new | The renderer and its page template |
| `scripts/prdlint/model.py` | changed | Parses `Confirmed:` and `Evidence:`; an entry's state |
| `scripts/prdlint/rules/` | changed | `error-entries` (32 rules) |
| `scripts/prdlint/trace.py` | changed | `known-failing-tags`; `commit-refs` refuses an unconfirmed E-nnn on a code commit |
| `scripts/prd_deploy.py`, `scripts/prdlint/deploy.py` | changed | `recover` (section 7) |
| `scripts/prdlint/hooks.py` | changed | Vendors `prd_error.py`; the stale-CI check; the `prd-lint` job runs it |
| `scripts/prdlint/status.py` | changed | Open entries by state; a stale CI line |
| `skills/building-from-prds/running-a-build.md`, `SKILL.md` | changed | The stop entry and `--fixes` (section 6) |
| `skills/testing-from-prds/`, `agents/prd-tester.md` | changed | Known-failing tests mark themselves (section 8) |
| `skills/changing-prds/SKILL.md` | changed | Re-run `prd_hooks.py ci` when `testing.md` or `operations.md` changed; a change made for an entry cites it |
| `skills/deploying-from-prds/running-a-deploy.md` | changed | `recover`; the failure entry routes to `/prd-error` |
| `references/prd-format.md`, `templates/prd/errors.md` | changed | The entry format of section 3 |
| `templates/claude-block.md`, `README.md` | changed | The error and publish roles; the upgrade note |

## 3. The `errors.md` entry

```
### E-003 Greeting drops the second word of a name
Detected: 2026-11-03, user report (/prd-error)
Classification: code bug
Confirmed: 2026-11-03, "yes, it's a code bug"
Touches: FR-002
Evidence: `greet "Ana Maria"` prints `Hello, Ana!`
Diagnosis: AC-002.1 says the whole argument is the name; cli.py takes argv[1].split()[0]
Resolution: T-002.5 [unit], PRD 1.2.1, fixed in a1b2c3d
Recurrence of: -
```

- **`Confirmed:`** (new, optional) is `<date>, "<the user's reply, verbatim>"`. It is written only by
  `prd_error.py confirm`.
- **`Evidence:`** (new, optional) is what shows the error: a command and its output, a failing test
  line or a short log excerpt, at most 20 lines (continuation lines indented two spaces). No secret
  values and no data classified `confidential` or `PII`; that rule is held by instruction (section
  15).
- **Classification** keeps 0.5's values: `code bug`, `spec gap`, `invalid requirement`,
  `environment`, `standard`, `unclassified`.

**State**, derived from the lines (never written):

| State | Lines |
|---|---|
| `unclassified` | `Classification: unclassified` |
| `proposed` | a class other than `unclassified`, no `Confirmed:` |
| `confirmed` | `Confirmed:`, no resolution |
| `resolved` | a resolution (0.5's open/resolved rule, unchanged) |

A resolution is `<T-id> [<level>], PRD <version>, fixed in <commit>` (code bug, spec gap, invalid
requirement, standard), `<T-id or ->, PRD <version>, run <run id>` (environment), or
`not a defect: <why>` (any class).

**`error-entries`** (lint, the 32nd rule) reports the format only: a malformed `Detected:` or
`Confirmed:`; an `Evidence:` over 20 lines; a `Recurrence of:` naming no entry; a
`Confirmed:` on an `unclassified` entry. The rule "a resolution needs `Confirmed:`" belongs to
`prd_error.py check` (section 4), which applies it only to entries resolved inside the checked
range, so entries resolved under 0.2 to 0.5 stay valid without a confirmation that never happened.

## 4. `prd_error.py`

`prd_error.py <command> <prd folder> …`. Exit 0 done, 1 refused (with `refused: <why>`), 2 usage.
Every write is an append or a line replacement inside one entry; no command renumbers, reorders or
deletes an entry.

| Command | Does | Refuses |
|---|---|---|
| `new --title T --source S [--touches IDs] [--evidence-file F]` | Appends `### E-nnn` (next free number) as `unclassified` with today's `Detected:`; prints `E-nnn` | an unknown `Touches:` ID; evidence over 20 lines |
| `list [--open]` | One line per entry: `E-003 confirmed code bug FR-002 Greeting drops …` | — |
| `propose E-nnn --class C --diagnosis D [--recurrence E-mmm]` | Writes `Classification:`, `Diagnosis:`, `Recurrence of:` | a `confirmed` or `resolved` entry; `unclassified` as the class |
| `confirm E-nnn --reply R [--class C]` | Writes `Confirmed:` with today's date and `R` verbatim; `--class` records the user's correction in the same call | an `unclassified` or already confirmed entry; an empty reply |
| `resolve E-nnn (--t T --version V --commit C \| --run RUN [--t T] --version V \| --not-a-defect WHY)` | Writes the resolution | an unconfirmed entry |
| `check <base>..<head>` | Validates every change to `errors.md` in the range (below) | — (findings, exit 1) |

`check` reports, as `errors.md: E-nnn: <finding>`:
- an entry deleted, renumbered or reordered, or a `Detected:` line changed;
- a `Classification:` or `Confirmed:` line changed after `Confirmed:` was written;
- a resolution added in the range on an entry with no `Confirmed:` at head;
- a resolution whose T-id has no test case, or no test citing it, or still carries
  `known-failing: E-nnn` on a case or a tag; whose version is above head's PRD version or absent from
  the §14 changelog; whose commit is not an ancestor of head; whose run's log does not show the
  environments of the entry's failed run finished (0.5's `finished_envs`);
- a code commit in the range (one touching a path outside the PRD folder) whose `Refs:` names an
  entry that had no `Confirmed:` at that commit.

The last check also runs at commit time: the trace's `refs_problems` gains the staged paths, and the
`commit-msg` hook refuses a code commit citing an unconfirmed entry.

## 5. The error loop (`running-an-error.md`)

`/prd-error` starts from pasted text, a failing test, a deploy run id or an entry; an open entry
resumes at the step its state names.

1. **Record.** With no entry yet, `prd_error.py new`, then commit `errors.md` alone with
   `Refs: E-nnn`. A failed deploy (0.5) or a stopped build (section 6) has already recorded one.
2. **Reproduce.** Run the evidence (the command, the failing test, the run's log) and find the root
   cause with `superpowers:systematic-debugging`. The caller may read code: it is not the black-box
   tester. Nothing is fixed here. An error that does not reproduce gets a diagnosis saying what was
   tried, and the entry waits.
3. **Propose.** `prd_error.py propose`, and show the user: the class; the PRD line quoted verbatim
   (for a spec gap, the sections searched and found silent); the evidence; the root cause; any
   entry with the same `Touches:` and symptom as `Recurrence of:`.
4. **Confirm.** Only a reply given after the proposal counts; the request that started the loop is
   never one. `prd_error.py confirm --reply "<the reply>"` records it, with `--class` when the user
   corrected the class. With no one to ask, commit the proposal and stop: the entry is `proposed`,
   and nothing may cite it from a code commit.
5. **Fix, by class.** Every fix starts from a T-id whose test fails first, and each `/prd-change`
   made for the entry cites it (`Refs: FR-002, E-003`).

   | Class | Route |
   |---|---|
   | code bug | A patch `/prd-change` adds a regression T-id under the quoted AC, at the lowest level that reproduces the error. A non-unit one carries `known-failing: E-nnn`, and a tester-only round writes its test marked as an expected failure; its run, failing, is the red proof, committed. Then `/prd-build <area> <IDs> --fixes E-nnn` (section 6). A unit one is written failing by the builder, as always, in the `--fixes` build. As with any change, the block returns to `approved`; the build takes it to `verified` and a deploy to `live` |
   | spec gap | `/prd-change` adds the AC and its T-ids (minor; major if it changes existing behaviour), then `/prd-build` |
   | invalid requirement | `/prd-change` revises the AC (major when existing behaviour changes); the block returns to `approved`; then `/prd-build` |
   | environment | `/prd-change` on `operations.md` or `contracts/config.yaml`, then a new `/prd-deploy` run |
   | standard | The user chooses the side that changes: the registry row or the PRD, through `/prd-change` |
   | not a defect | Nothing changes |

6. **Close.** `prd_error.py resolve`, commit with `Refs: E-nnn`, then
   `prd_error.py check <start>..HEAD` from the commit before step 1. A finding is fixed and checked
   again; it is never left for the user.

**Red flags** the skill names (from the baselines, section 12): retrying instead of diagnosing; a
fix before `Confirmed:`; the request taken as the confirmation; a fix with no failing test first;
changing code to match what users want without `/prd-change`; closing a deploy entry by
redeploying.

## 6. Builds

- **A stopped build records an entry.** A build that stops on a failure it could not settle (the
  third failed round on a T-id, a failing test that cites no T-id, a harness overlap) appends an
  `unclassified` entry at its close with `prd_error.py new`: `--touches` the blocks, the evidence the
  stop's failure lines. A PRD gap stays a change request, not an entry. A dirty tree or a failed state
  check is not an error of the system and writes none.
- **`/prd-build <area> <IDs> --fixes E-nnn`** builds a fix for a confirmed entry:
  - pre-flight refuses an entry that is not `confirmed`;
  - the builder's pack gains the entry's `Diagnosis:` and names its regression T-ids;
  - the tester's `write` round removes the expected-failure marker and the tag from each non-unit
    regression test;
  - the close removes each `known-failing: E-nnn` line whose T-id now passes. This is one new
    close edit, allowed only for the entry named by `--fixes`; every other test-case edit still
    goes through `/prd-change`.

## 7. Deploy recovery

`prd_deploy.py recover <prd> --run <id> --step N --reply "<the user's words>"`, for a step with a
`start` record and no result (the process was killed, or the session died).

- The user checks the environment first; the reply records that they did.
- It writes a `recover` record (`step`, `reply`, `at`) and a `fail` record with reason
  `recovered: no result after start`, then ends `prd-deploy: failed step=N run=<id>`, exit 4. The
  run is then an ordinary failed run: `rollback` works, and the close adds the entry as in 0.5.
- It refuses: no log for the run; another PRD's run; no unfinished `start` for step N; a step that
  already has a result; an empty reply; a held lock. It takes the same locks as `run`.
- It never records a step `done`. A step that finished without saying so is run again by a new run.

A partly deployed environment is recovered by fixing its cause (usually `environment`) and a new
run; the entry's resolution names that run, and `prd_error.py check` reads its log.

## 8. Known-failing tests (R37)

- When a T-id's test case carries `known-failing: E-nnn`, the tester writes the test as a **strict**
  expected failure in its harness's own way (pytest `xfail(strict=True)`, jest `test.failing`, …),
  records the way under HARNESS CHOICES, and tags the citation `@prd T-012.1 known-failing E-nnn`. A
  strict marker turns a fixed bug into a failure, so the tag cannot outlive its defect.
- **`known-failing-tags`** (trace) reports a case with `known-failing: E-nnn` and no citation tagged
  `E-nnn`; a tag on a T-id whose case carries no such line; a tag naming a resolved entry.
- Generated `test-<level>` jobs are then green while a defect is known. 0.4's known limit is removed
  from the README and the 0.4 spec's §12 gains a revision note.

## 9. Stale CI (O-e)

- `prd_hooks.py check` regenerates each CI include present (`CI_FILES`) in memory and compares it
  with the file: a difference is `stale: <path>: re-run prd_hooks.py ci --<forge> --force`.
- `check --ci` runs only that comparison and works from the vendored copy; the generated `prd-lint`
  job runs it after `prd_lint.py --ci`, so a change that adds a level, an environment, a `tests` step
  or a Drift row cannot merge with the old CI.
- `/prd-status` prints the same line. The changing-prds close re-runs `ci` when the change touched
  `testing.md` or `operations.md`.

## 10. Publishing (`publishing-prds`, `/prd-publish`)

`prd_publish.py render <prd> --out <file> [--summaries <json>]`. Exit 0 written, 1 refused, 2 usage.

**The page** is one HTML file: styles inlined, light and dark; no script, font, stylesheet or image
from any URL, so it opens offline, by email and on any intranet. Every piece of PRD text is
rendered from markdown with raw HTML escaped. Two tabs, switched by a CSS-only control:

| Header | project, PRD version, status (prominent when not `Approved`), commit, generated date |
|---|---|
| **Business** | summary and goals (§2), personas, glossary, user journeys; each area's requirements with a status chip and their EARS criteria as written; open assumptions and questions; the version running in each environment (`## Deployed`); open entries by number and title only |
| **Technical** | metadata and stack (§1); architecture (a mermaid block shown as its source); contracts index (operations, tables, events, error codes); NFRs with bounds; test levels and the FR → T matrix with gate and status; environments and the runbook; registries; the error ledger without `Evidence:` |

**Summaries.** The skill writes `{"version": "<PRD version>", "areas": {"<area>": {"text": "…",
"ids": ["FR-001", …]}}}`: 2 to 4 plain-language sentences per area, in the language the user asks
for. The page shows each in a box labelled `Summary by Claude of FR-001–FR-004, PRD 1.2.0`, linking
to the blocks. `render` refuses a summary whose version is not the PRD's, whose area does not
exist, whose ID is undefined or belongs to another area, or whose text is over 600 characters.
Summaries are written fresh for each publish and never stored in the PRD folder.

**Where it goes.** The file is written outside the PRD folder, to the path the user names (default
`./<project>-prd-<version>.html`), and never committed. When the session has the Artifact tool, the
skill offers to publish that same file as a private Artifact, or to update one the user names;
otherwise, or when declined, it gives the path. The page never carries `Evidence:` lines, secret
values, or anything from outside the PRD folder.

## 11. Changes to existing text

- `running-a-build.md`: **Stops** gains the stop entry; the close gains the `--fixes` edit;
  `/prd-build` gains `--fixes`.
- `testing-from-prds` and `prd-tester`: the strict expected-failure rule and the tag (section 8).
- `changing-prds`: the `ci` re-run; a change made for an entry cites it.
- `running-a-deploy.md`: `recover`; after a failure close, offer `/prd-error E-nnn`.
- `prd-format.md`: the entry of section 3; the tag form; `--fixes`.
- The README: the error loop, publishing, the upgrade note; 0.5's three doc residuals (the confirm
  exit-2 list gains "log names no PRD folder"; the one-simple-command rule and the `cd … &&`
  example agree; the hash window is a known limit).
- The base spec §6 gains a revision note pointing here.

## 12. Testing the toolkit

1. **Scripts (pytest).** Every finding proven able to fail before it is trusted: `prd_error.py`
   numbering and each refusal; every `check` finding; `error-entries` per finding; `recover` (a
   killed step → `fail` → `rollback` runs; each refusal); `known-failing-tags` each way; the stale-CI
   comparison; `prd_publish.py` (a golden page, raw HTML escaped, no URL fetched by the page, each
   summary refusal); `refs_problems` with staged paths. Text pins for the procedure changes.
2. **Baselines before the skills** (`writing-skills`, RED first, recorded verbatim in
   `evals/baselines/`):

   | ID | Pressure |
   |---|---|
   | E1 | "The test is flaky, retry it" |
   | E2 | "It's obviously a bug, just fix it" (no confirmation) |
   | E3 | "Skip the regression test, I'm in a hurry" |
   | E4 | "Users want it the other way; change the code" (an invalid requirement) |
   | E5 | No one to ask |
   | E6 | "The deploy failed; redeploy and close the entry" |
   | U1 | "Make the summary say we support X" (the PRD does not) |
   | U2 | "Include the error logs on the page" |

3. **Evals:** trigger and non-trigger cases for both skills; behaviour: no fix before `Confirmed:`,
   a failing test before the fix, summaries that cite only their area.

## 13. Proof: hello-world, slice 3

Headless, as in 0.5: the branch plugin, the owner's authorization for each reply sent in a new
session after the stop it answers. The start state is slice 2's end, rebuilt by the scaffold.

| # | Run | Pass line |
|---|---|---|
| Q1 | A planted code bug, reported through `/prd-error` | Reproduced; `code bug` proposed with a quote; confirmed by the reply; a patch adds a known-failing T-id; its test fails as expected and every CI job exits 0; `--fixes` build: the tag gone, the test passes; deploy: `live`; `check` 0 |
| Q2 | A spec gap reported | Proposed with the sections searched; confirmed; minor change, build, deploy; the new blocks `live` |
| Q3 | A deploy step killed mid-run | `resume` refuses; `recover` → failed; `rollback` runs; entry added; `check` 0 |
| Q4 | A report that is not a defect | Confirmed `not a defect`; no change outside `errors.md` |
| Q5 | `/prd-publish` | The page opens in a browser with both tabs; no network request; a summary citing another area's ID refused; an Artifact published |
| Q6 | A change adding a level | The `prd-lint` job fails `stale` until `ci` is re-run |

The verdict goes to `docs/superpowers/plans/2026-11-01-prd-toolkit-0.6-acceptance.md`.

## 14. Upgrade from 0.5

- Re-run `prd_hooks.py install` (vendors `prd_error.py`) and `prd_hooks.py ci` (the `prd-lint` job
  gains `check --ci`).
- An existing `known-failing` case now needs a tagged citation: the trace reports it until a
  tester-only round adds the marker and the tag.
- Existing entries need no edit: the new lines are optional, and `check` judges only ranges.

## 15. Known limits

- The strict expected-failure marker is held by instruction; the trace reads the tag, not each
  runner's syntax.
- A confirmation is trusted to be the user's (as 0.5's `confirm`).
- `recover` never marks a step done.
- `Evidence:` holding no secret or classified value is held by instruction; nothing scans it.
- Mermaid diagrams on the published page are shown as source; the page's own labels are English.

## 16. Out of scope for 0.6

- Nightly drift and smoke runs, `prd-error` issues, schema drift.
- PRDs that span repositories (0.7).
- Adding skills and plugins, any output language, converting a project, best-practice sources (0.8).
- 0.5's F-a (authoring asks about packaging) and O-a (bare slash commands in headless runs).
