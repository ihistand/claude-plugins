# PRD format reference

The grammar `prd_lint.py` parses. Written for agents: follow it exactly, and the lint passes.
A PRD is a folder, `docs/prd/<project>/`, where `<project>` is a lowercase slug. The model
(`scripts/prdlint/model.py`) reads only the syntax below; prose outside it is free.

## Folder

```
prd.md                   index (14 sections)
features/<area>.md       UJ and FR blocks                      mandatory, at least one .md
nfr.md                   NFR blocks and ## Observability       mandatory
test-cases/<area>.yaml   one entry per T-id                    mandatory
testing.md  operations.md  errors.md                           mandatory
contracts/errors.yaml                                          mandatory
contracts/openapi.yaml, schema.sql, events.md | asyncapi.yaml,
  permissions.yaml, config.yaml, data-classification.yaml,
  dependencies/<service>.yaml, fixtures/, <custom>             optional
```

Optional files, each of which may be marked not applicable: `contracts/openapi.yaml`,
`contracts/schema.sql`, `contracts/events.md` or `contracts/asyncapi.yaml` (either one fills the
slot), `contracts/permissions.yaml`, `contracts/config.yaml`, `contracts/data-classification.yaml`,
`contracts/dependencies/`, `contracts/fixtures/`.

A file that does not exist is listed in section 1 of `prd.md`, one line each:

```
- Not applicable: `contracts/asyncapi.yaml` — no message queues
```

(The separator is an em dash, `—`.) Mandatory files are never listed as not applicable.

## prd.md frontmatter

```
---
prd: orders
version: 1.0.0
status: Approved
owner: Sample Owner
updated: 2026-10-29
sql-dialect: postgres
---
```

| Key | Format |
|---|---|
| `prd` | `^[a-z][a-z0-9-]*$`, equal to the folder name |
| `version` | `X.Y.Z`, digits only |
| `status` | `Draft`, `In review` or `Approved` |
| `owner` | free text, required |
| `updated` | `YYYY-MM-DD` |
| `sql-dialect` | a sqlglot dialect; required when `contracts/schema.sql` exists |

## prd.md sections

Level-2 headings, exactly these, in this order:

```
## 1. Metadata & stack      ## 8. Adoption map
## 2. Summary & goals       ## 9. Versioning
## 3. Glossary              ## 10. Design & UI
## 4. Architecture          ## 11. Requirement index
## 5. Standards registry    ## 12. Assumptions index
## 6. Skills registry       ## 13. Open questions
## 7. Contract types        ## 14. Changelog
```

A section whose subject does not apply has the body `Not applicable: <reason>`. Section 13 is
the single line `None.` when empty; open questions are bullet lines and block approval.

Tables (the header row is parsed; column names and order are fixed):

| Section | Header |
|---|---|
| 3 Glossary | `\| Term \| Meaning \| Banned synonyms \|` |
| 5 Standards | `\| Object (glob) \| Linter command \| Rules live in \| Applies to \| Decision \|` |
| 6 Skills | `\| Object or activity \| Skill \| Decision \|` |
| 7 Contract types | `\| Type \| Files (glob) \| Validator \|` |
| 8 Adoption map | `\| Area \| State \| Boundary \|` (omit when `Not applicable: new project`); `sections` checks the header and that each state is one of the four below; `index-consistent` checks that an area past `not started` has its `features/<area>.md` |
| 11 Requirement index | `\| ID \| Title \| Status \| File \| Since \|` (UJ, FR and NFR only) |
| 12 Assumptions | `\| ID \| Assumption \| Status \|` |
| 14 Changelog | `\| Version \| Date \| Change \| IDs \|` |

