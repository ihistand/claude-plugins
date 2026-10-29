# prd-toolkit: agent-first PRD skill — design

> **Date:** 2026-10-29
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Marketplace:** `ihistand` (this repo), new plugin `prd-toolkit` 0.1.0

## 1. Purpose

A Product Requirements Document becomes the primary design artifact for a project: written
and approved before any code, and specific enough that an AI coding agent builds from it
without guessing. The PRD is the agent's prompt baseline, its context payload and the source of
its test list.

The skill exists because general brainstorming (superpowers) produces a free-form design doc
with no fixed sections, no requirement IDs, no acceptance-criteria format, no gap scan and no
tracing from requirements to tests. Those are what an agent-first PRD needs.

### Decisions already made

| Decision | Choice |
|---|---|
| Audience | Generic, any project; lives in the personal `ihistand` marketplace. No Acuantia conventions in the skill. |
| PRD home | Markdown committed in the target project's repo, versioned by git. |
| Scope | Authoring and change requests only. An approved PRD hands off to superpowers `writing-plans`; the skill does not break work into tasks or verify the finished build. |
| Approach | A thin skill writing a PRD folder (`prd.md` plus machine-checkable `schema.sql` / `openapi.yaml`), borrowing proven ideas instead of adopting a framework. |

### Prior art and what is borrowed

Surveyed 2026-10-29. None is adopted wholesale; text adapted from MIT sources is credited in
`NOTICE`. Taskmaster (Commons Clause) and spec-workflow-mcp (GPL-3.0) text is not copied.

