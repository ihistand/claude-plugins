---
name: authoring-prds
description: Use when the user wants a PRD, product spec or requirements document written before building a new product, service or feature set, or runs /prd-new - interviews to a PRD folder (docs/prd/<project>/) with contracts and test cases that agents build, test and deploy from (when the user says not to ask questions, writes that folder with every unknown marked), or when asked to continue or resume a draft PRD, or to approve, sign off or change the status of a draft PRD under docs/prd/
---

# Authoring PRDs

## Overview

**The PRD is the authority.** Every agent that later creates, changes, deploys or tests the
system works from it, not from the code (spec section 1). A PRD is a folder,
`docs/prd/<project>/`, copied from the template: an index, features with EARS acceptance
criteria, contracts, one test case per T-id, testing, operations and an error ledger. It is not
a `PRD.md` essay.

**Core principle:** a value the user did not give you is not a fact. Mark it. A PRD that reads
finished but rests on unmarked guesses sends every builder and tester the wrong way at once.

**Violating the letter of these rules is violating the spirit.** A hurried user, a vague
request or "just approve it" changes the questions you ask, never the gates.

Grammar and shapes live in the references; read them before writing, do not guess:
`${CLAUDE_PLUGIN_ROOT}/references/prd-format.md` (folder, blocks, test-case fields),
`contract-types.md`, `ears.md`, `clarify-categories.md`, `quality-checklist.md`,
`test-levels.md` (same folder).

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
A PRD that is not adopted yet has no `.prd-toolkit/` until the hooks install, so in every command
below `<scripts>` is the plugin's `scripts` directory, written as a literal absolute path (in
double quotes if it holds a space): the plugin root is two directories above the skill's base
directory (Claude Code shows it as "Base directory for this skill" when the skill loads), and
`<scripts>` is `<plugin root>/scripts`. A script that is not found is a tool error: report it,
never guess another path.

Lint, the mechanical gate:

```bash
uv run --script <scripts>/prd_lint.py docs/prd/<slug>; echo "prd-lint-exit=$?"
```

The gate is the `prd-lint-exit=` value lint prints: `0` clean, `1` violations, `2` usage or internal error. Ignore the Bash call's own success; the trailing echo always succeeds. Use this form every time you run lint.

## Non-negotiable rules

1. **Never invent a value.** Unknown → `[NEEDS CLARIFICATION: question]`. Inferred, including
   every "sensible default" → `[ASSUMPTION A-nn: text]` plus a `prd.md` §12 row with status
   `open`. Numbers, versions, roles, limits and retention periods are values.
   An assumption needs a basis you can name (the repo, the request, a common convention). A
   value only the user can know (a hostname, URL, person, group name, secret name, budget) has
   none: it is a `NEEDS CLARIFICATION` marker, never a placeholder assumption such as
   `go.example.internal`.
   Packaging: for a project that ships code, each of the four packaging elements is either stated or written as its own `[NEEDS CLARIFICATION: <element> …]` marker in section 1, never left out; this holds when the user says not to ask questions.
2. **Every AC gets at least one test case** in `test-cases/<area>.yaml` with all seven
   sufficiency elements, and the requirement's `Tests:` line cites it.
3. **Never set `Approved` while lint fails**, and never without the user's explicit approval
   after phases 1 to 6 pass. "Looks fine to me" over an open gate is not approval.
4. **No adjective is a requirement.** "Fast", "secure", "scalable" become NFR blocks with a
   number and a unit, and security becomes concrete ACs (who is denied, with which error).
   A bound the user has not given is a question with a recommended number, never a silent pick.
5. **Silence is not an answer.** Ask, then stop and wait. Never answer your own questions, and
   never write "if there's no answer, the default stands".
6. **Never offer to break a rule "if the user insists".** No offer to drop the test cases, to
   approve "as it stands", or to skip a gate. A user who refuses a rule gets a Draft that
   cannot be approved, and the reason; never a promise to remove the rule on request.

## The seven phases

