"""prd-toolkit 0.7 final review, minor items 3-8 and 11."""
import os
import sys
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, lint
from legacy import commit
from linked import run_links
from test_links_check import change_orders, op, rp, synced


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def _append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


# ---------------------------------------------------------------- 3: a prose path under an upstream's name

def test_prose_path_with_a_file_extension_is_not_a_table(tmp_path):
    """`orders/cli.py` names a file in the upstream's repository, not column `py` of table `cli`."""
    orders, reports = synced(tmp_path)
    _append(rp(reports) / "features/api.md", "\nThe client calls `orders/cli.py` and reads `orders/notes.md`.\n")
    assert [f.message for f in lint(rp(reports)) if f.rule == "upstream-refs"] == []
    r = run_links("sync", rp(reports), "orders")
    assert r.code == 0, r.err
    from prdlint import citations, model

    assert ("table", "cli") not in citations.collect(model.load(rp(reports))).get("orders", {})


def test_prose_table_citation_still_counts(tmp_path):
    orders, reports = synced(tmp_path)
    _append(rp(reports) / "features/api.md", "\nThe report reads `orders/missing.amount`.\n")
    assert any("missing" in f.message for f in lint(rp(reports)) if f.rule == "upstream-refs")


# ---------------------------------------------------------------- 4: table names are case-insensitive

def test_table_citation_case_insensitive_in_lint_and_sync(tmp_path):
    orders, reports = synced(tmp_path, ["table:orders/Orders", "op:orders/getOrder"])
    snap = rp(reports) / "contracts/upstream/orders/schema.sql"
    assert "CREATE TABLE orders" in snap.read_text(encoding="utf-8")
    assert [f.message for f in lint(rp(reports)) if f.rule in ("upstream-refs", "snapshot-cited")] == []
    r = run_links("check", rp(reports))
    assert r.code == 0 and "upstream orders table:orders: same" in r.out, r


# ---------------------------------------------------------------- 6: impact's exits, and git that cannot run

def test_impact_refused_is_a_tool_error(tmp_path):
    orders, reports = synced(tmp_path)
    r = run_links("impact", op(orders), "--base", "no-such-ref")
    assert (r.code, r.out) == (2, ""), r
    assert r.err.startswith("prd_links: ") and "no-such-ref" in r.err, r.err
    links_md = op(orders) / "links.md"
    links_md.write_text(links_md.read_text(encoding="utf-8").replace("| reports | `../reports` |", "| orders | `../reports` |"),
                        encoding="utf-8")
    r = run_links("impact", op(orders))
    assert (r.code, r.out, r.err.strip()) == (2, "", "prd_links: a PRD cannot link to itself"), r


def test_impact_still_exits_1_when_a_consumer_cites_a_changed_item(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    r = run_links("impact", op(orders), "--base", "HEAD~1")
    assert r.code == 1, r


@pytest.mark.parametrize("args", [
    ("check", "{reports}"),
    ("impact", "{orders}"),
    ("sync", "{reports}", "orders"),
    ("add", "{reports}", "../dashboards"),
])
def test_git_that_cannot_run_is_a_tool_error(tmp_path, args):
    orders, reports = synced(tmp_path)
    (tmp_path / "dashboards").mkdir()
    empty = tmp_path / "no-git"
    empty.mkdir()
    env = {**os.environ, "PATH": str(empty)}
    argv = [a.format(reports=rp(reports), orders=op(orders)) for a in args]
    r = run_links(*argv, env=env)
    assert (r.code, r.out) == (2, ""), (argv, r)
    assert r.err.startswith("prd_links: git cannot run"), r.err


# ---------------------------------------------------------------- 7: no links.md, no 0.7 folder handling

def test_without_links_changes_folder_lints_as_on_main(prd):
    (prd / "changes").mkdir()
    (prd / "changes/notes.md").write_text("# Notes\n\nTODO: write these.\n", encoding="utf-8")
    (prd / "changes/CS-001.md").write_text("# CS-001 x\n\nStatus: paused\n", encoding="utf-8")
    found = lint(prd)
    assert any(f.rule == "placeholder" and f.file == "changes/notes.md" for f in found), [(f.rule, f.file) for f in found]
    assert [f for f in found if f.rule == "change-sets"] == []


def test_without_links_upstream_folder_lints_as_on_main(prd):
    from prdlint import model

    d = prd / "contracts/upstream/transform"
    d.mkdir(parents=True)
    (d / "notes.md").write_text("# Notes\n\nTODO: later.\n", encoding="utf-8")
    loaded = model.load(prd)
    assert "contracts/upstream/transform/notes.md" in loaded.docs
    assert loaded.snapshots == {}
    found = lint(prd)
    assert any(f.rule == "placeholder" and f.file == "contracts/upstream/transform/notes.md" for f in found)
    assert [f for f in found if f.rule == "snapshot-cited"] == []


def test_trailer_check_stays_universal(prd):
    """A PRD without links.md still has its records read, so a `Change-set:` trailer naming one resolves."""
    from prdlint import model

    (prd / "changes").mkdir()
    (prd / "changes/CS-001.md").write_text("# CS-001 x\n", encoding="utf-8")
    assert "CS-001" in model.load(prd).change_sets


# ---------------------------------------------------------------- 8: one grammar fault, one finding

RECORD = """# CS-001 Show the greeting as JSON

Started: 2026-11-03 in orders
Status: running

| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |
|---|---|---|---|---|---|---|---|---|
| 1 | orders | `.` | cs-001-json | 1.1.0 | — | — | verified | approved |

## Log

- 2026-11-03 started
"""

LINKS = ("# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n\n"
         "## Consumers\n\n| Consumer | Location |\n|---|---|\n")


@pytest.mark.parametrize("old,new,message", [
    ("Status: running", "Status: paused", "CS-001: status 'paused' is outside the grammar"),
    ("| verified | approved |", "| verified | deployed |", "CS-001: row orders: state 'deployed' is outside the grammar"),
    ("| verified | approved |", "| shipped | approved |", "CS-001: row orders: target 'shipped' is outside the grammar"),
])
def test_one_grammar_fault_one_finding(prd, old, new, message):
    (prd / "links.md").write_text(LINKS, encoding="utf-8")
    (prd / "changes").mkdir()
    (prd / "changes/CS-001.md").write_text(RECORD.replace(old, new), encoding="utf-8")
    assert [f.message for f in lint(prd) if f.rule == "change-sets"] == [message]


# ---------------------------------------------------------------- 11: a relative XDG_CACHE_HOME

def test_relative_xdg_cache_home_is_ignored(monkeypatch, tmp_path):
    from prdlint import links

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CACHE_HOME", "relative/cache")
    assert links._cache_dir("https://example.invalid/x.git").parent == tmp_path / ".cache/prd-toolkit/links"
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "abs"))
    assert links._cache_dir("https://example.invalid/x.git").parent == tmp_path / "abs/prd-toolkit/links"


# ---------------------------------------------------------------- 5: the snapshot is not all verbatim

ROOT = Path(__file__).parent.parent
SPEC = ROOT.parent / "docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md"
REEMITTED = ("SQL statements and events.md sections copied verbatim; OpenAPI operations and custom YAML keys "
             "re-emitted from the parsed YAML (comments and flow style are not kept)")


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").replace("> ", " ").split())


@pytest.mark.parametrize("path", [ROOT / "references/prd-format.md", SPEC])
def test_snapshot_is_not_called_verbatim(path):
    text = _flat(path)
    assert REEMITTED in text
    assert "copied verbatim by" not in text and "only, copied verbatim," not in text
