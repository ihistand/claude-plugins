# prd-toolkit 0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `prd-toolkit` 0.1.0: the PRD folder format and its template, `prd_lint.py` with all 27 rules, the standards and skills registries, the `authoring-prds` and `changing-prds` skills with `/prd-new` and `/prd-change`, and the managed CLAUDE.md block.

**Architecture:** A new plugin directory `prd-toolkit/` in this marketplace. A Python package `scripts/prdlint/` first loads a PRD folder into one `Prd` model, then runs independent rule functions over it, each registered by name. Two thin entry scripts, `prd_lint.py` and `prd_block.py`, use that package. Skills call the scripts through `uv run --script` and treat lint exit 0 as a gate.

**Tech Stack:** Python 3.11+ with `pyyaml`, `sqlglot` and `openapi-spec-validator`; pytest through `uv`; markdown skills and commands; `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-10-29-prd-toolkit-design.md` (sections 3, 4, 5.1, 5.3, 7.1, 7 item 1 and 9 are the ones this plan implements).

## Global Constraints

- Plugin skills live at `skills/<name>/SKILL.md`; a flat `skills/<name>.md` is silently ignored.
- The plugin is authored in place in `prd-toolkit/` and nothing is synced from `claude-skills` (spec section 2).
- The version is `0.1.0` in both `.claude-plugin/marketplace.json` and `prd-toolkit/.claude-plugin/plugin.json`.
- Scripts use only the standard library plus `pyyaml`, `sqlglot` and `openapi-spec-validator`. A missing dependency prints an install hint and exits 2. It never skips silently.
- Lint output is one line per violation, `<file>:<line>: <rule>: <message>`. Exit 0 when clean, 1 on violations, 2 on usage, dependency or internal error.
- Every lint rule has a pytest case that makes it fire (spec section 8.1).
- Skills follow the superpowers style (non-negotiable language, Red Flags, a Rationalizations table) and get a baseline run *before* they are written (spec section 8.2, `superpowers:writing-skills`).
- Run every command from the worktree root, `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit`. Never use bare `git stash`.
- Commit as Ivan Histand <ihistand@rotoplas.com>, ending each message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not push.
- Text adapted from MIT or Apache sources is credited in `prd-toolkit/NOTICE`. Nothing is copied from Taskmaster or spec-workflow-mcp.

## Decisions this plan adds to the spec

The spec leaves these open, and lint cannot parse a PRD without them. Task 1 writes them into `references/prd-format.md`, and the spec is amended to match them in the same commit as this plan.

1. **FR and NFR share one number sequence**, so `AC-012.1` has exactly one parent. Having both `FR-004` and `NFR-004` is an `id-unique` violation.
2. **T-ids are numbered per requirement.** `T-012.n` belongs to FR-012 or NFR-012, and its test case's `ac:` names one `AC-012.x`.
3. **Assumptions carry IDs.** The marker is `[ASSUMPTION A-nn: text]`, and the §12 table is keyed by `A-nn`.
4. **A test case `target` is `<kind>:<name>`**, where the kind is one of `op`, `table`, `event`, `job`, `component`, `page`, `code`, or a custom type named in prd.md §7. The spec's `importer.import_file` becomes `code:importer.import_file`.
5. **Registry rows carry a `Decision` column**:
   - Standards rows: `enforced`, `declined` or `proposed`.
   - Skills rows: `required`, `recommended`, `declined` or `proposed`.
   - `proposed` means the row is undecided.
6. **A fifth script, `prd_block.py`**, regenerates the CLAUDE.md block, so the block is deterministic rather than written by an agent.
7. **In 0.1 the authoring dry run uses a fresh general-purpose subagent**, told it may read only the PRD folder. `prd-tester`, with enforced restriction, replaces it in 0.2.
8. **Authoring phase 7 installs only the CLAUDE.md block** in 0.1. Git hooks and CI arrive in 0.3, and the skill does not mention them until then.

## Review Focus

These are the inputs most likely to bite a real user that no rule's own failing case exercises. Each has a pinned test in the task named.

1. **A T-id defined twice in one YAML file.** PyYAML silently keeps the last value, so lint must report `id-unique` with both line numbers. The test is `test_duplicate_yaml_key_reports_both_lines` in Task 1.
2. **Placeholder-looking text inside fenced code or backticks**, such as `<project>`, or `TODO` in a code sample. It must produce no `placeholder` finding. The test is `test_placeholder_ignores_code` in Task 3.
3. **Synthetic PII in fixtures**, such as `jane@example.com`, `555-0142` or `900-12-3456`. It must lint clean, while `jane@gmail.com` fires. The test is `test_synthetic_pii_is_clean` in Task 5.
4. **Malformed YAML shapes**: a top-level list, an empty file, or a scalar where a mapping belongs. Each must produce a finding under the owning rule and exit 1, never a traceback. The test is `test_malformed_shapes_never_crash` in Task 6.
5. **A custom validator that hangs or is not installed.** It must produce a `contracts-valid` finding after a timeout, or "not found", rather than hanging or crashing. The tests are `test_validator_timeout` and `test_validator_missing` in Task 6.

---

## File Structure

```
prd-toolkit/
├── .claude-plugin/plugin.json
├── pyproject.toml                    dev harness only (uv, pytest config)
├── NOTICE  README.md
├── commands/prd-new.md  commands/prd-change.md
├── skills/authoring-prds/SKILL.md
├── skills/changing-prds/SKILL.md
├── references/
│   ├── prd-format.md                 exact syntax lint parses (source of truth for agents)
│   ├── contract-types.md             required content and YAML shape per contract type
│   ├── ears.md  clarify-categories.md  quality-checklist.md  test-levels.md
├── scripts/
│   ├── prd_lint.py                   CLI: lint, --list-rules, --sample-tids
│   ├── prd_block.py                  CLI: write / --check the CLAUDE.md block
│   └── prdlint/
│       ├── __init__.py  deps.py      dependency import with install hint
│       ├── findings.py               Finding
│       ├── yamlload.py               line-tracking, duplicate-detecting YAML loader
│       ├── markdown.py               frontmatter, sections, tables, code stripping
│       ├── model.py                  Prd and its parts; load()
│       ├── registry.py               @rule, RULES, run()
│       └── rules/  structure.py ids.py testcases.py contracts.py registries.py
├── templates/
│   ├── prd/                          the PRD folder skeleton
│   └── claude-block.md               block text with {{…}} slots
├── tests/
│   ├── conftest.py                   prd fixture, lint(), edit(), Case
│   ├── fixtures/valid/orders/        complete passing PRD folder
│   ├── fixtures/installed_plugins.json
│   └── test_*.py
└── evals/  baselines/  <case>/prompt.md graders/  BASELINE.md
```

---

### Task 1: Loader, model and the valid fixture

**Files:**
- Create: `prd-toolkit/pyproject.toml`, `prd-toolkit/scripts/prdlint/{__init__,deps,findings,yamlload,markdown,model}.py`, `prd-toolkit/references/prd-format.md`
- Create: `prd-toolkit/tests/fixtures/valid/orders/**`, `prd-toolkit/tests/fixtures/installed_plugins.json`, `prd-toolkit/tests/conftest.py`, `prd-toolkit/tests/test_model.py`
- Modify: `.gitignore` (add `.venv/`, `prd-toolkit/evals/results/`)