| Source (license) | Borrowed |
|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) (MIT) | `[NEEDS CLARIFICATION]` markers; clarify pass scoring categories Clear / Partial / Missing; multiple-choice questions with a recommended answer; requirements-quality checklist ("unit tests for English"); data model and contracts as separate files |
| [cc-sdd](https://github.com/gotalab/cc-sdd) (MIT) | EARS acceptance criteria; a mechanical review gate before judgement checks |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) (MIT) | `[ASSUMPTION]` tags and an assumptions index for sign-off; a glossary with banned synonyms; the "NFR theater" check (bounds, not adjectives) |
| Anthropic `doc-coauthoring` (Apache-2.0) | Reader testing: a fresh, context-free agent works from the document alone |
| mattpocock `grilling` (MIT) | Ask only what only the user knows; look facts up with subagents instead |

Spec Kit was the only candidate for adoption. It was declined because its spec deliberately
excludes the stack and schema (spreading one PRD over four or more files), it installs a CLI
and a `.specify/` folder per repo with a branch per feature, and it duplicates superpowers'
gating and planning.

## 2. Packaging and components

```
claude-skills/writing-agent-prds/          # canonical source (ihistand/claude-skills)
├── SKILL.md                               # phases, gates, red flags, rationalization table
├── templates/prd.md                       # the section skeleton (section 4)
├── references/ears.md                     # EARS patterns, good and bad examples
├── references/clarify-categories.md       # gap-scan categories and what "Clear" means for each
├── references/quality-checklist.md        # requirements-quality checks
├── scripts/prd_lint.py                    # the mechanical gate (section 5)
├── tests/                                 # pytest for prd_lint.py, fixture PRD folders
└── NOTICE                                 # attribution for adapted MIT text

claude-plugins/prd-toolkit/                # this repo
├── .claude-plugin/plugin.json
├── skills/writing-agent-prds/             # synced copy; never hand-edited
├── commands/prd-new.md                    # /prd-new
├── commands/prd-change.md                 # /prd-change
├── evals/                                 # claude plugin eval suite
└── README.md
```

- The skill is canonical in `~/projects-ivan/claude-skills/writing-agent-prds/` and mirrored
  into the plugin by `scripts/sync-skills.sh` (a new `SKILLS` entry), as `stl-generator` is.
- `prd_lint.py` runs with the Python standard library plus `sqlglot` (DDL parsing) and
  `openapi-spec-validator`; both are needed only when the PRD folder holds those files. The
  script prints an install hint and fails, never silently skips, when a needed one is absent.
- Version recorded in both `marketplace.json` and `prd-toolkit/.claude-plugin/plugin.json`.

### Output in the target project

```
docs/prd/<project>/
├── prd.md          # always
├── schema.sql      # when the project has a database: DDL is the source of truth
└── openapi.yaml    # when the project exposes an HTTP API
```

`<project>` is a lowercase slug. `docs/prd/` is the default; the command accepts another root.

## 3. Authoring flow (`/prd-new`)

Seven phases. Each has a gate, and no phase starts before the previous gate passes.

| # | Phase | What happens | Gate |
|---|---|---|---|
| 1 | Context | Read the target repo's CLAUDE.md, README, existing schemas and code, and any notes the user names. Facts the user does not uniquely hold (library versions, API limits, pricing) go to subagents. No questions to the user yet. | A short note to the user of what was found and where |
| 2 | Draft | Fill the whole template from the context. Every gap becomes `[NEEDS CLARIFICATION: <question>]`; every inference becomes `[ASSUMPTION: <claim>]`. Requirements get IDs, EARS criteria and named tests. | Draft written to disk so the user can read along |
| 3 | Clarify rounds | Score each clarify category Clear / Partial / Missing. Ask up to 5 multiple-choice questions per round with AskUserQuestion, each with a recommended option, ranked by impact × uncertainty. Write each answer into the PRD immediately. Repeat until no `NEEDS CLARIFICATION` remains and every category is Clear. Total questions are uncapped. | Zero markers; every category Clear |
| 4 | Assumption sign-off | Walk the assumptions index; the user confirms or corrects each. Corrections change the PRD. | Every assumption `confirmed` or `corrected` |
| 5 | Mechanical gate | `prd_lint.py docs/prd/<project>` exits 0, then the quality checklist is applied. | Lint exit 0; checklist items all pass |
| 6 | Reader test | A fresh subagent receives only the PRD folder (no conversation, no repo). It lists every question it would need answered before building, and writes the test list for three randomly chosen FRs. Any question it raises is a gap: back to phase 3. Its test lists must match the PRD's named tests. | Zero questions; test lists consistent |
| 7 | Approval | The user reviews. Status becomes `Approved`, version `1.0.0`, and the folder is committed in the target repo. The skill then tells the user to run superpowers `writing-plans` on `prd.md`; plan tasks cite FR IDs. | Explicit user approval |

### Clarify categories

Stack and versions · data model · user flows · error and empty states · edge cases ·
integrations · security and auth · non-functional bounds · terminology (glossary) · done
signals. `references/clarify-categories.md` defines what Clear means for each, for example
"non-functional bounds: every NFR has a number, a unit and a measurement method".

### Change requests (`/prd-change`)

For a requirement that moves after approval:

1. Read the current PRD; restate the requested change.
2. Impact list: the FRs, ACs, NFRs, schema objects and endpoints the change touches.
3. New behaviour gets new IDs. A removed requirement keeps its ID with status `Removed`; IDs
   are never reused.
4. Version bump: **major** when existing behaviour changes or is removed, **minor** when
   behaviour is added, **patch** for wording only.
5. Changelog row: version · date · change · IDs affected.
6. Rerun lint (whole folder) and the reader test (changed sections).
7. User approval, commit, and a note that any plan built from the earlier version must be
   updated before work continues.

### Red flags and rationalizations

SKILL.md carries a "Red Flags — STOP" list and a rationalization table, in this repo's
superpowers style. The baseline run (section 6) decides their final wording; the starting set:

| Rationalization | Reality |
|---|---|
| "The user is in a hurry; skip the reader test" | The reader test is the only check that the PRD stands alone. It costs one subagent. |
| "The stack is obvious" | Unstated stacks are where agents hallucinate. Name versions. |
| "'Fast' is clear enough" | An NFR without a number cannot be tested. Ask for the bound. |
| "I'll ask the user which version of X is current" | Look it up. Ask only what only the user knows. |
| "They implied the answer" | A marker is resolved by the user's answer or a confirmed assumption, never by inference. |
| "It's a small change; no version bump" | Every change after approval bumps the version and gets a changelog row. |

## 4. PRD format

### `prd.md` skeleton

```
---
prd: <project>
version: 0.1.0
status: Draft | In review | Approved
owner: <name>
updated: YYYY-MM-DD
supersedes: <previous version or ->
sql-dialect: <sqlglot dialect, only when schema.sql exists>
---
 1  Metadata & stack     exact languages, frameworks, versions, hosting, repos; a "not used" list
 2  Summary & goals      one-sentence objective, goals with numbers, personas, Out of scope
 3  Glossary             one term = one meaning; synonyms banned elsewhere in the document
 4  Architecture         components and what calls what (mermaid), external integrations
 5  Data model           prose plus a pointer to schema.sql, which is the source of truth
 6  API contracts        prose plus a pointer to openapi.yaml; non-HTTP contracts (jobs, events, files) inline
 7  State                where state lives; lifecycle or state machine per entity
 8  Features             grouped by area; one FR block each
 9  Non-functional       NFR-nnn, each with a number, a unit and how it is measured
10  Design & UI          only when there is a UI: tokens, component library, layout rules
11  Acceptance & tests   Definition of Done, test strategy, coverage targets, FR → test matrix
12  Assumptions index    every [ASSUMPTION] with status open / confirmed / corrected
13  Open questions       must be empty to approve
14  Changelog            version · date · change · IDs affected
```

Sections that do not apply (a CLI has no UI) say `Not applicable: <reason>` rather than being
deleted, so the reader test can tell omission from oversight.

### Requirement block

```
### FR-012 Reject a duplicate order import
Flow: 1. Importer reads a file → 2. computes order_key → 3. looks up orders.order_key
      → 4a. new: inserts  4b. exists: skips and logs
Acceptance (EARS):
- AC-012.1 When an imported row's order_key already exists, the importer shall skip the row
  and write one `duplicate` entry to import_log.
- AC-012.2 If the import file is empty, the importer shall finish with status `empty` and
  insert no rows.
Edge cases: the same key twice in one file → AC-012.3
Tests: T-012.1 (unit, test_import.py::test_duplicate_skipped), T-012.2, T-012.3
Traces: UJ-02, schema orders.order_key UNIQUE
```

ID scheme: `UJ-nn` user journeys, `FR-nnn` functional, `NFR-nnn` non-functional,
`AC-nnn.n` acceptance criteria under their FR or NFR, `T-nnn.n` tests under their AC.

## 5. `prd_lint.py` rules

Exit 0 when clean; exit 1 listing every violation as `prd.md:<line>: <rule>: <message>`.

| Rule | Fails when |
|---|---|
| `frontmatter` | A required key is missing, or `status`/`version` is malformed |
| `sections` | One of the 14 sections is missing or out of order |
| `id-format` | An ID does not match its pattern |
| `id-unique` | An ID is defined twice |
| `id-removed-reused` | An ID marked `Removed` in the changelog is defined again as active |
| `fr-has-ac` | An FR or NFR has no AC |
| `ac-ears` | An AC does not start with When / While / If / Where / The system shall |
| `ac-has-test` | An AC has no T |
| `nfr-bound` | An NFR has no number with a unit |
| `markers-open` | A `[NEEDS CLARIFICATION` remains (only when `status` is `In review` or `Approved`) |
| `assumption-indexed` | An inline `[ASSUMPTION` has no row in section 12, or a row is still `open` at approval |
| `placeholder` | TBD, TODO, FIXME, `???` or `<...>` placeholders outside code blocks |
| `vague-word` | fast, quick, secure, scalable, user-friendly, robust, intuitive, seamless in an AC or NFR without a number in the same line |
| `glossary-synonym` | A term listed as a banned synonym appears outside the glossary |
| `schema-parses` | `schema.sql` exists and sqlglot cannot parse it, using the dialect named by `sql-dialect:` in the frontmatter (default: sqlglot's generic dialect) |
| `schema-refs` | A backticked `table.column` in `prd.md` names a table or column absent from `schema.sql` |
| `openapi-valid` | `openapi.yaml` exists and fails validation |
| `open-questions-empty` | Section 13 has entries while `status` is `Approved` |

## 6. Testing the skill

1. **Lint tests (pytest).** One fixture folder that passes every rule, plus one fixture per
   rule that must fail with that rule's name. Each check is proven able to fail before it is
   trusted.
2. **Baseline before SKILL.md** (superpowers `writing-skills`). Without the skill, run three
   pressure scenarios and record the failures verbatim:
   - "Write a PRD for a small inventory app; I'm in a hurry."
   - "Here's a vague idea [paragraph]; make it buildable."
   - "Add a feature to this approved PRD [fixture]."
   The red flags and rationalization table are written against what actually went wrong. A
   rerun with the skill must fix each recorded failure.
3. **`claude plugin eval` suite**, run before every version bump:
   - Triggers on: "write a PRD", "spec this out before we build", "requirements doc for an
     agent to build from".
   - Does not trigger on: "write an implementation plan", "draft a business memo", "fix this
     bug".
   - Behaviour: every question carries a recommended option; the produced folder passes lint;
     after a change request no ID is reused and the version is bumped.
4. **Dogfood.** The first real run of `/prd-new` is the Heimdall pilot (the Looker
   replacement), in whichever repo holds the pilot code. Findings feed 0.1.1.

## 7. Out of scope

- Task breakdown from the PRD (superpowers `writing-plans` does it).
- Verifying the finished build against the PRD.
- Claude Docs or Google Docs output; review happens through merge requests on the markdown.
- Organization-specific defaults (Acuantia stack, Jira linkage). A separate overlay plugin in
  the Acuantia marketplace can add them later.
- Business PRDs for human stakeholders only (pricing, go-to-market).

## 8. Open items

- Two clones of `ihistand/claude-skills` exist (`~/projects/claude-skills` and
  `~/projects-ivan/claude-skills`, both at `d46657f`). `sync-skills.sh` reads the
  `projects-ivan` one; the skill is authored there.
- Whether `claude plugin eval` can drive AskUserQuestion turns non-interactively decides how
  much of the behaviour suite is automated; check during implementation and fall back to
  scripted transcripts reviewed by hand.
