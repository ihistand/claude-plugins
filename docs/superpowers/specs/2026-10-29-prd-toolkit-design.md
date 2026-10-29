# prd-toolkit: the living PRD — design

> **Date:** 2026-10-29 (revised the same day: from "PRD then hand off" to "PRD as the living authority")
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Marketplace:** `ihistand` (this repo), new plugin `prd-toolkit`

## 1. Purpose and principles

The PRD is the single authority every agent works from, for the life of a product: to create
objects, change them, deploy them and, above all, test them. It is never "done". An agent that
needs to know how the system behaves reads the PRD, not the code.

Four principles run through every part of the design:

1. **The PRD is the authority.** Behaviour, contracts, environments and standards live in it.
   Code implements the PRD; it never defines behaviour the PRD lacks.
2. **Spec-first, enforced.** Every behaviour change starts as a PRD change (new version, new or
   revised IDs). Code follows. CI fails when the implementation no longer matches the
   contracts.
3. **Black-box testable.** Every contract is complete enough that a testing agent writes the
   test from the PRD alone, without opening the source. A test the PRD cannot support is a PRD
   gap, sent back as a change request, never worked around by reading code.
4. **Error-Driven Development (EDD).** Runtime errors, failed tests, failed deploys, production
   incidents and agent mistakes are first-class feedback. Each one runs Detect → Diagnose →
   Fix → Improve, and the lesson is written back into the PRD so every later agent inherits
   it. Spec-first prevents the errors we foresee; EDD captures the ones we did not and makes
   them foreseen.

### Decisions

| Decision | Choice |
|---|---|
| Audience | Generic, any project, in the personal `ihistand` marketplace. Organization conventions enter through each project's registries (section 3.3), not the toolkit. |
| PRD home | A folder of markdown and contract files committed in the target repo, versioned by git. |
| Scope | The whole lifecycle: author, adopt, change, build, test, deploy, handle errors. Task breakdown stays with superpowers `writing-plans`. |
| Truth flow | Spec-first, enforced by CI drift checks. |
| Agent guidance | One skill per role, plus role subagents. |
| Test agent | Reads the PRD folder, the test directories and the harness config only; gaps go back as change requests. Unit tests stay with the build agent. |
| Existing projects | A dedicated adoption skill reverse-engineers a running project, area by area. First target: the `looker` repo. |

### Prior art and what is borrowed

Surveyed 2026-10-29. None is adopted wholesale; text adapted from MIT sources is credited in
`prd-toolkit/NOTICE`. Taskmaster (Commons Clause) and spec-workflow-mcp (GPL-3.0) text is not
copied.