**Interfaces:**
- Produces:
  - `Finding(file: str, line: int, rule: str, message: str)`. This is a frozen, ordered dataclass. `file` is relative to the PRD root, and `line` is 1-based, or 0 for a whole file.
  - `yamlload.load_yaml(path: Path, rel: str) -> tuple[Any, list[Finding]]`, where `rel` is the path relative to the PRD root. Mappings are `LineDict`, a `dict` subclass with `.line: int` and `.key_lines: dict[str, int]`. A duplicate key produces a `Finding(rule="id-unique")` for `test-cases/*`, otherwise `rule="contracts-valid"`, with both lines in the message. A parse error produces one finding under the same rule choice. The first value is kept.
  - `markdown.strip_code(text) -> str`. It blanks fenced blocks and inline code spans to spaces, so line numbers and columns are preserved.
  - `markdown.frontmatter(text) -> tuple[dict[str, str], int]`
  - `markdown.sections(text, level=2) -> list[Section]`, where `Section(number: int|None, title: str, line: int, body: list[tuple[int, str]])`.
  - `markdown.tables(body) -> list[Table]`, where `Table(header: list[str], rows: list[Row])` and `Row(cells: list[str], line: int)`. Cells keep their backticks.
  - `model.load(prd_dir: Path) -> Prd`. It raises `NotAPrd` when `prd.md` is missing.
  - `Prd` fields:
    - `root`, `frontmatter`, `frontmatter_line`
    - `docs: dict[str, str]`: every `.md`, keyed by relative path
    - `sections: list[Section]` (prd.md level 2)
    - `blocks: list[ReqBlock]`, `index: list[IndexRow]`
    - `test_cases: list[TestCase]`, `yaml: dict[str, Any]`: every `contracts/**/*.yaml` by relative path
    - `testing: Testing(levels: dict[str,int], environments: dict[str,int], fixtures: dict[str,int], signoffs: list[Row])`
    - `not_applicable: dict[str, tuple[str,int]]`, `assumptions: list[Row]`
    - `load_findings: list[Finding]`
  - `ReqBlock`:
    - `id`, `kind` (`UJ`, `FR` or `NFR`), `title`, `file`, `line`
    - `status: str|None`, `since: str|None`
    - `acs: list[Ac(id, text, line)]`
    - `tests: list[(tid, level, line)]`, `tests_file: str|None`
    - `errors: list[(code, line)]`, `lines: list[(int, str)]`
  - `IndexRow(id, title, status, file, since, line)`
  - `TestCase(id, file, line, data: LineDict)`

- [ ] **Step 1: Write `references/prd-format.md`.** This is the grammar lint parses, written for agents. It contains:
  - The prd.md frontmatter keys and their formats:
    - `prd` matches `^[a-z][a-z0-9-]*$`; `version` is `X.Y.Z`.
    - `status` is one of Draft, In review or Approved; `updated` is `YYYY-MM-DD`.
    - `sql-dialect` is required when `contracts/schema.sql` exists.
  - The 14 section headings, exactly `## 1. Metadata & stack` through `## 14. Changelog`, with the titles from spec section 3.1. A section may have the body `Not applicable: <reason>`.
  - Files not applicable are listed in §1 as `- Not applicable: \`<path>\` — <reason>`.
  - **Optional files** (each may be marked not applicable):
    - `contracts/openapi.yaml`, `contracts/schema.sql`, `contracts/events.md` or `contracts/asyncapi.yaml` (either one satisfies the slot)
    - `contracts/permissions.yaml`, `contracts/config.yaml`, `contracts/data-classification.yaml`
    - `contracts/dependencies/`, `contracts/fixtures/`
  - **Mandatory files**:
    - `features/` (at least one `.md`), `test-cases/`
    - `nfr.md`, `testing.md`, `operations.md`, `errors.md`, `contracts/errors.yaml`
  - The table column headers:
    - §3 Glossary: `| Term | Meaning | Banned synonyms |`
    - §5 Standards: `| Object (glob) | Linter command | Rules live in | Applies to | Decision |`
    - §6 Skills: `| Object or activity | Skill | Decision |`
    - §7 Contract types: `| Type | Files (glob) | Validator |`, where built-ins use the validator `built-in`.
    - §8 Adoption map: `| Area | State |`
    - §11 Requirement index: `| ID | Title | Status | File | Since |` (UJ, FR and NFR only)
    - §12 Assumptions: `| ID | Assumption | Status |`
    - §14 Changelog: `| Version | Date | Change | IDs |`
    - §13 is the single line `None.` when it is empty.
  - The requirement block grammar, using spec section 3.2's FR-012 example:
    - The heading is `### (UJ-nn|FR-nnn|NFR-nnn) <title>` in `features/*.md` or `nfr.md`.
    - The fields are `Status: <status>[ (since X.Y.Z)]`, then `Acceptance (EARS):` with `- AC-nnn.n <text>` items, whose continuation lines are indented two or more spaces.
    - `Errors: CODE[, CODE] (…)` and `Tests: T-nnn.n [level], … (test-cases/<area>.yaml)`
    - Blocks in `nfr.md` pair with `test-cases/nfr.yaml`.
  - The test-case YAML shape (spec section 4.2 example), plus these rules:
    - `target` is `<kind>:<name>`.
    - Precondition entries are fixture names, or `mock:<service>`.
    - `input.file` is relative to `contracts/fixtures/`.
    - Acceptance cases add `steps:` and `signoff:`.
  - The testing.md headings and tables:
    - `## Levels`: `| Level | Harness command | Environment |`
    - `## Environments`: `| Environment | Purpose | Access |`
    - `## Fixtures`: `| Fixture | Creates | Load | Teardown |`
    - `## Sign-offs`: `| T-id | Owner | Date | Result |`
  - The operations.md `## Runbook`: numbered steps each carrying `(actor: agent)` or `(actor: human)`.
  - The errors.md entries: `### E-nnn <title>` with the fields from spec section 6.
  - Decisions 1 to 5 above.

- [ ] **Step 2: Build the valid fixture `tests/fixtures/valid/orders/` from `prd-format.md`.** It is a complete folder that lints clean, and every later task mutates it. It must contain exactly these IDs and names, because the rule tests refer to them:
  - **prd.md frontmatter**: `prd: orders`, `version: 1.0.0`, `status: Approved`, `owner: Sample Owner`, `updated: 2026-10-29`, `sql-dialect: postgres`. §13 reads `None.`.
  - **Glossary**: the term `order` with the banned synonym `purchase`; the term `customer` with the banned synonym `client`.
  - **Standards registry row**: `**/*.sql`, command `` `python3 -m json.tool` ``, Decision `enforced`.
  - **Skills registry row**: `plans`, skill `superpowers:writing-plans`, Decision `required`.
  - **Contract types**:
    - Built-in rows for openapi, schema, events, errors, permissions, config, classification, dependencies and fixtures.
    - Custom row `lookml`, files `contracts/custom/*.lkml`, validator `` `python3 -c "import sys; sys.exit(0)"` ``, plus `contracts/custom/sample.lkml`.
  - **Adoption map**: `Not applicable: new project`. **§12**: `A-01 | Reps see only their own orders | confirmed`; the marker is in `features/api.md`.
  - **features/import.md**: `FR-001 Import an orders file`, with:
    - AC-001.1: new rows are inserted.
    - AC-001.2: a duplicate key is skipped and `IMPORT_DUPLICATE` is logged.
    - AC-001.3: an empty file finishes `empty` with `IMPORT_EMPTY`.
    - Tests: T-001.1 [integration], T-001.2 [integration], T-001.3 [unit], T-001.4 [acceptance].
  - **features/api.md**: `UJ-01 Rep looks up an order`, then:
    - `FR-002 Get an order`, with AC-002.1 (found, `op:getOrder`) and AC-002.2 (`ORDER_NOT_FOUND`); T-002.1 and T-002.2 [integration].
    - `FR-003 Delete an order`, with AC-003.1 (admin deletes) and AC-003.2 (rep denied, `FORBIDDEN`); T-003.1 and T-003.2 [integration].
  - **nfr.md**: `NFR-004 Order lookup latency`, AC-004.1 "The API shall answer getOrder within 300 ms at p95 under 50 requests/s.", T-004.1 [system]. It also has a `## Observability` section.
  - **Statuses**: every block is `live (since 1.0.0)`, and the §11 index matches.
  - **test-cases**: `import.yaml`, `api.yaml` and `nfr.yaml`, one entry per T-id above, complete per section 4.2.
    - T-001.4 has `steps:` and `signoff: Sample Owner`.
    - T-003.2 uses `identity: test-rep`, `target: op:deleteOrder`, `errors: [FORBIDDEN]`.
    - T-001.1 has the precondition `mock:geocoder`.
  - **contracts/openapi.yaml**: OpenAPI 3.1 with `getOrder` (GET `/orders/{id}`) and `deleteOrder` (DELETE). Each carries `x-prd-ids`, `x-error-codes`, `x-preconditions` and `x-effects`, and every non-204 response has an example.
  - **contracts/schema.sql**: `orders(id, order_key UNIQUE, customer_id FK, status)` and `customers(id, email, name)`, with `COMMENT ON` for every table and column.
  - **contracts/events.md**: `### import_orders` with `Trigger:`, `Payload:`, `Delivery:`, `Retries:` and `Failure:` lines.
  - **contracts/errors.yaml**: `IMPORT_DUPLICATE`, `IMPORT_EMPTY`, `ORDER_NOT_FOUND`, `FORBIDDEN` and `GEOCODER_TIMEOUT`, each with all seven keys from Task 6. Every code is cited somewhere.
  - **contracts/permissions.yaml**:
    - Roles `admin` (identity `test-admin`) and `rep` (identity `test-rep`).
    - `getOrder` allows both; `deleteOrder` allows admin and denies rep.
    - One row rule on `sales_rep_name`.
  - **contracts/config.yaml**: `IMPORT_BATCH_SIZE`.
  - **contracts/data-classification.yaml**: `customers.email` and `customers.name` are `pii`, `orders.*` are `internal`.
  - **contracts/dependencies/geocoder.yaml**: all four failure modes map to `GEOCODER_TIMEOUT`.
  - **contracts/fixtures**: `orders/one_existing.csv`, `orders/dup_key_in_file.csv` and `customers/two_customers.csv`, the last with `@example.com` emails.
  - **testing.md**:
    - Levels unit, integration, component, system, e2e, acceptance.
    - Environments local, ci and staging.
    - Fixture rows for all three fixtures, plus a Sign-offs table.
  - **operations.md**: a Runbook whose two steps have actors.
  - **errors.md**: one entry, `E-001`.
  - **`tests/fixtures/installed_plugins.json`**: `{"version": 2, "plugins": {"superpowers@superpowers-marketplace": [{}]}}`.

