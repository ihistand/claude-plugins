"""0.7 lint rules: links-format, upstream-refs, snapshot-cited, change-sets, and the prefix in test-refs and schema-refs."""
import pytest
from conftest import Case, lint
from linked import add_cases, link, make_linked_repos
from prdlint import model, snapshot
from prdlint.registry import RULES

HEAD = "-- Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. Dialect: postgres.\n"
SQL = "CREATE TABLE orders_daily (id int, total int);\nCREATE TABLE customers (id int);\n"
RULES4 = ("links-format", "upstream-refs", "snapshot-cited", "change-sets")


def links_md(upstreams="| transform | `../transform` | 2.3.0 | 4f1c9a2 | live in staging |", consumers="", headings=("# Links", "## Upstreams", "## Consumers"),
             header="| Upstream | Location | Version | Commit | Needs |"):
    out = []
    for h in headings:
        out.append(h + "\n")
        if h == "## Upstreams":
            out.append(f"\n{header}\n|---|---|---|---|---|\n{upstreams}\n")
        elif h == "## Consumers":
            out.append(f"\n| Consumer | Location |\n|---|---|\n{consumers}\n")
    return "\n".join(out)


def put(prd, rel, text):
    p = prd / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def setup(prd, cited=("table:transform/orders_daily", "table:transform/customers"), links=None, sql=SQL):
    put(prd, "links.md", links if links is not None else links_md())
    put(prd, "contracts/upstream/transform/schema.sql", HEAD + sql)
    add_cases(prd, list(cited))


def found(prd, *rules):
    rules = rules or RULES4
    return [(f.rule, f.message) for f in lint(prd) if f.rule in rules]


def test_baseline_is_clean(prd):
    setup(prd)
    assert lint(prd) == []


def test_rule_count():
    import prdlint.rules  # noqa: F401

    from test_coverage import SPEC_RULES

    assert len(RULES) == len(SPEC_RULES) and set(RULES4) <= set(RULES)


# ---- links-format

@pytest.mark.parametrize("missing", ["# Links", "## Upstreams", "## Consumers"])
def test_missing_heading(prd, missing):
    setup(prd, links=links_md(headings=tuple(h for h in ("# Links", "## Upstreams", "## Consumers") if h != missing)))
    assert ("links-format", f'links.md: missing heading "{missing}"') in found(prd)


def test_upstreams_header(prd):
    setup(prd, links=links_md(header="| Upstream | Location | Version | Commit |"))
    f = [(f.line, f.message) for f in lint(prd) if f.rule == "links-format"]
    assert any(m == "links.md:%d: Upstreams header must be | Upstream | Location | Version | Commit | Needs |" % n for n, m in f), f


@pytest.mark.parametrize("row,message", [
    ("| Transform | `../transform` | | | |", "upstream 'Transform' is not a PRD slug"),
    ("| transform | `../a` | | | |\n| transform | `../b` | | | |", "upstream 'transform' appears twice"),
    ("| transform | ../transform | | | |", "location must be a backticked path or a backticked <git URL>#<folder>"),
    ("| transform | `git@example.com:org/x.git` | | | |", "location must be a backticked path or a backticked <git URL>#<folder>"),
    ("| transform | `../t` | 2.3 | 4f1c9a2 | |", "version '2.3' must be X.Y.Z"),
    ("| transform | `../t` | 2.3.0 | xyz | |", "commit 'xyz' must be 7-40 hex digits"),
    ("| transform | `../t` | 2.3.0 | | |", "version and commit are both set or both empty"),
    ("| transform | `../t` | | 4f1c9a2 | |", "version and commit are both set or both empty"),
    ("| transform | `../t` | | | deployed |", "needs 'deployed' must be verified or live in <env>"),
])
def test_row_findings(prd, row, message):
    setup(prd, links=links_md(upstreams=row))
    assert ("links-format", message) in found(prd, "links-format")


@pytest.mark.parametrize("row", [
    "| transform | `../transform` | | | |",
    "| transform | `git@example.com:org/x.git#docs/prd/transform` | 2.3.0 | 4f1c9a2e | verified |",
    "| transform | `https://example.com/org/x.git#docs/prd/transform` | 2.3.0 | 4f1c9a2 | live in staging |",
])
def test_row_passes(prd, row):
    setup(prd, links=links_md(upstreams=row))
    assert found(prd, "links-format") == []


