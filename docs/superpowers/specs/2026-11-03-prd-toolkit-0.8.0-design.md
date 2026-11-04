# prd-toolkit 0.8.0: target profiles, packs, languages and judged cases — design

> **Date:** 2026-11-03
> **Author:** Ivan Histand & Claude Code
> **Status:** Approved by the owner 2026-11-03
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and the 0.2 to 0.7 addenda
> (`2026-11-02-prd-toolkit-0.7-design.md` last). Governed by `2026-11-03-prd-toolkit-0.8-umbrella.md`.
> Where this spec and any of them disagree, this spec wins for 0.8.0.

> **Revisions.**
> - §9 (spec writing, R-1): the brainstorm had the builder of a `document` area run the pack's
>   `checks` level after writing, in place of tests first. Those checks are the tester's tests,
>   which the builder neither writes nor waits for (0.4), so the builder instead runs the §5
>   standards linters the area's pack proposes, and the `checks` level runs at reconcile like every
>   non-unit level. Ratified by the owner 2026-11-03.
> - §7 (plan ruling): the quote check collapses every run of whitespace to one space on both the quote
>   and the output, and normalizes nothing else (case, punctuation and quotes stay exact), so a grader
>   that re-wraps a line passes and one that paraphrases does not.
> - §7 (plan ruling): the default grader runs `claude -p --output-format json --json-schema <schema>
>   --tools "" --strict-mcp-config --setting-sources "" --disable-slash-commands --no-session-persistence
>   [--model M]` with the prompt on stdin and a fresh temporary directory as cwd. It does not use `--bare`,
>   which requires `ANTHROPIC_API_KEY`. The binary is `$PRD_JUDGE_CLAUDE` when set (tests), else `claude`.
> - §9 (plan ruling): authoring phase 1 lists packs with `prd_lint.py --list-packs`, one line per pack,
>   `<name> <version> (<source>) — <description>`, built-ins first, then installed plugins in
>   `installed_plugins.json` order; no new script.
> - §4 (plan ruling): `${PACK}` is substituted per argument after `shlex.split`, so a pack path with
>   spaces stays one argument.
> - §3 (plan ruling): the `Target:` line is the first line at column 0 matching `^Target:` after the
>   level-1 heading and before the first level-3 heading, with blank lines and HTML comments allowed
>   between. A `Target:` line after the first level-3 heading is a `pack-resolves` finding (`Target: must
>   come before the first requirement`), and one above the level-1 heading is another (`Target: must come
>   after the file's level-1 heading`).
> - §13 P3 (R28): the stub plugin is found through a `PRD_PLUGINS_FILE` list, since discovery does not see `--plugin-dir` plugins.
> - §1, §9, §16 (owner, 2026-11-03): the 0.8 line is renumbered (umbrella Revisions): the machine
>   interface is 0.8.1, best practices 0.8.2, conversion 0.8.3. The changing-prds refusal names 0.8.3.
> - §7 T-004.2 example threshold 0.66, not 0.67 (2 of 3 is 0.666…; final review)

## 1. Scope

Until 0.7 a PRD describes a service in English: OpenAPI operations, SQL tables and events, tested by
a harness that calls code and compares exact output. 0.8.0 lets a PRD describe **other kinds of
output in other human languages**, and lets other plugins **extend the toolkit** without forking it.

0.8.0 delivers:
- **target profiles**: a PRD's default pack and output language in §1, overridden per area by a
  `Target:` line (section 3);