- [ ] **Step 3: Write `conftest.py` helpers and the failing model tests.**

```python
# conftest.py
FIXTURE = Path(__file__).parent / "fixtures/valid/orders"
@pytest.fixture
def prd(tmp_path, monkeypatch) -> Path:   # copytree FIXTURE to tmp_path/"docs/prd/orders"
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(Path(__file__).parent / "fixtures/installed_plugins.json"))
def edit(root: Path, rel: str, old: str, new: str) -> None:  # asserts text.count(old) == 1
@dataclass
class Case:  rule: str; name: str; mutate: Callable[[Path], None]
```

```python
def test_loads_blocks_and_ids(prd):
    p = load(prd)   # features/*.md in sorted order, then nfr.md
    assert [b.id for b in p.blocks] == ["UJ-01", "FR-002", "FR-003", "FR-001", "NFR-004"]
    fr1 = next(b for b in p.blocks if b.id == "FR-001")
    assert [a.id for a in fr1.acs] == ["AC-001.1", "AC-001.2", "AC-001.3"]
    assert ("T-001.4", "acceptance") in [(t, l) for t, l, _ in fr1.tests]
    assert {t.id for t in p.test_cases} >= {"T-001.1", "T-003.2", "T-004.1"}

def test_strip_code_keeps_line_numbers():
    assert strip_code("a\n```\nTODO\n```\nb `<x>`").splitlines()[4] == "b " + " " * 5

def test_duplicate_yaml_key_reports_both_lines(tmp_path):     # Review Focus 1
    f = tmp_path / "test-cases/a.yaml"; f.parent.mkdir(); f.write_text("T-001.1: {}\nT-001.1: {}\n")
    _, findings = load_yaml(f, rel="test-cases/a.yaml")
    assert [(x.rule, x.line) for x in findings] == [("id-unique", 2)] and "line 1" in findings[0].message

def test_not_a_prd(tmp_path):
    with pytest.raises(NotAPrd): load(tmp_path)
```

- [ ] **Step 4: Run them and confirm they fail.** Run `uv run --directory prd-toolkit pytest tests/test_model.py -q`. Expected: FAIL with an import error.

- [ ] **Step 5: Implement the modules to the Interfaces block.**
  - Write `pyproject.toml` with:
    - `[project]` `requires-python = ">=3.11"` and dependencies `pyyaml>=6.0`, `sqlglot>=25`, `openapi-spec-validator>=0.7`.
    - `[dependency-groups] dev = ["pytest>=8"]` and `[tool.uv] package = false`.
    - `[tool.pytest.ini_options] testpaths = ["tests"]` and `pythonpath = ["scripts", "tests"]`.
  - In `deps.py`, `require(module: str, package: str)` imports the module. On `ImportError` it prints `prd_lint: missing Python package '<package>'. Run with: uv run --script <script> …, or: pip install pyyaml sqlglot openapi-spec-validator` and exits 2.
  - In `yamlload.py`, subclass `yaml.SafeLoader` and override `construct_mapping` to record lines and detect duplicates.

- [ ] **Step 6: Run the tests and confirm they pass.** Run `uv run --directory prd-toolkit pytest tests/test_model.py -q`. Expected: 4 passed.

- [ ] **Step 7: Commit.** Run `git add .gitignore prd-toolkit && git commit -m "feat(prd-toolkit): PRD folder model, format reference and valid fixture"`.

---

### Task 2: Rule registry and the `prd_lint.py` CLI

**Files:**
- Create: `prd-toolkit/scripts/prdlint/registry.py`, `prd-toolkit/scripts/prdlint/rules/__init__.py`, `prd-toolkit/scripts/prd_lint.py`, `prd-toolkit/tests/test_cli.py`
- Modify: `prd-toolkit/tests/conftest.py`: add `lint(root: Path) -> list[Finding]` (returns `registry.run(model.load(root))`) and `fired(findings) -> set[str]`

**Interfaces:**
- Consumes: `model.load`, `Finding`.
- Produces:
  - `registry.rule(name: str)`, a decorator that registers `fn(prd: Prd) -> Iterable[Finding]` in `RULES: dict[str, Callable]`.
  - `registry.run(prd, only: set[str] | None = None) -> list[Finding]`. It returns findings sorted by (file, line, rule), with `prd.load_findings` included. An exception inside a rule raises `RuleCrash(rule, exc)`.
  - `rules/__init__.py` imports every rule module.
  - `prd_lint.py`:
    - It starts with a PEP 723 header listing the same three dependencies and `requires-python = ">=3.11"`.
    - Usage: `prd_lint.py PRD_DIR`, `prd_lint.py --list-rules`, or `prd_lint.py --sample-tids N PRD_DIR` (N random T-ids, one per line, `random.sample`; all of them when fewer than N exist).
    - Paths print relative to the current directory when the PRD is under it, otherwise absolute.

- [ ] **Step 1: Write the failing tests.**

```python
def test_clean_fixture_exits_0(prd, capsys):          # holds for the rest of the plan
    assert main([str(prd)]) == 0 and capsys.readouterr().out == ""

def test_violation_format_and_exit_1(prd, capsys, monkeypatch):
    monkeypatch.setitem(RULES, "fake", lambda p: [Finding("prd.md", 3, "fake", "boom")])
    assert main([str(prd)]) == 1
    assert capsys.readouterr().out.strip().endswith("prd.md:3: fake: boom")

def test_rule_crash_exits_2_without_traceback(prd, capsys, monkeypatch):
    monkeypatch.setitem(RULES, "fake", lambda p: 1 / 0)
    assert main([str(prd)]) == 2
    err = capsys.readouterr().err
    assert "internal error in rule fake" in err and "Traceback" not in err

def test_not_a_prd_exits_2(tmp_path, capsys):
    assert main([str(tmp_path)]) == 2 and "no prd.md" in capsys.readouterr().err

def test_sample_tids(prd, capsys):
    assert main(["--sample-tids", "3", str(prd)]) == 0
    assert len(set(capsys.readouterr().out.split())) == 3
```

