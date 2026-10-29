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
| 8 Adoption map | `\| Area \| State \|` (omit when `Not applicable: new project`) |
| 11 Requirement index | `\| ID \| Title \| Status \| File \| Since \|` (UJ, FR and NFR only) |
| 12 Assumptions | `\| ID \| Assumption \| Status \|` |
| 14 Changelog | `\| Version \| Date \| Change \| IDs \|` |

Cells keep backticks; a `|` inside backticks does not split a cell. Section 7 built-in rows use
the validator `built-in`; a custom type gives a validator command that exits 0 when its files
are valid. Registry Decision values (decision 5): standards `enforced`, `declined` or
`proposed`; skills `required`, `recommended`, `declined` or `proposed`. `proposed` means the row
is undecided, and an undecided row blocks approval. Adoption states: `not started`,
`extracted`, `confirmed`, `adopted`. Assumption status: `open`, `confirmed`, `corrected`.

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
- A marker `[ASSUMPTION A-nn: text]` may appear anywhere in prose; it must be indexed in section 12.

### Decisions the grammar rests on

1. FR and NFR share one number sequence, so `AC-012.1` has exactly one parent. Both `FR-004`
   and `NFR-004` is an `id-unique` violation.
2. T-ids are numbered per requirement: `T-012.n` belongs to FR-012 or NFR-012, and its test
   case's `ac:` names one `AC-012.x` of that requirement.
3. Assumptions carry IDs: `[ASSUMPTION A-nn: text]`, indexed by `A-nn` in section 12.
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
    leaks: none                           # nothing classified in logs or error bodies
```

- `target` resolves against the contracts: `op:` an `operationId`, `table:` a table in
  `schema.sql`, `event:` and `job:` a `### name` heading in `events.md`.
- A precondition is a fixture name (a path under `contracts/fixtures/` without the extension) or
  `mock:<service>` (a file in `contracts/dependencies/`).
- An acceptance case adds `steps:` (plain-language actions) and `signoff:` (the business owner).
- A mapping key repeated in a file is an `id-unique` violation; the first value is kept.

## testing.md

```
## Levels        | Level | Harness command | Environment |
## Environments  | Environment | Purpose | Access |
## Fixtures      | Fixture | Creates | Load | Teardown |
## Sign-offs     | T-id | Owner | Date | Result |
```

Level-2 headings with those names; the first column of each table is the name that other files
refer to (levels, environments, fixtures).

## operations.md

`## Runbook` holds numbered steps; each ends with `(actor: agent)` or `(actor: human)`. Other
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

## Contract YAML shapes

| File | Shape |
|---|---|
| `errors.yaml` | `CODE: {meaning, when, status: <int>, message, log_level, retryable: <bool>, metric}` |
| `permissions.yaml` | `roles: {<r>: {identity}}`, `operations: {<op>: {allow: [..], deny: [..]}}` (every role in exactly one list), `row_rules: [{role, operation, predicate, attribute}]` |
| `config.yaml` | `settings: {<NAME>: {type, default, environments: {<env>: <value>}, owner}}` |
| `data-classification.yaml` | `tables: {<t>: {retention, deletion, columns: {<col>: public\|internal\|confidential\|pii}}}`, `masking: {logs, errors, fixtures}` |
| `dependencies/<svc>.yaml` | `sends, expects, auth: {secret}, limits, mock, failures: {timeout, 4xx, 5xx, outage}`; failure values are error codes |
| `openapi.yaml` | OpenAPI 3.1; each operation has `operationId`, `x-prd-ids`, `x-error-codes`, `x-preconditions`, `x-effects`; every non-204 response has an example |
| `schema.sql` | parses in the `sql-dialect`; `COMMENT ON` for every table and column |
| `events.md` | per `### <name>`: `Trigger:`, `Payload:`, `Delivery:`, `Retries:`, `Failure:` lines |

Error codes are `UPPER_SNAKE_CASE`. `status` is an HTTP status or an exit code.

## Not parsed

`Flow:`, `Edge cases:` and `Traces:` lines, and all prose, are free text for people and agents.
