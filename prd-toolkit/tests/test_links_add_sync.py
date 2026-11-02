"""prd_links.py add and sync, and the location reader (prd-toolkit 0.7, Task 4)."""
import hashlib
import os
import subprocess
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, lint
from legacy import commit, git
from linked import bare_origin, link, make_linked_repos, run_links

ROW = "| orders | `../orders` |"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def head(repo: Path, ref: str = "main") -> str:
    return git(repo, "rev-parse", ref).strip()


def upstream_row(reports: Path) -> list[str]:
    text = (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8")
    line = next(x for x in text.split("\n") if x.startswith("| orders |"))
    return [c.strip() for c in line.strip().strip("|").split("|")]


def snap(reports: Path) -> Path:
    return reports / "docs/prd/reports/contracts/upstream/orders"


def edit_orders(orders: Path, rel: str, old: str, new: str) -> None:
    p = orders / "docs/prd/orders" / rel
    text = p.read_text(encoding="utf-8")
    assert old in text
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def rule_findings(prd: Path, *rules: str):
    return [f for f in lint(prd) if f.rule in rules]


# ---------------------------------------------------------------- add

def test_add_writes_both_sides(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    r = run_links("add", reports / "docs/prd/reports", "`../orders`")
    assert r.code == 0, r.err
    assert "| orders | `../orders` |  |  |  |" in (reports / "docs/prd/reports/links.md").read_text()
    assert "| reports | `../reports` |" in (orders / "docs/prd/orders/links.md").read_text()
    for prd in (reports / "docs/prd/reports", orders / "docs/prd/orders"):
        assert rule_findings(prd, "links-format") == []


def test_add_needs_and_existing_file(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    link(reports, [])
    (reports / "docs/prd/reports/links.md").write_text(
        (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8").replace(ROW + " | | |\n", ""), encoding="utf-8")
    r = run_links("add", reports / "docs/prd/reports", "../orders", "--needs", "verified")
    assert r.code == 0, r.err
    text = (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8")
    assert "| orders | `../orders` |  |  | verified |" in text and text.count("## Upstreams") == 1
    assert rule_findings(reports / "docs/prd/reports", "links-format") == []


def test_add_url_prints_consumer_row(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    bare = bare_origin(orders)
    loc = f"`{bare.as_uri()}#docs/prd/orders`"
    r = run_links("add", reports / "docs/prd/reports", loc)
    assert r.code == 0, r.err
    assert f"| orders | {loc} |  |  |  |" in (reports / "docs/prd/reports/links.md").read_text()
    assert not (orders / "docs/prd/orders/links.md").exists()
    assert "| reports |" in r.out and "Consumers" in r.out
    assert rule_findings(reports / "docs/prd/reports", "links-format") == []


def test_add_refusals(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    prd = reports / "docs/prd/reports"
    # self-link
    r = run_links("add", prd, "`../reports`")
    assert (r.code, r.out) == (1, "") and "refused: a PRD cannot link to itself" in r.err
    assert not (prd / "links.md").exists()
    # a location with no PRD
    (tmp_path / "empty").mkdir()
    git(tmp_path / "empty", "init", "-q", "-b", "main")
    r = run_links("add", prd, "`../empty`")
    assert (r.code, r.out) == (1, "") and r.err.startswith("refused: ") and "holds no PRD" in r.err
    assert not (prd / "links.md").exists()
    # a location that does not exist
    r = run_links("add", prd, "`../nowhere`")
    assert (r.code, r.out) == (1, "") and r.err.startswith("refused: ")
    assert not (prd / "links.md").exists()
    # an existing row
    assert run_links("add", prd, "`../orders`").code == 0
    before = {p: p.read_text() for p in (prd / "links.md", orders / "docs/prd/orders/links.md")}
    r = run_links("add", prd, "`../orders`")
    assert (r.code, r.out) == (1, "") and "refused: " in r.err and "orders" in r.err
    assert {p: p.read_text() for p in before} == before


def test_add_usage(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    for args in ((), ("add",), ("add", reports / "docs/prd/reports"), ("add", reports / "docs/prd/reports", "`../orders`", "--needs", "soon")):
        r = run_links(*args)
        assert r.code == 2 and r.out == "", args
    assert not (reports / "docs/prd/reports/links.md").exists()


# ---------------------------------------------------------------- sync

def test_sync_copies_only_cited(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert r.code == 0, r.err
    files = sorted(p.name for p in snap(reports).iterdir())
    assert files == ["schema.sql"]
    sql = (snap(reports) / "schema.sql").read_text(encoding="utf-8")
    c = head(orders)
    assert sql.split("\n")[0] == f"-- Snapshot of orders 1.0.0 at {c}, written by prd_links.py sync. Do not edit. Dialect: postgres."
    assert "CREATE TABLE orders" in sql and "COMMENT ON COLUMN orders.status" in sql
    assert "CREATE TABLE customers" not in sql and "COMMENT ON TABLE customers" not in sql
    row = upstream_row(reports)
    assert row[2:4] == ["1.0.0", c]
    assert lint(reports / "docs/prd/reports") == []


def test_sync_copies_an_upstream_custom_type_the_downstream_does_not_declare(tmp_path):
    """R-10b: reports cites cli:orders/greet; only orders declares the custom type cli."""
    orders, reports = make_linked_repos(tmp_path)
    edit_orders(orders, "prd.md", "| lookml | `contracts/custom/*.lkml` |",
                "| cli | `contracts/cli.yaml` | `python3 -c \"import sys; sys.exit(0)\"` |\n| lookml | `contracts/custom/*.lkml` |")
    (orders / "docs/prd/orders/contracts/cli.yaml").write_text("greet:\n  output: a line\nbye:\n  output: another\n", encoding="utf-8")
    commit(orders, "Add the cli contract type", "docs")
    assert "| cli |" not in (reports / "docs/prd/reports/prd.md").read_text(encoding="utf-8")
    link(reports, ["cli:orders/greet"])
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert r.code == 0, r.err
    assert sorted(p.name for p in snap(reports).iterdir()) == ["cli.yaml"]
    text = (snap(reports) / "cli.yaml").read_text(encoding="utf-8")
    assert text.split("\n")[0] == f"# Snapshot of orders 1.0.0 at {head(orders)}, written by prd_links.py sync. Do not edit. Type: cli."
    assert "greet:" in text and "bye" not in text
    assert lint(reports / "docs/prd/reports") == []
    assert lint(orders / "docs/prd/orders") == []


def test_sync_reads_default_branch_not_worktree(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    edit_orders(orders, "contracts/schema.sql", "sales_rep_name text NOT NULL\n", "sales_rep_name text NOT NULL,\n  uncommitted_col int\n")
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert r.code == 0, r.err
    sql = (snap(reports) / "schema.sql").read_text(encoding="utf-8")
    assert "uncommitted_col" not in sql and "sales_rep_name" in sql
    assert upstream_row(reports)[3] == head(orders)


def test_sync_reads_origin_head_when_set(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    bare_origin(orders)
    pushed = head(orders)
    link(reports, ["table:orders/orders"])
    edit_orders(orders, "contracts/schema.sql", "sales_rep_name text NOT NULL\n", "sales_rep_name text NOT NULL,\n  unpushed_col int\n")
    commit(orders, "Local only", "docs")
    assert head(orders) != pushed
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert r.code == 0, r.err
    assert "unpushed_col" not in (snap(reports) / "schema.sql").read_text(encoding="utf-8")
    assert upstream_row(reports)[3] == pushed


def test_sync_ref(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    git(orders, "checkout", "-q", "-b", "cs-001-x")
    edit_orders(orders, "contracts/schema.sql", "sales_rep_name text NOT NULL\n", "sales_rep_name text NOT NULL,\n  region text\n")
    edit_orders(orders, "prd.md", "version: 1.0.0", "version: 1.1.0")
    commit(orders, "Add region", "docs")
    branch = head(orders, "cs-001-x")
    git(orders, "checkout", "-q", "main")
    r = run_links("sync", reports / "docs/prd/reports", "orders", "--ref", "cs-001-x")
    assert r.code == 0, r.err
    sql = (snap(reports) / "schema.sql").read_text(encoding="utf-8")
    assert "region text" in sql and f"orders 1.1.0 at {branch}," in sql
    assert upstream_row(reports)[2:4] == ["1.1.0", branch]


def test_sync_unknown_ref(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    r = run_links("sync", reports / "docs/prd/reports", "orders", "--ref", "no-such-branch")
    assert (r.code, r.out) == (1, "") and r.err.startswith("refused: ") and "no-such-branch" in r.err
    assert not snap(reports).exists()


def test_sync_missing_item_writes_nothing(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders", "table:orders/nope"])
    links_before = (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8")
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert (r.code, r.out) == (1, "") and r.err.startswith("refused: ") and "table:nope" in r.err
    assert (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8") == links_before
    assert not snap(reports).exists()


def test_sync_asyncapi_item_not_citable(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    (orders / "docs/prd/orders/contracts/asyncapi.yaml").write_text(
        "asyncapi: 3.0.0\ninfo: {title: Orders events, version: 1.0.0}\nchannels:\n  order_shipped:\n    address: orders.shipped\n", encoding="utf-8")
    commit(orders, "Add asyncapi", "docs")
    link(reports, ["event:orders/order_shipped"])
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert (r.code, r.out) == (1, "") and "refused: event:order_shipped: asyncapi items cannot be cited across repositories" in r.err
    assert not snap(reports).exists()


@pytest.mark.parametrize("rename_folder", [True, False])
def test_sync_wrong_prd_at_location(tmp_path, rename_folder):
    orders, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    edit_orders(orders, "prd.md", "prd: orders", "prd: billing")
    if rename_folder:
        git(orders, "mv", "docs/prd/orders", "docs/prd/billing")
    commit(orders, "Rename the PRD", "docs")
    links_before = (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8")
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert (r.code, r.out) == (1, "") and "refused: `../orders` holds PRD billing, not orders" in r.err
    assert (reports / "docs/prd/reports/links.md").read_text(encoding="utf-8") == links_before
    assert not snap(reports).exists()


def test_sync_wrong_prd_at_url(tmp_path):
    orders, reports = make_linked_repos(tmp_path)
    edit_orders(orders, "prd.md", "prd: orders", "prd: billing")
    commit(orders, "Rename the PRD", "docs")
    loc = f"`{bare_origin(orders).as_uri()}#docs/prd/orders`"
    link(reports, ["table:orders/orders"])
    p = reports / "docs/prd/reports/links.md"
    p.write_text(p.read_text(encoding="utf-8").replace("`../orders`", loc), encoding="utf-8")
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert (r.code, r.out) == (1, "") and f"refused: {loc} holds PRD billing, not orders" in r.err
    assert not snap(reports).exists()
    from prdlint import links
    with pytest.raises(links.Refused, match="holds PRD billing, not orders"):
        links.open_side(reports, links.parse_location(loc), expect="orders")


def test_sync_removes_uncited_files(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders", "op:orders/getOrder"])
    assert run_links("sync", reports / "docs/prd/reports", "orders").code == 0
    assert sorted(p.name for p in snap(reports).iterdir()) == ["openapi.yaml", "schema.sql"]
    cases = reports / "docs/prd/reports/test-cases/api.yaml"
    cases.write_text(cases.read_text(encoding="utf-8").replace("target: op:orders/getOrder", "target: table:orders/customers"), encoding="utf-8")
    r = run_links("sync", reports / "docs/prd/reports", "orders")
    assert r.code == 0, r.err
    assert sorted(p.name for p in snap(reports).iterdir()) == ["schema.sql"]
    assert "openapi.yaml" in r.out
    assert "CREATE TABLE customers" in (snap(reports) / "schema.sql").read_text(encoding="utf-8")
    assert lint(reports / "docs/prd/reports") == []


def test_sync_unknown_upstream(tmp_path):
    _, reports = make_linked_repos(tmp_path)
    link(reports, ["table:orders/orders"])
    r = run_links("sync", reports / "docs/prd/reports", "billing")
    assert (r.code, r.out) == (1, "") and "refused: no Upstreams row 'billing'" in r.err


def _tree(root: Path, skip: Path) -> dict[str, tuple[int, int]]:
    out = {}
    for dirpath, _, names in os.walk(root):
        if Path(dirpath).is_relative_to(skip):
            continue
        for n in names:
            p = Path(dirpath) / n
            st = p.lstat()
            out[p.relative_to(root).as_posix()] = (st.st_mtime_ns, st.st_size)
    return out


def test_cache_dir_only(tmp_path, monkeypatch):
    orders, reports = make_linked_repos(tmp_path)
    bare = bare_origin(orders)
    url = bare.as_uri()
    link(reports, ["table:orders/orders"])
    p = reports / "docs/prd/reports/links.md"
    p.write_text(p.read_text(encoding="utf-8").replace("`../orders`", f"`{url}#docs/prd/orders`"), encoding="utf-8")
    cache = tmp_path / "cache"
    for _ in range(2):  # the first run clones, the second fetches
        before = _tree(tmp_path, cache)
        r = run_links("sync", reports / "docs/prd/reports", "orders")
        assert r.code == 0, r.err
        after = _tree(tmp_path, cache)
        changed = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
        assert changed <= {"reports/docs/prd/reports/links.md", "reports/docs/prd/reports/contracts/upstream/orders/schema.sql"}
    assert "reports/docs/prd/reports/contracts/upstream/orders/schema.sql" in after
    entries = list((cache / "prd-toolkit/links").iterdir())
    assert [e.name for e in entries] == [hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]]
    assert not any(x.name == ".git" for x in entries[0].rglob(".git"))
    assert upstream_row(reports)[3] == head(orders)
    assert lint(reports / "docs/prd/reports") == []


# ---------------------------------------------------------------- the location reader

def test_parse_location():
    from prdlint import links

    loc = links.parse_location("`../orders`")
    assert (loc.path, loc.url, loc.folder) == ("../orders", None, None)
    loc = links.parse_location("`git@example.com:org/bi.git#docs/prd/dashboards`")
    assert (loc.path, loc.url, loc.folder) == (None, "git@example.com:org/bi.git", "docs/prd/dashboards")
    for bad in ("../orders", "`https://example.com/x.git`", "`https://example.com/x.git#`", "``"):
        with pytest.raises(ValueError):
            links.parse_location(bad)


def test_git_calls_are_bounded(tmp_path, monkeypatch):
    from prdlint import links

    seen = {}
    real = subprocess.Popen

    def spy(cmd, *a, **kw):
        seen.setdefault("env", kw.get("env"))
        return real(cmd, *a, **kw)

    orders, _ = make_linked_repos(tmp_path)
    monkeypatch.setattr(subprocess, "Popen", spy)
    monkeypatch.setenv("PRD_LINKS_TIMEOUT", "7")
    side = links.open_side(tmp_path / "reports", links.parse_location("`../orders`"), expect="orders")
    assert side.default_branch() == "main" and side.commit("main") == git(orders, "rev-parse", "main").strip()
    assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert links._timeout() == 7