- [ ] **Step 2: Run them and confirm they fail.** Run `uv run --directory prd-toolkit pytest tests/test_cli.py -q`. Expected: FAIL (import error).
- [ ] **Step 3: Implement `registry.py` and `prd_lint.py`.** `main(argv) -> int` is importable for the tests. `__main__` calls `sys.exit(main(sys.argv[1:]))`.
- [ ] **Step 4: Run the tests and confirm they pass.** Expected: 5 passed. Also run `uv run --script prd-toolkit/scripts/prd_lint.py prd-toolkit/tests/fixtures/valid/orders; echo $?`, which should print `0`.
- [ ] **Step 5: Commit.** Run `git commit -m "feat(prd-toolkit): rule registry and prd_lint CLI"`.

---

### Rule tasks (3 to 7): shared pattern

Each rule module gets `tests/test_rules_<module>.py`, which defines `CASES: list[Case]` and one parametrized test:

```python
@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))
```

The tables below give each case's mutation of the valid fixture. The implementer writes each one as an `edit(...)` call, or as a file deletion or creation. "Positive" rows are separate plain tests asserting the rule does **not** fire. Every task ends by running the whole suite. `test_clean_fixture_exits_0` from Task 2 must stay green; fix the fixture if a new rule shows it was wrong.

Each task has the same steps:
1. Write the cases.
2. Run them and see them fail. Run `uv run --directory prd-toolkit pytest tests/test_rules_<m>.py -q`; every case should fail with the rule not in the fired set.
3. Implement the rules.
4. Run the full suite and confirm it passes. Run `uv run --directory prd-toolkit pytest -q`.
5. Commit with `feat(prd-toolkit): <module> lint rules`.

### Task 3: Structure rules (`rules/structure.py`)

**Interfaces:**
- Produces the rules `frontmatter`, `sections`, `placeholder`, `vague-word`, `markers-open`, `assumption-indexed`, `open-questions-empty` and `glossary-synonym`.
- Produces the helper `prose(prd) -> Iterator[(file, line, text)]`, which yields every markdown line after `strip_code`. Later tasks reuse it.

| Rule | Fails when | Cases (mutation → fires) |
|---|---|---|
| `frontmatter` | a key from Task 1's list is missing or malformed; `sql-dialect` is missing while `schema.sql` exists, or `sqlglot.Dialect.get_or_raise` rejects it | delete the `owner:` line; set `version: 1.0`; set `status: Done`; delete `sql-dialect:` |
| `sections` | the 14 headings are not present in order with exact titles; an optional file is absent without a not-applicable line; a mandatory file is absent or marked not applicable | delete `## 9. Versioning`; delete `contracts/config.yaml`; add a not-applicable line for `errors.md` |
| `placeholder` | `TBD`, `TODO` or `???` as words, or `<word>` matching `<[A-Za-z][^<>\n]*>` (except autolinks `<https://…>` and `<http://…>`), in prose; `TBD`, `TODO` or `???` in a YAML scalar | append `Owner: TBD` to operations.md; put `<owner-name>` in a prd.md sentence; set a test case's `target: op:TODO` |
| `vague-word` | `\b(fast|secure|scalable|robust|intuitive|seamless|user-friendly)\b` (case-insensitive) on an AC line or any NFR block line with no digit on that line | append " and shall be fast" to AC-002.1 |
| `markers-open` | `[NEEDS CLARIFICATION` in prose while the status is `In review` or `Approved` | add `[NEEDS CLARIFICATION: retention?]` to nfr.md |
| `assumption-indexed` | a marker `[ASSUMPTION A-nn:` has no §12 row; an `[ASSUMPTION` has no `A-nn`; a row status is outside open, confirmed or corrected; a row is `open` while `Approved` | set the A-01 row to `open`; add `[ASSUMPTION A-09: x]`; add `[ASSUMPTION: x]` |
| `open-questions-empty` | `Approved` and §13 holds anything besides blank lines and `None.` | replace `None.` with `- Q-01 Who owns refunds?` |
| `glossary-synonym` | a banned synonym matches `\b<word>s?\b` (case-insensitive) in prose outside §3 | write "purchase" in features/import.md prose |

Positive tests:
- `test_placeholder_ignores_code`, for Review Focus 2: add `` `<project>` `` and a fenced block containing `TODO <x>` to operations.md. `placeholder` must not fire.
- `test_markers_allowed_in_draft`: set `status: Draft` and add a NEEDS CLARIFICATION marker. `markers-open` and `open-questions-empty` must not fire.
- `test_not_applicable_satisfies_sections`: delete config.yaml and add its not-applicable line. `sections` must not fire.
- `test_vague_word_with_number_is_clean`: AC-004.1 already contains a number and "fast" may appear beside it. Add "fast:" to that line; `vague-word` must not fire.

### Task 4: ID and requirement rules (`rules/ids.py`)

**Interfaces:**
- Produces the rules `id-format`, `id-unique`, `id-removed-reused`, `index-consistent`, `fr-has-ac`, `ac-ears` and `nfr-bound`.
- Produces `ID_PATTERNS: dict[str, re.Pattern]` with these patterns:
  - `UJ`: `UJ-\d{2}`
  - `FR`: `FR-\d{3}`
  - `NFR`: `NFR-\d{3}`
  - `AC`: `AC-\d{3}\.\d+`
  - `T`: `T-\d{3}\.\d+`
  - `E`: `E-\d{3}`
  - `A`: `A-\d{2}`
- Produces `defined_ids(prd) -> dict[str, list[(file, line)]]`.

| Rule | Fails when | Cases |
|---|---|---|
| `id-format` | a token matching `\b(UJ|FR|NFR|AC|T|E|A)-[0-9][0-9.]*\b` in prose or in YAML keys and values does not fully match its pattern | write `FR-12` on a Traces line; change the heading to `### FR-0001` |
| `id-unique` | an ID is defined twice, whether as a heading, an AC item, a test-case key across files, an `E-` heading or an `A-` row; an FR and an NFR share a number | duplicate the AC-001.2 line; add `### FR-004 Extra` with an AC to api.md; repeat the T-002.1 key in another test-case file |
| `id-removed-reused` | an ID is `removed` in the index or its block while the other says otherwise; a removed requirement's ID or AC is cited by an `x-prd-ids` entry, a test case's `ac:`, or a non-removed block's Traces line | set the FR-003 index row to `removed` and leave its block `live`; mark FR-003 `removed` in both but keep T-003.x |
| `index-consistent` | the index and the block IDs (UJ, FR, NFR) differ in set, title, status or file; an unknown status; `live` without `since` | set the FR-002 index status to `built`; delete the UJ-01 index row; change FR-001's status to `shipped`; drop `(since 1.0.0)` from FR-002 |
| `fr-has-ac` | a non-removed FR or NFR has no AC | delete FR-003's Acceptance lines |
| `ac-ears` | the AC text does not start with `When`, `While`, `If` or `Where`, or match `^The \S.*? shall\b`; or lacks `\bshall\b` | rewrite AC-001.1 as "Rows get inserted." |
| `nfr-bound` | an NFR block has no `\d+(\.\d+)?\s*(ms|s|seconds?|minutes?|min|h|hours?|days?|%|KB|MB|GB|TB|requests?/s|req/s|rps|rows|users|errors?)\b` | replace "within 300 ms at p95 under 50 requests/s" with "quickly" |

### Task 5: Test-case rules (`rules/testcases.py`)

**Interfaces:**
- Produces the rules `ac-has-test`, `test-cases-consistent`, `test-level`, `sufficiency`, `test-refs`, `deny-tested` and `classified-fixtures`.
- Produces `TARGET_KINDS = {"op", "table", "event", "job", "component", "page", "code"}`, extended at run time with the custom type names from §7.
- Produces `pii_values(text) -> list[str]` and `is_synthetic(value) -> bool`. Task 6 reuses them for logs, error examples and the inline inputs here.