Cells keep backticks; a `|` inside backticks does not split a cell. Section 7 built-in rows use
the validator `built-in`; a custom type gives a validator command that exits 0 when its files
are valid. Registry Decision values (decision 5): standards `enforced`, `declined` or
`proposed`; skills `required`, `recommended`, `declined` or `proposed`. `proposed` means the row
is undecided, and an undecided row blocks approval. A `required` skill must be installed: a
`plugin:skill` row needs the plugin in `~/.claude/plugins/installed_plugins.json` and, when that
file records an `installPath`, `<installPath>/skills/<skill>/SKILL.md`; a bare skill needs
`.claude/skills/<skill>/SKILL.md` in the home directory or the repo. A skill built into Claude
Code (`code-review`, `security-review`, `simplify`, `init`) can only be `recommended`. Adoption states: `not started`,
`extracted`, `confirmed`, `adopted`. The Boundary cell lists the area's files as backticked
globs (`features/import.md`, `src/importer/**`), comma-separated; the loader reads each
backtick span as one glob. Assumption status: `open`, `confirmed`, `corrected`, or `awaiting <who>`
(a named person, for example `awaiting Sam Rivera`; a bare `awaiting` is a violation).

## Requirement blocks

Heading `### <ID> <title>` at level 3, in `features/*.md` (read in sorted file order) or `nfr.md`.
`<ID>` is `UJ-nn`, `FR-nnn` or `NFR-nnn`. A block runs to the next heading of level 3 or
shallower. Field lines start at column 0; a continuation line is indented two or more spaces.

```
### FR-012 Reject a duplicate order import
Status: live (since 1.2.0)
Flow: 1. Importer reads a file → 2. computes order_key → 3. looks up orders.order_key
      → 4a. new: inserts  4b. exists: skips and logs
Acceptance (EARS):
- AC-012.1 When an imported row's order_key already exists, the importer shall skip the
  row and log IMPORT_DUPLICATE.
- AC-012.2 If the import file is empty, the importer shall finish with status `empty`.
Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)
Edge cases: the same key twice in one file → AC-012.1
Tests: T-012.1 [integration], T-012.2 [unit]  (test-cases/import.yaml)
Traces: UJ-02; `orders.order_key` UNIQUE; fixture orders/one_existing
```

An optional `Source: <path>:<line> @<sha>` field line (continuation lines allowed) records the
code a block was read from when an existing system is adopted. An `as-built` block must have one
(`index-consistent`).

- `Status:` is `approved`, `built`, `verified`, `live`, `as-built` or `removed`, optionally
  followed by `(since X.Y.Z)`. `live` always carries `since`.
- `Acceptance (EARS):` lists `- AC-nnn.n <text>` items. `nnn` equals the parent's number. The
  text starts with When, While, If, Where or "The <thing> shall"; extra lines are indented.
- A removed AC keeps its line, with `(removed in X.Y.Z)` between the ID and its original
  text: `- AC-001.3 (removed in 2.0.0) If the import file is empty, …`. Its test cases are
  deleted, and its T-ids leave the `Tests:` line. `ac-ears`, `ac-has-test` and `vague-word` skip
  it; a test case whose `ac:` cites it, or an `x-prd-ids` or `Traces:` entry that does, is an
  `id-removed-reused` violation.
- `Errors:` is a comma-separated list of catalogue codes, then an optional parenthetical.
  Use `Errors: -` for none.
- `Tests:` lists `T-nnn.n [level]` items, then `(test-cases/<area>.yaml)`. Blocks in `nfr.md`
  pair with `test-cases/nfr.yaml`. A UJ block has no ACs and no tests.
- A marker `[ASSUMPTION A-nn: text]` may appear in any text file of the PRD folder (markdown
  prose, or YAML, SQL and JSON values and comments); it must be indexed in section 12. A
  `[NEEDS CLARIFICATION: …]` marker is found in the same files, and none may remain once the
  status is `In review` or `Approved`. Fixture data under `contracts/fixtures/`, other file
  types (custom-type files such as `.lkml`), and hidden or editor-backup files are not scanned.
- Literal angle-bracket text in prose (for example `<the data_state>`) goes in a code span: the
  `placeholder` rule flags bare `<name>` text as an unfilled template slot, and lint ignores code spans.

### Decisions the grammar rests on

1. FR and NFR share one number sequence, so `AC-012.1` has exactly one parent. Both `FR-004`
   and `NFR-004` is an `id-unique` violation.
2. T-ids are numbered per requirement: `T-012.n` belongs to FR-012 or NFR-012, and its test
   case's `ac:` names one `AC-012.x` of that requirement.
3. Assumptions carry IDs: `[ASSUMPTION A-nn: text]`, indexed by `A-nn` in section 12. An `open`
   assumption blocks approval. `awaiting <who>` is for intent only the named person can
   confirm: the user has named that person, and the row is allowed while the PRD is Approved.
