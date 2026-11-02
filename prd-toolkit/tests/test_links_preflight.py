"""Links in the deploy pre-flight, status, context packs and the published page (prd-toolkit 0.7, Task 8)."""
import re

import pytest
from conftest import PLUGINS_FILE
from legacy import commit
from linked import run_links
from prdlint import context, deploy, model, publish, status
from test_hooks_stale import GITLAB  # noqa: F401
from test_links_check import CITED, change_orders, op, rp, synced


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def drift_reasons(reports):
    prd = model.load(rp(reports))
    return [r for r in deploy.preflight(prd, reports) if r.startswith("prd_links")]


def test_preflight_refuses_on_drift(tmp_path):
    orders, reports = synced(tmp_path)
    assert drift_reasons(reports) == []
    change_orders(orders)
    assert drift_reasons(reports) == ["prd_links check found drift: op:deleteOrder, table:orders"]


def test_preflight_passes_on_unreachable(tmp_path):
    orders, reports = synced(tmp_path)
    (orders.parent / "orders").rename(orders.parent / "moved")
    r = run_links("check", rp(reports))
    assert r.code == 3, r
    assert drift_reasons(reports) == []


def test_preflight_without_links_adds_nothing(prd):
    import subprocess
    root = prd.parent.parent.parent
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    assert not [r for r in deploy.preflight(model.load(prd), root) if "prd_links" in r]


def _items(repo):
    prd_dir = next((repo / "docs/prd").iterdir())
    return status.build_status(model.load(prd_dir), repo)


def part(items, name):
    return [i.text for i in items if i.part == name]


def test_status_parts_on_a_linked_fixture(tmp_path):
    orders, reports = synced(tmp_path)
    up = part(_items(reports), "Upstreams")
    assert len(up) == 1 and re.fullmatch(r"orders 1\.0\.0 at [0-9a-f]{40}, needs default, check: same 3", up[0]), up
    assert part(_items(reports), "Consumers") == ["None."]
    assert part(_items(reports), "Change sets") == ["None."]
    assert part(_items(orders), "Upstreams") == ["None."]
    assert part(_items(orders), "Consumers") == ["reports ../reports"]
    change_orders(orders)
    assert part(_items(reports), "Upstreams")[0].endswith("check: changed 1, removed 1, same 1")


def test_status_unreachable_upstream_has_no_check(tmp_path):
    orders, reports = synced(tmp_path)
    (orders.parent / "orders").rename(orders.parent / "moved")
    assert re.fullmatch(r"orders 1\.0\.0 at [0-9a-f]{40}, needs default", part(_items(reports), "Upstreams")[0])


def test_status_change_sets(tmp_path):
    orders, reports = synced(tmp_path)
    cs = rp(reports) / "changes"
    cs.mkdir()
    (cs / "CS-001.md").write_text(
        "# CS-001 Add a flag\n\nStarted: 2026-11-02 in reports\nStatus: running\n\n"
        "| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |\n|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | orders | `../orders` | cs-001-add-a-flag | 1.0.0 → 1.1.0 | — | — | verified | approved |\n"
        "| 2 | reports | `.` | cs-001-add-a-flag | 1.0.0 | — | orders verified | verified | proposed |\n\n## Log\n\n- 2026-11-02 started\n",
        encoding="utf-8")
    (cs / "CS-002.md").write_text(
        "# CS-002 Old\n\nStarted: 2026-10-01 in reports\nStatus: done\n\n"
        "| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |\n|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | reports | `.` | cs-002-old | 1.0.0 | — | — | verified | verified |\n\n## Log\n\n- 2026-10-01 done\n", encoding="utf-8")
    assert part(_items(reports), "Change sets") == ["CS-001 running: orders approved; reports proposed"]


def test_status_part_order():
    p = status.PARTS
    assert p[p.index("Open errors") + 1:p.index("Open errors") + 4] == ("Upstreams", "Consumers", "Change sets")


def test_context_pack_holds_the_snapshot_text(tmp_path):
    orders, reports = synced(tmp_path)
    prd = model.load(rp(reports))
    pack = context.build_pack(prd, "api", None)
    got = {i.id: i.text for i in pack if i.part == "Upstream contracts"}
    from prdlint import snapshot
    c = snapshot.contracts_of_snapshot(prd.snapshots["orders"])
    assert set(got) == {"table:orders/orders", "op:orders/getOrder", "op:orders/deleteOrder"}, got
    assert got["table:orders/orders"] == snapshot.item_text(c, "table", "orders")
    assert got["op:orders/getOrder"] == snapshot.item_text(c, "op", "getOrder")
    assert "## Upstream contracts" in context.render_text(pack)


def test_context_pack_leaves_other_areas_out(tmp_path):
    orders, reports = synced(tmp_path)
    pack = context.build_pack(model.load(rp(reports)), "import", None)
    assert [i.text for i in pack if i.part == "Upstream contracts"] == ["None."]


def test_context_pack_without_links_has_no_part(prd):
    assert not [i for i in context.build_pack(model.load(prd), "import", None) if i.part == "Upstream contracts"]


def test_published_page_shows_both_links_tables_and_loads_nothing(tmp_path):
    orders, reports = synced(tmp_path)
    from datetime import date
    page = publish.render_page(model.load(rp(reports)), reports, None, date(2026, 11, 1))
    assert "<h2>Links</h2>" in page
    assert "<th>Upstream</th>" in page and "<th>Consumer</th>" in page
    for tag in ("<script", "<link", "@import"):
        assert tag not in page
    assert "url(" not in page.split("</style>")[0]
    again = publish.render_page(model.load(op(orders)), orders, None, date(2026, 11, 1))
    assert "<th>Consumer</th>" in again
