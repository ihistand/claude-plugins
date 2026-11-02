"""0.7 model: links.md, upstream snapshots and change-set records."""
from conftest import lint
from linked import link, make_linked_repos
from prdlint import model

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

SQL_HEADER = "-- Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. Dialect: postgres.\n"
YAML_HEADER = "# Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. Type: cli.\n"

RECORD = """# CS-001 Show the greeting as JSON in the client

Started: 2026-11-03 in greet
Status: running
Approval: 2026-11-03, "go ahead"

| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |
|---|---|---|---|---|---|---|---|---|
| 1 | greet | `.` | cs-001-json-greeting | 1.1.0 → 1.2.0 | FR-003 | — | live in staging | live in staging |
| 2 | greet-client | `../greet-client` | cs-001-json-greeting | 1.0.0 → 1.1.0 | FR-002 | greet live in staging | verified | approved |

## Log

- 2026-11-03 greet built and verified (Refs: FR-003)
- 2026-11-03 greet deployed to staging, run 20261103-1412
"""


def put(prd, rel, text):
    p = prd / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_no_links_file(prd):
    p = model.load(prd)
    assert p.links is None and p.snapshots == {} and p.change_sets == {}


def test_links_rows(prd):
    put(prd, "links.md", LINKS)
    l = model.load(prd).links
    assert [(r.name, r.location, r.version, r.commit, r.needs) for r in l.upstreams] == [
        ("transform", "`../transform`", "2.3.0", "4f1c9a2", "live in staging")]
    assert [(r.name, r.location) for r in l.consumers] == [("dashboards", "`git@example.com:org/bi.git#docs/prd/dashboards`")]
    assert set(l.headings) == {"# Links", "## Upstreams", "## Consumers"} and l.headings["# Links"] == 1


def test_snapshot_kept_out_of_docs_and_yaml(prd):
    put(prd, "contracts/upstream/transform/schema.sql", SQL_HEADER + "CREATE TABLE t (id int);\n")
    put(prd, "contracts/upstream/transform/cli.yaml", YAML_HEADER + "greet:\n  args: []\n")
    put(prd, "contracts/upstream/transform/events.md", "<!-- Snapshot of transform 2.3.0 at 4f1c9a2, written by prd_links.py sync. Do not edit. -->\n# Events\n")
    p = model.load(prd)
    assert not any(r.startswith("contracts/upstream/") for r in list(p.docs) + list(p.yaml))
    f = {s.rel: s for s in p.snapshots["transform"]}
    assert f["contracts/upstream/transform/schema.sql"].header == {"prd": "transform", "version": "2.3.0", "commit": "4f1c9a2", "dialect": "postgres"}
    assert f["contracts/upstream/transform/schema.sql"].text == "CREATE TABLE t (id int);\n"
    assert f["contracts/upstream/transform/cli.yaml"].header["type"] == "cli" and "greet" in f["contracts/upstream/transform/cli.yaml"].data
    assert f["contracts/upstream/transform/events.md"].header == {"prd": "transform", "version": "2.3.0", "commit": "4f1c9a2"}


def test_snapshot_without_header(prd):
    put(prd, "contracts/upstream/transform/schema.sql", "CREATE TABLE t (id int);\n")
    s = model.load(prd).snapshots["transform"][0]
    assert s.header is None and s.text == "CREATE TABLE t (id int);\n"


def test_change_set_parsed(prd):
    put(prd, "changes/CS-001.md", RECORD)
    p = model.load(prd)
    cs = p.change_sets["CS-001"]
    assert "changes/CS-001.md" not in p.docs
    assert (cs.id, cs.title, cs.status, cs.started) == ("CS-001", "Show the greeting as JSON in the client", "running", "2026-11-03 in greet")
    assert cs.approvals == ['2026-11-03, "go ahead"']
    assert cs.problems == [] and len(cs.rows) == 2 and len(cs.log) == 2
    assert cs.rows[1].waits_for == "greet live in staging" and cs.rows[1].version == "1.0.0 → 1.1.0"


def test_change_set_problems(prd):
    bad = RECORD.replace("| Order | PRD |", "| Number | PRD |").replace("| 2 | greet-client | `../greet-client` | cs-001-json-greeting | 1.0.0 → 1.1.0 | FR-002 | greet live in staging | verified |", "| 2 | greet-client | `../greet-client` | cs-001-json-greeting | 1.0.0 → 1.1.0 | FR-002 | greet live in staging |")
    put(prd, "changes/CS-001.md", bad)
    cs = model.load(prd).change_sets["CS-001"]
    lines = [n for n, _ in cs.problems]
    assert lines == [7, 10] and len(cs.rows) == 1
    assert "changes/CS-001.md" not in model.load(prd).docs


def test_snapshot_dotfile_ignored_and_unreadable_reported(prd):
    put(prd, "contracts/upstream/transform/.DS_Store", "x")
    (prd / "contracts/upstream/transform/x.sql").write_bytes(b"\xff\xfe\x00bad")
    p = model.load(prd)
    assert [s.rel for s in p.snapshots["transform"]] == ["contracts/upstream/transform/x.sql"]
    assert p.snapshots["transform"][0].header is None
    assert [(f.file, f.rule, f.message) for f in p.load_findings] == [
        ("contracts/upstream/transform/x.sql", "snapshot-cited", "contracts/upstream/transform/x.sql: not a readable UTF-8 snapshot file")]


def test_snapshot_yaml_error_is_a_load_finding(prd):
    put(prd, "contracts/upstream/transform/cli.yaml", YAML_HEADER + "greet: [unclosed\n")
    p = model.load(prd)
    assert p.snapshots["transform"][0].data is None
    assert any(f.file == "contracts/upstream/transform/cli.yaml" for f in p.load_findings)


def test_parse_ref():
    assert model.parse_ref("table:transform/orders_daily") == ("table", "transform", "orders_daily")
    assert model.parse_ref("code:a/b") == ("code", None, "a/b")
    assert model.parse_ref("op:getOrder") == ("op", None, "getOrder")
    assert model.parse_ref("cli:greet/greet") == ("cli", "greet", "greet")
    assert model.parse_ref("table:Bad/x") == ("table", None, "Bad/x")


def test_level_envs(prd):
    assert model.load(prd).testing.level_envs["unit"] == "local"


def test_make_linked_repos(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE
    from legacy import git
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    orders, reports = make_linked_repos(tmp_path)
    for repo in (orders, reports):
        assert git(repo, "status", "--porcelain") == "" and git(repo, "branch", "--show-current").strip() == "main"
    assert lint(reports / "docs/prd/reports") == []
    link(reports, ["op:orders/getOrder"])
    assert (reports / "docs/prd/reports/links.md").is_file()