4. A test case `target` is `<kind>:<name>`, kind one of `op`, `table`, `event`, `job`,
   `component`, `page`, `code` or a custom type named in section 7.
5. Registry rows carry a `Decision` column (values above).
6. IDs are never reused. The next free FR or NFR number is the highest FR or NFR number in
   the PRD, removed ones included, plus 1. The next free AC number in a block is the highest
   AC number in that block, removed ones included, plus 1. The next free T number for a
   requirement is the highest it has ever used plus 1, counting the T-ids that `Tests:` lines,
   `test-cases/` and section 14 changelog rows name, since a deleted test case survives only
   in the changelog. A removed requirement keeps its block and index row with status
   `removed`; a removed AC keeps its line, marked as above. Every removed ID, T-ids included,
   is listed in the IDs cell of the changelog row for the version that removes it.

## Test cases

`test-cases/<area>.yaml` is a mapping from T-id to a case. Every case has all seven
sufficiency elements:

```yaml
T-012.2:
  ac: AC-012.2
  level: unit                             # a level defined in testing.md
  target: code:importer.import_file       # <kind>:<name>
  environment: local                      # an environment from testing.md
  identity: none                          # or a test identity from permissions.yaml
  preconditions: [orders/one_existing]    # fixture names, or mock:<service>
  input:
    file: orders/dup_key_in_file.csv      # relative to contracts/fixtures/; or inline values
  expect:
    output: {status: ok, inserted: 1, skipped: 1}
    effects:
      - "log: IMPORT_DUPLICATE once"
    errors: []                            # codes from contracts/errors.yaml
    leaks: none                           # nothing classified in the testing.md Leak checks sinks
```

- `target` resolves against the contracts: `op:` an `operationId`, `table:` a table in
  `schema.sql`, `event:` and `job:` a `### name` heading in `events.md`.
- A precondition is a fixture name (a path under `contracts/fixtures/` without the extension) or
  `mock:<service>` (a file in `contracts/dependencies/`).
- An acceptance case adds `steps:` (plain-language actions) and `signoff:` (the business owner).
  Its rules (observable results only, fresh data on persistent environments, a step per
  expectation) are in [test-levels.md](test-levels.md).
- `known-failing: E-nnn` (optional) marks a case that fails on purpose until the code is fixed. The
  entry must be in `errors.md` and still open; a resolved or unknown entry is a `test-refs`
  violation.
- A custom contract type whose files are YAML mappings makes `<type>:<name>` resolvable: `<name>`
  must be a top-level key of one of the type's `.yaml` files under `contracts/` (`test-refs`). A
  type whose files are not YAML mappings there is not checked. A custom type whose glob matches no file is a `contracts-valid`
  violation.
- `refs:` (optional) lists what the case depends on outside its contracts: each entry is a path
  in the PRD folder, optionally followed by `#` and the exact text of a heading in that file
  (`prd.md#Component: MyLinksPage`, `testing.md#Harness`). The dry-run tester reads every entry.
  An entry whose file or heading does not exist is a `test-refs` violation.
- A mapping key repeated in a file is an `id-unique` violation; the first value is kept.

## testing.md

```
## Levels        | Level | Harness command | Environment |
## Harness       - **<Slot>.** <convention>   (bullets, not a table)
## Environments  | Environment | Purpose | Access | Base URL | Database | Logs |
## Leak checks   | Sink | Read from | Scanned for |
## Fixtures      | Fixture | Creates | Load | Teardown |
## Sign-offs     | T-id | Owner | Date | Result |
```

Level-2 headings with those names; the first column of each table is the name that other files
refer to (levels, environments, fixtures).

- Levels: each `Harness command` is **one simple command** in backticks, such as
  `` `uv run pytest tests` ``; the `prd-tester` guard runs nothing else. It blocks a command whose
  first word is `cd`, `env`, `sh`, `bash`, `zsh`, `eval` or `exec`; one containing `$`, `{` or
  `~`; one with an env-var prefix (`TEST_ENV=ci pytest`); and chains with `&&`, `||`, `;` or `|`. Put a setting such as
  `TEST_ENV` in the Environment switch slot, set by the runner, not in the command.
