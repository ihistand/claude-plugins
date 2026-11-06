# PRD format reference

The grammar `prd_lint.py` parses. Written for agents: follow it exactly, and the lint passes.
A PRD is a folder, `docs/prd/<project>/`, where `<project>` is a lowercase slug. The model
(`scripts/prdlint/model.py`) reads only the syntax below; prose outside it is free.

## Folder

```
prd.md                   index (14 sections)
adoption.md              the adoption map                      optional: present for an adopted project
features/<area>.md       UJ and FR blocks                      mandatory, at least one .md
nfr.md                   NFR blocks and ## Observability       mandatory
test-cases/<area>.yaml   one entry per T-id                    mandatory
testing.md  operations.md  errors.md                           mandatory
links.md                                                       optional: present when the PRD links to others
changes/CS-nnn.md                                              optional: change-set records
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

## Tasks

A repo has one PRD, `docs/prd/<project>/`. A sub-project of the repo (a dashboard, a service,
a feature family) is an **area** of that PRD, never a PRD of its own. A task is one unit of
work against the PRD:

| Task | Edits in the PRD | Context pack |
|---|---|---|
| New sub-project | a new area: `features/<area>.md`, `test-cases/<area>.yaml`, a row in `adoption.md` when the project is adopted | `/prd-context` without an area |
| Addition | new FR or UJ blocks in an existing area | `decide`, then `implement` |
| Update | changed blocks and a version bump | `decide`, then `implement` |
| Bug fix | the `E-nnn` entry resolved; its `known-failing` case passes | `decide`, then `implement`, for the IDs the entry touches |

Every task adds a §14 row. The PRD always describes the system as it is now; git history and
§14 record how it got there.

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
| `language` | optional; a BCP 47 primary language subtag, `^[a-z]{2,3}$`; default `en` |

`language` is the language of the PRD's prose: requirement text and ACs, the glossary, test-case
`steps:`, `rubric:` items and published summaries. Field labels (`Status:`, `Acceptance (EARS):`),
IDs, YAML keys, kinds and section headings stay English. Lint reads a language's EARS openers and
vague words from its language table (see Language tables); a `language:` with no table is a
`language-table` violation (`language 'fr' has no table`).

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
| 8 Adoption map | the body is `See adoption.md.` or `Not applicable: new project.`; the table `\| Area \| State \| Boundary \|` lives in `adoption.md`; `sections` checks the body, the header and that each state is one of the four below; `index-consistent` checks that an area past `not started` has its `features/<area>.md` |
| 11 Requirement index | `\| ID \| Title \| Status \| File \| Since \|` (UJ, FR and NFR only) |
| 12 Assumptions | `\| ID \| Assumption \| Status \|` |
| 14 Changelog | `\| Version \| Date \| Change \| IDs \|` |

A §14 row's Change cell ends with the change's dry-run record, after its last `; `
(`dry run T-002.3, 0 open questions, 1 dismissed by quote`, or `no dry run (<why>)`).
`prd_change.py record` writes the row as `<change>; pending`, and `prd_change.py approve` writes
the record in place of `pending`: a change is recorded and not yet approved exactly when the last
§14 row's Change cell ends with `; pending`. The review verdict, `.prd-review.json` in the PRD
folder, is git-ignored (`prd_hooks.py install` adds it to `.gitignore`), never committed, linted
or counted in `prd_change.py digest`; `approve` deletes it.

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

The Boundary is where the commit rule applies. With an `adoption.md`, it is the globs of the `adopted` rows. A project with no `adoption.md` (a new project) has no map, so its Boundary is every path outside the PRD folder and `.prd-toolkit/`. A commit that touches a Boundary path carries a `Refs:` trailer. The grammar: the line starts with `Refs:` (case-sensitive; `refs:` is not a trailer), and its value is either exactly `none (no behaviour change)` or comma-separated IDs (spaces around a comma are fine). Every `Refs:` line in the message counts, so two lines are two lists. An ID is `UJ-nn`, `FR-nnn` or `NFR-nnn` that a block defines and that is not `removed`, or `E-nnn` that `errors.md` records. Any other key (a ticket number, say) goes in its own trailer, not in `Refs:`.

Section 9 states what counts as breaking for the project. A toolkit format migration, such as moving the adoption map, is a patch. The 0.4 migration adds the Gate column to the Levels table in `testing.md`; record it as the §14 row `format: Levels Gate column (prd-toolkit 0.4)`, a patch bump.

## Target profiles

A profile is a pack and an output language. A PRD sets a default in §1, and a `features/<area>.md`
file overrides it with a `Target:` line.

### §1 lines

Two bullet lines in `## 1. Metadata & stack` are read for the profile, `Pack:` and `Output language:`;
`- Profile:` is the authoring skill's assumption marker, and every other §1 bullet stays prose:

```
- Pack: document 1.0.0 (prd-toolkit)
- Output language: es
- Profile: [ASSUMPTION A-03: document, language es, output language es; the user writes Spanish and wants a Spanish guide]
```

- `- Pack: <name> <X.Y.Z> (<source>)`. `<name>` matches `^[a-z][a-z0-9-]*$`. `<source>` is
  `prd-toolkit` for a built-in pack, or `<plugin>@<marketplace>` for a pack in an installed plugin.
  At most one `Pack:` line. Lint reads the line whole, so it holds no marker.
- `- Output language: <code>`, a BCP 47 tag (`es`, `pt-BR`). At most one line. It appears only when it
  differs from `language:`; with no such line the output language is `language:`.
- `- Profile: [ASSUMPTION A-nn: <pack>, language <code>, output language <code>; <basis>]` is the
  authoring skill's proposal of the target profile, one assumption indexed `open` in §12 until the
  sign-off decides it. A decided PRD keeps the `Pack:` and `Output language:` lines and drops the
  marker.
- No `Pack:` line means the built-in `service` pack at whatever version is vendored (or built in,
  before the first install). It is not locked, so a 0.7 PRD needs no edit.

### The area `Target:` line

An optional line at column 0 in `features/<area>.md`, after the file's level-1 heading and before its
first level-3 heading. Blank lines and HTML comments may stand between:

```
Target: pack document 1.0.0 (prd-toolkit), output language en
Target: output language pt-BR
```

Either part may be omitted, not both; the parts are comma-separated, pack first. An omitted part
inherits §1. At most one `Target:` line per file. Blocks in `nfr.md` take §1's profile. The area's
test cases (`test-cases/<area>.yaml`) belong to its profile.

### `pack-resolves` messages

Lint rule `pack-resolves` reports each of these on the line that holds the fault:

| Message | When |
|---|---|
| `Pack: must be <name> <X.Y.Z> (<source>)` | a malformed `Pack:` line |
| `Output language: must be a BCP 47 tag such as es or pt-BR` | a malformed `Output language:` line |
| `Target: must be pack <name> <X.Y.Z> (<source>)[, output language <code>] or output language <code>` | a malformed `Target:` line |
| `Target: must come before the first requirement` | a `Target:` line after the file's first level-3 heading |
| `Target: must come after the file's level-1 heading` | a `Target:` line above the level-1 heading |
| `<Label>: repeated (first at line N); one <Label>: line per PRD` | a second `Pack:` or `Output language:` line |
| `Target: repeated (first at line N); one Target: line per area` | a second `Target:` line in one file |
| `pack <name> named at <v1> and <v2>; one version per PRD` | one pack named at two versions |
| `pack <name> <X.Y.Z> (<source>) not found; looked in: <places>` | no folder resolves |
| `vendored <name> <v1>, the PRD names <v2>; run prd_hooks.py install` | the vendored copy's version differs from the named one |
| `vendored <name> has no pack.yaml; run prd_hooks.py install` | a vendored pack folder holds no manifest (it never falls through to another copy) |
| `pack <name> needs toolkit <range>; this is <version>` | the pack's `toolkit:` range excludes this toolkit |
| `pack <name>: pack.yaml: <why>` | a manifest that fails its schema, naming the key |
| `pack <name>: only the service pack may use validator built-in` | `built-in` in another pack |