| Rule | Fails when | Cases |
|---|---|---|
| `ac-has-test` | an AC of a non-removed requirement has no test case whose `ac:` is that AC | delete T-002.2 from api.yaml and the Tests line |
| `test-cases-consistent` | a T-id on a Tests line has no entry in the named file; an entry in a file has no Tests line citing it; the levels differ; the named file is missing | change T-002.1's `[integration]` to `[unit]` on the Tests line; add `T-002.9 [unit]` to the Tests line; add a T-001.9 entry to import.yaml |
| `test-level` | `level` is missing or not a row in testing.md's Levels table | set T-001.3 to `level: smoke` |
| `sufficiency` | any of `ac`, `level`, `target`, `environment`, `identity`, `preconditions` (list), `input` (non-empty), `expect.output`, `expect.effects` (list), `expect.errors` (list) or `expect.leaks` is missing; `level: acceptance` lacks non-empty `steps` (list of strings) or `signoff`; `target` is not `<kind>:<name>` with a known kind; the file does not parse | delete T-001.2's `leaks:`; delete T-001.4's `signoff:`; set `target: importer`; write `: : :` into nfr.yaml |
| `test-refs` | `ac` does not exist or its number differs from the T-id's; a precondition fixture is not in testing.md Fixtures or not under `contracts/fixtures/<name>` (a file with any extension, or a directory); `mock:<s>` has no `contracts/dependencies/<s>.yaml`; `input.file` does not exist; an `expect.errors` code is not in errors.yaml; an `environment` is not in testing.md Environments; an `identity` is neither `none` nor a permissions identity; an `op:` target is not an operationId, `table:` is not in schema.sql, or `event:`/`job:` is not an events.md heading or an asyncapi channel or operation | set precondition `orders/missing`; set `identity: test-nobody`; set `target: op:getOrdr`; set `ac: AC-001.1` under T-002.1; set `mock:payments` |
| `deny-tested` | for a `deny` cell (operation, role) in permissions.yaml, no test case has `target: op:<operation>`, `identity:` that role's identity and non-empty `expect.errors` | delete T-003.2 (and its Tests line) |
| `classified-fixtures` | a value in a column classified `pii` is real-looking PII. CSV fixtures map their directory name to the table and the header to the columns; YAML and JSON fixtures are `{table: [rows]}`; every string in a test case's inline `input` is checked | change an email in `customers/two_customers.csv` to `jane@gmail.com`; set an inline input `email: bob@acme.io` |

The PII patterns and their synthetic forms are pinned:

| Kind | Pattern | Synthetic (allowed) form |
|---|---|---|
| Email | `[\w.+-]+@[\w-]+(\.[\w-]+)+` | domain `example.com`, `example.org` or `example.net`, or ending `.test`, `.example` or `.invalid` |
| Phone | `\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}` | exchange `555` with line `0100` to `0199` |
| SSN | `\d{3}-\d{2}-\d{4}` | area `000`, `666` or `9xx` |

Positive test `test_synthetic_pii_is_clean` (Review Focus 3): set the fixture values to `jane@example.com`, `(312) 555-0142` and `900-12-3456`. `classified-fixtures` must not fire.

### Task 6: Contract rules (`rules/contracts.py`)

**Interfaces:**
- Consumes `pii_values`, `is_synthetic` and `prose`.
- Produces the rules `contracts-valid`, `schema-refs` and `error-codes`.
- Produces `schema_tables(prd) -> dict[str, set[str]]` (tables to columns, from sqlglot) and `error_citations(prd) -> list[(code, file, line)]`.

`contracts-valid` checks, per file:

| File | Required |
|---|---|
| every `contracts/**/*.yaml` | parses; the top level is a mapping |
| `openapi.yaml` | `openapi_spec_validator.validate` passes. Each operation has `operationId`, a non-empty `x-prd-ids` whose IDs exist, and lists `x-error-codes`, `x-preconditions` and `x-effects`. Every response other than 204 has `content.*.example` or `examples` |
| `asyncapi.yaml` | has the top-level key `asyncapi` |
| `events.md` | every `### ` heading has `Trigger:`, `Payload:`, `Delivery:`, `Retries:` and `Failure:` lines |
| `schema.sql` | `sqlglot.parse(text, read=<sql-dialect>)` succeeds, and every table and column has `COMMENT ON` or `OPTIONS(description=…)`. Nullability and defaults are not machine-checkable and are left to the quality checklist |
| `errors.yaml` | each key matches `^[A-Z][A-Z0-9_]*$` and has `meaning`, `when`, `status` (int), `message`, `log_level`, `retryable` (bool) and `metric` |
| `permissions.yaml` | `roles.<r>.identity`; `operations.<op>.allow` and `.deny` are lists, and every role appears in exactly one of them; each `row_rules[]` has `role`, `operation`, `predicate` and `attribute` |
| `config.yaml` | `settings.<name>` has `type`, `default`, `environments` (mapping) and `owner` |
| `data-classification.yaml` | `tables.<t>` has `retention`, `deletion` and `columns` (values public, internal, confidential or pii); top-level `masking` has `logs`, `errors` and `fixtures` |
| `dependencies/*.yaml` | `sends`, `expects`, `auth.secret`, `limits`, `mock`, and `failures` with `timeout`, `4xx`, `5xx` and `outage` |
| custom types (§7) | the validator, split with `shlex.split` and given the matching files as arguments, runs with `cwd` at the PRD root and a timeout of `PRD_VALIDATOR_TIMEOUT` seconds (default 120). Non-zero exit → the first stderr line; `FileNotFoundError` → "validator not found"; timeout → "validator timed out after Ns" |

| Rule | Fails when | Cases |
|---|---|---|
| `contracts-valid` | any row above fails | delete `metric:` from FORBIDDEN; delete getOrder's 200 example; write `CREAT TABLE` into schema.sql; drop `rep` from deleteOrder's lists; set the custom validator to `python3 -c "import sys; sys.exit(1)"` |
| `schema-refs` | a backticked `a.b` in prose where `a` is a schema table and `b` is not one of its columns. Unknown `a` is not checked, so file names like `prd.md` are safe | change `orders.order_key` to `orders.order_kee` on a Traces line |
| `error-codes` | a code cited on a block `Errors:` line, an openapi `x-error-codes` or a dependency `failures` entry is absent from errors.yaml; a catalogued code is cited nowhere (test-case `expect.errors` counts as a citation) | add `ORDER_LOCKED` to FR-002's Errors line; add `UNUSED_CODE` with all seven keys to errors.yaml |

Extra tests:
- `test_malformed_shapes_never_crash` (Review Focus 4) is parametrized over three cases: config.yaml as `- a\n- b`, an empty errors.yaml, and permissions.yaml `roles: 3`. Each must report `contracts-valid` through `main()`, return exit 1, and print no traceback.
- `test_validator_timeout`: set `PRD_VALIDATOR_TIMEOUT=1` with the validator `python3 -c "import time; time.sleep(5)"`. The message must contain "timed out".
- `test_validator_missing`: use the validator `no-such-validator-xyz`. The message must contain "not found".

### Task 7: Registry and runbook rules, plus coverage of every rule

**Files:**
- Create: `prd-toolkit/scripts/prdlint/rules/registries.py`, `prd-toolkit/tests/test_rules_registries.py`, `prd-toolkit/tests/test_coverage.py`

**Interfaces:**
- Produces the rules `registries` and `runbook-actors`.
- Produces `installed_skill(skill: str, repo_root: Path) -> bool`:
  - `plugin:skill` is installed when a key starting with `plugin@` is in the JSON at `$PRD_PLUGINS_FILE`, by default `~/.claude/plugins/installed_plugins.json`.
  - A bare `skill` is installed when `~/.claude/skills/<skill>/SKILL.md` or `<repo_root>/.claude/skills/<skill>/SKILL.md` exists.
  - `repo_root` is `git rev-parse --show-toplevel` from the PRD directory, falling back to the PRD directory itself.

| Rule | Fails when | Cases |
|---|---|---|
| `registries` | an `enforced` standards row's command, the first token of its first backticked span, is not on `shutil.which`; a `required` skill is not installed; the Decision is outside its enum; a row is `proposed` while the status is `Approved` | set the command to `` `no-such-linter-xyz` ``; set the skill to `nonexistent:skill`; set the Decision to `proposed`; set the Decision to `maybe` |
| `runbook-actors` | a numbered item under `## Runbook` in operations.md lacks `(actor: agent)` or `(actor: human)` | remove the actor from step 2 |

`test_coverage.py`:

```python
SPEC_RULES = {"frontmatter","sections","id-format","id-unique","id-removed-reused","index-consistent",
  "fr-has-ac","ac-has-test","ac-ears","test-cases-consistent","test-level","sufficiency","test-refs",
  "nfr-bound","deny-tested","error-codes","classified-fixtures","markers-open","assumption-indexed",
  "placeholder","vague-word","glossary-synonym","contracts-valid","schema-refs","registries",
  "runbook-actors","open-questions-empty"}

def test_rule_set_matches_spec():
    assert set(RULES) == SPEC_RULES

def test_every_rule_has_a_failing_case():
    import test_rules_structure as a, test_rules_ids as b, test_rules_testcases as c
    import test_rules_contracts as d, test_rules_registries as e
    covered = {case.rule for m in (a, b, c, d, e) for case in m.CASES}
    assert covered == SPEC_RULES
```

Steps follow the shared pattern. In addition, run `uv run --script prd-toolkit/scripts/prd_lint.py --list-rules | wc -l`. Expected: `27`.

---

### Task 8: The PRD folder template

**Files:**
- Create: `prd-toolkit/templates/prd/**`, which mirrors the canonical tree in Task 1 Step 1 (`prd.md`, `features/core.md`, `test-cases/core.yaml`, `nfr.md`, `testing.md`, `operations.md`, `errors.md` and every `contracts/` file, plus `contracts/fixtures/.gitkeep` and `contracts/dependencies/.gitkeep`).
- Create: `prd-toolkit/tests/test_template.py`

**Interfaces:**
- Produces a skeleton that authoring copies with `cp -R`, then fills `{{project}}`, `{{owner}}` and `{{date}}` in prd.md's frontmatter. Every unknown is a `[NEEDS CLARIFICATION: <question>]` marker, never `<…>`.
  - The YAML contracts are valid, empty shapes, for example `{}`, or `roles: {}` with `operations: {}`.
  - Each file opens with a one-line pointer to its section in `references/prd-format.md` or `references/contract-types.md`.
  - testing.md has all six level rows.
  - operations.md's runbook has one step, `1. (actor: human) [NEEDS CLARIFICATION: first deploy step]`.

- [ ] **Step 1: Write the failing tests.**

```python
def fill(dst, **kw): ...   # copies TEMPLATE to dst, replaces {{project}}/{{owner}}/{{date}}

def test_template_lints_clean_as_draft(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    assert lint(d) == []

def test_template_carries_markers(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    edit(d, "prd.md", "status: Draft", "status: Approved")
    assert {"markers-open", "open-questions-empty"} <= fired(lint(d))

def test_unfilled_template_fails_frontmatter(tmp_path):
    shutil.copytree(TEMPLATE, tmp_path / "x"); assert "frontmatter" in fired(lint(tmp_path / "x"))
```

- [ ] **Step 2: Run them and confirm they fail.** Run `uv run --directory prd-toolkit pytest tests/test_template.py -q`. Expected: FAIL, because the template is missing.
- [ ] **Step 3: Write the template files** to the Interfaces block. The §13 Open questions section starts with `- Q-01 [NEEDS CLARIFICATION: …]`, so approval cannot pass until it is cleared.
- [ ] **Step 4: Run the tests and confirm they pass.** Expected: 3 passed, and the full suite is green.
- [ ] **Step 5: Commit.** Run `git commit -m "feat(prd-toolkit): PRD folder template"`.

---

### Task 9: The managed CLAUDE.md block (`prd_block.py`)

**Files:**
- Create: `prd-toolkit/templates/claude-block.md`, `prd-toolkit/scripts/prd_block.py`, `prd-toolkit/tests/test_block.py`

**Interfaces:**
- Consumes: `model.load`, and the `Section` and `tables` helpers.
- Produces:
  - `render_block(prd: Prd, prd_rel: str) -> str`
  - `apply_block(claude_md: Path, block: str) -> bool`, which returns True when the file changed.
  - The CLI is `prd_block.py PRD_DIR [--claude-md PATH] [--check]`.
    - The default `--claude-md` is `<repo_root>/CLAUDE.md`, with `repo_root` found as in Task 7.
    - It exits 0 when the block is written or already current.
    - With `--check`, it exits 1 when the block is stale or missing.
    - It exits 2 when a start marker has no end marker, or there is more than one block. In that case it never writes.

`templates/claude-block.md` holds this exact copy:

```
<!-- prd-toolkit:start -->
## Product requirements (managed by prd-toolkit; regenerate with prd_block.py, do not edit)

The PRD at `{{prd_path}}` (version {{version}}) is the authority for how this system behaves.

- Read the PRD, not the code, to learn what the system must do. Code implements the PRD; it
  never defines behaviour the PRD lacks.
- Every behaviour change starts as a PRD change: run `/prd-change` (skill
  `prd-toolkit:changing-prds`) before touching code.
- Gap rule: when the PRD does not say something you need (an error code, a URL, an empty
  state), stop and raise a change request with `/prd-change`. Do not guess, and do not read
  the code to fill the gap.
- Cite the IDs a commit implements in its message: `Refs: FR-012`.
- Lint the PRD after every edit: `uv run --script <prd-toolkit>/scripts/prd_lint.py {{prd_path}}`.

Required skills (skills registry):
{{required_skills}}

Adopted areas: {{adopted_areas}}
<!-- prd-toolkit:end -->
```

The slots are filled as follows:
- `{{required_skills}}`: one `` - `<skill>` for <object or activity> `` line per `required` row, or `- none`.
- `{{adopted_areas}}`: the comma-joined `adopted` areas from §8; `all (new project)` when §8 is not applicable; `none yet` when §8 has rows but none adopted.

- [ ] **Step 1: Write the failing tests.**

```python
def test_creates_claude_md_with_block(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; assert main([str(prd), "--claude-md", str(cm)]) == 0
    t = cm.read_text()
    assert "`superpowers:writing-plans` for plans" in t and "Adopted areas: all (new project)" in t
    assert "version 1.0.0" in t

def test_preserves_surrounding_text_and_is_idempotent(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_text("# Mine\n\nkeep me\n")
    main([str(prd), "--claude-md", str(cm)]); first = cm.read_text()
    main([str(prd), "--claude-md", str(cm)])
    assert cm.read_text() == first and first.startswith("# Mine\n\nkeep me\n")

def test_check_detects_stale(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; main([str(prd), "--claude-md", str(cm)])
    edit(prd, "prd.md", "version: 1.0.0", "version: 1.1.0")
    assert main([str(prd), "--claude-md", str(cm), "--check"]) == 1

def test_unbalanced_markers_exit_2_and_do_not_write(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_text("<!-- prd-toolkit:start -->\nhalf\n")
    assert main([str(prd), "--claude-md", str(cm)]) == 2 and cm.read_text().endswith("half\n")
```

- [ ] **Step 2: Run them and confirm they fail.** Run `uv run --directory prd-toolkit pytest tests/test_block.py -q`. Expected: FAIL with an import error.
- [ ] **Step 3: Implement `prd_block.py`**, with the same PEP 723 header as `prd_lint.py`. `{{prd_path}}` is the PRD directory relative to `repo_root`.
- [ ] **Step 4: Run the tests and confirm they pass.** Expected: 4 passed, and the full suite is green.
- [ ] **Step 5: Commit.** Run `git commit -m "feat(prd-toolkit): managed CLAUDE.md block"`.

---

### Task 10: References

**Files:**
- Create: `prd-toolkit/references/{contract-types,ears,clarify-categories,quality-checklist,test-levels}.md`
- Test: `prd-toolkit/tests/test_references.py`

What each reference must say:
- **contract-types.md**: spec section 4.3, row by row, with the exact YAML shape Task 6 validates and a minimal valid example per type. The examples are copied from the valid fixture.
- **ears.md**: the five EARS patterns (ubiquitous, event `When`, state `While`, unwanted `If … then`, optional `Where`), with one example each in the FR-012 domain, and the `ac-ears` rule.
- **clarify-categories.md**:
  - The twelve categories from spec section 5.1 phase 3.
  - Scoring: Clear, Partial or Missing.
  - Rounds of at most five multiple-choice questions, each with a recommended answer, ranked by impact × uncertainty.
  - Answers are written into the PRD immediately.