- **packs**: the `pack.yaml` manifest, discovery, vendoring and the version lock (section 4), and
  two built-in packs, `service` (0.7's behaviour) and `document` (Markdown documents) (section 5);
- **PRD languages**: frontmatter `language:`, with EARS and vague-word tables for `en` and `es`
  (section 6);
- **judged cases**: a test case scored by a model grader against its rubric, run by the new
  `prd_judge.py` (section 7);
- **lint severity** `warn`, and four rules (36 → 40), among them the warning `platform-word`
  (section 8);
- the skills, agents and other scripts that use them (sections 9 and 10).

It is **proven by** four scratch projects: a Spanish user guide, a CLI with its guide in one PRD, an
external pack, and an unchanged 0.7 PRD (section 13).

### Decisions

| Decision | Choice |
|---|---|
| Release split | An umbrella note and sub-releases: 0.8.0 targets and languages and the extension surface, 0.8.1 the machine interface, 0.8.2 best practices and finding or writing skills, 0.8.3 conversion |
| What a test is for a non-code target | **Two kinds of check.** Script checks where the output allows them; a **judged** case for the rest, scored by a model grader against a rubric, passing at or above its threshold |
| Human languages | **The grammar stays English; prose follows `language:`.** Labels, IDs and kinds stay English; EARS openers and vague words come from a per-language table (`en`, `es` in 0.8.0) |
| Output language | **A separate setting** in the target profile, defaulting to `language:`; any BCP 47 code |
| What a pack is | **A manifest plus files, shipped in any plugin, vendored into the repo.** Gates run the vendored, locked copy |
| Profiles per PRD | **A default in §1, overridable per area** by a `Target:` line |
| Platform words in requirements | **A soft lint rule**, `platform-word`, at severity `warn`; it never blocks approval |
| How a judged case runs | **`prd_judge.py`, grading through headless `claude -p`**, median of N runs; a pack may override the grader |
| Release vehicle | Branch from `main` after 0.7.1 merges; version 0.8.0 in `plugin.json`, `marketplace.json` and `web/src/data/plugins.js` |

## 2. Components

| Component | New or changed | Purpose |
|---|---|---|
| `scripts/prdlint/packs.py` | new | Parse `Pack:` and `Target:` lines; resolve, validate and lock packs |
| `scripts/prdlint/languages.py` | new | Load a language table; give EARS patterns, vague words and labels |
| `references/languages/en.yaml`, `es.yaml` | new | The two language tables |
| `packs/service/`, `packs/document/` | new | The built-in packs |
| `scripts/prd_judge.py`, `scripts/prdlint/judge.py` | new | Run a judged case |
| `templates/judge/grader.md` | new | The default grader's prompt |
| `scripts/prdlint/findings.py`, `registry.py`, `prd_lint.py` | changed | Severity; four rules |
| `scripts/prdlint/rules/ids.py`, `structure.py` | changed | EARS and vague words from the language table |
| `scripts/prdlint/rules/` (test-refs, contracts-valid) | changed | Pack target kinds; `pack` validator cell |
| `scripts/prdlint/hooks.py` | changed | Vendor packs and `prd_judge.py` |
| `scripts/prdlint/context.py`, `publish.py`, `status.py` | changed | Target lines, pack defaults, labels |
| skills, agents, references, templates | changed | Section 9 and 11 |

## 3. Target profiles

### Frontmatter

`prd.md` frontmatter gains an optional key:

| Key | Format |
|---|---|
| `language` | a BCP 47 primary language subtag, `^[a-z]{2,3}$`; default `en` |

`language:` is the language of the PRD's prose: requirement text and ACs, the glossary, test-case
`steps:`, `rubric:` items and published summaries. Field labels (`Status:`, `Acceptance (EARS):`),
IDs, YAML keys, kinds and section headings stay English.

### §1 lines

Two bullet lines in `## 1. Metadata & stack` are parsed; every other §1 bullet stays prose:

```
- Pack: document 1.0.0 (prd-toolkit)
- Output language: es
```

- `- Pack: <name> <X.Y.Z> (<source>)`. `<name>` matches `^[a-z][a-z0-9-]*$`. `<source>` is
  `prd-toolkit` for a built-in pack, or `<plugin>@<marketplace>` for a pack in an installed plugin.
  At most one `Pack:` line.
- `- Output language: <code>`, a BCP 47 tag (`es`, `pt-BR`). At most one line.
- **No `Pack:` line** means the built-in `service` pack at whatever version is vendored (or built in,
  before the first install). It is not locked, so a 0.7 PRD needs no edit.
- **No `Output language:` line** means the PRD's `language:`.

### The area `Target:` line

An optional line in `features/<area>.md`, at column 0, after the file's level-1 heading and before its
first level-3 heading:

```
Target: pack document 1.0.0 (prd-toolkit), output language en
Target: output language pt-BR
```

Either part may be omitted, not both; the parts are comma-separated, pack first. An omitted part
inherits §1. At most one `Target:` line per file. Blocks in `nfr.md` take §1's profile.

### Resolution

An area's **profile** is its `Target:` line's parts, else §1's, else the defaults above. Its test
cases (`test-cases/<area>.yaml`) belong to that profile. Every script that needs a profile asks
`packs.profile(prd, area)`; none reads the lines itself.

## 4. Packs

### The manifest

A pack is a folder with a `pack.yaml`:

```yaml
pack: document                 # equals the folder name
version: 1.0.0
toolkit: ">=0.8.0,<0.9"        # the toolkit versions it works with (PEP 440 specifier)
description: Markdown documents written for people.
contract-types:
  - {type: outline, files: contracts/outline.yaml, validator: "uv run --script ${PACK}/validate_outline.py"}
target-kinds: {doc: outline}   # a test-case kind and the contract type its names resolve in
levels:
  - {level: checks, command: "uv run pytest tests/checks", environment: local, gate: build}
  - {level: judged, command: "uv run pytest tests/judged", environment: local, gate: build}
harness: {HTTP requests: "Not applicable: no HTTP interface", ...}
standards: [{object: "docs/**/*.md", linter: "...", rules: "...", applies: "..."}]
skills: [{activity: "...", skill: "..."}]
vocabulary: []                 # platform words for platform-word
builder-tests: none            # unit (default) or none
rubrics: rubrics.md            # rubric conventions; optional
clarify: clarify.md            # extra clarify questions; optional
grader: "uv run --script ${PACK}/grade.py"   # optional; replaces the default grader
languages: languages/          # extra PRD-language tables; optional
```

- `${PACK}` expands to the pack's folder wherever the pack is resolved. It is the only expansion.
- Only `pack`, `version` and `toolkit` are required. Every list may be empty.
- `contract-types[].validator` is a command, or `built-in` (only the built-in `service` pack may use
  `built-in`). It follows the custom-type contract: it runs from the PRD root with the matching files
  appended, and exit 0 passes.
- `target-kinds` maps a kind to one of the pack's contract types. `<kind>:<name>` then resolves to a
  top-level key of that type's YAML files, as a custom type's name does in 0.7.
- `levels`, `harness`, `standards` and `skills` are **defaults**: the authoring skill copies them into
  `testing.md` and §5/§6 (as `proposed` rows), and the user decides them. Lint never reads them from
  the manifest; the PRD's own files are the authority.
- `harness` keys are the fifteen Harness slot names; an omitted slot stays a
  `[NEEDS CLARIFICATION]` marker.
- `vocabulary` is a list of words or short phrases, matched case-insensitively as whole words.

### Discovery and the lock

`packs.resolve(name, version, source)` looks in this order and takes the first hit:

1. `.prd-toolkit/packs/<name>/`, when the repository has `.prd-toolkit/`;
2. the toolkit's own `packs/<name>/` (source `prd-toolkit`);
3. `<installPath>/prd-packs/<name>/` of the plugin `<source>`, from
   `~/.claude/plugins/installed_plugins.json`.

When a vendored copy exists, it is the only candidate: its `version` must equal the one the PRD names,
or `pack-resolves` reports `vendored <name> <v1>, the PRD names <v2>; run prd_hooks.py install`. One
pack name has one version across the PRD: two `Target:` lines naming `document 1.0.0` and
`document 1.1.0` is a violation. A pack whose `toolkit:` range excludes the running toolkit is a
violation that names the range.

### §7 rows for pack contract types

A pack contract type appears in §7 like any type, with the Validator cell `pack`:

```
| outline | `contracts/outline.yaml` | pack |
```

`contracts-valid` runs the resolved pack's validator for a `pack` row. A `pack` row whose type no
resolved pack declares is a `contracts-valid` violation. The PRD stays readable without the manifest,
and a repository that vendors its packs validates offline.

### Vendoring

`prd_hooks.py install` copies every pack the PRD names (§1 and `Target:` lines), plus `service`, into
`.prd-toolkit/packs/<name>/`, replacing an earlier copy. It refuses a pack it cannot resolve, naming
where it looked. `prd_hooks.py check` reports a vendored pack that differs from its source.

## 5. Built-in packs

### `service` 1.0.0

0.7's PRD, declared: contract types `openapi`, `schema`, `events`, `errors`, `permissions`, `config`,
`classification`, `dependencies` and `fixtures`, each `validator: built-in`; no `target-kinds` (the
0.7 kinds are built in); no `levels` or `harness` (the template keeps its markers); empty
`vocabulary`; `builder-tests: unit`. The built-in validators stay in code: the manifest lists them,
and lint behaves as in 0.7.

### `document` 1.0.0

Markdown documents written for people: a user guide, a runbook for humans, a policy.

- **Contract type `outline`**, `contracts/outline.yaml`: one top-level key per document.

  ```yaml
  install-guide:
    path: docs/guide/install.md
    audience: first-time users on Windows or macOS
    purpose: install the CLI and run it once
    sections: [Requirements, Install, First run, Common problems]
    terms: [CLI, token]
    length: {min-words: 300, max-words: 1200}
  ```

  `validate_outline.py` checks that every key has `path`, `audience`, `purpose` and a non-empty
  `sections`; that `path` is a relative `.md` path outside the PRD folder; that `terms` and
  `sections` are lists of strings; and that `length`, when present, has integers with
  `min-words` ≤ `max-words`.
- **`target-kinds: {doc: outline}`**: `target: doc:install-guide`.
- **Levels:** `checks` (Gate `build`): tests a script can decide, written by the tester: the
  sections present in order, every `terms` entry used, no banned synonym from §3, relative links
  resolving, word count in range. `judged` (Gate `build`): rubric cases (section 7).
- **Harness defaults:** HTTP requests, Database access, Browser identity, Persistent environments
  and Leaks `Not applicable` with reasons; Tools on the runner names `uv` and `claude` (the default
  grader); Layout `Test roots: `tests/``; Assertions states that a judged test asserts
  `prd_judge.py`'s exit code and nothing else.
- **`builder-tests: none`.** No `unit` level: the builder writes the documents (section 9).
- **Standards:** one proposed row for a Markdown linter on the documents' paths; the user decides it.
- **`rubrics.md`:** how to write rubric items (one observable claim per item; name the section, term
  or reader action it is about; no "is clear", "reads well", "is good"; 3 to 8 items; a threshold of
  1.0 only when every item is a hard requirement).
- **`clarify.md`:** audience, the reader's prior knowledge, reading level, tone, length, format
  conventions, and the output language when it differs from the PRD's.
- **Vocabulary:** empty.

## 6. PRD languages

A **language table** is `references/languages/<code>.yaml` in the toolkit, or `languages/<code>.yaml`
in a pack the PRD names (the toolkit's own wins when both exist):

```yaml
language: es
ears:
  openers: [Cuando, Mientras, Si, Donde]
  ubiquitous: '^(El|La|Los|Las) \S.*? deberán?\b'
vague:
  - rápido
  - rápida
  - seguro
  - segura
  - escalable
  - robusto
  - robusta
  - intuitivo
  - intuitiva
  - fluido
  - fluida
  - amigable
  - fácil de usar
labels: {business: Negocio, technical: Técnico, ...}
```

- `ac-ears` accepts an AC whose text starts with one of `openers` as a whole word, or matches
  `ubiquitous`. The message names the language's openers.
- `vague-word` uses `vague` (case-insensitive, whole words); the "measurable number on the line"
  exemption is unchanged.
- `labels` holds the page chrome `prd_publish.py` prints; the plan lists the keys. A missing key falls
  back to `en`.
- **`en.yaml` reproduces 0.7 exactly**: openers `When`, `While`, `If`, `Where`; ubiquitous
  `^The \S.*? shall\b`; the seven vague words of 0.7. A regression test holds every existing fixture's
  lint output unchanged.

## 7. Judged cases

### The case

A test case is **judged** when its `expect` has `rubric:`. It keeps the seven sufficiency elements;
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

- `rubric:` is a non-empty list of non-empty strings, in the PRD's `language:`.
- `threshold:` is a number in (0, 1]. `runs:` is optional, an integer ≥ 1, default 3.
- `output:` must be absent. `effects:`, `errors:` and `leaks:` keep their 0.7 meaning.
- Any level may hold judged cases; the `document` pack names one `judged`.

### Scoring

The grader marks each rubric item `pass` or `fail`. A `pass` must carry a quote: text copied verbatim
from the output that shows the item holds. **A `pass` whose quote is not a substring of the output
counts as a `fail`**, and the record keeps the quote. A run's score is passed items ÷ items. The case
passes when the median score of its runs is ≥ `threshold`.

### `prd_judge.py`

```
uv run --script .prd-toolkit/prd_judge.py <prd dir> <T-id> <output file> [--runs N] [--model M] [--record-dir D]
```

- Reads the case, its area's profile and the pack's `grader:`. `--runs` overrides `runs:`.
- **Default grader.** Each run is one headless `claude -p --output-format json` in a new empty
  temporary directory, with no tools, no MCP servers, no plugins and no `CLAUDE.md` loaded. The prompt
  is `templates/judge/grader.md` with the rubric and the output text; it holds nothing else from the
  PRD and nothing from the code. The plan pins the exact flags against the installed CLI, and a test
  proves a tool call is refused. The grader answers `{"items": [{"item", "pass", "quote"}]}`.
- **Pack grader.** A pack's `grader:` command replaces one run. It is called as
  `<grader> --rubric <file.json> --output <output file>` and prints the same JSON to stdout.
  `prd_judge.py` still does the quote check, the scoring, the median and the record.
- **Bad answer.** Output that is not that JSON, or names items that are not the rubric's, is retried
  once; a second bad answer ends the case with exit 2.
- **Record.** `<record dir>/<T-id>.json`, default `<first test root>/.prd-judge/`: the T-id, output
  path and its SHA-256, threshold, model, grader (`default` or the command), every run's items and
  score, the median and the verdict. `prd_hooks.py install` adds `.prd-judge/` to `.gitignore`.
- **Exit codes:** 0 pass; 1 fail (prints each failed item and the median); 2 the case could not be
  judged (no such T-id, not a judged case, the output file missing, `claude` not on PATH, two bad
  answers), with a hint. A test asserts exit 0, so exit 2 is a test error, never a pass.

The tester writes judged tests that produce or locate the built output and call `prd_judge.py`; the
test never grades. The citation stays `@prd <T-id>`.

## 8. Lint

### Severity

`Finding` gains `severity`, `error` (default) or `warn`. A warn finding prints as
`<file>:<line>: warn: <rule>: <message>`; an error prints as in 0.7. The exit code counts errors only.
`--list-rules` prints each rule's severity.

`registry.run(prd)` returns errors only, as every in-process caller expects: the deploy pre-flight
(`prdlint/deploy.py`, "prd_lint has findings") and `prd_error.py`. `registry.run(prd, warnings=True)`
returns both, and only `prd_lint.py` asks for it. The skills read the exit code
(`prd-lint-exit=`), so a warning never stops a gate.

### New rules

| Rule | Severity | Reports |
|---|---|---|
| `pack-resolves` | error | a malformed `Pack:`, `Output language:` or `Target:` line, or a repeated one; a pack not found (naming where it looked); a vendored version that differs from the named one; two versions of one pack; a `toolkit:` range that excludes this toolkit; a manifest that fails its schema (naming the key); `built-in` in a pack other than `service` |
| `judged-case` | error | a `rubric:` that is not a non-empty list of non-empty strings; a missing or out-of-range `threshold:`; a bad `runs:`; `output:` beside `rubric:` |
| `language-table` | error | a `language:` with no table (`language 'fr' has no table`) |
| `platform-word` | warn | a word of the area's pack `vocabulary` in an FR or NFR title or AC text: `AC-012.1 names 'explore', a word of pack dashboards: move it to a contract, a Harness slot or the area's Target` |

`test-refs` resolves a pack's target kinds; `contracts-valid` runs `pack` validators (section 4).

## 9. Skills and agents

- **authoring-prds.**
  - Phase 1 lists the packs on this machine (built-ins and installed plugins' `prd-packs/`) and
    proposes the default pack, `language:` and output language beside the pack's §5 and §6 rows, all
    `proposed`; phase 4 decides them like any row.
  - Phase 2 applies the pack after copying the template: drops the contracts the pack does not use
    as `Not applicable` lines, adds the pack's contract types to §7 (`pack` validator) and their
    files, fills Levels and Harness slots from the defaults, and writes prose in `language:`.
  - Phase 3 adds the pack's `clarify.md` questions to the rounds; category 1 asks the target profile.
  - Judged cases follow the pack's `rubrics.md`; the skill gains a WRONG vs CORRECT pair (a rubric of
    "is clear" against one of observable claims) and a Red Flag for a rubric item no quote can prove.
- **adopting-prds.** Proposes a pack from the area's Boundary files and writes the area's `Target:`
  line on the user's confirmation.
- **testing-from-prds and prd-tester.** A judged case's test calls `prd_judge.py`; the tester never
  grades output itself (a Red Flag). Dry runs may sample judged T-ids, which are not `unit`; the dry
  run judges whether the test could be written from the PRD alone, never a score.
- **building-from-prds and prd-builder.** "The code" becomes "the area's output". For an area whose
  pack says `builder-tests: none`, the builder writes the outputs its contracts name (for `document`,
  each `outline` entry's `path`, under the Boundary) and runs the §5 standards linters that apply,
  in place of writing unit tests first (R-1). Its other rules stand: never the PRD folder, never a
  tester's test. The skill states the exception and a Red Flag for using it on an area whose pack
  says `unit`.
- **changing-prds.** Refuses to change the pack of an area that holds a `built`, `verified` or
  `live` requirement: `retargeting an area is a conversion (prd-toolkit 0.8.3)`. An output-language
  change, or a pack change on an area with no built requirement, is a change with a version bump.
- **handling-errors.** A `prd_judge.py` exit 2 is proposed as `environment`.

## 10. Other tools

- **`prd_hooks.py`** vendors packs (section 4) and adds `prd_judge.py` to the vendored scripts.
- **`prd_context.py`.** Both packs carry the area's profile; the implement pack adds the pack's
  Harness defaults it used and, when the area has judged cases, `rubrics.md`.
- **`prd_publish.py`** prints its chrome from the language table's `labels`.
- **`prd_status.py`** shows each area's pack and output language. Judged scores stay in the build
  report.

## 11. Changes to existing text

- `references/prd-format.md`: frontmatter `language`; the §1 lines; the `Target:` line; judged
  cases; the `pack` Validator cell; warn severity.
- `references/contract-types.md`: a `pack` section (the manifest, `${PACK}`, the validator contract)
  and the `outline` type.
- `references/test-levels.md`: judged cases and the `checks` level.
- `references/clarify-categories.md`: category 1 asks the target profile.
- `templates/prd/prd.md`: commented `Pack:` and `Output language:` hints in §1.
- `README.md`: packs, languages, judged cases, `prd_judge.py`, 40 rules, version 0.8.0.

## 12. Testing the toolkit

Pytest, the independent floor:

- `packs.py`: the three discovery places in order; vendored-only once vendored; lock mismatch; two
  versions; `toolkit:` range; every manifest key's schema; `built-in` outside `service`; `${PACK}`.
- Profiles: §1 lines, `Target:` lines, inheritance, malformed and repeated lines.
- Languages: `en` reproduces 0.7 (every fixture's lint output byte-identical); `es` openers,
  ubiquitous form and vague words; a pack-supplied table; an unknown language.
- `judged-case`; `platform-word` as a warn that leaves exit 0; the warn line shape; `registry.run`
  without warnings; the deploy pre-flight and `prd_error.py` unaffected by a warning.
- `prd_judge.py` with a stub pack grader: median, threshold, a fabricated quote failing, a bad answer
  retried once then exit 2, `claude` missing exit 2, the record's fields.
- The default grader's isolation: a run whose rubric asks it to read a file gets no tool.
- `validate_outline.py` fails on each defect it checks (each check proved able to fail).
- `prd_hooks.py install` vendors the named packs and `service`, and `.gitignore` gains `.prd-judge/`.

Evals (`claude plugin eval` before the bump, with/without the skill):

- authoring proposes a pack and writes rubric items that are observable claims;
- authoring a Spanish PRD writes Spanish EARS openers;
- the tester's judged test calls `prd_judge.py` and grades nothing;
- the builder on a `document` area writes the document and runs the linters, with no unit tests;
- changing-prds refuses to retarget a built area.

## 13. Proof

In scratch repositories, recorded in `2026-11-03-prd-toolkit-0.8.0-acceptance.md`:

- **P1, a Spanish user guide.** `/prd-new` for an installation guide of a small CLI, `language: es`,
  pack `document`. Passes when: lint exits 0 with Spanish ACs; the dry run passes with judged T-ids in
  its sample; `/prd-build` writes the guide; the `checks` and `judged` levels pass, with
  `.prd-judge/` records showing every median at or above its threshold.
- **P2, a CLI and its guide in one PRD.** `service` by default, the guide as a `document` area with
  `Target: pack document 1.0.0 (prd-toolkit), output language en`. Passes when both areas build to
  `verified` in one PRD, and `/prd-status` shows each area's profile.
- **P3, an external pack.** A stub plugin with `prd-packs/demo/` (a custom contract type, a target
  kind, a vocabulary of two words), loaded with `--plugin-dir`. Passes when the pack resolves, is
  vendored and locked; a requirement holding a vocabulary word gets a `platform-word` warning with
  lint exit 0; and a vendored version that differs from §1 fails `pack-resolves`.
- **P4, an unchanged 0.7 PRD.** The hello-world `greet` PRD from 0.7. Passes when it lints, builds and
  deploys under 0.8.0 with no edit to its PRD folder.

## 14. Upgrade from 0.7

Nothing is required. Re-run `prd_hooks.py install` to vendor the 0.8.0 scripts and the `service`
pack. A PRD that adds `language:`, a `Pack:` line, an `Output language:` line or a `Target:` line takes
a patch bump with the §14 row `format: target profiles (prd-toolkit 0.8)`.

## 15. Known limits

- **Judged cases are not deterministic.** The median of three runs damps a flip, but a case near its
  threshold can still flip between runs; `rubrics.md` says how to choose a threshold, and the record
  shows every run.
- **Cost and access.** Each judged case costs N model calls per suite run, and the runner needs
  Claude Code signed in (or a pack grader). A CI job that runs a `judged` level needs that too.
- **Network inside a tester's suite.** A suite-mode `prd-tester` that runs a judged level runs
  `claude -p` from its harness command, which needs network access in that sandbox.
- **PRD languages** are `en` and `es` unless a pack adds a table; labels stay English.
- **Documents** are Markdown only; another format needs a pack.
- **Pack discovery reads `~/.claude/plugins/installed_plugins.json`** (override: the `PRD_PLUGINS_FILE`
  environment variable). A plugin loaded only with `claude --plugin-dir` is not in that file, so its
  pack is not found as a source.

## 16. Out of scope for 0.8.0

- The machine interface (0.8.1).
- Best-practice sources, and finding, installing or writing skills and packs (0.8.2).
- Conversion (0.8.3).
- Judged scores in `/prd-status`.
- A pack for Claude skills as a subject (the toolkit's own PRD builds on judged cases).
- Non-Markdown document formats, and PRD languages beyond `en` and `es` in the toolkit itself.