def test_consumer_location(prd):
    setup(prd, links=links_md(consumers="| dashboards | bad |"))
    assert ("links-format", "location must be a backticked path or a backticked <git URL>#<folder>") in found(prd)


# ---- upstream-refs

def test_target_names_no_row(prd):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "table:other/orders_daily"])
    assert found(prd, "upstream-refs") == [("upstream-refs", "T-002.5: target table:other/orders_daily names no Upstreams row 'other'")]


def test_target_absent_from_snapshot(prd):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "table:transform/nope"])
    assert found(prd, "upstream-refs") == [("upstream-refs", "T-002.5: target table:transform/nope: no table 'nope' in the transform snapshot")]


CLI_HEAD = "# Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. Type: cli.\n"


def test_upstream_custom_type_resolves_from_the_snapshot_header(prd):
    """R-10b: the downstream does not declare the upstream's custom type; the snapshot header's Type: names it."""
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "cli:transform/greet"])
    put(prd, "contracts/upstream/transform/cli.yaml", CLI_HEAD + "greet:\n  output: a line\n")
    assert [f for f in lint(prd)] == []


@pytest.mark.parametrize("snap,message", [
    (None, "T-002.5: target cli:transform/greet: no cli 'greet' in the transform snapshot"),
    ("bye:\n  output: a line\n", "T-002.5: target cli:transform/greet: no cli 'greet' in the transform snapshot"),
])
def test_upstream_custom_target_absent_from_snapshot(prd, snap, message):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "cli:transform/greet"])
    if snap is not None:
        put(prd, "contracts/upstream/transform/cli.yaml", CLI_HEAD + snap)
    assert ("upstream-refs", message) in found(prd, "upstream-refs")


@pytest.mark.parametrize("kind", ["component", "page"])
def test_prefixed_target_of_a_kind_that_never_crosses(prd, kind):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", f"{kind}:transform/x"])
    assert found(prd, "upstream-refs") == [
        ("upstream-refs", f"T-002.5: target {kind}:transform/x: kind '{kind}' does not cross repositories")]


def test_sufficiency_leaves_a_prefixed_custom_kind_to_upstream_refs(prd):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "cli:transform/greet", "nope:greet"])
    msgs = [m for _, m in found(prd, "sufficiency")]
    assert not any("target kind 'cli' is unknown" in m for m in msgs), msgs
    assert any(m.startswith("T-002.6: target kind 'nope' is unknown") for m in msgs), msgs


# ---- R-10c: without links.md every target is judged as before 0.7 (findings taken from main's prd_lint.py)

def test_without_links_md_slug_like_targets_and_traces_are_not_prefixed(prd):
    add_cases(prd, ["page:admin/users", "component:checkout/Cart"])
    p = prd / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Traces: FR-002, FR-003", "Traces: FR-002, FR-003, see:docs/x", 1), encoding="utf-8")
    assert not (prd / "links.md").exists()
    assert [(f.rule, f.message) for f in lint(prd)] == []


def test_without_links_md_prefix_like_targets_keep_their_old_findings(prd):
    add_cases(prd, ["table:transform/orders_daily", "cli:greet/greet"])
    assert [(f.rule, f.message) for f in lint(prd)] == [
        ("test-refs", "T-002.3: target table:transform/orders_daily: no table 'transform/orders_daily' in contracts/schema.sql"),
        ("sufficiency", "T-002.4: target kind 'cli' is unknown (known: code, component, event, job, lookml, op, page, table)"),
    ]


def test_with_links_md_a_slug_like_traces_token_is_a_citation(prd):
    setup(prd)
    p = prd / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Traces: FR-002, FR-003", "Traces: FR-002, FR-003, see:docs/x", 1), encoding="utf-8")
    assert found(prd, "upstream-refs") == [("upstream-refs", "UJ-01: target see:docs/x names no Upstreams row 'docs'")]


def test_op_and_event_absent(prd):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "op:transform/getX", "event:transform/gone"])
    assert {m for _, m in found(prd, "upstream-refs")} == {
        "T-002.5: target op:transform/getX: no op 'getX' in the transform snapshot",
        "T-002.6: target event:transform/gone: no event 'gone' in the transform snapshot"}


def test_traces_token(prd):
    setup(prd)
    api = prd / "features/api.md"
    api.write_text(api.read_text(encoding="utf-8").replace("Traces: FR-002, FR-003", "Traces: FR-002, `table:transform/nope`, table:other/x"), encoding="utf-8")
    assert sorted(found(prd, "upstream-refs")) == [
        ("upstream-refs", "UJ-01: target table:other/x names no Upstreams row 'other'"),
        ("upstream-refs", "UJ-01: target table:transform/nope: no table 'nope' in the transform snapshot")]