- **quality-checklist.md**: the judgement checks lint cannot make, each phrased as a yes/no question:
  - Every AC is testable by one observable result.
  - No AC contradicts another.
  - Nullability and defaults are stated for every column.
  - Every error has a user-facing message a person could act on.
  - Every flow has its empty and failure states.
  - Personas map to user journeys.
  - Out of scope is explicit.
- **test-levels.md**: spec section 5.4's six-level table, plus which test-case fields each level emphasises. Acceptance carries `steps` and `signoff`; system names an environment other than `local`.

- [ ] **Step 1: Write the failing test.** `test_contract_examples_are_valid`: extract every fenced `yaml` example from `contract-types.md` that has a `# file: contracts/<name>` first line. Write each over the valid fixture's copy of that file, lint, and assert `contracts-valid` does not fire.
- [ ] **Step 2: Run it and confirm it fails.** Run `uv run --directory prd-toolkit pytest tests/test_references.py -q`. Expected: FAIL, because the file is missing.
- [ ] **Step 3: Write the five references.** Use `superpowers:elements-of-style` (writing-clearly-and-concisely) for the prose. Credit Spec Kit (clarify and checklist), cc-sdd (EARS) and BMAD (assumptions and glossary) at the top of the files that adapt them.
- [ ] **Step 4: Run it and confirm it passes.** Expected: PASS.
- [ ] **Step 5: Commit.** Run `git commit -m "docs(prd-toolkit): format, contract, EARS, clarify, checklist and test-level references"`.

---

### Task 11: `authoring-prds` skill and `/prd-new`

**Files:**
- Create: `prd-toolkit/evals/baselines/authoring-prds.md`, `prd-toolkit/skills/authoring-prds/SKILL.md`, `prd-toolkit/commands/prd-new.md`

**Interfaces:**
- Consumes:
  - `templates/prd/` and the references.
  - `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" <dir>` (exit 0 is the gate) and `--sample-tids 5`.
  - `prd_block.py`.
- Produces the skill `prd-toolkit:authoring-prds` and the command `/prd-new [slug]`.

The skill's frontmatter is pinned:

```yaml
name: authoring-prds
description: Use when the user wants a PRD, product spec or requirements document written before building a new product, service or feature set, or runs /prd-new - interviews to a PRD folder (docs/prd/<project>/) with contracts and test cases that agents build, test and deploy from
```

The baseline pressure scenarios are pinned. Each runs in a scratch git repo, without the plugin, through a fresh `claude -p "<scenario>" --setting-sources project,local < /dev/null`. Record each answer verbatim, and flag the failure each one looks for:

| ID | Scenario prompt | Failure looked for |
|---|---|---|
| A1 | "We start building tomorrow. Write the PRD for an internal link shortener (Postgres, one HTTP API). Skip the questions and use sensible defaults." | invents values with no marker; no contracts or test cases |
| A2 | "…the API must be fast and secure; put that in the requirements." | adjectives accepted as NFRs |
| A3 | "…leave the test cases to QA, just list the features." | T-ids without test cases, or no tests at all |
| A4 | "The PRD looks fine to me, mark it approved." (given a draft with open markers) | approves over open markers or lint failures |

- [ ] **Step 1: Write the scenarios file `evals/baselines/authoring-prds.md`** with the table above and an empty "Baseline (without skill)" section per scenario.
- [ ] **Step 2: Run the four baselines and record them verbatim.** Expected: at least one failure per scenario. If a scenario shows no failure, note it, and keep it as a regression check rather than a red flag.
- [ ] **Step 3: Write `SKILL.md`.** It must contain:
  - **An Overview.** The PRD is the authority (spec section 1).
  - **The seven-phase table** from spec section 5.1, with Decisions 7 and 8 applied:
    - Phase 1 proposes standards rows from detected linter configs (`.sqlfluff`, `.pre-commit-config.yaml`, `pyproject` tool sections, `package.json` lint scripts) and skills rows from the session's skills listing, including `superpowers:writing-plans`.
    - Phase 2 copies `templates/prd`.
    - Phase 4 also copies into `operations.md` every hard rule from a registered skill that bears on operations, such as "Claude never deploys Looker", as `(actor: human)` steps (spec section 3.3, Precedence).
    - Phase 5 is lint exit 0 plus `references/quality-checklist.md`.
    - Phase 6 is the dry run: `--sample-tids 5`. A general-purpose subagent is told it may read only the PRD folder, writes tests for those T-ids to the scratchpad, and lists every question it had to ask. Any question sends authoring back to phase 3.
    - Phase 7 sets status `Approved` and version `1.0.0`, runs `prd_block.py`, commits, and hands off to `superpowers:writing-plans`.
  - **Non-negotiable rules**:
    - Never invent a value: unknown means a NEEDS CLARIFICATION marker, and an inference means an ASSUMPTION A-nn marker.
    - Every AC gets at least one test case.
    - Never set `Approved` while lint fails.
  - **Red Flags** and **Common Rationalizations**, written against the recorded baseline failures and quoting them.
  - **Related skills**: `changing-prds`, `superpowers:writing-plans` and `superpowers:brainstorming`. Brainstorming decides *whether* and *what*; this skill writes the authority.

  `commands/prd-new.md`: frontmatter `description: Start a PRD for a new project (prd-toolkit)`. The body is "Invoke the prd-toolkit:authoring-prds skill and follow it exactly. $ARGUMENTS, when given, is the project slug."
- [ ] **Step 4: Re-run A1 to A4 with the plugin.** Use `claude -p "<scenario>" --plugin-dir ./prd-toolkit --setting-sources project,local < /dev/null` and record each answer under "With skill". Expected: each recorded failure is gone. For any that persists, add a red flag or a rationalization row and re-run that scenario.
- [ ] **Step 5: Commit.** Run `git commit -m "feat(prd-toolkit): authoring-prds skill and /prd-new"`.

---

### Task 12: `changing-prds` skill and `/prd-change`

**Files:**
- Create: `prd-toolkit/evals/baselines/changing-prds.md`, `prd-toolkit/skills/changing-prds/SKILL.md`, `prd-toolkit/commands/prd-change.md`

**Interfaces:**
- Consumes: the lint CLI, `prd_block.py`, and `references/prd-format.md`.
- Produces the skill `prd-toolkit:changing-prds` and the command `/prd-change <description>`.

The skill's frontmatter is pinned:

```yaml
name: changing-prds
description: Use when changing what a system does in a repo that has a docs/prd/ folder - a new feature, a changed rule or status code, a bug fix that alters behaviour, a removed requirement - or when /prd-change runs, or when an agent hits something the PRD does not say; the PRD changes first, with new IDs and a version bump, before any code
```

The baseline scenarios run in a scratch git repo holding a copy of the valid fixture at `docs/prd/orders/`:

| ID | Scenario prompt | Failure looked for |
|---|---|---|
| C1 | "getOrder should return 410 instead of 404 for deleted orders. Tiny wording fix in the PRD." | a patch or minor bump for a behaviour change (it must be major, 2.0.0); test cases and errors.yaml left stale |
| C2 | "Admins can now archive an order. FR-003 was removed, so reuse FR-003." (fixture with FR-003 `removed`) | reuses FR-003 (it must be FR-005) |
| C3 | "One-line change: also accept CSV files with a BOM. Just fix the importer, the PRD can follow." | code first, or no PRD change |
| C4 | "Drop the empty-file rule (AC-001.3), we don't need it." | deletes the AC and its T-id instead of marking them removed; no changelog row |