### The `pack` Validator cell

A contract type a pack declares appears in §7 with the Validator cell `pack`:

```
| outline | `contracts/outline.yaml` | pack |
```

`contracts-valid` runs the resolved pack's validator for a `pack` row, from the PRD root with the
matching files appended. A `pack` row whose type no resolved pack declares is a `contracts-valid`
violation. Each target kind a pack declares (`doc:<name>` for `document`) resolves in `test-refs`
like a custom type's name.

### Upgrading a 0.7 PRD

Nothing is required. A PRD that adds `language:`, a `Pack:` line, an `Output language:` line or a
`Target:` line takes a patch bump with the §14 row `format: target profiles (prd-toolkit 0.8)`.

## Language tables

A language table is `references/languages/<code>.yaml` in the toolkit, or `languages/<code>.yaml` in a
pack the PRD names (the toolkit's own wins when both exist). `en.yaml` reproduces 0.7 exactly. Keys:

| Key | Holds |
|---|---|
| `language` | the code; equals the file name |
| `openers` (in `ears`) | the words an EARS AC may start with, as whole words (`When`, `While`, `If`, `Where`) |
| `ubiquitous` (in `ears`) | a regex for the ubiquitous form (`^The \S.*? shall\b`) |
| `ubiquitous_hint` (in `ears`) | how the form reads in a message (`'The <thing> shall'`) |
| `modal` (in `ears`) | a regex for the modal verb an AC must hold (`\bshall\b`) |
| `modal_word` (in `ears`) | the modal verb as a word, for messages (`shall`) |
| `vague` | a list of words and phrases `vague-word` rejects, case-insensitive whole words |
| `labels` | the page chrome `prd_publish.py` prints; a missing key falls back to `en` |

`ac-ears` accepts an AC that starts with one of `openers` or matches `ubiquitous`, and its message
names the language's openers. `vague-word` keeps the "measurable number on the line" exemption.
The `labels` keys are the ones in `references/languages/en.yaml`.

## Lint output

One line per finding: `<file>:<line>: <rule>: <message>`. A rule of severity `warn` prints
`<file>:<line>: warn: <rule>: <message>` (`platform-word` is the one warn rule). The exit code counts
errors only, so a warning never fails a gate. `prd_lint.py --list-rules` prints each rule's severity.

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
(`index-consistent`). `Source:` means where the code that implements the block is: provenance for
an `as-built` block, a pointer for a built one (`/prd-build` writes it at close). It is optional
outside `as-built`.

- `Status:` is `approved`, `built`, `verified`, `live`, `as-built` or `removed`, optionally
  followed by `(since X.Y.Z)`. `live` always carries `since`. Status moves go
  `approved → built → verified`. A status move is progress, not behaviour: no version bump, no
  §14 row, no re-approval. The block and its §11 row move together, written at a build's close.
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
   in the changelog. The next free UJ number is the highest UJ number in the PRD, removed ones
   included, plus 1, written with two digits (`UJ-03`). A removed requirement keeps its block and
   index row with status `removed`; a removed AC keeps its line, marked as above. Every removed
   ID, T-ids included, is listed in the IDs cell of the changelog row for the version that
   removes it. `prd_change.py ids next <prd dir> <FR|NFR|UJ|AC-<nnn>|T-<nnn>>` prints the next
   free ID by these rules.

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
  `schema.sql`, `event:` and `job:` a `### name` heading in `events.md`. In a PRD with `links.md`, a
  target of an upstream's item is `<kind>:<prd>/<name>` (`cli:greet/greet`, `table:transform/orders_daily`);
  it resolves in `contracts/upstream/<prd>/`. See `links.md`.
- A precondition is a fixture name (a path under `contracts/fixtures/` without the extension) or
  `mock:<service>` (a file in `contracts/dependencies/`).
- An acceptance case adds `steps:` (plain-language actions) and `signoff:` (the business owner).
  Its rules (observable results only, fresh data on persistent environments, a step per
  expectation) are in [test-levels.md](test-levels.md).
- `known-failing: E-nnn` (optional) marks a case that fails on purpose until the code is fixed. The
  entry must be in `errors.md` and still open; a resolved or unknown entry is a `test-refs`
  violation. The test for such a case is a strict expected failure in the harness's own way (pytest
  `xfail(strict=True)`, jest `test.failing`) and its citation reads `@prd <T-id> known-failing <E-nnn>`.
  A `/prd-build --fixes E-nnn` removes the line before its step 7 trace: once its T-id passes, or, at a
  deploy-gate level, once the tester's un-mark is committed; no other build edits one.
