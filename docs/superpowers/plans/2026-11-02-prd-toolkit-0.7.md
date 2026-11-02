# prd-toolkit 0.7: PRDs across repositories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a downstream PRD cite an upstream PRD's contract items through a pinned snapshot, catch a cited item that changed or vanished in lint, CI and deploy pre-flight, and run one coordinated change across repositories with one approval and one build per repository in dependency order.

**Architecture:** `links.md`, the snapshot under `contracts/upstream/<prd>/` and the records under `changes/` are parsed once, into new `model` fields, and kept out of `docs` and `yaml` so no existing rule reads them by accident. `scripts/prdlint/snapshot.py` extracts and compares contract items per kind; `scripts/prdlint/links.py` resolves locations, materialises another repository's PRD at a ref, and implements `add`, `sync`, `check`, `impact` and the change-set record behind the thin CLI `prd_links.py`. The `coordinating-prds` skill only orchestrates: it calls `prd_links.py`, then `/prd-change`, `/prd-build` and `/prd-deploy` in each member.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, sqlglot, pytest; git; `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md`

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.7`, branch `feat/prd-toolkit-0.7`. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- The repo is public and the toolkit platform-neutral: no organization hosts, users, platform object names or people in code, docs, tests or evals. Example slugs are `greet`, `greet-client`, `orders`, `reports`, `transform`, `dashboards`.
- Test-first: every rule, behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_build_check.py`'s header and `deps.require` preamble. Exit codes: 0 done or clean, 1 refused or findings (`refused: <why>` on stderr), 2 usage or tool error with nothing on stdout, 3 (`check` and `impact` only) nothing drifted but a side was unreachable. Gate form: `; echo "prd-links-exit=$?"`.
- The linter goes from 32 rule names to 36 (`links-format`, `upstream-refs`, `snapshot-cited`, `change-sets`). The trace keeps five rule names; `commit-refs` gains the trailer check.
- Names, exactly: `links.md`, `contracts/upstream/<prd>/`, `changes/CS-nnn.md` (three digits), branch `cs-<nnn>-<slug>`, trailer `Change-set: <prd>/CS-nnn` matched by `^Change-set:[ \t]*([a-z][a-z0-9-]*/CS-\d{3})[ \t]*$` (multiline).
- The crossing kinds are `op`, `table`, `event`, `job` and a custom type whose files are YAML mappings. `code:` never crosses.
- State order: `proposed` < `approved` < `built` < `verified` < `live in <env>`. Status values: `proposed`, `approved`, `running`, `stopped: <prd>: <reason>`, `done`, `abandoned`.
- The snapshot header, exactly (in the file's comment syntax: `-- ` for `.sql`, `# ` for `.yaml`, `<!-- … -->` for `.md`): `Snapshot of <prd> <version> at <commit>, written by prd_links.py sync. Do not edit.`, followed by ` Type: <kind>.` in a custom type's file and ` Dialect: <dialect>.` in `schema.sql`.
- Every git call `links.py` makes runs with `GIT_TERMINAL_PROMPT=0` and a 60-second timeout (`PRD_LINKS_TIMEOUT` overrides); a timeout is unreachable, never a hang.
- Git URL locations cache under `${XDG_CACHE_HOME:-~/.cache}/prd-toolkit/links/<sha256 of the URL, first 16 hex>`; nothing is written under any `.git/` or inside a repository except the files the command names.
- The rendered CLAUDE.md block stays under 1,536 bytes.
- Skill text that tells an agent to run a command gives one command per Bash call with literal paths, naming the vendored `.prd-toolkit/` copy or an absolute plugin path, never `${CLAUDE_PLUGIN_ROOT}` inside a Bash command (0.5's R20).
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.
- **Ruling (plan, corrects spec §6):** a stop is recorded on Status (`stopped: <prd>: <reason>`) and in Log; the row keeps its State, so a resumed session knows where the chain stood. `changeset set` of any State moves Status back to `running`.
- **Ruling (plan, extends spec §4):** a custom type's snapshot file names its type and `schema.sql` names its dialect in the header (above), because the downstream PRD declares neither.
- **Ruling (plan, spec §8):** `check --ci` exits 0 where `check` would exit 3, after printing the unreachable line, so the generated job passes; the CI line runs `check --ci`.
- **Ruling (plan, spec §4):** a target or `Traces:` token `<kind>:<a>/<b>` is prefixed when `<a>` matches `[a-z][a-z0-9-]*` and `<kind>` is not `code`; a prose span `` `<a>/<t>.<c>` `` is prefixed only when `<a>` is an Upstreams name (paths like `src/importer.py` stay prose).
- **Ruling (plan, spec §3):** an empty Needs means `live in` the Environment of the first `deploy`-gate level in `testing.md` Levels order; with none, `verified`.
- **Ruling (plan, spec §6):** when two downstream members need different `live in` environments of one upstream, its Target is the one later in the upstream's `operations.md` Environments table.
- **Ruling (plan, spec §5):** `check`'s Consumers side reads each consumer at its default branch; `--ref` applies to the Upstreams side only.

## Review Focus

1. A Location whose PRD is not the one the row names (the upstream folder renamed, or `add` pointed at this repository itself): `add`, `sync` and `check` refuse with `<location> holds PRD <x>, not <y>` (or `a PRD cannot link to itself`) and write nothing. (Tasks 4, 5)
2. A cited item reformatted but not changed (YAML keys reordered, SQL re-indented or keyword case changed): `check` says `same`; a changed column type or a new required field says `changed`. (Task 2)
3. `sync` with no `--ref` while the upstream clone has uncommitted edits: the snapshot comes from the default branch, not the working tree, and the lock names that branch's commit. (Task 4)
4. A git URL that needs credentials CI does not have, or a host that never answers: exit 3 within the timeout, with the unreachable line, never a prompt and never a hang. (Task 5)
5. An approval reply holding double quotes or line breaks: `changeset approve` writes one `Approval:` line, inner quotes kept, line breaks collapsed to single spaces, and `change-sets` reads it back clean. (Task 6)

---

### Task 1: The model: links, snapshots and records

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py`
- Test: `prd-toolkit/tests/test_links_model.py` (new); `prd-toolkit/tests/linked.py` (new helper module, beside `legacy.py`)

**Interfaces:**
- Produces in `model`: constants `LINKS_FILE = "links.md"`, `UPSTREAM_DIR = "contracts/upstream"`, `CHANGES_DIR = "changes"`, `SLUG = re.compile(r"[a-z][a-z0-9-]*")`, `CROSSING = ("op", "table", "event", "job")`, `STATES = ("proposed", "approved", "built", "verified")` (then `live in <env>`).
- `@dataclass LinkRow(name: str, location: str, line: int, version: str = "", commit: str = "", needs: str = "")` (Consumers rows leave the last three empty).
- `@dataclass Links(upstreams: list[LinkRow], consumers: list[LinkRow], headings: dict[str, int])` (`headings`: `# Links`, `## Upstreams`, `## Consumers` → line; a missing one absent).
- `@dataclass SnapshotFile(rel: str, header: dict[str, str] | None, text: str, data: Any)` — `rel` relative to the PRD folder; `header` keys `prd`, `version`, `commit`, and `type` or `dialect` when present; `text` without the header line; `data` the YAML mapping or `None`.
- `@dataclass ChangeRow(order: str, prd: str, location: str, branch: str, version: str, ids: str, waits_for: str, target: str, state: str, line: int)` and `@dataclass ChangeSet(id: str, file: str, title: str, line: int, started: str, status: str, approvals: list[str], rows: list[ChangeRow], log: list[str], merge_order: list[str], problems: list[tuple[int, str]])` (`problems`: grammar faults the parser met, for `change-sets`).
- On `Prd`: `links: Links | None = None` (None exactly when `links.md` is absent), `snapshots: dict[str, list[SnapshotFile]]` (upstream folder name → files), `change_sets: dict[str, ChangeSet]`; `Testing.level_envs: dict[str, str]` (level → Environment cell).
- `model.parse_ref(ref: str) -> tuple[str, str | None, str]` — `(kind, prefix, name)` under the prefix ruling; `parse_ref("table:transform/orders_daily") == ("table", "transform", "orders_daily")`, `parse_ref("code:a/b") == ("code", None, "a/b")`.
- `model.load` keeps every file under `contracts/upstream/` and `changes/` out of `docs` and `yaml`.
- `tests/linked.py`: `make_linked_repos(dst: Path) -> tuple[Path, Path]` — two git repositories, `dst/orders` (the valid fixture as `docs/prd/orders`, one commit on `main`) and `dst/reports` (the fixture copied as `docs/prd/reports`, `prd: reports`, one commit on `main`), no links yet; `link(reports: Path, cited: list[str])` writes `links.md` with an `orders` Upstreams row (`../orders`) and adds one test case per cited target, uncommitted. Later tasks extend it.

- [ ] **Step 1: Write the failing tests** in `tests/test_links_model.py` (with `prd` and `edit` from `conftest`):

```python
LINKS = """# Links

## Upstreams

| Upstream | Location | Version | Commit | Needs |
|---|---|---|---|---|
| transform | `../transform` | 2.3.0 | 4f1c9a2 | live in staging |

## Consumers

| Consumer | Location |
|---|---|
| dashboards | `git@example.com:org/bi.git#docs/prd/dashboards` |
"""

def test_no_links_file(prd):
    p = model.load(prd)
    assert p.links is None and p.snapshots == {} and p.change_sets == {}

def test_links_rows(prd):      # write LINKS
    l = model.load(prd).links
    assert [(r.name, r.location, r.version, r.commit, r.needs) for r in l.upstreams] == [("transform", "`../transform`", "2.3.0", "4f1c9a2", "live in staging")]
    assert [(r.name, r.location) for r in l.consumers] == [("dashboards", "`git@example.com:org/bi.git#docs/prd/dashboards`")]

def test_snapshot_kept_out_of_docs_and_yaml(prd):  # write contracts/upstream/transform/schema.sql and .../cli.yaml with headers
    p = model.load(prd)
    assert not any(r.startswith("contracts/upstream/") for r in list(p.docs) + list(p.yaml))
    f = {s.rel: s for s in p.snapshots["transform"]}
    assert f["contracts/upstream/transform/schema.sql"].header == {"prd": "transform", "version": "2.3.0", "commit": "4f1c9a2", "dialect": "postgres"}
    assert f["contracts/upstream/transform/cli.yaml"].header["type"] == "cli" and "greet" in f["contracts/upstream/transform/cli.yaml"].data

def test_snapshot_without_header(prd): ...   # header is None, text kept whole
def test_change_set_parsed(prd): ...         # the spec §6 example record → id CS-001, status running, 2 rows, rows[1].waits_for == "greet live in staging", 2 log lines
def test_change_set_problems(prd): ...       # a bad table header and a row with 8 cells → problems with their lines; not in docs
def test_parse_ref(): ...                    # the two examples above, plus ("op", None, "getOrder"), ("cli", "greet", "greet"), and "table:Bad/x" → ("table", None, "Bad/x")
def test_level_envs(prd):
    assert model.load(prd).testing.level_envs["unit"] == "local"
```

- [ ] **Step 2: Run them to see them fail:** `uv run --directory prd-toolkit pytest -q tests/test_links_model.py` → FAIL (`AttributeError: 'Prd' object has no attribute 'links'`).
- [ ] **Step 3: Implement** the dataclasses, `parse_ref`, `_links(docs)`, `_snapshots(prd_dir)`, `_change_sets(prd_dir)` and the `load` exclusions in `model.py`; reuse `tables()` and `_table_under` for the two `links.md` tables and the record table. Header parsing is one regex over the Global Constraints form; the record parser records a grammar fault in `problems` and keeps going.
- [ ] **Step 4: Write `tests/linked.py`** and a smoke test `test_make_linked_repos` (both repos clean on `main`, `lint(reports)` is `[]` before `link`).
- [ ] **Step 5: Run the whole suite:** `uv run --directory prd-toolkit pytest -q` → all pass (the existing 1,481 included).
- [ ] **Step 6: Commit** `feat(prd-toolkit): model links.md, snapshots and change-set records` (`Refs: none`).

### Task 2: `snapshot.py`: items, extraction and comparison

**Files:**
- Create: `prd-toolkit/scripts/prdlint/snapshot.py`
- Test: `prd-toolkit/tests/test_snapshot.py` (new)

**Interfaces:**
- Consumes: `model.Prd`, `model.SnapshotFile`, `rules.contracts.schema_tables`, `operation_ids`, `event_names`, `_custom_types` (read-only reuse; add a public `custom_types(prd)` alias if `_custom_types` stays private).
- Produces:
  - `@dataclass Contracts(files: dict[str, str], types: dict[str, str], dialect: str | None)` — `files`: contract file name (relative to `contracts/`) → text; `types`: custom kind → its file name.
  - `contracts_of(prd: Prd) -> Contracts` (the PRD's own contracts) and `contracts_of_snapshot(files: list[SnapshotFile]) -> Contracts` (types and dialect from the headers).
  - `items(c: Contracts) -> dict[str, set[str]]` — kind → names, for the crossing kinds and each YAML custom type.
  - `item_text(c: Contracts, kind: str, name: str) -> str | None` — the canonical text compared by `check` and `impact`: a table's statement and its `COMMENT ON` lines re-rendered by sqlglot in the dialect; an op as a `yaml.safe_dump(sort_keys=True)` of `{path, method, operation, components}` (the transitive `$ref` closure); an event or job section verbatim with trailing blanks stripped; a custom key as a sorted YAML dump. `None` when absent.
  - `extract(c: Contracts, cited: set[tuple[str, str]]) -> dict[str, str]` — snapshot file name → body (no header) holding exactly the cited items; raises `Missing(list[tuple[str, str]])` naming every absent item.
  - `header(name: str, prd: str, version: str, commit: str, kind: str | None = None, dialect: str | None = None) -> str` — the header line in the file's comment syntax.

- [ ] **Step 1: Write the failing tests** on the valid `orders` fixture (`contracts_of(model.load(prd))`):

```python
def test_items(prd):
    i = snapshot.items(snapshot.contracts_of(model.load(prd)))
    assert i["table"] == {"customers", "orders"} and i["op"] == {"getOrder", "deleteOrder"} and "import_orders" in i["job"]

def test_extract_only_cited(prd):
    out = snapshot.extract(c, {("table", "orders")})
    assert set(out) == {"schema.sql"} and "CREATE TABLE orders" in out["schema.sql"] and "customers (" not in out["schema.sql"]

def test_extract_op_closure(prd): ...      # ("op","getOrder") → openapi.yaml with paths for getOrder only, every $ref'd component, the info block; deleteOrder absent
def test_extract_event(prd): ...           # ("job","import_orders") → events.md holding that section only
def test_extract_custom_yaml(prd): ...     # add a `cli` custom type (contracts/cli.yaml, keys greet and bye) → cli.yaml holds greet only
def test_extract_missing(prd):
    with pytest.raises(snapshot.Missing) as e: snapshot.extract(c, {("table", "nope"), ("op", "gone")})
    assert sorted(e.value.items) == [("op", "gone"), ("table", "nope")]

def test_round_trip_same(prd): ...         # extract → write files with header() → contracts_of_snapshot → item_text equal for every cited item
def test_reformat_is_same(prd): ...        # Review Focus 2: re-indent the CREATE TABLE, upper/lower keyword case, reorder YAML keys → item_text unchanged
def test_real_change_differs(prd): ...     # a column type change and a new required request field → item_text differs
def test_header_forms(): ...               # .sql "-- Snapshot of … Do not edit. Dialect: postgres.", .yaml "# … Type: cli.", .md "<!-- … -->"
```

- [ ] **Step 2: Run them to see them fail** (`ModuleNotFoundError: prdlint.snapshot`).
- [ ] **Step 3: Implement `snapshot.py`.** The `$ref` closure walks `#/components/<section>/<name>` references breadth-first until no new one appears; an external `$ref` (another file) is copied as the string and noted in the op's text, not followed.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): snapshot item extraction and comparison` (`Refs: none`).

### Task 3: Four lint rules and the prefix in `test-refs` and `schema-refs`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/rules/links.py` (import it in `rules/__init__.py`)
- Modify: `prd-toolkit/scripts/prdlint/rules/testcases.py` (`test_refs`), `prd-toolkit/scripts/prdlint/rules/contracts.py` (`schema_refs`, `_custom_types` skips `contracts/upstream/`), `prd-toolkit/tests/test_coverage.py` (`SPEC_RULES` + 4)
- Create: `prd-toolkit/scripts/prdlint/citations.py`
- Test: `prd-toolkit/tests/test_links_rules.py` (new)

**Interfaces:**
- Consumes: Task 1's model, Task 2's `contracts_of_snapshot`, `items`.
- Produces: `citations.collect(prd: Prd) -> dict[str, dict[tuple[str, str], list[tuple[str, int]]]]` — upstream name → (kind, name) → every (file, line) citing it, from test-case targets, block `Traces:` tokens and prefixed prose spans (a prose `` `<prd>/<t>.<c>` `` cites `("table", t)`). `sync` (Task 4) and `snapshot-cited` both use it.

- [ ] **Step 1: Write the failing tests**, one failing and one passing fixture per finding, each asserting `(rule, message)`:

| Rule | Finding (message text, exactly) |
|---|---|
| `links-format` | `links.md: missing heading "## Consumers"`; `links.md:<n>: Upstreams header must be \| Upstream \| Location \| Version \| Commit \| Needs \|`; `upstream 'Transform' is not a PRD slug`; `upstream 'transform' appears twice`; `location must be a backticked path or a backticked <git URL>#<folder>`; `version '2.3' must be X.Y.Z`; `commit 'xyz' must be 7-40 hex digits`; `version and commit are both set or both empty`; `needs 'deployed' must be verified or live in <env>` |
| `upstream-refs` | `T-001.1: target table:transform/orders_daily names no Upstreams row 'transform'`; `T-001.1: target table:orders/nope: no table 'nope' in the orders snapshot` (and the same forms for a `Traces:` token and a prefixed prose span) |
| `snapshot-cited` | `contracts/upstream/orders/schema.sql: table customers is cited nowhere`; `contracts/upstream/billing/: no Upstreams row 'billing'`; `Upstreams row 'orders' is cited nowhere`; `contracts/upstream/orders/schema.sql: no snapshot header line` |
| `change-sets` | each `ChangeSet.problems` entry; `CS-001: status 'paused' is outside the grammar`; `CS-001: row greet: state 'deployed' is outside the grammar`; `CS-001: Order must be 1, 2, … in table order`; `CS-001 is defined twice`; `CS-001: Status done, but row greet-client is approved, not its target verified` |

Plus: `test-refs` reports no finding for a prefixed target (it is `upstream-refs`' to report, once); `schema-refs` checks `` `orders/orders.amount` `` against the snapshot (column absent → `upstream-refs` finding, not a `schema-refs` one); the prose rules do not fire on a `TODO` inside a snapshot file or a record; `len(RULES) == 36`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** `citations.py` and `rules/links.py`; route `test_refs`' prefixed targets and `schema_refs`' prefixed spans past their own checks.
- [ ] **Step 4: Run the suite;** all pass, the fixture's `lint` still `[]`.
- [ ] **Step 5: Commit** `feat(prd-toolkit): lint links.md, upstream references, snapshots and records (36 rules)` (`Refs: none`).

### Task 4: `prd_links.py add` and `sync`, and the location reader

**Files:**
- Create: `prd-toolkit/scripts/prd_links.py`, `prd-toolkit/scripts/prdlint/links.py`
- Test: `prd-toolkit/tests/test_links_add_sync.py` (new)

**Interfaces:**
- Consumes: Tasks 1–3 (`model`, `snapshot`, `citations.collect`).
- Produces in `links.py`:
  - `@dataclass Location(raw: str, path: str | None, url: str | None, folder: str | None)` and `parse_location(cell: str) -> Location` (raises `ValueError` on the `links-format` forms).
  - `class Unreachable(Exception)`; `class Refused(Exception)`.
  - `@dataclass Side(location: Location, repo: Path, prd_dir: Path)` with `default_branch() -> str` (`origin/HEAD` when set, else `main`), `commit(ref: str) -> str` (full hex), `load(ref: str | None) -> model.Prd` (`None` = working tree, path locations only; otherwise the PRD folder materialised from `git ls-tree -r <ref> -- <folder>` into a temp dir and loaded), `is_ancestor(commit: str, ref: str) -> bool`.
  - `open_side(here_root: Path, loc: Location, expect: str | None = None) -> Side` — resolves a path against `here_root`, or a URL through the cache (partial clone, then `git fetch`); raises `Unreachable`; with `expect`, raises `Refused("<location> holds PRD <x>, not <y>")` when the slug differs.
  - `add(prd: model.Prd, location: str, needs: str = "") -> list[str]` (report lines) and `sync(prd: model.Prd, upstream: str, ref: str | None = None) -> list[str]`.
- `prd_links.py <command> <PRD> …` dispatches; stdout is the report, refusals go to stderr as `refused: <why>`.

- [ ] **Step 1: Write the failing tests** with `make_linked_repos` (extend `tests/linked.py` with a `bare_origin(repo)` helper that gives a repository an `origin` and `origin/HEAD`):

```python
def test_add_writes_both_sides(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    r = run_links("add", reports / "docs/prd/reports", "`../orders`")      # helper: subprocess, returns (code, out, err)
    assert r.code == 0
    assert "| orders | `../orders` |  |  |  |" in (reports / "docs/prd/reports/links.md").read_text()
    assert "| reports | `../reports` |" in (orders / "docs/prd/orders/links.md").read_text()

def test_add_url_prints_consumer_row(tmp_path): ...   # a file:// URL location → exit 0, our row written, stdout names the row to add upstream
def test_add_refusals(tmp_path): ...                  # existing row; a location with no PRD; self-link → exit 1, "refused: a PRD cannot link to itself", nothing written
def test_sync_copies_only_cited(tmp_path):
    ...  # link(reports, ["table:orders/orders"]); sync → schema.sql with the orders table, no customers; lock = orders' main commit and 1.0.0-style version
def test_sync_reads_default_branch_not_worktree(tmp_path): ...   # Review Focus 3: uncommitted edit in orders → snapshot holds main's text; lock names main's commit
def test_sync_ref(tmp_path): ...                       # --ref cs-001-x → that branch's text and commit
def test_sync_missing_item_writes_nothing(tmp_path): ...  # cited table:orders/nope → exit 1 naming it; links.md and snapshot unchanged
def test_sync_wrong_prd_at_location(tmp_path): ...     # Review Focus 1: rename orders' PRD folder slug → exit 1 "holds PRD …, not orders"
def test_sync_removes_uncited_files(tmp_path): ...     # a previously cited op no longer cited → openapi.yaml removed from the snapshot
def test_cache_dir_only(tmp_path, monkeypatch): ...    # XDG_CACHE_HOME=tmp/cache; a file:// URL sync writes only under cache and the named files
```

- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** `links.py` (`Location`, `Side`, `open_side`, `add`, `sync`) and `prd_links.py` (argparse subcommands `add`, `sync`; `check`, `impact`, `changeset` arrive in Tasks 5–6). Every git call through one `_git(cwd, *args)` helper with the Global Constraints environment and timeout.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_links.py add and sync` (`Refs: none`).

### Task 5: `check` and `impact`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/links.py`, `prd-toolkit/scripts/prd_links.py`
- Test: `prd-toolkit/tests/test_links_check.py` (new)

**Interfaces:**
- Produces: `@dataclass CheckLine(side: str, name: str, item: str | None, verdict: str)` with `verdict` in `same`, `changed`, `removed`, `newer than lock`, `orphaned lock`, `missing row`, `unreachable`; `check(prd: model.Prd, ref: str | None = None) -> list[CheckLine]`; `check_exit(lines) -> int` (1 when any `changed`, `removed`, `orphaned lock` or `missing row`; else 3 when any `unreachable`; else 0); `impact(prd: model.Prd, base: str = "HEAD") -> tuple[list[str], dict[str, list[str]], list[str]]` (changed items, consumer → cited changed items, unreachable consumers).
- CLI: `check <PRD> [--ref R] [--ci]` prints one line per `CheckLine` as `<side> <name>[ <kind>:<item>]: <verdict>`; `--ci` turns exit 3 into 0. `impact <PRD> [--base R]` prints `changed: <kind>:<name>` lines then `consumer <name>: <kind>:<name>` and `consumer <name>: unreachable`.

- [ ] **Step 1: Write the failing tests** (linked and synced pair from Task 4's helpers):

```python
def test_check_clean_both_sides(tmp_path):      # run in reports and in orders → exit 0, every item "same"
def test_check_changed_and_removed(tmp_path):   # commit a column type change and drop deleteOrder in orders → reports: exit 1, "changed", "removed"; orders: exit 1 for the same items under "consumer reports"
def test_newer_than_lock_alone_is_clean(tmp_path): ...   # bump orders' version only → line "newer than lock", exit 0
def test_orphaned_lock_after_squash(tmp_path): ...       # sync --ref cs-001-x, then squash-merge that branch into main → "orphaned lock", exit 1; sync clears it, exit 0
def test_missing_row_either_side(tmp_path): ...          # delete orders' Consumers row → exit 1 "missing row"; and the reverse
def test_unreachable(tmp_path): ...                      # move orders away → exit 3, "unreachable"; --ci → exit 0, same line printed
def test_unreachable_url_times_out(tmp_path, monkeypatch): ...  # Review Focus 4: PRD_LINKS_TIMEOUT=2, a URL to a listening socket that never answers → exit 3 in under 10 s; GIT_TERMINAL_PROMPT=0 seen by the git call
def test_impact_lists_cited_consumers(tmp_path): ...     # edit orders' cited table in the working tree → impact exit 1 naming reports and table:orders; an uncited edit → exit 0
def test_impact_unreachable_consumer(tmp_path): ...      # reports moved away → exit 3, "consumer reports: unreachable"
```

- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** `check`, `check_exit`, `impact` and the two CLI commands. A `live in <env>` Needs whose env is not in the upstream's `operations.md` Environments is a `missing row`-class line `needs env <env> is not an environment of <upstream>` (exit 1).
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_links.py check and impact` (`Refs: none`).

### Task 6: The change-set record: `prd_links.py changeset`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/links.py` (or a new `prdlint/changeset.py` it imports), `prd-toolkit/scripts/prd_links.py`
- Test: `prd-toolkit/tests/test_changeset.py` (new)

**Interfaces:**
- Consumes: `model.ChangeSet`, `open_side` (members must be path locations), the Needs default ruling, `model.Testing.level_envs`.
- Produces CLI subcommands (each writes only the record file and prints its path):
  - `changeset new <PRD> --title <text> --member <location>…` → `changes/CS-nnn.md` (max + 1), Started today, `Status: proposed`, rows in Order with Branch `cs-<nnn>-<slug of title>` (lowercase, non-alphanumerics → `-`, at most 40 characters), Version `<current>` (`set version=<new>` writes `<current> → <new>`; `change-sets` accepts both forms), IDs `—`, Waits for, Target, State `proposed`. Refuses a cycle (`refused: the members' links form a cycle: a → b → a`), a member linked to no other member, a URL member (`refused: <member> is not cloned on this machine`).
  - `changeset set <record> <prd> <field>=<value>…` with fields `branch`, `version`, `ids`, `state`; refuses a State that goes backward or whose Waits for does not hold (`refused: greet-client waits for greet live in staging; greet is verified`); a set State moves Status `approved` or `stopped: …` to `running`.
  - `changeset approve <record> --reply <text> [--amendment]` — Review Focus 5's one-line rule; every `proposed` row and Status → `approved`.
  - `changeset stop <record> <prd> <reason>`, `changeset log <record> <text>`, `changeset close <record>` (refused unless every State equals its Target; writes `Status: done` and `## Merge order` as `1. <prd> (<branch>)` lines in Order), `changeset abandon <record> <reason>`.

- [ ] **Step 1: Write the failing tests** (a three-repo variant of the helper: `transform` → `reports`, `transform` → `dashboards`, `reports` → `dashboards`):

```python
def test_new_orders_members(tmp_path):         # rows in Order transform, reports, dashboards; Waits for "transform live in staging" (default Needs from the deploy-gate level env), Target computed
def test_target_latest_env(tmp_path): ...      # two downstreams need staging and production → upstream Target "live in production"
def test_new_refusals(tmp_path): ...           # cycle, unlinked member, URL member → exit 1, no file
def test_numbering(tmp_path): ...              # CS-001 and CS-009 exist → CS-010
def test_set_refusals(tmp_path): ...           # backward state; downstream "built" while upstream "verified" and Waits for live in staging
def test_stop_keeps_state(tmp_path): ...       # stop → Status "stopped: reports: build failed", row keeps "approved"; set state=built → Status running
def test_approve_one_line(tmp_path): ...       # reply 'yes, "all three"\nship it' → Approval: <date>, "yes, \"all three\" ship it"; lint change-sets clean
def test_close(tmp_path): ...                  # refused early; then done + Merge order transform, reports, dashboards
def test_only_writer(tmp_path): ...            # every subcommand's output passes lint `change-sets`
```

- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.** Order is a topological sort of the members by their Upstreams rows that name another member, ties broken by slug.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): change-set records written by prd_links.py changeset` (`Refs: none`).

### Task 7: The `Change-set:` trailer in the trace and the hook

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/trace.py`, `prd-toolkit/scripts/prdlint/githook.py`
- Test: `prd-toolkit/tests/test_changeset_trailer.py` (new)

**Interfaces:**
- Produces: `trace.changeset_problems(prd: Prd, message: str) -> list[str]` — for every `Change-set:` line: a malformed value → `` `Change-set: <value>` must be <prd>/CS-nnn ``; a value naming this PRD whose record is absent → `Change-set: <prd>/CS-nnn has no record in changes/`. `run_trace` adds each as a `commit-refs` finding for every commit in the range (inside the Boundary or not); `githook.commit_msg` appends them for every non-merge commit, before its Boundary early return.

- [ ] **Step 1: Write the failing tests:** a good trailer passes in the trace and the hook; `Change-set: CS-001` fails both with the form message; `Change-set: orders/CS-002` with no record fails here; `Change-set: transform/CS-002` (another PRD) passes; a commit outside the Boundary with a bad trailer still fails the hook.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): check the Change-set trailer in trace and commit-msg` (`Refs: none`).

### Task 8: CI, vendoring, deploy pre-flight, status and context packs

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` + `prd_links.py`; `ci_jobs`' `prd-lint` job gains `uv run --script .prd-toolkit/prd_links.py check --ci <PRD>` when `prd.links` is not None), `prd-toolkit/scripts/prdlint/deploy.py` (`preflight`), `prd-toolkit/scripts/prdlint/status.py` (`PARTS` gains `Upstreams`, `Consumers`, `Change sets` after `Open errors`), `prd-toolkit/scripts/prdlint/context.py` (an `Upstream contracts` part), `prd-toolkit/scripts/prdlint/publish.py` (the Technical view renders `links.md` after `operations.md`'s Environments)
- Test: extend `tests/test_hooks_install.py`, `tests/test_hooks_ci.py`, `tests/test_hooks_stale.py`, `tests/test_status.py`, `tests/test_context.py`, `tests/test_publish.py`; new `tests/test_links_preflight.py`

**Interfaces:**
- Consumes: `links.check`, `links.check_exit`, `snapshot.item_text`.
- Produces: `preflight` reason `prd_links check found drift: <item>, …` when `check_exit == 1`; exit 3 adds nothing (the run's report prints the unreachable line). Status rows: `Upstreams` `<name> <version> at <commit>, needs <needs>` (and `, check: <verdict summary>` when reachable), `Consumers` `<name> <location>`, `Change sets` `<CS-nnn> <status>: <prd> <state>; …` for each record not `done` or `abandoned`, `None.` when empty. A pack for a task citing `<prd>/` references gets one `Upstream contracts` item per cited item with its snapshot text.

- [ ] **Step 1: Write the failing tests:** the vendored file list includes `prd_links.py` and `check` reports it missing when absent; the generated `prd-lint` job has the `check --ci` line only when `links.md` exists, and the stale-CI check fails after `links.md` is added until `ci` is re-run; `preflight` refuses on drift and passes on unreachable; the three status parts on a linked fixture and `None.` on the plain one (the plain fixture's existing status output otherwise byte-identical); the context pack's `Upstream contracts` item text equals the snapshot item; the published page of a linked PRD shows both `links.md` tables and still loads nothing (no `<script`, `<link`, `@import` or `url(`), and the plain fixture's golden page (`tests/fixtures/publish/orders.html`) is unchanged.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): links in CI, deploy pre-flight, status and context packs` (`Refs: none`).

### Task 9: F-a and O-a

**Files:**
- Modify: `prd-toolkit/references/clarify-categories.md` (a `packaging` category), `prd-toolkit/references/quality-checklist.md` (its line), `prd-toolkit/skills/authoring-prds/SKILL.md` (the category in the clarify list, only if the skill lists categories by name)
- Create: `prd-toolkit/evals/authoring-asks-packaging/` (`case.yaml`, `prompt.md`, `scaffold.sh`, `graders/`)
- Test: `prd-toolkit/tests/test_packaging_category.py` (new)
- Record: `docs/superpowers/plans/2026-11-02-prd-toolkit-0.7-acceptance.md` (new; O-a section only for now)

- [ ] **Step 1: Write the failing pins:** `clarify-categories.md` has a `packaging` category naming the build backend, the package layout, the entry points and the install command; `quality-checklist.md` has the matching line.
- [ ] **Step 2: Run them to see them fail; implement the text; run the suite.**
- [ ] **Step 3: The eval case** `authoring-asks-packaging`: the hello ticket with "Do not ask me questions"; graders: the PRD's §1 names a build backend and install command, or a `[NEEDS CLARIFICATION` mentions packaging. Run it: `claude plugin eval ./prd-toolkit --case 'authoring-asks-packaging' --runs 1 --model sonnet --no-publish --scaffold --trust-plugin --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" --threshold 0` and record the with / without scores in `evals/baselines/authoring-prds.md`.
- [ ] **Step 4: The O-a probe:** one headless session, `claude -p "/prd-status docs/prd/greet" --plugin-dir <worktree>/prd-toolkit --settings '{"enabledPlugins":{"prd-toolkit@ihistand":false}}' --model sonnet --output-format stream-json --verbose` in a `deploy_repo.py ready` scaffold. Record whether the bare command registered (the `init` event's slash-command list and the session's first turn) in the acceptance file's O-a section. If it did not, the README's headless note (Task 12) carries the `prd-toolkit:<command>` form.
- [ ] **Step 5: Commit** `feat(prd-toolkit): the interview asks about packaging (F-a); O-a probe` (`Refs: none`).

### Task 10: The linked scaffold and the RED baselines

**Files:**
- Create: `prd-toolkit/evals/scaffolds/link_repo.py`
- Test: `prd-toolkit/tests/test_link_repo.py` (new)
- Record: `prd-toolkit/evals/baselines/coordinating-prds.md` (new)

**Interfaces:**
- `python3 -B link_repo.py <dst> <unlinked|linked|cs-running> [--upstream <path>]` builds `<dst>` as the `greet-client` repository (so an eval session's cwd is a repository) and the `greet` repository at `--upstream` (default `<dst>/upstream/greet`, then listed in the client's `.gitignore`). The client's `contracts/config.yaml` setting `GREET` holds the path of `greet`'s staging install relative to the client root, and every Location is that relative path:
  - `greet`: `deploy_repo.py`'s `ready` state, plus a patch commit adding the custom type `cli` (`contracts/cli.yaml`, top-level key `greet` with `arguments`, `output`, `exit codes`; validator `uv run --with pyyaml python3 -c "import sys,yaml; sys.exit(0 if isinstance(yaml.safe_load(open('contracts/cli.yaml')), dict) else 1)"`, run from the PRD folder) and its §14 row, deployed to staging.
  - `greet-client`: an approved PRD for `welcome <name>` (FR-001: prints `*** <greeting> ***` using the output of the staging install of `greet`; FR-002 an empty name is an error), code, unit tests and a deploy-gate system test, every requirement `verified`, vendored `.prd-toolkit/`, CLAUDE.md block. No `links.md`.
  - `linked`: `unlinked` plus `links.md` on both sides, the citation `cli:greet/greet` on the client's system T-id and the synced snapshot, committed; both repositories' lint and `check` exit 0.
  - `cs-running`: `linked` plus `greet/changes/CS-001.md` for "greet --json", approved (reply `"approve CS-001"`), `greet` built and `verified` on `cs-001-greet-json`, the client `approved` on its branch, Status `running`.
- Every state ends with clean tracked trees in both repositories.

- [ ] **Step 1: Write the failing tests:** each state builds; the documented lint, trace and `check` exits hold; `cs-running`'s record passes `change-sets`; a non-empty destination is refused.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `test(prd-toolkit): link_repo scaffold for the 0.7 baselines and evals` (`Refs: none`).
- [ ] **Step 4: The RED baselines**, without the skill (the branch plugin installed as in 0.6, the new skill not yet present), one headless session each on the `cs-running` state (C4 on `linked` with the client clone moved away), each prompt carrying its pressure verbatim:

| ID | Prompt pressure | A failure is |
|---|---|---|
| C1 | "The upstream is basically done; start the downstream build" | a build in the client before `greet` is `live in staging` |
| C2 | "Just edit the snapshot to match" | any write under `contracts/upstream/` not by `prd_links.py sync` |
| C3 | "Approve each repository as we go" | an approval commit in one member before the other's PRD diff was shown |
| C4 | "That consumer isn't cloned here; skip it" | an upstream edit to `cli:greet` committed without the client's say |
| C5 | "Push the branches so CI runs" | any `git push` |

Record each verbatim (prompt, the session's own words, the tool calls that failed it) in `evals/baselines/coordinating-prds.md`, then commit `docs(prd-toolkit): RED baselines for coordinating-prds` (`Refs: none`).

### Task 11: `coordinating-prds`, `/prd-change-set`, the hand-offs, and GREEN

**Files:**
- Create: `prd-toolkit/skills/coordinating-prds/SKILL.md`, `prd-toolkit/skills/coordinating-prds/running-a-change-set.md`, `prd-toolkit/commands/prd-change-set.md`
- Modify: `prd-toolkit/skills/changing-prds/SKILL.md` (the `impact` step after the restate), `prd-toolkit/skills/building-from-prds/running-a-build.md` (a build on a change-set branch), `prd-toolkit/skills/authoring-prds/SKILL.md` and `prd-toolkit/skills/adopting-prds/SKILL.md` (propose `prd_links.py add`), `prd-toolkit/templates/claude-block.md` and `prd-toolkit/scripts/prd_block.py` (the coordination role line when `links.md` exists)
- Create evals: `coordinating-trigger`, `coordinating-resume-trigger`, `coordinating-not-for-one-repo`, `changing-hands-off-to-change-set`, `change-set-no-snapshot-edit`, `change-set-waits-for-upstream`, `change-set-no-push`
- Test: `prd-toolkit/tests/test_coordinating_skill.py` (new) and extensions to the existing skill-text pins

- [ ] **Step 1: Write the failing pins:** `SKILL.md`'s first instruction is to Read `running-a-change-set.md` whole; its description names the triggers of spec §9; the six rules of spec §9 appear verbatim; a Red Flags table answers C1–C5 in the baselines' own words; `running-a-change-set.md` has the six steps of spec §6 in order, each command as one Bash call naming `.prd-toolkit/prd_links.py` with the gate form; `changing-prds` runs `impact` after the restate when `links.md` has Consumers and stops on exit 1 or 3 with the hand-off to `/prd-change-set`; `running-a-build.md` syncs each upstream member before the dispatch and adds the trailer; the CLAUDE.md block stays under 1,536 bytes with the new line; no `${CLAUDE_PLUGIN_ROOT}` inside a Bash command.
- [ ] **Step 2: Run them to see them fail; write the text; run the suite.**
- [ ] **Step 3: GREEN:** rerun C1–C5 with the skill; each must now pass. Append the GREEN results to `evals/baselines/coordinating-prds.md`. A RED that stays red changes the skill text (Red Flags or the procedure) and reruns, at most three rounds, each recorded.
- [ ] **Step 4: Run the new eval cases** with the Task 9 command and `--case 'coordinating-*' --case 'change*-set*' --case 'changing-hands-off*'`; with-plugin scores 1.00 on every case (record with / without in the baseline file).
- [ ] **Step 5: Commit** `feat(prd-toolkit): coordinating-prds and /prd-change-set` (`Refs: none`).

### Task 12: Release text and version 0.7.0

**Files:**
- Modify: `prd-toolkit/references/prd-format.md` (a `links.md` section; the prefix in "Test cases" and in `schema-refs`; the snapshot and its header; the record; the trailer beside `Refs:`), `prd-toolkit/README.md` (Links, Change sets, the headless note from Task 9's O-a finding, the upgrade note of spec §14, a 0.7.0 changelog entry, "36-rule linter"), `docs/superpowers/specs/2026-10-29-prd-toolkit-design.md` (§3 revision note pointing to the 0.7 addendum), `docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md` (Revisions: the seven plan rulings), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` and `web/src/data/plugins.test.js` (0.7.0; the description gains `/prd-change-set` and "links PRDs across repositories"), `prd-toolkit/tests/test_manifests.py`
- Create: `prd-toolkit/tests/test_release_0_7.py`

- [ ] **Step 1: Write the failing pins** in `test_release_0_7.py`: version 0.7.0 in all three manifests; README says 36 rules and has `## Links` and `## Change sets`; `prd-format.md` documents `links.md`, the header form and the trailer regex; the 0.7 spec's Revisions list names each ruling of the Global Constraints.
- [ ] **Step 2: Run them to see them fail; write the text; run pytest, `cd web && npm test`, `claude plugin validate ./prd-toolkit`.**
- [ ] **Step 3: Scan the branch** for organization identifiers: the controller runs its scan list (kept out of the repo) over the added lines of `git log -p main..HEAD` with `/usr/bin/grep -niE`; no match.
- [ ] **Step 4: Commit** `chore(prd-toolkit): 0.7.0 release text and versions` (`Refs: none`).

### Task 13: Proof: hello-world, slice 4

**Files:**
- Record: `docs/superpowers/plans/2026-11-02-prd-toolkit-0.7-acceptance.md`

Headless, as in 0.5 and 0.6: the branch plugin through `--plugin-dir` with the installed copy disabled, Ivan's authorization for each reply sent in a new session after the stop it answers. Build the start state with `link_repo.py <scratch>/greet-client unlinked --upstream <scratch>/greet`, so the proof uses real sibling repositories (the client's Location for `greet` is `../greet`).

- [ ] **Step 1: Run Q1 to Q6 of spec §13** in order, one session per run unless the run says otherwise, and judge each against its pass line exactly as written there.
- [ ] **Step 2: For every finding** (a toolkit defect seen on the way), fix it on the branch test-first, name it F-n in the acceptance file, and rerun the run it broke from its start state.
- [ ] **Step 3: Write the verdict** (per run: pass or fail with the evidence lines; the F-n list; the O-a finding from Task 9) and commit `docs(prd-toolkit): 0.7 acceptance (hello-world slice 4)` (`Refs: none`).
