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
    assert drift_reasons(reports) == ["prd_links check found drift: orders op:deleteOrder, orders table:orders"]


def _record(folder, status, members, number="001"):
    """A change-set record under `folder`/changes/ with one row per member slug (the first is where it started)."""
    rows = "".join(f"| {i} | {m} | `.` | cs-{number}-x | 1.0.0 | — | — | verified | approved |\n" for i, m in enumerate(members, 1))
    (folder / "changes").mkdir(exist_ok=True)
    (folder / "changes" / f"CS-{number}.md").write_text(
        f"# CS-{number} x\n\nStarted: 2026-11-02 in {members[0]}\nStatus: {status}\n\n"
        "| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |\n|---|---|---|---|---|---|---|---|---|\n"
        f"{rows}\n## Log\n\n- 2026-11-02 started\n", encoding="utf-8")


def preflight_with_notes(reports):
    notes: list[str] = []
    reasons = [r for r in deploy.preflight(model.load(rp(reports)), reports, notes=notes) if r.startswith("prd_links")]
    return reasons, notes


ALLOWED = ["drift allowed by orders/CS-001: upstream orders table:orders: changed",
           "drift allowed by orders/CS-001: upstream orders op:deleteOrder: removed"]


def test_preflight_lets_drift_through_between_members_of_an_open_change_set(tmp_path):
    """R-13a (F-3): the upstream's record, found through links.md, lists both PRDs; the drift is reported, not refused."""
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), "running", ["orders", "reports"])
    reasons, notes = preflight_with_notes(reports)
    assert reasons == [] and sorted(notes) == sorted(ALLOWED), (reasons, notes)


def test_preflight_lets_drift_through_with_its_own_record(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(rp(reports), "approved", ["reports", "orders"])
    reasons, notes = preflight_with_notes(reports)
    assert reasons == [] and sorted(notes) == sorted(n.replace("orders/CS-001", "reports/CS-001") for n in ALLOWED), notes


@pytest.mark.parametrize("status", ["done", "abandoned"])
def test_preflight_refuses_drift_when_the_record_is_closed(tmp_path, status):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), status, ["orders", "reports"])
    reasons, notes = preflight_with_notes(reports)
    assert reasons == ["prd_links check found drift: orders op:deleteOrder, orders table:orders"] and notes == []


@pytest.mark.parametrize("members", [["orders", "dashboards"], ["reports", "dashboards"]])
def test_preflight_refuses_drift_when_a_side_is_not_a_member(tmp_path, members):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), "running", members)
    reasons, notes = preflight_with_notes(reports)
    assert reasons == ["prd_links check found drift: orders op:deleteOrder, orders table:orders"] and notes == []


def test_preflight_refuses_drift_with_no_record(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    reasons, notes = preflight_with_notes(reports)
    assert reasons == ["prd_links check found drift: orders op:deleteOrder, orders table:orders"] and notes == []


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
    assert "url(" not in page
    again = publish.render_page(model.load(op(orders)), orders, None, date(2026, 11, 1))
    assert "<th>Consumer</th>" in again


def test_status_url_upstream_makes_no_git_call(tmp_path):
    orders, reports = synced(tmp_path)
    links_md = rp(reports) / "links.md"
    links_md.write_text(links_md.read_text(encoding="utf-8").replace("`../orders`", "`https://example.invalid/orders.git#docs/prd/orders`", 1), encoding="utf-8")
    up = part(_items(reports), "Upstreams")
    assert re.fullmatch(r"orders 1\.0\.0 at [0-9a-f]{40}, needs default, check: not run \(git URL; run prd_links.py check\)", up[0]), up
    assert not (tmp_path / "cache").exists()


def test_status_check_error_is_shown(tmp_path):
    orders, reports = synced(tmp_path)
    links_md = rp(reports) / "links.md"
    links_md.write_text(links_md.read_text(encoding="utf-8").replace("| orders | `../orders` |", "| reports | `../orders` |", 1), encoding="utf-8")
    up = part(_items(reports), "Upstreams")
    assert up and ", check: error (a PRD cannot link to itself)" in up[0], up


def test_a_run_prints_each_drift_line_it_let_through(tmp_path, monkeypatch, capsys):
    """R-13a: the run's report shows every let-through line before the run starts."""
    import prd_deploy

    orders, reports = synced(tmp_path)

    def fake_preflight(prd, root, until=None, notes=None):
        notes.append("drift allowed by orders/CS-001: upstream orders table:orders: changed")
        return []

    class Started(Exception):
        pass

    def stop(*a, **k):
        raise Started

    monkeypatch.setattr(deploy, "preflight", fake_preflight)
    monkeypatch.setattr(deploy, "new_run_id", stop)
    with pytest.raises(Started):
        prd_deploy._new_run(type("A", (), {"until": None, "timeout": 60})(), model.load(rp(reports)), reports, [])
    assert capsys.readouterr().out == "drift allowed by orders/CS-001: upstream orders table:orders: changed\n"


# ---------------------------------------------------------------- R-F2: check --ci applies the R-13a let-through

def test_check_ci_lets_drift_through_between_members_of_an_open_change_set(tmp_path):
    """R-F2: each member's CI would report the other as drift while the change set is open; --ci prints the line as
    allowed and does not fail on it."""
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), "running", ["orders", "reports"])
    r = run_links("check", rp(reports), "--ci")
    assert (r.code, r.err) == (0, ""), r
    out = r.out.splitlines()
    assert sorted(x for x in out if x.startswith("drift allowed by ")) == sorted(ALLOWED), out
    assert "upstream orders op:getOrder: same" in out
    assert "upstream orders table:orders: changed" not in out


def test_check_without_ci_still_reports_drift_in_an_open_change_set(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), "running", ["orders", "reports"])
    r = run_links("check", rp(reports))
    assert r.code == 1, r
    assert "upstream orders table:orders: changed" in r.out.splitlines()
    assert "drift allowed" not in r.out


@pytest.mark.parametrize("status", ["done", "abandoned"])
def test_check_ci_fails_on_drift_once_the_record_is_closed(tmp_path, status):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), status, ["orders", "reports"])
    r = run_links("check", rp(reports), "--ci")
    assert r.code == 1, r
    assert "upstream orders table:orders: changed" in r.out.splitlines()
    assert "drift allowed" not in r.out


def test_check_ci_fails_on_drift_with_a_non_member(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    _record(op(orders), "running", ["orders", "dashboards"])
    assert run_links("check", rp(reports), "--ci").code == 1


def test_preflight_and_check_ci_share_one_lookup():
    """R-F2: the open-record lookup is one function, in links, used by both."""
    import inspect

    from prdlint import links

    assert not hasattr(deploy, "_open_change_sets")
    assert "links.let_through(" in inspect.getsource(deploy.preflight)
    assert callable(links.let_through)