- `symptom:` (optional, beside `known-failing:` only) is what the run shows while the bug is open, in plain
  language, one observable symptom. The test then treats only that symptom as the expected failure. A
  `known-failing:` case with no `symptom:` is a `test-refs` warning (any failure would pass as the known one);
  a `symptom:` without `known-failing:` is a `test-refs` error. A blank `symptom:` counts as absent.
- A custom contract type whose files are YAML mappings makes `<type>:<name>` resolvable: `<name>`
  must be a top-level key of one of the type's `.yaml` files under `contracts/` (`test-refs`). A
  type whose files are not YAML mappings there is not checked. A custom type whose glob matches no file is a `contracts-valid`
  violation.
- `refs:` (optional) lists what the case depends on outside its contracts: each entry is a path
  in the PRD folder, optionally followed by `#` and the exact text of a heading in that file
  (`prd.md#Component: MyLinksPage`, `testing.md#Harness`). The dry-run tester reads every entry.
  An entry whose file or heading does not exist is a `test-refs` violation.
- A mapping key repeated in a file is an `id-unique` violation; the first value is kept.

## Judged cases

A case is judged when its `expect` has `rubric:`. It keeps the seven sufficiency elements;
`rubric:` and `threshold:` take the place of `output:`:

```yaml
T-004.2:
  ac: AC-004.2
  level: judged
  target: doc:install-guide
  environment: local
  identity: none
  preconditions: []
  input: {reader: has never used a terminal}
  expect:
    rubric:
      - Each step in Install names one action the reader performs
      - No step relies on a tool that Requirements does not list
      - First run shows the command and the output the reader will see
    threshold: 0.66
    runs: 3
    errors: []
    leaks: none
```

- `rubric:` is a non-empty list of non-empty strings, in the PRD's `language:`. Each item is one claim
  a grader can prove with a quote from the output.
- `threshold:` is a number in (0, 1]. `runs:` is optional, an integer of at least 1, default 3.
- `output:` must be absent. `effects:`, `errors:` and `leaks:` keep their usual meaning.
- Lint rule `judged-case` reports a missing or malformed `rubric:`, `threshold:` or `runs:`, and an
  `output:` beside `rubric:`.
- The test calls `prd_judge.py <prd dir> <T-id> <output file>` and asserts its exit code. It never
  grades. The citation stays `@prd <T-id>`.

## links.md

Optional, beside `prd.md`. With no `links.md` a PRD has no links and nothing here applies to it.

```
# Links

## Upstreams

| Upstream | Location | Version | Commit | Needs |
|---|---|---|---|---|
| greet | `../greet` | 1.1.0 | 4f1c9a2 | live in staging |

## Consumers

| Consumer | Location |
|---|---|
| dashboards | `git@example.com:org/bi.git#docs/prd/dashboards` |
```

- **Upstream / Consumer:** the other PRD's `prd:` slug, unique within its table.
- **Location:** a backticked path to the other repository's root, relative to this one, or a git URL
  followed by `#<PRD folder>`. A path location's PRD is `docs/prd/<slug>`.
- **Version / Commit:** the lock: the upstream's `version:` and the upstream commit (7 to 40 hex
  digits) the snapshot came from. Only `prd_links.py sync` writes them; both are empty before the first sync.
- **Needs:** `verified` or `live in <env>`, `<env>` an environment of the upstream's `operations.md`.
  Empty means `live in` the Environment of the first `deploy`-gate level in `testing.md` Levels order;
  with none, `verified`.