| Source (license) | Borrowed |
|---|---|
| [GitHub Spec Kit](https://github.com/github/spec-kit) (MIT) | `[NEEDS CLARIFICATION]` markers; the clarify pass scoring categories Clear / Partial / Missing; multiple-choice questions with a recommended answer; the requirements-quality checklist; contracts and data model as separate files; the "constitution" idea, here the standards and skills registries |
| [cc-sdd](https://github.com/gotalab/cc-sdd) (MIT) | EARS acceptance criteria; a mechanical gate before judgement checks; requirement IDs carried into tasks |
| [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) (MIT) | `[ASSUMPTION]` tags with an index for sign-off; a glossary with banned synonyms; "bounds, not adjectives" for NFRs |
| Anthropic `doc-coauthoring` (Apache-2.0) | Reader testing by a fresh, context-free agent, here the test-agent dry run |
| mattpocock `grilling` (MIT) | Ask only what only the user knows; subagents look facts up |

Spec Kit was the only candidate for adoption. It was declined because its spec excludes the
stack and contracts by design, it installs a CLI and a `.specify/` folder per repo with a
branch per feature, it treats the spec as a pre-build artifact rather than a living authority,
and it duplicates superpowers' gating and planning.

## 2. Packaging

The toolkit is authored directly in this repo as `prd-toolkit/`. Unlike `stl-generator`, its
seven skills share scripts, agents, hooks and templates and are useless apart, so the plugin
itself is the source of truth; nothing is synced from `claude-skills`.

```
prd-toolkit/
├── .claude-plugin/plugin.json
├── skills/
│   ├── authoring-prds/SKILL.md        # new project: interview → PRD
│   ├── adopting-prds/SKILL.md         # existing project: code → PRD, area by area
│   ├── changing-prds/SKILL.md         # every behaviour change; the target of every gap
│   ├── building-from-prds/SKILL.md    # implement FRs; unit tests; cite IDs
│   ├── testing-from-prds/SKILL.md     # integration → acceptance tests from the PRD alone
│   ├── deploying-from-prds/SKILL.md   # run the operations.md runbook
│   └── handling-errors/SKILL.md       # EDD loop; triggers only in a repo with a PRD folder
├── agents/
│   ├── prd-builder.md
│   ├── prd-tester.md                  # restricted to PRD, tests and harness config
│   └── prd-deployer.md
├── commands/                          # /prd-new /prd-adopt /prd-change /prd-status /prd-error
├── scripts/                           # prd_lint.py, prd_trace.py, prd_drift.py, prd_status.py,
│                                      # prd_block.py (the managed CLAUDE.md block)
├── templates/                         # PRD folder skeleton, CLAUDE.md block, git hooks, CI jobs
├── references/                        # ears.md, clarify-categories.md, quality-checklist.md,
│                                      # contract-types.md, test-levels.md
├── tests/                             # pytest for the scripts; fixture PRD folders
├── evals/                             # claude plugin eval suite
├── NOTICE
└── README.md
```

Skills reach the scripts through `${CLAUDE_PLUGIN_ROOT}/scripts/`. The scripts use the Python
standard library plus `pyyaml`, `sqlglot` and `openapi-spec-validator`; a missing dependency
prints an install hint and fails, never skips silently. Version is recorded in both
`marketplace.json` and `plugin.json`.

## 3. The PRD folder

```
docs/prd/<project>/
├── prd.md               index: metadata, stack, goals, glossary, architecture, registries,
│                        adoption map, versioning, ID registry, changelog
├── features/<area>.md   FR blocks: numbered flow, EARS criteria, edge cases, T-ids
├── test-cases/<area>.yaml  one entry per T-id: the seven sufficiency elements (section 4.2)
├── contracts/
│   ├── openapi.yaml                 HTTP API
│   ├── schema.sql                   database DDL
│   ├── events.md | asyncapi.yaml    jobs, queues, files, webhooks
│   ├── errors.yaml                  the shared error catalogue
│   ├── permissions.yaml             roles × operations, row-level rules
│   ├── config.yaml                  settings and feature flags per environment
│   ├── data-classification.yaml     sensitivity, retention, masking
│   ├── dependencies/<service>.yaml  third-party services we call
│   ├── fixtures/                    named test datasets
│   └── <custom>                     stack-specific types declared in prd.md
├── nfr.md               NFR-nnn with numbers; observability (log fields, metrics, alerts)
├── testing.md           test levels, harness commands, environments, fixture load and
│                        teardown, acceptance sign-offs
├── operations.md        environments, URLs, deploy and rollback runbook, secrets by name
└── errors.md            the EDD ledger (E-nnn)
```

`<project>` is a lowercase slug; `docs/prd/` is the default root. `features/` says what the
system does, `contracts/` describes its interfaces, and `test-cases/` says how each behaviour
is checked; the tests themselves live in the repo's own test directories and cite their T-ids.
A file whose subject does not exist (no UI, no HTTP API) is omitted, and `prd.md` lists it as
`Not applicable: <reason>` so omission is visible. The exact syntax lint parses is
`references/prd-format.md`.

### 3.1 `prd.md`

```
---
prd: <project>
version: 1.4.0
status: Draft | In review | Approved
owner: <name>
updated: YYYY-MM-DD
sql-dialect: <sqlglot dialect, when schema.sql exists>
---
 1  Metadata & stack      exact languages, frameworks, versions, hosting, repos; a "not used" list
 2  Summary & goals       one-sentence objective, goals with numbers, personas, out of scope
 3  Glossary              one term = one meaning; banned synonyms
 4  Architecture          components and what calls what (mermaid); external integrations
 5  Standards registry    object glob → linter command → where its rules live → code/contract
 6  Skills registry       object glob or activity → skill → required/recommended/declined
 7  Contract types        built-in types in use, plus custom types with format and validator
 8  Adoption map          area → not started / extracted / confirmed / adopted (adopted repos only)
 9  Versioning            what is breaking for API, schema and events; compatibility window;
                          migration rule (expand → migrate → contract)
10  Design & UI           when there is a UI: tokens, component library, component contracts
11  Requirement index     every ID with title, status, feature file, version introduced
12  Assumptions index     every [ASSUMPTION] with status open / confirmed / corrected
13  Open questions        must be empty to approve
14  Changelog             version · date · change · IDs affected
```

### 3.2 IDs, requirement blocks and status

| ID | Meaning |
|---|---|
| `UJ-nn` | user journey |
| `FR-nnn` | functional requirement |
| `NFR-nnn` | non-functional requirement |
| `AC-nnn.n` | acceptance criterion under its FR or NFR |
| `T-nnn.n` | test under its AC, tagged with a level |
| `E-nnn` | error ledger entry |
| `A-nn` | assumption, marked `[ASSUMPTION A-nn: …]` and indexed in `prd.md` §12 |

IDs are never reused. A removed requirement keeps its ID with status `removed`. FRs and NFRs
draw from one number sequence, so `AC-012.1` has exactly one parent. T-ids are numbered per
requirement (`T-012.n`), and each test case names the AC it checks.

```
### FR-012 Reject a duplicate order import
Status: live (since 1.2.0)
Flow: 1. Importer reads a file → 2. computes order_key → 3. looks up orders.order_key
      → 4a. new: inserts  4b. exists: skips and logs
Acceptance (EARS):
- AC-012.1 When an imported row's order_key already exists, the importer shall skip the row
  and write one `duplicate` entry to import_log.
- AC-012.2 If the import file is empty, the importer shall finish with status `empty` and
  insert no rows.
Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)
Edge cases: the same key twice in one file → AC-012.3
Tests: T-012.1 [integration], T-012.2 [integration], T-012.3 [unit]  (test-cases/import.yaml)
Traces: UJ-02; `orders.order_key` UNIQUE; fixture orders/one_existing
```

| Status | Meaning |
|---|---|
| `as-built` | adoption only: extracted from code, not yet confirmed as intended |
| `approved` | specified, not built |
| `built` | code merged |
| `verified` | its T-tests pass in CI |
| `live` | running in production, with the PRD version that introduced it |
| `removed` | retired; the ID is never reused |

### 3.3 Registries

**Standards registry.** Each row binds an object glob to a linter the user chose; the toolkit
enforces that every row runs, not what the rules are.

| Object (glob) | Linter command | Rules live in | Applies to | Decision |
|---|---|---|---|---|
| `definitions/**/*.sqlx` | `dataform-sqlx-lint` ([acuantia/dataform-sqlx-lint](https://github.com/acuantia/dataform-sqlx-lint)) | project lint config | code | enforced |
| `**/*.sql` | `sqlfluff lint` | `.sqlfluff` | code, `schema.sql` | enforced |
| `contracts/openapi.yaml` | `spectral lint` | `.spectral.yaml` | contract | proposed |

(Rows are examples; each project declares its own. Decision is `enforced`, `declined` or
`proposed`; `proposed` is undecided.)

**Skills registry.** Authoring and adoption read the installed plugins and skills
(`claude plugin list`, the skills listing) and propose rows matching the project's objects and
activities. Each row's Decision is `proposed` until the user marks it `required`, `recommended` or
`declined`; declined rows stay so they are not proposed again. For the Looker repo the proposal would include
`acuantia-looker:acuantia-looker` for `**/*.lkml` and dashboards, `acuantia-looker:annotate` for
commits, `acuantia-dataform:schema-change-protocol` for upstream table changes, and
`superpowers:systematic-debugging` and `superpowers:writing-plans` for their activities.

Precedence: **the PRD decides what** (behaviour, contracts, IDs); **a registered skill decides
how** (conventions). A conflict stops the agent and becomes an `E-nnn` entry classified
`standard`; the user decides which side changes. Hard rules from a registered skill that bear
on operations are copied into `operations.md` so the PRD stands alone (Looker deploys become
`actor: human` steps).

## 4. Contracts and the sufficiency rule

### 4.1 The sufficiency rule

For every T-id its test case (section 4.2) gives the test agent seven things, inline or by
reference into `contracts/`; if any is missing the T-id is incomplete and lint fails it:

1. **Target:** the endpoint, table, job, component or page.
2. **Environment and auth:** which environment, which test identity, which secret by name.
3. **Preconditions:** the named fixture that sets up the state (and the dependency mock, if any).
4. **Input:** a concrete example.
5. **Expected output:** schema plus a concrete example.
6. **Expected side effects:** rows written, events emitted, messages sent, and nothing
   classified leaked to logs or error bodies.
7. **Expected errors:** catalogue codes, each with the input that triggers it.

### 4.2 Test cases

Each area has `test-cases/<area>.yaml`, next to `features/<area>.md`, with one entry per T-id.
It is YAML because the seven elements are data: lint checks every field is present and every
reference resolves, so sufficiency is a schema check rather than an agent's judgement. It is
split by area so a tester loads one feature file and one test-case file, and parallel changes
do not conflict. It sits outside `contracts/` because contracts describe the system and test
cases describe checks against it. The folder is `test-cases/`, not `tests/`, so an agent
looking for test code does not mistake a test spec for a test.

```yaml
T-012.3:
  ac: AC-012.3
  level: unit                             # a level defined in testing.md
  target: code:importer.import_file       # <kind>:<name>
  environment: local
  identity: none                          # or a test identity from permissions.yaml
  preconditions: [orders/one_existing]    # contracts/fixtures/, plus any dependency mock
  input:
    file: orders/dup_key_in_file.csv      # a fixture file, or an inline value
  expect:
    output: {status: ok, inserted: 1, skipped: 1}
    effects:
      - import_log: 1 row, kind = duplicate
    errors: []                            # codes from contracts/errors.yaml
    leaks: none                           # nothing classified in logs or error bodies
```

A `target` is `<kind>:<name>`, with kind `op` (an `operationId`), `table`, `event`, `job`,
`component`, `page`, `code` (a unit's function, unit level only) or a custom type from
`prd.md` §7; lint resolves `op`, `table`, `event` and `job` against the contracts. An
error-path case lists its codes under `expect.errors` with the input that triggers them. An
acceptance case adds `steps:`, a list of plain-language actions for the people who sign off,
and `signoff:` naming the business owner. The FR block's `Tests:` line stays as the index; lint
fails when it and the test-case file disagree. `prd_status.py` generates the FR → T matrix from
the test cases, so nobody maintains it by hand.

### 4.3 Required content per contract type

| Contract | Required per item |
|---|---|
| `openapi.yaml` | `operationId`; `x-prd-ids`; auth scheme and required role; fully typed request (required fields, formats, ranges, enums); every response status with schema and at least one example, errors included; `x-error-codes`; `x-preconditions` (fixtures); `x-effects` (tables, events); idempotency, pagination and rate limits where they apply |
| `schema.sql` | every column's type, nullability and default; primary, foreign, unique and check constraints; `COMMENT ON` for every table and column |
| `events.md` / `asyncapi.yaml` | trigger or schedule; payload schema and example; delivery guarantee and ordering; retries and idempotency key; failure behaviour and dead-letter handling |
| `errors.yaml` | per code: meaning; when it occurs; HTTP status or exit code; user-facing message; log level; retryable or not; the metric it increments |
| `permissions.yaml` | role × operation allow/deny; row-level rules as predicates on a named user attribute; a test identity per role. Every deny cell needs a test as well as every allow |
| `config.yaml` | per setting and flag: name, type, default, value per environment, who may change it |
| `data-classification.yaml` | sensitivity per table and column (public, internal, confidential, PII); retention and deletion; masking in logs, errors and fixtures. Fixtures hold synthetic PII only |
| `dependencies/<service>.yaml` | what we send and expect, with examples; auth and secret name; rate limits and quotas; the sandbox or mock tests use (tests never call production third parties); behaviour on timeout, 4xx, 5xx and outage, mapped to error codes |
| `fixtures/` | per dataset: name, the state it creates, load and teardown commands (in `testing.md`) |
| UI component contracts (`prd.md` §10) | name; typed inputs; every state (loading, empty, error, populated); events emitted; test hooks (`data-testid` names); accessibility rules |
| Custom types (`prd.md` §7) | a format, a validator command, and how each item supplies the seven sufficiency elements. Example: a Looker semantic-model type for explores, fields with their SQL, dashboards with tiles and filters, and user attributes, validated by the Looker validator |

Observability lives in `nfr.md`: log fields, metric names and alert thresholds, each tied to
error codes. An error the system cannot surface is an error EDD cannot catch.

## 5. Lifecycle

### 5.1 Authoring a new project (`/prd-new`, `authoring-prds`)

| # | Phase | Gate |
|---|---|---|
| 1 | **Context.** Read the repo, its CLAUDE.md and notes; subagents look up facts the user does not uniquely hold. Propose standards- and skills-registry rows from what is installed and configured. | A short note of what was found |
| 2 | **Draft.** Fill the folder; gaps become `[NEEDS CLARIFICATION: q]`, inferences `[ASSUMPTION: …]`. | Draft on disk |
| 3 | **Clarify rounds.** Score the clarify categories (stack, data model, flows, error and empty states, edge cases, integrations, permissions, configuration, data classification, NFR bounds, terminology, done signals). Up to 5 multiple-choice questions per round, each with a recommended answer, ranked by impact × uncertainty; answers written in immediately. Total uncapped. | Zero markers; every category Clear |
| 4 | **Sign-off.** Assumptions index and registry rows confirmed by the user. | No `open` assumption; every registry row decided |
| 5 | **Mechanical gate.** `prd_lint.py` exits 0; the quality checklist passes. | Lint exit 0 |
| 6 | **Test-agent dry run.** A fresh `prd-tester` with only the PRD folder writes the real tests for five random T-ids. Any question it must ask is a gap: back to phase 3. | Five tests written with zero questions |
| 7 | **Approval.** Status `Approved`, version `1.0.0`, committed; the CLAUDE.md block, hooks and CI jobs installed (section 7). Hand off to `writing-plans`. | Explicit user approval |

### 5.2 Adopting an existing project (`/prd-adopt`, `adopting-prds`)

- **Code first, interview second.** One subagent per area reads the code, git history, docs and,
  where it can query it, the live system. Each extracted requirement starts `as-built` with
  provenance (file, line, commit) and becomes `confirmed` only when the user says the
  behaviour is intended. Apparent bugs go to `errors.md` as `E-nnn`, never into requirements.
- **Incremental.** The adoption map tracks each area. Spec-first enforcement, trace and drift
  apply only to `adopted` areas; the rest of the repo works as before.
- **Registries discovered.** Existing linters (pre-commit, CI jobs) and installed plugins are
  proposed as registry rows.
- **Characterization tests close an area.** `prd-tester` writes T-tests from the extracted PRD
  alone and runs them against the live system. A pass proves the PRD describes reality; a
  failure is a PRD error or a real bug, and the user decides which. An area is `adopted` only
  when its tests pass. Then phases 5 to 7 of authoring apply to it.

### 5.3 Changing (`/prd-change`, `changing-prds`)

1. Restate the change; list the FRs, ACs, NFRs and contract items it touches.
2. Edit the PRD: new IDs for new behaviour, revised ACs, contracts, fixtures, test cases. Affected
   requirements go to `approved`.
3. Bump the version: **major** when existing behaviour changes or is removed, **minor** when
   behaviour is added, **patch** for wording only. Add a changelog row.
4. Lint, and a dry run on the changed T-ids.
5. User approval and commit; any plan built from an earlier version is flagged for update.

### 5.4 Building and testing (in parallel)

After `writing-plans` turns the changed IDs into tasks, `prd-builder` and `prd-tester` work at
the same time from the same PRD. The tester never sees the code, so its tests check the build
independently: they pass only when the code matches the contract.

| Level | Written from | Owner | Reads code? | Runs |
|---|---|---|---|---|
| Unit | the builder's own design | builder | yes | CI, milliseconds |
| Integration | `contracts/` | tester | no | CI, against real database and services in containers, dependency mocks |
| Component / UI | component contracts | tester | no | CI |
| System | FRs and NFRs in a production-like environment | tester | no | staging |
| End-to-end | user journeys (UJ-nn) | tester | no | staging; smoke subset on production |
| Acceptance | EARS criteria and Definition of Done; UAT sign-off by the owner named in the test case | tester writes scripts from `steps:`; people sign | no | staging; sign-off recorded in `testing.md` |

The builder runs every matching standards-registry linter and invokes every required
registered skill before committing; each behaviour commit cites its IDs. Requirements move to
`built` on merge and `verified` when their T-tests pass in CI.

### 5.5 Deploying (`deploying-from-prds`)

`prd-deployer` follows `operations.md` step by step: staging, the system/E2E/acceptance suites
against staging, production, the smoke subset. Every step has an `actor` (`agent` or `human`);
at a `human` step the deployer stops and hands off. A step that fails, or a situation the
runbook does not cover, is not improvised around: it becomes an `E-nnn`. Requirements move to
`live` with the PRD version running.

### 5.6 The gap rule

Any agent that meets something the PRD does not say (a missing error code, an unknown URL, an
unspecified empty state) stops and raises a change request. It does not guess and does not read
around the PRD.

## 6. Error-Driven Development

```
Detect ──► Diagnose ──► Fix ──► Improve
```

| Step | What happens |
|---|---|
| **Detect** | Errors arrive from test failures, deploy failures, production logs and APM, nightly drift and smoke runs (`prd-error` issues), user reports, lint exceptions and agents' own mistakes. `/prd-error` starts the loop on any of them. |
| **Diagnose** | `handling-errors` (with `superpowers:systematic-debugging`) classifies the error against the PRD: **code bug** (PRD right, code wrong), **spec gap** (PRD silent), **invalid requirement** (PRD wrong), **environment** (runbook wrong) or **standard** (a registry rule conflicts with the PRD or the code). |
| **Fix** | A regression test that fails first, at the lowest level that reproduces the error; then the fix. A code bug fixes against the existing AC; the others go through `/prd-change`. |
| **Improve** | The lesson is written into the PRD: a new edge case, error code, NFR, runbook step or revised requirement. An invalid requirement moves its FR back to `approved` under a new version. |

`errors.md` holds one entry per error:

```
### E-031 Duplicate rows when a file is re-uploaded within one second
Detected: 2026-11-04, production log (IMPORT_DUPLICATE not raised), prd-error #48
Classification: spec gap
Diagnosis: AC-012.1 assumed sequential uploads; concurrent uploads race the lookup
Resolution: AC-012.4 + T-012.4 [integration] and its test case added in 1.5.0; unique index already enforced
Recurrence of: -
```

A recurring error gets a new entry pointing to the earlier one, so repeat failures are visible.

## 7. Enforcement in the target repo

1. **Managed CLAUDE.md block** between `<!-- prd-toolkit:start -->` and `<!-- prd-toolkit:end -->`,
   regenerated on every PRD change: the PRD path, the authority and gap rules, which skill each
   role uses, the required registry skills, and which areas are adopted.
2. **Git hooks** (installed by authoring and adoption; opt-out per repo):
   - `commit-msg`: a commit touching code in an adopted area cites live IDs
     (`Refs: FR-012, E-031`) or declares `Refs: none (no behaviour change)`.
   - `pre-commit`: standards-registry linters on staged files matching each glob.
3. **CI jobs**, templates for GitLab CI and GitHub Actions, all required to merge:

   | Job | Runs |
   |---|---|
   | `prd-lint` | `prd_lint.py` |
   | `prd-trace` | `prd_trace.py` |
   | `standards` | every standards-registry row |
   | `test-unit`, `test-integration`, `test-component` | per `testing.md` |
   | `test-system`, `test-e2e` | against staging after the staging deploy |
   | `drift` | `prd_drift.py`: live schema vs `schema.sql` (introspection command from `operations.md`), deployed config vs `config.yaml` |

   A nightly scheduled run repeats `drift` and the smoke suite against production; each failure
   opens a `prd-error` issue, which `handling-errors` starts from.
4. **Role subagents.** `prd-builder`, `prd-tester`, `prd-deployer` load their role skills.
   `prd-tester` is restricted to the PRD folder, test directories and harness config, enforced
   by an agent-scoped PreToolUse hook if the platform supports one, otherwise by instruction
   plus the dry run (open item).
5. **`/prd-status`** prints requirement counts by status, the adoption map, open `E-nnn`
   entries, the PRD version per environment, what is specified but unbuilt, and the FR → T
   matrix generated from `test-cases/`.

### 7.1 `prd_lint.py` rules

Exit 0 when clean; otherwise every violation as `<file>:<line>: <rule>: <message>`, exit 1.

| Rule | Fails when |
|---|---|
| `frontmatter` | a required key is missing or `status`/`version` is malformed |
| `sections` | a `prd.md` section is missing or out of order; an omitted file is not listed as not applicable |
| `id-format` / `id-unique` / `id-removed-reused` | an ID is malformed, defined twice, or a removed ID reappears as active |
| `index-consistent` | the requirement index and the feature files disagree on an ID, title or status |
| `fr-has-ac` / `ac-has-test` | an FR or NFR has no AC; an AC has no T |
| `ac-ears` | an AC does not start with When / While / If / Where / The system shall |
| `test-cases-consistent` | a T-id on an FR block's `Tests:` line has no test-case entry, an entry has no `Tests:` line citing it, or the two disagree on its level |
| `test-level` | a test case has no level, or a level not defined in `testing.md` |
| `sufficiency` | a test case is missing any of the seven elements of section 4.1 (schema check on `test-cases/*.yaml`) |
| `test-refs` | a test case references a fixture, error code, `operationId`, event, table, role or test identity that does not exist in `contracts/`, or an `ac:` that is not its parent AC |
| `nfr-bound` | an NFR has no number with a unit |
| `deny-tested` | a deny cell in `permissions.yaml` has no T-id |
| `error-codes` | an error code is cited but absent from `errors.yaml`, or catalogued but never cited |
| `classified-fixtures` | a fixture or a test case's inline input holds a value matching a PII pattern in a column classified PII |
| `markers-open` | a `[NEEDS CLARIFICATION` remains while status is `In review` or `Approved` |
| `assumption-indexed` | an `[ASSUMPTION` has no index row, or a row is `open` at approval |
| `placeholder` / `vague-word` | TBD, TODO, `???` or `<...>` outside code blocks; fast, secure, scalable, robust, intuitive, seamless, user-friendly in an AC or NFR without a number on the same line |
| `glossary-synonym` | a banned synonym appears outside the glossary |
| `contracts-valid` | `schema.sql` fails to parse in its dialect; `openapi.yaml`, `asyncapi.yaml` or a YAML contract fails validation; a custom type's validator exits non-zero |
| `schema-refs` | a backticked `table.column` in the PRD is absent from `schema.sql` |
| `registries` | a standards row's command is not on PATH; a required skills-registry plugin is not installed; a registry row is undecided at approval |
| `runbook-actors` | an `operations.md` step has no `actor` |
| `open-questions-empty` | open questions remain while status is `Approved` |

### 7.2 `prd_trace.py` rules

| Rule | Fails when |
|---|---|
| `t-implemented` | a T-id of an adopted or new area has no test citing it (`@prd T-012.1` in a comment, docstring or test name) |
| `test-cites-live` | a test cites an ID that does not exist or is `removed` |
| `commit-refs` | a commit in the merge range touches code in an adopted area without `Refs:` |
| `status-current` | an FR is `verified` or `live` while one of its T-tests is missing |

## 8. Testing the toolkit

1. **Scripts (pytest).** One passing fixture PRD folder, plus one fixture per lint, trace and
   drift rule that must fail with that rule's name. Every check is proven able to fail before
   it is trusted.
2. **A baseline per role skill, before it is written** (superpowers `writing-skills`). Pressure
   scenarios run without the skill, failures recorded verbatim, then the red flags and
   rationalization table written against them. Starting scenarios: the tester "in a hurry, just
   peek at the handler"; the builder with "a small change, no need to touch the PRD"; the
   deployer when "the runbook step failed, try something else"; the error handler with "the
   test is flaky, retry it"; the adopter "the code clearly intends this, mark it confirmed".
3. **`claude plugin eval` suite**, run before every version bump: trigger and non-trigger cases
   per skill, and behaviour assertions (the tester never opens source; a gap produces a change
   request; every error produces an `E-nnn`; required registry skills are invoked).

## 9. Milestones and rollout

Each milestone gets its own implementation plan and release.

| Release | Delivers | Proven by |
|---|---|---|
| 0.1 | PRD folder format and templates (test cases included), `prd_lint.py`, standards and skills registries, `authoring-prds`, `changing-prds`, the CLAUDE.md block | Authoring a small sample project from scratch |
| 0.2 | `adopting-prds`, `testing-from-prds`, `prd_trace.py`, the dry run, `prd-tester` | Adopting one Looker area (the sales rep KPI family), its characterization tests passing against looker.acuantia.com through the API |
| 0.3 | `building-from-prds`, `deploying-from-prds`, git hooks, CI templates, `prd_drift.py`, `/prd-status`, `prd-builder`, `prd-deployer` | One Looker change made end to end through the workflow |
| 0.4 | `handling-errors`, `errors.md`, nightly drift and smoke, `prd-error` issues, `/prd-error` | A real Looker error taken through Detect, Diagnose, Fix and Improve |

**Looker rollout.** `looker/` is a team repo; its PRD folder, hooks and CI jobs land through a
merge request. Its contract types (explores, fields, dashboards, user attributes) are declared
in `prd.md` with the Looker validator. Its runbook marks deploy steps `actor: human`, because
Claude never deploys Looker unless Ivan asks in his own words; the registered
`acuantia-looker` skill carries that rule and the runbook repeats it.

## 10. Out of scope

- Task breakdown (superpowers `writing-plans`).
- Claude Docs or Google Docs output; review happens through merge requests on the markdown.
- Organization-specific defaults inside the toolkit; they enter through each project's
  registries.
- Business PRDs for human stakeholders only (pricing, go-to-market).

## 11. Open items

- Whether Claude Code supports PreToolUse hooks scoped to one subagent, which decides how
  `prd-tester`'s read restriction is enforced.
- Whether `claude plugin eval` can drive AskUserQuestion turns non-interactively; if not, the
  behaviour evals fall back to scripted transcripts reviewed by hand.
- How characterization tests reach a live system that has no test environment (Looker has
  one production instance): read-only API queries against production, or a dev-mode
  workspace. Decide during 0.2.