def test_prose_span_column(prd):
    setup(prd)
    api = prd / "features/api.md"
    api.write_text(api.read_text(encoding="utf-8") + "\nThe feed reads `transform/orders_daily.total` and `transform/orders_daily.amount`.\n", encoding="utf-8")
    fs = found(prd, "upstream-refs", "schema-refs", "test-refs")
    assert fs == [("upstream-refs", "`transform/orders_daily.amount`: no column 'amount' in table orders_daily in the transform snapshot")]


def test_prose_path_stays_prose(prd):
    setup(prd)
    api = prd / "features/api.md"
    api.write_text(api.read_text(encoding="utf-8") + "\nSee `src/importer.py` and `other/orders.id`.\n", encoding="utf-8")
    assert lint(prd) == []


def test_test_refs_ignores_prefixed(prd):
    setup(prd, cited=["table:transform/orders_daily", "table:transform/customers", "table:other/x"])
    assert found(prd, "test-refs") == []


def test_unprefixed_still_checked(prd):
    setup(prd)
    p = prd / "test-cases/api.yaml"
    p.write_text(p.read_text(encoding="utf-8").replace("target: op:getOrder", "target: op:getOrderX", 1), encoding="utf-8")
    assert any(r == "test-refs" for r, _ in found(prd, "test-refs"))


def test_no_links_file_target_is_judged_as_before_0_7(prd):
    """R-10c: without links.md a slug-like target is not prefixed; test-refs judges it as main does."""
    add_cases(prd, ["table:transform/x"])
    assert found(prd, "upstream-refs") == []
    assert found(prd, "test-refs") == [("test-refs", "T-002.3: target table:transform/x: no table 'transform/x' in contracts/schema.sql")]


# ---- snapshot-cited

def test_item_cited_nowhere(prd):
    setup(prd, cited=["table:transform/orders_daily"])
    assert found(prd, "snapshot-cited") == [("snapshot-cited", "contracts/upstream/transform/schema.sql: table customers is cited nowhere")]


def test_snapshot_without_row(prd):
    setup(prd)
    put(prd, "contracts/upstream/billing/schema.sql", HEAD + "CREATE TABLE b (id int);\n")
    assert ("snapshot-cited", "contracts/upstream/billing/: no Upstreams row 'billing'") in found(prd, "snapshot-cited")


def test_row_cited_nowhere(prd):
    setup(prd, cited=[])
    assert ("snapshot-cited", "Upstreams row 'transform' is cited nowhere") in found(prd, "snapshot-cited")


def test_no_header(prd):
    setup(prd)
    put(prd, "contracts/upstream/transform/schema.sql", SQL)
    assert ("snapshot-cited", "contracts/upstream/transform/schema.sql: no snapshot header line") in found(prd, "snapshot-cited")


def test_prose_does_not_fire_in_snapshot_or_record(prd):
    setup(prd)
    marker = "-- [NEEDS CLARIFICATION: x] [ASSUMPTION: y] TODO\n"
    put(prd, "contracts/upstream/transform/schema.sql", HEAD + SQL + marker)
    put(prd, "contracts/upstream/transform/extra.yaml", "# Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. Type: cli.\n# [NEEDS CLARIFICATION: x] TODO\n")
    put(prd, "changes/CS-001.md", RECORD.replace("go ahead", "TODO later [NEEDS CLARIFICATION: x] [ASSUMPTION: y]"))
    assert [f for f in lint(prd) if f.rule in ("placeholder", "markers-open", "assumption-indexed", "vague-word")] == []


# ---- change-sets

RECORD = """# CS-001 Show the greeting as JSON

Started: 2026-11-03 in orders
Status: running
Approval: 2026-11-03, "go ahead"

| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |
|---|---|---|---|---|---|---|---|---|
| 1 | greet | `.` | cs-001-json | 1.1.0 → 1.2.0 | FR-003 | — | live in staging | live in staging |
| 2 | greet-client | `../greet-client` | cs-001-json | 1.0.0 | FR-002, FR-004 | greet live in staging; greet verified | verified | approved |

## Log

- 2026-11-03 greet built

## Merge order

1. greet (cs-001-json)
"""