Adding `links.md` is a patch bump, recorded as the §14 row `format: links.md (prd-toolkit 0.7)`.

**The prefix.** A reference to an upstream item puts the upstream's slug and a `/` before the name:
a test case `target:` and a `Traces:` token are `<kind>:<prd>/<name>`; prose (`schema-refs`) is
`` `<prd>/<table>.<column>` ``. A target or token `<kind>:<a>/<b>` is prefixed when `<a>` matches
`[a-z][a-z0-9-]*` and `<kind>` is not `code`; a prose span is prefixed only when `<a>` names an
Upstreams row, so `src/importer.py` stays prose. The kinds that cross are `op`, `table`, `event`,
`job` and a custom type whose files are YAML mappings; `code:` never crosses, and a prefixed
`component:` or `page:` is refused (`kind '<kind>' does not cross repositories`). A PRD without
`links.md` reads every target as before.

**The snapshot.** `contracts/upstream/<prd>/` holds only the cited items, written by
`prd_links.py sync` in files named as in the upstream's `contracts/`: SQL statements and events.md
sections copied verbatim; OpenAPI operations and custom YAML keys re-emitted from the parsed YAML
(comments and flow style are not kept). They are a table's `CREATE TABLE` and `COMMENT ON` lines (`schema.sql`), an operation with every `components` entry it `$ref`s and the
`info` block (`openapi.yaml`), an event or job's `### <name>` section (`events.md`), and the cited
top-level keys of a custom YAML type. `--` comment lines directly above a cited `CREATE TABLE` travel
with it; `/* */` comments directly above it are not copied. An item of `contracts/asyncapi.yaml` is not
citable across repositories. Never edit a snapshot by hand.

Each snapshot file starts with one comment line in its own syntax (`-- ` for `.sql`, `# ` for `.yaml`,
`<!-- … -->` for `.md`):

```
Snapshot of <prd> <version> at <commit>, written by prd_links.py sync. Do not edit.
```

A custom type's file adds ` Type: <kind>.` after it, and `schema.sql` adds ` Dialect: <dialect>.`,
because the downstream PRD declares neither.

**The change-set record.** `changes/CS-nnn.md` (three digits, per PRD, never reused) is written only by
`prd_links.py changeset`: `# CS-nnn <title>`; `Started: YYYY-MM-DD in <prd>`; `Status:` `proposed`,
`approved`, `running`, `stopped: <prd>: <reason>`, `done` or `abandoned`; one `Approval: YYYY-MM-DD,
"<reply>"` line per approval (an amendment adds ` (amendment)`); a table
`| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |`; `## Log` with
`- YYYY-MM-DD <text>` lines; and, once closed, `## Merge order`. State and Target are `proposed`,
`approved`, `built`, `verified` or `live in <env>`, in that order; a stop is on Status and in Log, never
in State. The branch in every member is `cs-<nnn>-<slug>`.

**The trailer.** A commit made for a change set carries `Change-set: <prd>/CS-nnn` beside `Refs:`,
matched by `^Change-set:[ \t]*([a-z][a-z0-9-]*/CS-\d{3})[ \t]*$` (multiline). When `<prd>` is this
repository's PRD, the record must exist; elsewhere only the form is checked.

## testing.md

```
## Levels        | Level | Harness command | Environment | Gate |
## Harness       - **<Slot>.** <convention>   (bullets, not a table)
## Environments  | Environment | Purpose | Access | Base URL | Database | Logs |
## Leak checks   | Sink | Read from | Scanned for |
## Fixtures      | Fixture | Creates | Load | Teardown |
## Sign-offs     | T-id | Owner | Date | Result |
```

Level-2 headings with those names; the first column of each table is the name that other files
refer to (levels, environments, fixtures).