- Environments: `Base URL` is where a test reaches the system (`none` for a job with no
  endpoint), `Database` names the database or connection a test reads and writes (never a
  password), and `Logs` says where the environment's logs are read (a file, a command or a log
  query). A test's credentials come from its role's `secret` in `contracts/permissions.yaml`.
- Harness holds one bullet per convention a test relies on, in this order: Lifecycle,
  Environment switch, Database access, Tools on the runner, Clean state, Persistent environments,
  Layout, HTTP requests, Fixtures, Browser identity, Assertions, Waits, Effects, Leaks, Acceptance.
  Each states the convention, not a helper's code; a helper's internals are the dry-run tester's
  HARNESS CHOICES. A slot that does not apply reads `Not applicable: <reason>`. The Layout
  bullet also ends with `Test roots: ` and the test directories, each in backticks (for example
  `tests/`); the loader reads those as the roots the tester may write under. Anything inside a
  `[NEEDS CLARIFICATION: …]` marker is ignored, so an unfilled template has no roots. The loader
  reads only the comma-separated backticked list right after `Test roots:` and stops at the first
  other text, so ``Test roots: `tests/` (not `src/`)`` gives `tests/` alone. `Test roots:` and its
  whole list sit on the Layout bullet's first line: a wrapped continuation line is not read. The
  `sections` rule checks that testing.md has a `## Harness` section, that every slot is present in
  the order above, that the Layout bullet has `Test roots:`, and that the list is not empty (a
  `Test roots:` that lists no backticked directory and holds no marker is a finding, because the
  guard would then block every write); `[NEEDS CLARIFICATION]` markers block `In review` until
  every slot is answered.
- Leak checks define `expect.leaks: none`: one row per sink a test scans (application logs, error
  bodies, and any other output such as metrics labels or events), where the test reads it, and
  which classified columns from `contracts/data-classification.yaml` must not appear in it.

## operations.md

`## Runbook` holds numbered steps, each with `(actor: agent)` or `(actor: human)` on the step's
first line. Other
headings (Environments, Secrets by name) are free.

## errors.md

One entry per error, newest last:

```
### E-001 <title>
Detected: <date>, <source>
Classification: code bug | spec gap | invalid requirement | environment | standard
Diagnosis: <why>
Resolution: <the AC, T-id and version that fixed it>
Recurrence of: <E-nnn or ->
```

An entry is **open** when it has no `Resolution:` line, or the value after `Resolution:` is
empty, `-`, or starts with `open` (case-insensitive); otherwise it is resolved. Headings inside
code fences are not entries.

## Contract YAML shapes

| File | Shape |
|---|---|
| `errors.yaml` | `CODE: {meaning, when, status: <int>, message, log_level, retryable: <bool>, metric}` |
| `permissions.yaml` | `roles: {<r>: {identity, secret}}` (`secret` is the name of the secret that holds the identity's credential, never a value), `operations: {<op>: {allow: [..], deny: [..]}}` (every role in exactly one list), `row_rules: [{role, operation, predicate, attribute}]` |
| `config.yaml` | `settings: {<NAME>: {type, default, environments: {<env>: <value>}, owner}}` |
| `data-classification.yaml` | `tables: {<t>: {retention, deletion, columns: {<col>: public\|internal\|confidential\|pii}}}`, `masking: {logs, errors, fixtures}` |
| `dependencies/<svc>.yaml` | `sends, expects, auth: {secret}, limits, mock, failures: {timeout, 4xx, 5xx, outage}`; failure values are error codes |
| `openapi.yaml` | OpenAPI 3.1; each operation has `operationId`, `x-prd-ids`, `x-error-codes`, `x-preconditions`, `x-effects`; every non-204 response has an example |
| `schema.sql` | parses in the `sql-dialect`; `COMMENT ON` for every table and column |
| `events.md` | per `### <name>`: `Trigger:`, `Payload:`, `Delivery:`, `Retries:`, `Failure:` lines |

Error codes are `UPPER_SNAKE_CASE`. `status` is an HTTP status or an exit code.

## Not parsed

`Flow:` and `Edge cases:` lines, and all prose, are free text for people and agents. `Traces:`
is free text too, except that an AC or requirement ID on it is checked by `id-removed-reused`.