- [ ] **Step 1: Write the scenarios file** in the same layout as Task 11.
- [ ] **Step 2: Run the four baselines and record them verbatim.**
- [ ] **Step 3: Write `SKILL.md`.** It must contain:
  - **The five steps of spec section 5.3, verbatim in substance.** Step 2 names the test cases and the errors.yaml and openapi entries to revise. Step 4 runs lint and a dry run on the changed T-ids only, using the same subagent instruction as Task 11's phase 6.
  - **The version rule as a table**:
    - **Major**: existing behaviour changes or is removed.
    - **Minor**: behaviour is added.
    - **Patch**: wording only.
    - Worked examples: C1 is major and C2 is minor.
  - **ID rules**:
    - The next free number is the highest FR or NFR number + 1, across both kinds.
    - Removed IDs keep their row and block with status `removed`, and their test cases are deleted. The `id-removed-reused` rule enforces this.
  - **The gap rule**, as the entry point for any agent that meets PRD silence.
  - **Step 5**: after approval, rerun `prd_block.py` and flag any plan file under `docs/superpowers/plans/` that cites a changed ID.
  - **Red Flags** and **Rationalizations** from the recorded baselines.

  `commands/prd-change.md`: frontmatter `description: Change the PRD before changing behaviour (prd-toolkit)`. The body invokes `prd-toolkit:changing-prds` with `$ARGUMENTS` as the change.
- [ ] **Step 4: Re-run C1 to C4 with the plugin** as in Task 11 Step 4. Expected:
  - C1 ends at `version: 2.0.0` with a changelog row.
  - C2 creates FR-005.
  - C3 edits the PRD before any code.
  - C4 leaves AC-001.3 marked removed.
  - Lint exits 0 after each.
- [ ] **Step 5: Commit.** Run `git commit -m "feat(prd-toolkit): changing-prds skill and /prd-change"`.

---

### Task 13: Plugin eval suite

**Files:**
- Create: `prd-toolkit/evals/<case>/{prompt.md,case.yaml,scaffold.sh,graders/*.md}` for the four cases below, and `prd-toolkit/evals/BASELINE.md`

Format reference: https://code.claude.com/docs/en/plugin-evals.md. Frontmatter starts at column 0, and unknown keys are errors.

| Case | Setup | Prompt (one task, ends "Do not ask me questions.") | Graders |
|---|---|---|---|
| `authoring-new-prd` | none; `max_turns: 80`, `timeout_seconds: 1500`, `allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]` | A1 without "skip the questions", plus "mark anything you would need to ask me" | `tool_used` Skill `input_match: '"skill"\s*:\s*"(?:prd-toolkit:)?authoring-prds"'`; `tool_used` Write `input_match: 'docs/prd/[a-z0-9-]+/prd\.md'`; `tool_used` Write `input_match: 'NEEDS CLARIFICATION|ASSUMPTION A-\d'`; `tool_used` Bash `input_match: 'prd_lint\.py'` |
| `authoring-not-for-readme` | none | "Write a README.md for a small Python CLI that renames photos by EXIF date." | `tool_used` Skill with that input_match, `min: 0`, `max: 0`, `arm: both`; `file_exists` `README.md` |
| `changing-major-bump` | `scaffold.sh` copies `../../tests/fixtures/valid/orders` (resolved from `${BASH_SOURCE[0]}`) to `docs/prd/orders`, then `git init` and commits | C1, minus "tiny wording fix" | Skill fired (changing-prds); regex on `{source: file, path: docs/prd/orders/prd.md}` `version: 2\.0\.0`; regex on the same file `\|\s*2\.0\.0\s*\|` |
| `changing-new-id-not-reused` | the same scaffold, then marks FR-003 `removed` in the block and index and deletes T-003.x | C2 | Skill fired; regex on `{source: file, path: docs/prd/orders/features/api.md}` `### FR-005 `; regex on that file `### FR-003 [^\n]*[Aa]rchiv`, `match: not_contains` |

- [ ] **Step 1: Write the four cases.**
- [ ] **Step 2: Run** `claude plugin eval ./prd-toolkit --runs 1 --model sonnet --scaffold --trust-plugin --no-publish`. Expected:
  - Every `skill-fired` grader passes in the with arm.
  - No case is at Δ ≤ 0.
  - Confirm `suite.plugins[].path` in `aggregate-result.json` is the worktree's `prd-toolkit`, not the installed cache.
  - Before deciding anything from a 0.00, read the answers with `--keep-temp`. A correct answer can be followed by trailing status messages, so check the whole transcript, not just the last message.
- [ ] **Step 3: Fix any skill-description trigger misses.** Re-run only the failing case with `--case <name> --runs 3`.
- [ ] **Step 4: Record `evals/BASELINE.md`** in the acuantia layout: a with, w/out and Δ table, a note per case on what the without arm got wrong, and the gate verdict.
- [ ] **Step 5: Commit.** Run `git commit -m "test(prd-toolkit): plugin eval suite and baseline"`.

---

### Task 14: Release wiring

**Files:**
- Create: `prd-toolkit/.claude-plugin/plugin.json`, `prd-toolkit/README.md`, `prd-toolkit/NOTICE`
- Modify: `.claude-plugin/marketplace.json`, `README.md`, `CLAUDE.md`, `web/src/data/plugins.js`, `web/src/data/plugins.test.js`

`plugin.json` follows the `stl-generator-toolkit` shape: `name: prd-toolkit`, `version: 0.1.0`, the same `author`, `"skills": "./skills"` and `"commands": "./commands"`. Its description is pinned and is also used in marketplace.json:

> A living PRD as the single authority agents build, test and deploy from: a PRD folder with contracts and black-box test cases, a 27-rule linter, standards and skills registries, and skills to author and change it. Includes /prd-new and /prd-change.

- [ ] **Step 1: Write the failing web test.** In `plugins.test.js`, expect 3 plugins and `ids` to contain `'prd-toolkit'`. Run `cd web && npm ci && npm test`. Expected: FAIL on the length.
- [ ] **Step 2: Wire up the release.**
  - Add the `plugins.js` entry: commands `/prd-new` and `/prd-change`, each with a workflow string; the two skills; and a reference to the spec on GitHub.
  - Add the marketplace.json entry (`version: 0.1.0`).
  - Add a root README section.
  - In `CLAUDE.md`, under "Skill Source of Truth", add: "`prd-toolkit` is the exception: it is authored in place in this repo (its skills share scripts, templates and references and are useless apart) and is not in `sync-skills.sh`." Also name it in Project Overview.
  - `NOTICE` credits GitHub Spec Kit, cc-sdd, BMAD-METHOD and mattpocock `grilling` (MIT), and Anthropic doc-coauthoring (Apache-2.0). Copy each copyright line from that repo's own LICENSE file, never from memory.
  - `prd-toolkit/README.md` covers install, the lint CLI, the folder layout, and a link to the spec.
- [ ] **Step 3: Verify.**
  - Run `cd web && npm test`. Expected: PASS.
  - Run `uv run --directory prd-toolkit pytest -q`. Expected: all pass.
  - Run `claude plugin validate ./prd-toolkit`. Expected: no errors.
  - Run `claude -p "list your skills" --plugin-dir ./prd-toolkit --setting-sources project,local < /dev/null`. Expected: it names `prd-toolkit:authoring-prds` and `prd-toolkit:changing-prds`.
- [ ] **Step 4: Commit.** Run `git commit -m "feat(prd-toolkit): 0.1.0 release wiring"`.

---

### Task 15: Acceptance (authoring a sample project from scratch)

This is the "proven by" check for 0.1 in spec section 9. It is interactive, with Ivan answering the clarify rounds.

- [ ] **Step 1: Create the sample repo.** Create a scratch git repo at `/private/tmp/claude-502/-Users-ihistand-projects/60dd65b1-db0f-46ec-8ba7-73ba40a65c1c/scratchpad/prd-sample`. Ivan picks the project; the default is the internal link shortener from A1.
- [ ] **Step 2: Author it.** In a session started with `--plugin-dir <worktree>/prd-toolkit`, run `/prd-new` and go through all seven phases with Ivan.
- [ ] **Step 3: Verify.**
  - Lint exits 0.
  - The dry run reports zero questions on five sampled T-ids.
  - `prd_block.py --check` exits 0.
  - Status is `Approved` at `1.0.0`.
  - Every finding raised along the way is either fixed in the toolkit (with a new test case) or written down as a 0.2 item in `docs/superpowers/plans/2026-10-29-prd-toolkit-0.1-acceptance.md`.
- [ ] **Step 4: Commit the toolkit fixes and the acceptance note.** The sample repo itself stays in the scratchpad.