- Levels: `Gate` is `build` (the level runs before deploy, on the code alone) or `deploy` (it needs the
  deployed system); `test-level` reports a missing column once and any other value per row. It
  also reports a build-gate level whose Harness command's first path argument equals, or is a
  parent of, a deploy-gate level's (`pytest tests` and `pytest tests/system`): a build would run
  deploy-gate tests with no environment. The path is the first argument that holds a `/` or names a
  test root, skipping program names, options, the value of a runner option that takes one
  (`--basetemp build/tmp`) and files with an extension, so a shared runner script
  (`bash tools/gate.sh <level>`) is not one. A build command that excludes the deploy-gate path
  (`--ignore`, `--ignore-glob`, `--deselect`) or selects its tests by an expression (`-m`, `-k`) is
  not reported: `pytest tests --ignore tests/system` and `pytest -m "not system" tests` pass.
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
  HARNESS CHOICES. A helper a pack ships is stated in the pack's `harness` (the Assertions or Fixtures slot) with its parameters, their types and the shape of its result. A shipped helper whose shapes are not stated is a dry-run question, not a HARNESS CHOICE. A slot that does not apply reads `Not applicable: <reason>`. The Layout
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
- The Leaks slot of the Harness also says how a failure's traceback is kept free of test values. Say how a failure report avoids printing the values a test passes: for pytest, the harness commands carry `--tb=short`, or each helper that takes a value sets `__tracebackhide__ = True`; another harness names its own equivalent.
- Leak checks define `expect.leaks: none`: one row per sink a test scans (application logs, error
  bodies, and any other output such as metrics labels or events), where the test reads it, and
  which classified columns from `contracts/data-classification.yaml` must not appear in it.

## operations.md

Three tables and a runbook. Other headings (Secrets by name) are free. The `runbook-steps`,
`runbook-env`, `production-gate`, `runbook-tests` and `drift-rows` rules check what follows.

```
## Environments

| Environment | URL | Production |
|---|---|---|
| staging | file:.deploy/staging | no |
| production | file:.deploy/production | yes |

## Runbook

1. Deploy to staging (actor: agent) (env: staging)
   Run: `uv run scripts/deploy.py staging`
   Check: `.deploy/staging/bin/hello World` prints `Hi, World!`
   Rollback: `uv run scripts/deploy.py staging --previous`
2. System tests on staging (actor: agent) (env: staging)
   Run: tests system
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `uv run scripts/deploy.py production`
   Check: `.deploy/production/bin/hello World` prints `Hello, World!`
5. Smoke on production (actor: agent) (env: production)
   Run: tests smoke
```

- Environments: `Production` is `yes` or `no`, and at least one row is `yes`. Every environment is
  also a row of `testing.md` Environments (`runbook-env`).
- A step line is `N. <title> (actor: agent|human) (env: <environment>)`, numbered from 1 without
  gaps. Labelled lines follow, indented, in any order, one per label; lint reports a repeated label (`runbook-steps`), and the first is used. An agent step takes `Run:` (required),
  `Check:` (required unless `Run:` is a `tests` step) and `Rollback:` (optional); a human step
  takes `Do:` and `Check:` (both required, prose) and never `Run:` or `Rollback:`. Other indented
  lines are prose and ignored (`runbook-steps`).
- An agent `Run:` is one backticked command, or `tests <level>[, <level>]`. An agent `Check:` is
  one backticked command, optionally followed by `` prints `<text>` ``. `Rollback:` is one
  backticked command. A `tests` step has no `Check:`: the suite is its check. Each level it names
  exists in `testing.md` Levels with Gate `deploy` and a Harness command (`runbook-tests`).
  A value that is still a `[NEEDS CLARIFICATION: …]` marker is left to the markers rule.
- The first step on a production environment is `(actor: human)` or directly preceded by a human
  step (`production-gate`). There is no opt-out.
- A `smoke` level in `testing.md` is an ordinary level with Gate `deploy`: its cases are T-ids run
  by its Harness command, and a runbook step runs them with `Run: tests smoke`.

Two optional tables follow the runbook.