def record(prd, text, name="CS-001"):
    if not (prd / "links.md").is_file():  # R-10c: change-sets runs only in a linked PRD
        put(prd, "links.md", links_md(upstreams=""))
    put(prd, f"changes/{name}.md", text)


def cs(prd):
    return [(f.rule, f.message) for f in lint(prd) if f.rule == "change-sets"]


def test_record_baseline(prd):
    record(prd, RECORD)
    assert lint(prd) == []


@pytest.mark.parametrize("old,new", [
    ("Status: running", "Status: stopped: greet-client: tests red"),
    ("Status: running", "Status: done"),  # row 2 below overrides
    ("Status: running", "Status: abandoned"),
    ('"go ahead"', '"go ahead" (amendment)'),
    ("| 1.0.0 |", "| 1.0.0 → 1.1.0 |"),
    ("| FR-002, FR-004 |", "| — |"),
])
def test_accepted_forms(prd, old, new):
    record(prd, RECORD.replace(old, new).replace("| verified | approved |", "| verified | verified |"))
    assert cs(prd) == []


def test_problems_reported(prd):
    record(prd, RECORD.replace("Started: 2026-11-03 in orders", "Started: yesterday"))
    assert any(m == "Started must read `YYYY-MM-DD in <prd>`" for _, m in cs(prd))


def test_status_outside_grammar(prd):
    record(prd, RECORD.replace("Status: running", "Status: paused"))
    assert ("change-sets", "CS-001: status 'paused' is outside the grammar") in cs(prd)


def test_state_outside_grammar(prd):
    record(prd, RECORD.replace("| live in staging | live in staging |", "| live in staging | deployed |"))
    assert ("change-sets", "CS-001: row greet: state 'deployed' is outside the grammar") in cs(prd)


def test_order(prd):
    record(prd, RECORD.replace("| 2 | greet-client", "| 3 | greet-client"))
    assert ("change-sets", "CS-001: Order must be 1, 2, … in table order") in cs(prd)


def test_defined_twice(prd):
    record(prd, RECORD)
    record(prd, RECORD.replace("# CS-001", "# CS-001", 1), name="CS-002")
    assert ("change-sets", "CS-001 is defined twice") in cs(prd)


def test_done_but_not_target(prd):
    record(prd, RECORD.replace("Status: running", "Status: done"))
    assert ("change-sets", "CS-001: Status done, but row greet-client is approved, not its target verified") in cs(prd)


def test_missing_lines(prd):
    record(prd, RECORD.replace("Started: 2026-11-03 in orders\n", "").replace("Status: running\n", "Status: running\nStatus: done\n").replace("## Log", "## Notes"))
    ms = {m for _, m in cs(prd)}
    assert {"CS-001: no Started: line", "CS-001: Status: appears twice", "CS-001: no ## Log section"} <= ms


def test_missing_status(prd):
    record(prd, RECORD.replace("Status: running\n", ""))
    assert ("change-sets", "CS-001: no Status: line") in cs(prd)


# ---- the linked repositories

def test_linked_repos_lint_clean(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    orders, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    prd = reports / "docs/prd/reports"
    o = model.load(orders / "docs/prd/orders")
    version = o.frontmatter["version"]
    body = snapshot.extract(snapshot.contracts_of(o), {("table", "orders")})
    for name, text in body.items():
        put(prd, f"contracts/upstream/orders/{name}", snapshot.header(name, "orders", version, "abcdef1", dialect=o.frontmatter.get("sql-dialect")) + "\n" + text)
    links = (prd / "links.md").read_text(encoding="utf-8").replace("| orders | `../orders` | | | |", f"| orders | `../orders` | {version} | abcdef1 | |")
    (prd / "links.md").write_text(links, encoding="utf-8")
    assert lint(prd) == []


def test_scan_would_fire_outside_snapshot(prd):
    setup(prd)
    put(prd, "contracts/extra.sql", "-- [NEEDS CLARIFICATION: x]\n")
    assert any(f.rule == "markers-open" for f in lint(prd))


def _with(root, **kw):
    setup(root, **kw)


CASES = [
    Case("links-format", "missing-consumers", lambda r: _with(r, links=links_md(headings=("# Links", "## Upstreams")))),
    Case("upstream-refs", "absent-item", lambda r: _with(r, cited=["table:transform/nope"])),
    Case("snapshot-cited", "uncited-item", lambda r: _with(r, cited=["table:transform/orders_daily"])),
    Case("change-sets", "unknown-status", lambda r: record(r, RECORD.replace("Status: running", "Status: paused"))),
]