| # | Phase | Gate |
|---|---|---|
| 1 | **Context.** Read the repo, its README, CLAUDE.md, AGENTS.md and docs. Look up facts the user does not uniquely hold (subagents may). Propose registry rows, Decision `proposed`: standards rows from detected linter configs (`.sqlfluff`, `.pre-commit-config.yaml`, `[tool.*]` sections in `pyproject.toml`, lint scripts in `package.json`); skills rows from this session's skills listing that match the project's objects and activities, always including `superpowers:writing-plans` for planning. A skills row may become `required` only for a plugin skill (`plugin:skill`) or one found under `.claude/skills/`, because lint checks it is installed; a skill built into Claude Code (`code-review`, `security-review`, `simplify`, `init`) may only be `recommended`. **Packs and languages:** list the packs on this machine with `uv run --script <scripts>/prd_lint.py --list-packs; echo "prd-lint-exit=$?"`, its own Bash call (in a repository that has `.prd-toolkit/`, `uv run --script .prd-toolkit/prd_lint.py --list-packs; echo "prd-lint-exit=$?"`); it prints one line per pack, `<name> <version> (<source>) — <description>`, built-ins first, then the installed plugins' packs. Choose the pack whose description fits what the PRD's outputs are: a service with an API, a database or events is `service`; Markdown documents written for people (a guide, a runbook, a policy) are `document`. Propose the default pack, `language:` (the language the user writes to you in) and the output language (the language of the outputs, `language:` unless the user says otherwise) as `proposed` rows beside the pack's §5 and §6 rows: §1 lines `- Pack: <name> <X.Y.Z> (<source>)` and `- Output language: <code>`, frontmatter `language: <code>`; phase 4 decides them like any row. A part of the project with another pack (a CLI's install guide in the CLI's PRD) is its own area with a `Target:` line. | A short note to the user of what was found |
| 2 | **Draft.** Copy `${CLAUDE_PLUGIN_ROOT}/templates/prd` to `docs/prd/<slug>/` with Read and Write and fill it (below). Gaps become `[NEEDS CLARIFICATION: q]`, inferences `[ASSUMPTION A-nn: …]`. Write features, contracts and test cases, not only prose. Then apply the pack (**Applying the pack**, below). | Draft on disk; the `prd-lint-exit=` value is `0` |
| 3 | **Clarify rounds** per `clarify-categories.md`: score all thirteen categories (ask category 13, packaging, whenever the project ships code; for a PRD with no code, mark it Not applicable with the reason); at most five multiple-choice questions per round, each with a recommended answer, ranked by impact × uncertainty; write each answer in immediately. Rounds are uncapped. Add the pack's `clarify.md` questions (beside its `pack.yaml`) to the rounds, and category 1 asks the target profile: the pack, `language:` and the output language, per area when one differs. | Zero `NEEDS CLARIFICATION` markers in any file, YAML and SQL comments included (delete each template hint once its slot is answered); §13 reads `None.`; every category Clear |
| 4 | **Sign-off.** Show every assumption (ID and text) and every registry row in your message; a confirmation covers only what the user was shown. The user confirms or corrects each assumption (§12 status `confirmed` or `corrected`), or names who will confirm intent only that person knows (`awaiting <who>`, which may stay through approval), and decides each row. Copy into `operations.md` every hard rule from a registered skill that bears on operations (for example "Claude never deploys Looker") as `(actor: human)` runbook steps, so the PRD stands alone. | No `open` assumption; no `proposed` row |
| 5 | **Mechanical gate.** Set status `In review`, run lint, then answer every question in `quality-checklist.md`, plus: every contract listed in §7 is populated, or deleted, dropped from §7 and declared `Not applicable` in §1. Lint cannot tell an empty skeleton (`paths: {}`, `roles: {}`) from a deliberate "none". | The `prd-lint-exit=` value is `0`; every checklist answer yes |
| 6 | **Test-agent dry run.** `uv run --script <scripts>/prd_lint.py --sample-tids 5 docs/prd/<slug>` picks the T-ids (at most five; fewer when the PRD has fewer). Unit T-ids are never sampled: unit cases read code and stay with the builder. A judged T-id is not unit and may be sampled: the dry run judges whether its test could be written from the PRD alone (a test that calls `prd_judge.py` on the output and asserts its exit code), never a score, and nothing is graded. Exit 1 from `--sample-tids` (no non-unit T-id) fails this gate; an empty dry run never passes. Dispatch the `prd-toolkit:prd-tester` agent as `${CLAUDE_PLUGIN_ROOT}/skills/testing-from-prds/dispatching.md` says (dry-run directory, state check, dispatch, judgment, cleanup): it writes the tests for those T-ids to the dry-run directory, `<first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/`, and lists every question it had to ask. Its guard allows reads in the PRD folder, the dry-run directory and the test roots, and writes only to the test roots and the scratch directory; the tester's own rule keeps a dry run to the PRD folder and its dry-run directory. Only when `prd-tester` is not in the Agent tool's list, dispatch a fresh general-purpose subagent with [dry-run-prompt.md](dry-run-prompt.md) instead. Either way, delete the dry-run directory after judging (dispatching.md's cleanup step), pass or fail. | One test per sampled T-id listed under TESTS; every question dismissed by an exact quote, per the triage in [dry-run-prompt.md](dry-run-prompt.md); FILES READ holds only paths under the PRD folder and the run's dry-run directory; the state check finds no change outside the dry-run directory |
| 7 | **Approval.** On the user's explicit approval: status `Approved`, version `1.0.0` (only on a first approval, when §14 holds no row at 1.0.0 or above; otherwise this is an approval of a change, and it goes through `prd-toolkit:changing-prds` step 5 instead), `updated` today, a §14 changelog row that records the dry run (`Approved; dry run T-003.1, T-007.2, … 0 open questions, 4 dismissed by quote`); the `prd-lint-exit=` value is `0`; then `uv run --script <scripts>/prd_block.py docs/prd/<slug>` writes the CLAUDE.md block; commit the folder and CLAUDE.md with `Refs: none (no behaviour change)`; offer to install the hooks and generate CI (`uv run --script <scripts>/prd_hooks.py install docs/prd/<slug>`, then `uv run --script <scripts>/prd_hooks.py ci --github docs/prd/<slug>`, or `--gitlab`; each its own call, then commit `.prd-toolkit/` and the CI file), and run them only on the user's explicit yes; hand off to `superpowers:writing-plans`. | Explicit user approval |

**Deploying.** Phases 3 and 4 also ask what a deploy needs: the environments and which environment
is production, the command that deploys each and the command that checks it (and a rollback, when
there is one), the human approval before production, and the smoke cases (a `testing.md` level
named `smoke` with Gate `deploy`). Write them to the grammar in
`${CLAUDE_PLUGIN_ROOT}/references/prd-format.md`: Environments `| Environment | URL | Production |`,
and runbook steps `N. <title> (actor: agent|human) (env: <environment>)` with labelled lines.
The runbook you write passes the `runbook-steps`, `runbook-env`, `production-gate`,
`runbook-tests` and `drift-rows` rules; an unknown command stays a `[NEEDS CLARIFICATION]`.

**Links.** When the project consumes or provides another PRD's contract items (it reads another
repository's table, calls its API, consumes its events), phase 1 notes it and phase 4 proposes
the link. On the user's yes, once the draft exists, run `prd_links.py add` as its own call, with
`<location>` the other repository's root as a path from this one, or `<git URL>#<PRD folder>`:
`uv run --script <scripts>/prd_links.py add docs/prd/<slug> <location>; echo "prd-links-exit=$?"`.
An upstream's items are cited with its prefix (`table:transform/orders_daily`) and copied by
`prd_links.py sync docs/prd/<slug> <upstream>`; lint reports the row cited nowhere until then.

A failed dry run is a gap: write each question into the file it names as a
`[NEEDS CLARIFICATION: …]` marker, set the status back to `Draft`, and go back to phase 3; then
run phases 5 and 6 again, phase 6 on a fresh sample. Do not answer the subagent, and do not let
it read code. A state check that finds a changed path outside the dry-run directory fails the dry
run too: report the paths to the user and restore nothing yourself. Delete the dry-run directory
either way (dispatching.md's cleanup step).

Before phase 7, check what this conversation holds. If it does not hold a passing checklist and
a passing dry-run report for the current files, run phases 5 and 6 now before approving. A
status of `In review` and a clean lint are not evidence that either ran; a new session starts
with neither.

In phase 7, if lint fails after you set `Approved`, put the status and version back, remove the
§14 row you added (a leftover 1.0.0 row would route this draft to `prd-toolkit:changing-prds`),
report each finding, and return to the phase it belongs to. Never commit an `Approved` PRD that fails lint.

### Phase 2 in detail

- **Slug:** `$ARGUMENTS` from `/prd-new`, else derive one and say so. Lowercase,
  `^[a-z][a-z0-9-]*$`. If `docs/prd/<slug>/` exists, read its §14 first. A row at 1.0.0 or
  above means it has been approved: stop, that is a change for `prd-toolkit:changing-prds`.
  No such row means it is a draft: resume it (below). Never copy the template over it.
- **Copy:** `mkdir -p docs/prd/<slug>`, then Read each file under
  `${CLAUDE_PLUGIN_ROOT}/templates/prd/` and Write it to the same relative path under
  `docs/prd/<slug>/` (Glob `**/*` in the template lists them; each `.gitkeep` sits beside a
  README.md and may be skipped). Never copy with a shell command: a sandbox that denies the
  plugin folder as a copy source blocks `cp`, and Read and Write are the granted tools.
- **Fill all four slots in every file** except `.gitkeep`: `{{project}}` the slug,
  `{{owner}}` the owner the user named, else `[NEEDS CLARIFICATION: who owns this product]`
  (never `git config user.name`: the owner is a value only the user knows),
  `{{date}}` today as `YYYY-MM-DD`, `{{sql_dialect}}` the database's sqlglot dialect
  (`postgres`, `mysql`, `bigquery`, `sqlite`, `tsql`, …).
- **No database:** delete `contracts/schema.sql`, drop its §7 row, drop the `sql-dialect:` line
  from the frontmatter, and add to §1
  ``- Not applicable: `contracts/schema.sql` — <reason>``. Database unknown: the same, with
  the reason `[NEEDS CLARIFICATION: is there a database, and which?]`.
- **Each optional contract** (openapi, events, permissions, config, classification,
  dependencies, fixtures): populate it, or delete it the same way with a reason.
- **Harness first:** fill `testing.md` `## Harness` (lifecycle, environment switch, clients,
  fixtures, assertions, leaks, …) before writing test cases. Every test case leans on those
  conventions; a slot you cannot fill stays a `NEEDS CLARIFICATION` marker for phase 3.
- **Levels:** fill each row's harness command and environment, and in a clarify round ask the
  user which Gate (`build` or `deploy`) each level runs at; never keep the template's Gate
  silently. `build` runs in every build and in merge CI; `deploy` runs against a deployed
  environment. A build-gate Harness command never collects a deploy-gate level's test path
  (`pytest tests` collects `tests/system`): give each level its own path. Lint reports an overlap
  (`test-level`).
- **Refs and acceptance:** a test case that depends on something outside its contracts (a
  component contract, an architecture fact, a Harness slot) cites it in `refs:`. An acceptance
  case follows the acceptance rules in `test-levels.md`: observable results only, fresh data on
  persistent environments, a step per expectation.
- **IDs:** FR and NFR share one number sequence; T-ids are per requirement (`T-004.1`).
- Run lint. A Draft with open markers lints clean; a lint failure here is a grammar error. Fix it.

### Applying the pack

The pack is the one phase 1 proposed (for a service, `service` is the default and needs no
`Pack:` line). Read its manifest with the Read tool: `.prd-toolkit/packs/<name>/pack.yaml` when the
repository has `.prd-toolkit/`; for the source `prd-toolkit`, otherwise, `<plugin root>/packs/<name>/pack.yaml`;
for an installed plugin's pack, `<installPath>/prd-packs/<name>/pack.yaml`, with the `installPath`
that `~/.claude/plugins/installed_plugins.json` records. Then, after copying the template:

1. **Contracts:** drop each contract the pack does not use (delete the file, drop its §7 row) and
   add to §1 ``- Not applicable: `<file>` — <reason>`` for it, as for any unused contract.
2. **Contract types:** add each of the pack's contract types to §7 with the Validator cell `pack`
   (`| outline | `contracts/outline.yaml` | pack |`), and write its files: for `document`, one
   `contracts/outline.yaml` key per document, with `path` (a `.md` path outside the PRD folder),
   `audience`, `purpose`, `sections`, `terms` and `length`. A test case's `target:` names it through
   the pack's target kind: `target: doc:install-guide`.
3. **Levels and Harness:** fill the Levels rows and the Harness slots from the pack's `levels` and
   `harness`; a slot the pack leaves out stays a `[NEEDS CLARIFICATION]` marker, and a template
   Levels row the pack does not name is dropped (no `unit` row for a pack whose
   `builder-tests:` is `none`, unless another area of the PRD needs it). Copy its
   `standards` and `skills` into §5 and §6 as `proposed` rows. The Gate of each level is still
   asked in a clarify round.
4. **Language:** write every prose line in the PRD's `language:`: features, ACs, test-case
   rubrics, glossary meanings. The EARS openers come from its language table: `en` opens with
   `When`, `While`, `If`, `Where` or `The … shall`; `es` with `Cuando`, `Mientras`, `Si`, `Donde`
   or a subject and `deberá` (`La guía deberá …`). Labels, IDs and kinds stay English.

Never declare a custom contract type, or write a validator, for an output a listed pack covers:
a Markdown guide is a `document` area, not a `doc` type with a `check_keys.py` of your own.

**Profile lines.** A PRD whose outputs are all of one pack names it in §1:
`- Pack: document 1.0.0 (prd-toolkit)`, and `- Output language: <code>` when the outputs' language
differs from `language:`. An area of another pack carries a `Target:` line under its level-1
heading, before its first `###` block:
`Target: pack document 1.0.0 (prd-toolkit), output language en`. Until phase 4 decides the
profile, mark it where it stands with a line `- Profile: [ASSUMPTION A-nn: <pack>, language <code>,
output language <code>; <basis>]` under the §1 lines, indexed `open` in §12.

**Judged cases.** What a script can check exactly (sections in order, terms used, word count,
links resolving) is a case at the pack's `checks` level. Everything else about the output's quality
is a judged case at its `judged` level: `expect` has `rubric:` and `threshold:` and no `output:`,
written as the pack's `rubrics.md` says (Read it beside `pack.yaml`). Each rubric item is one claim
a grader can prove with a quote copied from the output: it names the section, the term or the
reader action it is about, never "is clear", "reads well" or "is good". Three to eight items; a
threshold of 1.0 only when every item is a hard requirement.

### Resuming a draft

A folder with no §14 row at 1.0.0 or above has never been approved, whatever its status line
says. Continue it here; never through `prd-toolkit:changing-prds`, and never bump its version
for an answer. Redo phase 1 (the note to the user), keeping every registry row already decided.
Then run lint and resume at the first phase whose gate is open:

- Lint fails on grammar → phase 2.
- Any `NEEDS CLARIFICATION` marker, §13 not `None.`, or a category not Clear → phase 3.
- Any `open` assumption or `proposed` row → phase 4.
- Otherwise → phase 5. A new session holds no passing checklist or dry run, so phases 5 and 6
  always run again before phase 7.

Resuming before phase 5 sets the status back to `Draft`.

## When the user pushes

| User says | You do |
|---|---|
| "Skip the questions, use sensible defaults" | Draft the folder. Every default is an `[ASSUMPTION A-nn]`, indexed `open`. Then show the assumptions and round-1 questions, each with your recommended answer, so the user can confirm them in one reply. Status stays Draft. |
| "Make it fast and secure" | NFR blocks with a number and unit each; security as ACs with a denied role and an error code; unknown numbers asked with a recommendation. |
| "Leave the test cases to QA" | Write the test cases anyway. They are the spec QA tests from; QA still writes the test code. Do not offer to remove them. |
| "Looks fine, mark it approved" | Run lint and list the open gates (markers, §13 not `None.`, open assumptions, `proposed` rows, checklist, dry run). Run phases 5 and 6 here if this conversation holds no passing result for the current files. Approve only when all pass. |

## WRONG vs CORRECT

```
WRONG  (nfr.md)
- The API shall be fast and secure.
- Redirect p99 < 25 ms at 500 redirects/s.          ← invented, unmarked

CORRECT
### NFR-004 Redirect latency
Status: approved
Acceptance (EARS):
- AC-004.1 The redirect endpoint shall answer within 20 ms at p99 under 500 requests/s.
  [ASSUMPTION A-03: 20 ms p99 at 500 requests/s; no traffic data yet]
Errors: -
Tests: T-004.1 [system]  (test-cases/nfr.yaml)
```

And A-03 sits in §12 as `open` until the user confirms or corrects it in phase 4.

A judged case's rubric:

```
WRONG  (test-cases/guide.yaml, T-010.2)
    rubric:
      - The guide is clear and easy to follow       ← no quote can prove it
      - Install reads well                          ← a judgement, not a claim
    threshold: 1.0

CORRECT
    rubric:
      - Each step in Install names one action the reader performs
      - No step relies on a tool that Requirements does not list
      - First run shows the command and the output the reader will see
    threshold: 0.67
```

## Red Flags - STOP

- A single `docs/PRD.md` instead of the template folder.
- "It's ready to build from" or "ready for build" before phase 7.
- "Defaults were chosen without stakeholder input" with no `[ASSUMPTION]` markers in the text.
- "If there's no answer by M1, the default stands."
- "The speed numbers are my estimates" while the numbers stand unmarked.
- "Like you asked, it has no test cases." Features with IDs but no ACs or test cases.
- A "Verification" column ("Load test", "Code review") in place of test cases.
- "If you do want this one approved as it stands, say so and I'll change line 4."
- "If you'd still rather drop them, say so." Any offer to undo a rule on request.
- A placeholder value (`go.example.internal`, `TBD-team`) dressed as an assumption.
- Answering your own clarify questions, or moving past phase 3 without the user's answers.
- Setting `Approved` before running lint, or committing it after lint failed.
- Copying the template over an existing draft, or sending a never-approved draft to
  `prd-toolkit:changing-prds`.
- A dry run with no T-ids, or one that samples a unit case.
- A dry-run question dismissed without an exact quote of the PRD line that answers it.
- A rubric item no quote can prove: "is clear", "reads well", "is easy to follow", "is good".
- A custom contract type and a hand-written validator for a document (observed: a `doc` type in
  `contracts/docs.yaml` checked by `contracts/check_keys.py`), or a PRD for a guide written with no
  pack named, when `--list-packs` was never run.

**All of these mean: stop, mark what is unknown, and return to the phase whose gate is open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The user said skip the questions." | Then draft with assumptions and ask once, compactly. The user may confirm every recommendation in one reply; that is phase 4, done fast, not skipped. |
| "Each default is listed in an assumptions section." | Only the ones you noticed. Mark each inferred value where it stands, as `[ASSUMPTION A-nn]`, and index every one. |
| "Every open question has a proposed default, so none blocks starting." | An unconfirmed default is an open assumption. Building on it is building on a guess. |
| "These numbers are my estimates." | An estimate is an assumption. Mark it and ask for the real bound. |
| "QA owns testing." | QA owns test code. The test case (target, input, expected output, errors) is the requirement's definition of done, and it is yours. |
| "Features with IDs are enough for QA to map tests to." | A tester mapping a test to "F3 Slug rules" invents the input and the expected result. That is the PRD's job. |
| "Offering to drop it if they insist is respectful." | It tells the user the rule is optional. A refused rule leaves a Draft that cannot be approved; say that, and nothing more. |
| "A placeholder hostname is fine as an assumption." | An assumption is an inference with a basis. A placeholder is an invention; mark it `NEEDS CLARIFICATION`. |
| "The user approved it." | Approval is the last gate, not a bypass. Lint and the open gates decide whether it can be approved; the user decides whether it will be. |
| "It's only a Draft, so invented values do no harm." | A draft is what builders start from tomorrow. Unmarked values become code. |
| "The folder exists, so this is a change." | Only an approved PRD changes. A draft with no §14 row at 1.0.0 or above resumes here, at its first open gate. |
| "`--sample-tids` found nothing, so there is nothing to dry-run." | A PRD with no black-box case cannot be tested without its code. Exit 1 fails phase 6; write the integration, system or acceptance cases. |
| "The PRD clearly covers that question." | Then quote the line. No quote, no dismissal: a question you cannot answer with the PRD's own words is a gap. |
| "A custom type is quicker than learning the pack." | The pack's type is validated, vendored and locked, and its levels, Harness and rubric conventions come with it. Run `--list-packs`; use the pack that fits. |
| "The rubric item is obviously true of a good guide." | Then it can be quoted. An item the grader cannot prove with a copied quote fails every run, or passes on the grader's mood. |
| "Lint passed, so it is complete." | A Draft lints clean with every marker open, and lint cannot tell an empty contract skeleton from "none". Lint is one gate of seven. |

## Related skills

- **superpowers:brainstorming** decides *whether* to build and *what*. This skill writes the
  authority once that is settled.
- **superpowers:writing-plans** takes the approved PRD and breaks it into tasks (phase 7 hand-off).
- **prd-toolkit:testing-from-prds** is what `prd-tester` follows; its `dispatching.md` is
  phase 6's dispatch.
- **prd-toolkit:changing-prds** for any change once `docs/prd/<slug>/` has been approved
  (a §14 row at 1.0.0 or above). A never-approved draft resumes here.