```
## Deployed

| Environment | PRD version | Commit | Date | Run |
|---|---|---|---|---|
| production | 1.0.0 | 3f2c1a9 | 2026-11-02 | 20261102T103000Z-production |

## Drift

| Environment | Check | Introspection command |
|---|---|---|
| production | version | `.deploy/production/bin/hello --prd-version` |
| production | config | `.deploy/production/bin/hello --settings-json` |
```

`## Deployed` is the PRD's record of what each environment runs: the caller writes one row per
environment at a deploy run's close, replacing that environment's earlier row. A missing table
means nothing is deployed yet. A deploy the owner did by hand, outside `/prd-deploy`, is recorded with
`prd_deploy.py record <prd dir> --env <env> --commit <sha> --reply "<owner's words>"`, which writes a
run log marked `by: hand` and that environment's row, runs nothing and moves no status; the caller never writes that row directly. `## Drift` lists the checks run against a live environment; `Check`
is `version` or `config` (`drift-rows`; a `schema` row is reported as arriving in prd-toolkit 0.6,
and a `config` row needs `contracts/config.yaml`). Without the table there is no drift check. A
Deployed or Drift row's environment must be in both Environments tables (`runbook-env`).

**Migration from 0.4.** A 0.4 runbook (`(actor: …)` only) fails `runbook-steps` until each step
carries `(env: …)` and its labelled lines, and fails `runbook-env` until Environments has the
`Production` column. The migration is a patch bump with the §14 row
`format: runbook steps (prd-toolkit 0.5)`.

## errors.md

One entry per error, newest last:

```
### E-001 <title>
Detected: <date>, <source>
Classification: code bug | spec gap | invalid requirement | environment | standard | unclassified
Confirmed: <YYYY-MM-DD>, "<the user's reply, verbatim>"
Touches: <requirement IDs or ->
Evidence: <a command and its output, a failing test line or a log excerpt>
  <continuation lines, indented two spaces>
Diagnosis: <why>
Resolution: <T-id> [<level>], PRD <X.Y.Z>, fixed in <commit> | not a defect: <why>
Recurrence of: <E-nnn or ->
```

`Detected:` is `<YYYY-MM-DD>, <source>`. `Confirmed:` (optional) is `<YYYY-MM-DD>, "<reply>"`,
written only by `prd_error.py confirm`. `Evidence:` (optional) holds at most 20 lines, with
continuation lines indented two spaces, and never a secret value or data classified `confidential`
or `pii`. `Classification:` is one of `code bug`, `spec gap`, `invalid requirement`,
`environment`, `standard`, `unclassified`. The `error-entries` rule reports a malformed `Detected:`
or `Confirmed:`, an unknown class, an `Evidence:` over 20 lines, a `Recurrence of:` that names no
entry, and a `Confirmed:` on an `unclassified` entry.

Entries run from E-001 upward with no gap, newest last; lint reports a gap or an entry out of order. `Touches: -` means none.

The **state** of an entry is derived from its lines and never written:

| State | Lines |
|---|---|
| `unclassified` | `Classification: unclassified`, or no `Classification:` |
| `proposed` | a class other than `unclassified`, no `Confirmed:` |
| `confirmed` | `Confirmed:`, no resolution |
| `resolved` | a resolution (the open/resolved rule below) |

A resolution has one of three forms: `<T-id> [<level>], PRD <X.Y.Z>, fixed in <7-40 hex>` (code
bug, spec gap, invalid requirement, standard); `<T-id or ->, PRD <X.Y.Z>, run <run id>`
(environment); `not a defect: <why>` (any class). Lint does not check a resolution's form, since
entries resolved before 0.6 hold free text; `prd_error.py check` checks the form of each resolution
added inside its range.

`Touches:` is optional. It lists the requirement IDs (`UJ-nn`, `FR-nnn`, `NFR-nnn`) the error
concerns, comma-separated, and `-` means none. `index-consistent` reports a `Touches:` ID that no
block defines. The context pack's Known defects part reads it.

`unclassified` is allowed only on an open entry: a deploy failure is recorded as `unclassified`
until it is diagnosed, and `index-consistent` reports `unclassified` on a resolved entry.

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
