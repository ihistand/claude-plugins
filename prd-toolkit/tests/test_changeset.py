"""prd_links.py changeset: the change-set record and its only writer (prd-toolkit 0.7, Task 6)."""
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, edit, lint
from legacy import commit
from linked import _repo, make_three_repos, run_links

DAY = "2026-11-03"
TITLE = "Orders daily as JSON"
BRANCH = "cs-001-orders-daily-as-json"


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("PRD_LINKS_TODAY", DAY)


def prd_of(repo: Path) -> Path:
    return repo / "docs/prd" / repo.name


def changes(repo: Path) -> Path:
    return prd_of(repo) / "changes"


def new(transform: Path, *members: str, title: str = TITLE):
    args = ["changeset", "new", prd_of(transform), "--title", title]
    for m in members:
        args += ["--member", m]
    return run_links(*args)


def started(tmp_path, needs=None) -> tuple[Path, Path]:
    """The three repositories and CS-001 started in transform with every member; returns (transform, record)."""
    transform, _, _ = make_three_repos(tmp_path, needs)
    r = new(transform, "../dashboards", "../reports")
    assert r.code == 0, r.err
    return transform, changes(transform) / "CS-001.md"


def ok(*args):
    r = run_links("changeset", *args)
    assert r.code == 0, r.err
    return r


def refused(*args) -> str:
    r = run_links("changeset", *args)
    assert r.code == 1, (r.code, r.out, r.err)
    assert r.out == ""
    return r.err.strip()


def record(path: Path):
    from prdlint import model

    cs = model._change_set(f"changes/{path.name}", path.read_text(encoding="utf-8"))
    assert cs.problems == []
    return cs


def rows(path: Path) -> dict:
    return {r.prd: r for r in record(path).rows}


def clean(transform: Path) -> None:
    assert [f for f in lint(prd_of(transform)) if f.rule == "change-sets"] == []


# ---------------------------------------------------------------- new

def test_new_orders_members(tmp_path):
    transform, cs = started(tmp_path)
    r = run_links("changeset", "new", prd_of(transform), "--title", "x", "--member", "../reports", "--member", "../dashboards")
    assert Path(r.out.strip()).resolve() == (changes(transform) / "CS-002.md").resolve()
    assert cs.read_text(encoding="utf-8") == (
        f"# CS-001 {TITLE}\n\n"
        f"Started: {DAY} in transform\n"
        "Status: proposed\n\n"
        "| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        f"| 1 | transform | `.` | {BRANCH} | 1.0.0 | — | — | live in staging | proposed |\n"
        f"| 2 | reports | `../reports` | {BRANCH} | 1.0.0 | — | transform live in staging | live in staging | proposed |\n"
        f"| 3 | dashboards | `../dashboards` | {BRANCH} | 1.0.0 | — | transform live in staging; reports live in staging | verified | proposed |\n"
        "\n## Log\n")
    clean(transform)


def test_new_reads_each_version_where_the_branch_is_cut(tmp_path):
    """The 0.7 acceptance (F-2): step 1 leaves the change's edits in the starting tree, bump included, before `new`;
    the row's Version is the member's version on its default branch, so `set version=` writes `old → new`."""
    transform, _, _ = make_three_repos(tmp_path)
    edit(prd_of(transform), "prd.md", "\nversion: 1.0.0\n", "\nversion: 1.1.0\n")
    r = new(transform, "../dashboards", "../reports")
    assert r.code == 0, r.err
    cs = changes(transform) / "CS-001.md"
    assert rows(cs)["transform"].version == "1.0.0"
    ok("set", cs, "transform", "version=1.1.0")
    assert rows(cs)["transform"].version == "1.0.0 → 1.1.0"


def test_new_prints_only_its_path(tmp_path):
    transform, _, _ = make_three_repos(tmp_path)
    r = new(transform, "../reports", ".", "../dashboards", "../reports/")
    assert r.code == 0, r.err
    assert r.out.count("\n") == 1 and Path(r.out.strip()).resolve() == (changes(transform) / "CS-001.md").resolve()
    assert [x.prd for x in record(changes(transform) / "CS-001.md").rows] == ["transform", "reports", "dashboards"]


def test_default_needs_verified(tmp_path):
    """A downstream with no deploy-gate level needs `verified` by default."""
    transform, _, dashboards = make_three_repos(tmp_path)
    p = prd_of(dashboards) / "testing.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| deploy |", "| build |"), encoding="utf-8")
    assert new(transform, "../reports", "../dashboards").code == 0
    got = rows(changes(transform) / "CS-001.md")
    assert got["dashboards"].waits_for == "transform verified; reports verified"
    assert (got["transform"].target, got["reports"].target, got["dashboards"].target) == ("live in staging", "verified", "verified")


def test_target_latest_env(tmp_path):
    _, cs = started(tmp_path, {("dashboards", "transform"): "live in production"})
    got = rows(cs)
    assert got["transform"].target == "live in production"
    assert got["reports"].waits_for == "transform live in staging"
    assert got["dashboards"].waits_for == "transform live in production; reports live in staging"


def test_target_order_is_the_upstreams_table_order(tmp_path):
    """`later` means later in the upstream's operations.md Environments table, not alphabetical."""
    transform, _, _ = make_three_repos(tmp_path, {("reports", "transform"): "live in ci", ("dashboards", "transform"): "live in local"})
    assert new(transform, "../reports", "../dashboards").code == 0
    assert rows(changes(transform) / "CS-001.md")["transform"].target == "live in ci"


def test_target_unknown_env_between_two_is_refused(tmp_path):
    transform, _, _ = make_three_repos(tmp_path, {("dashboards", "transform"): "live in qa"})
    r = new(transform, "../reports", "../dashboards")
    assert r.code == 1
    assert "qa" in r.err and r.err.startswith("refused: ")
    assert not changes(transform).exists()


def test_new_refusals(tmp_path):
    transform, _, _ = make_three_repos(tmp_path)
    orders = _repo(tmp_path, "orders")
    commit(orders, "Add the PRD", "docs")
    url = "git@example.com:org/bi.git#docs/prd/bi"
    cases = [
        (["../reports", "../orders"], "refused: orders is linked to no other member"),
        ([], "refused: transform is linked to no other member"),
        (["../reports", url], f"refused: {url} is not cloned on this machine"),
        (["../reports", f"`{url}`"], f"refused: {url} is not cloned on this machine"),
        (["../missing"], None),
    ]
    for members, msg in cases:
        r = new(transform, *members)
        assert r.code == 1, (members, r)
        assert r.out == ""
        assert r.err.startswith("refused: ")
        if msg:
            assert r.err.strip() == msg
    # a cycle: dashboards becomes an upstream of transform too
    links = prd_of(transform) / "links.md"
    links.write_text(links.read_text(encoding="utf-8").replace(
        "|---|---|---|---|---|\n", "|---|---|---|---|---|\n| dashboards | `../dashboards` | | | |\n", 1), encoding="utf-8")
    r = new(transform, "../reports", "../dashboards")
    assert (r.code, r.err.strip()) == (1, "refused: the members' links form a cycle: dashboards → transform → dashboards")
    assert not changes(transform).exists()
    assert not (tmp_path / "cache").exists()


def test_new_usage_errors(tmp_path):
    transform, _, _ = make_three_repos(tmp_path)
    for title in ("", "---", "\n"):
        r = new(transform, "../reports", title=title)
        assert r.code == 2 and r.out == "", title
    r = run_links("changeset", "new", prd_of(transform), "--member", "../reports")
    assert r.code == 2
    assert not changes(transform).exists()


def test_numbering(tmp_path):
    transform, _, _ = make_three_repos(tmp_path)
    changes(transform).mkdir()
    for n in ("001", "009"):
        (changes(transform) / f"CS-{n}.md").write_text(f"# CS-{n} old\n", encoding="utf-8")
    (changes(transform) / "CS-1000.md").write_text("not a record\n", encoding="utf-8")
    r = new(transform, "../reports", title="Greet --json")
    assert r.code == 0, r.err
    path = changes(transform) / "CS-010.md"
    assert Path(r.out.strip()).resolve() == path.resolve()
    assert rows(path)["transform"].branch == "cs-010-greet-json"


def test_branch_slug():
    """R-P2: lowercase, each run of non-alphanumerics one `-`, edges stripped, at most 40, no trailing `-`."""
    from prdlint.changeset import slug

    assert slug("greet --json") == "greet-json"
    assert slug("  Show the greeting, as JSON!  ") == "show-the-greeting-as-json"
    assert slug("a" * 39 + " b") == "a" * 39
    assert slug("Résumé 2") == "r-sum-2"
    assert len(slug("x" * 80)) == 40


# ---------------------------------------------------------------- set

def test_set_fields(tmp_path):
    transform, cs = started(tmp_path)
    ok("set", cs, "transform", "version=1.1.0", "ids=FR-003,FR-004", "branch=cs-001-other")
    got = rows(cs)["transform"]
    assert (got.version, got.ids, got.branch) == ("1.0.0 → 1.1.0", "FR-003, FR-004", "cs-001-other")
    ok("set", cs, "transform", "version=1.2.0", "ids=—")
    got = rows(cs)["transform"]
    assert (got.version, got.ids) == ("1.0.0 → 1.2.0", "—")
    assert record(cs).status == "proposed"
    clean(transform)


def test_set_refusals(tmp_path):
    _, cs = started(tmp_path)
    assert refused("set", cs, "transform", "state=built") == "refused: CS-001 is not approved yet"
    ok("approve", cs, "--reply", "approve CS-001")
    assert refused("set", cs, "reports", "state=built") == "refused: reports waits for transform live in staging; transform is approved"
    ok("set", cs, "transform", "state=verified")
    before = cs.read_text(encoding="utf-8")
    assert refused("set", cs, "reports", "state=built") == "refused: reports waits for transform live in staging; transform is verified"
    assert refused("set", cs, "transform", "state=built") == "refused: transform cannot go back from verified to built"
    assert refused("set", cs, "orders", "state=built") == "refused: CS-001 has no row orders"
    assert cs.read_text(encoding="utf-8") == before
    for bad in ("state=deployed", "colour=red", "version=2", "ids=FR-3x", "branch=has space", "state"):
        r = run_links("changeset", "set", cs, "transform", bad)
        assert (r.code, r.out) == (2, ""), bad
    assert cs.read_text(encoding="utf-8") == before
    ok("set", cs, "transform", "state=live in staging")
    ok("set", cs, "reports", "state=built")
    # dashboards also waits for reports live in staging
    assert refused("set", cs, "dashboards", "state=built") == "refused: dashboards waits for reports live in staging; reports is built"
    ok("set", cs, "dashboards", "state=approved")  # not past approved: no wait applies


def test_set_verified_need(tmp_path):
    """R-F1: a need `verified` holds for `verified` or any `live in`; a need `live in <env>` for that env or any later
    one in the upstream's operations.md Environments order."""
    _, cs = started(tmp_path, {("reports", "transform"): "verified"})
    ok("approve", cs, "--reply", "yes")
    ok("set", cs, "transform", "state=live in staging")  # its Target, from dashboards' default need
    ok("set", cs, "reports", "state=built")  # a need `verified` holds for `live in staging`
    # dashboards' wait for transform holds; its wait for reports does not
    assert refused("set", cs, "dashboards", "state=built") == "refused: dashboards waits for reports live in staging; reports is built"


def fan_out(tmp_path) -> Path:
    """transform with two downstream members: reports needs it live in production, dashboards live in staging; CS-001
    started in transform and approved. Returns the record."""
    from linked import _links_md

    graph = {"transform": [], "reports": [("transform", "live in production")], "dashboards": [("transform", "live in staging")]}
    for name, ups in graph.items():
        repo = _repo(tmp_path, name)
        prd = prd_of(repo)
        edit(prd, "prd.md", "prd: orders", f"prd: {name}")
        (prd / "links.md").write_text(_links_md(ups, [d for d, us in graph.items() if any(u == name for u, _ in us)]),
                                      encoding="utf-8")
        commit(repo, "Add the PRD", "docs")
    transform = tmp_path / "transform"
    assert new(transform, "../reports", "../dashboards").code == 0
    cs = changes(transform) / "CS-001.md"
    assert rows(cs)["transform"].target == "live in production"
    ok("approve", cs, "--reply", "yes")
    return cs


def test_env_wait_holds_for_a_later_env(tmp_path):
    """R-F1, the final review's probe: once the upstream is live in production, a wait for live in staging holds."""
    cs = fan_out(tmp_path)
    for state in ("built", "verified", "live in production"):
        ok("set", cs, "transform", f"state={state}")
    ok("set", cs, "dashboards", "state=verified")
    ok("set", cs, "reports", "state=verified")
    ok("close", cs)
    assert record(cs).status == "done"


def test_env_state_cannot_go_back_to_an_earlier_env(tmp_path):
    cs = fan_out(tmp_path)
    ok("set", cs, "transform", "state=live in production")
    before = cs.read_text(encoding="utf-8")
    assert refused("set", cs, "transform", "state=live in staging") == "refused: transform: live in staging is before live in production"
    assert cs.read_text(encoding="utf-8") == before
    ok("set", cs, "transform", "state=live in production")  # the same environment again is no move back


def test_env_not_in_the_order_is_refused(tmp_path):
    cs = fan_out(tmp_path)
    before = cs.read_bytes()
    assert refused("set", cs, "transform", "state=live in qa") == "refused: transform's operations.md Environments has no qa"
    assert cs.read_bytes() == before


def test_set_past_the_target_is_refused(tmp_path):
    """R-F4: the Target is the furthest the change set needs; a deploy further (production) follows the close."""
    _, cs = started(tmp_path)
    ok("approve", cs, "--reply", "yes")
    walk(cs)
    before = cs.read_bytes()
    assert refused("set", cs, "transform", "state=live in production") == "refused: transform: live in production is past its Target live in staging"
    assert refused("set", cs, "dashboards", "state=live in staging") == "refused: dashboards: live in staging is past its Target verified"
    assert cs.read_bytes() == before
    ok("set", cs, "transform", "state=live in staging")  # at its Target again: no move
    ok("close", cs)


def test_record_argument_checked(tmp_path):
    transform, cs = started(tmp_path)
    r = run_links("changeset", "log", prd_of(transform) / "prd.md", "hello")
    assert r.code == 2
    r = run_links("changeset", "log", changes(transform) / "CS-007.md", "hello")
    assert r.code == 1 and r.err.startswith("refused: ")
    cs.write_text(cs.read_text(encoding="utf-8").replace("Status: proposed", "Status: paused"), encoding="utf-8")
    before = cs.read_text(encoding="utf-8")
    assert refused("log", cs, "hello").startswith("refused: ")
    assert cs.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------- stop, approve, close, abandon

def test_stop_keeps_state(tmp_path):
    transform, cs = started(tmp_path)
    ok("approve", cs, "--reply", "go")
    ok("set", cs, "transform", "state=live in staging")
    assert record(cs).status == "running"
    r = ok("stop", cs, "reports", "build\nfailed")
    assert r.out.strip() == str(cs)
    got = record(cs)
    assert got.status == "stopped: reports: build failed"
    assert rows(cs)["reports"].state == "approved"
    assert got.log[-1] == f"{DAY} reports stopped: build failed"
    clean(transform)
    ok("set", cs, "reports", "state=built")
    assert record(cs).status == "running"
    assert refused("stop", cs, "orders", "x") == "refused: CS-001 has no row orders"


def test_approve_one_line(tmp_path):
    transform, cs = started(tmp_path)
    ok("approve", cs, "--reply", 'yes, "all three"\nship it')
    text = cs.read_text(encoding="utf-8")
    assert f'\nApproval: {DAY}, "yes, "all three" ship it"\n' in text
    assert text.count("Approval:") == 1
    got = record(cs)
    assert got.status == "approved" and {r.state for r in got.rows} == {"approved"}
    assert got.approvals == [f'{DAY}, "yes, "all three" ship it"']
    clean(transform)
    assert refused("approve", cs, "--reply", "again").startswith("refused: CS-001 is approved")
    ok("set", cs, "transform", "state=built")
    ok("approve", cs, "--reply", '  fix it\r\n\r\n  "now"  ', "--amendment")
    got = record(cs)
    assert got.approvals[1] == f'{DAY}, "fix it "now"" (amendment)'
    assert rows(cs)["transform"].state == "built"
    clean(transform)


def test_amendment_needs_an_approval(tmp_path):
    _, cs = started(tmp_path)
    assert refused("approve", cs, "--reply", "x", "--amendment") == "refused: CS-001 has no approval to amend"
    r = run_links("changeset", "approve", cs, "--reply", " \n ")
    assert r.code == 2


def walk(cs: Path) -> None:
    ok("set", cs, "transform", "state=built")
    ok("set", cs, "transform", "state=verified")
    ok("set", cs, "transform", "state=live in staging")
    ok("set", cs, "reports", "state=verified")
    ok("set", cs, "reports", "state=live in staging")
    ok("set", cs, "dashboards", "state=verified")


def test_close(tmp_path):
    transform, cs = started(tmp_path)
    ok("approve", cs, "--reply", "approve CS-001")
    assert refused("close", cs) == "refused: CS-001: transform is approved, not its target live in staging"
    ok("set", cs, "transform", "state=built")
    assert refused("close", cs) == "refused: CS-001: transform is built, not its target live in staging"
    walk(cs)
    r = ok("close", cs)
    assert r.out.strip() == str(cs)
    text = cs.read_text(encoding="utf-8")
    assert text.endswith(f"\n## Merge order\n\n1. transform ({BRANCH})\n2. reports ({BRANCH})\n3. dashboards ({BRANCH})\n")
    got = record(cs)
    assert got.status == "done"
    assert got.merge_order == [f"transform ({BRANCH})", f"reports ({BRANCH})", f"dashboards ({BRANCH})"]
    clean(transform)
    for args in (("set", cs, "transform", "state=live in staging"), ("approve", cs, "--reply", "x", "--amendment"),
                 ("stop", cs, "reports", "x"), ("close", cs), ("abandon", cs, "x")):
        assert refused(*args) == "refused: CS-001 is done"


def test_abandon(tmp_path):
    transform, cs = started(tmp_path)
    ok("abandon", cs, "the client\nwas retired")
    got = record(cs)
    assert got.status == "abandoned"
    assert got.log == [f"{DAY} abandoned: the client was retired"]
    clean(transform)
    assert refused("set", cs, "transform", "ids=FR-001") == "refused: CS-001 is abandoned"


def test_only_writer(tmp_path):
    """Every subcommand's output passes lint's change-sets rule."""
    transform, cs = started(tmp_path)
    clean(transform)
    steps = [
        ("set", cs, "transform", "version=1.1.0", "ids=FR-003"),
        ("set", cs, "reports", "branch=cs-001-reports", "version=1.0.1", "ids=FR-001, FR-002"),
        ("log", cs, "scope confirmed:\n reports | dashboards"),
        ("approve", cs, "--reply", 'approve "CS-001"\nall of it'),
        ("set", cs, "transform", "state=built"),
        ("stop", cs, "transform", "a human step\nwithout a reply"),
        ("approve", cs, "--reply", "amend: \"retry\"", "--amendment"),
        ("set", cs, "transform", "state=verified"),
        ("set", cs, "transform", "state=live in staging"),
        ("set", cs, "reports", "state=built", "state=verified"),
        ("set", cs, "reports", "state=live in staging"),
        ("set", cs, "dashboards", "state=built"),
        ("set", cs, "dashboards", "state=verified"),
        ("close", cs),
        ("log", cs, "landed transform"),
    ]
    for step in steps:
        r = run_links("changeset", *step)
        assert r.code == 0, (step, r.err)
        clean(transform)
    got = record(cs)
    assert got.status == "done" and len(got.approvals) == 2 and len(got.log) == 4
    r = new(transform, "../reports", title="Second")
    assert r.code == 0
    second = changes(transform) / "CS-002.md"
    ok("abandon", second, "superseded")
    clean(transform)
    edit(prd_of(transform), "changes/CS-002.md", "Status: abandoned", "Status: paused")
    assert [f.rule for f in lint(prd_of(transform)) if f.rule == "change-sets"]  # the check can fail


# ---------------------------------------------------------------- fix round 1: what the table cannot hold, and the write

def test_state_env_must_be_a_name(tmp_path):
    _, cs = started(tmp_path)
    ok("approve", cs, "--reply", "yes")
    before = cs.read_bytes()
    for bad in ("live in a|b", "live in a;", "live in my env", "live in `x`"):
        r = run_links("changeset", "set", cs, "transform", f"state={bad}")
        assert (r.code, r.out) == (2, ""), bad
        assert bad in r.err
        assert cs.read_bytes() == before
    r = run_links("changeset", "set", cs, "transform", "state=live in stg-2.eu_west")
    # the grammar takes the name (not exit 2); the environment order then refuses it (R-F1, R-F4)
    assert (r.code, r.err.strip()) == (1, "refused: transform's operations.md Environments has no stg-2.eu_west")


def test_new_refuses_what_the_table_cannot_hold(tmp_path):
    transform, _, _ = make_three_repos(tmp_path, {("dashboards", "transform"): "live in a;b"})
    r = new(transform, "../reports", "../dashboards")
    assert (r.code, r.out) == (1, "")
    assert r.err.strip() == "refused: live in a;b cannot be written into the record table"
    odd = tmp_path / "x|y"
    odd.mkdir()
    repo = _repo(odd, "orders")
    commit(repo, "Add the PRD", "docs")
    r = new(transform, "../reports", "../x|y/orders")
    assert (r.code, r.out) == (1, "")
    assert r.err.strip() == "refused: `../x|y/orders` cannot be written into the record table"
    assert not changes(transform).exists()


def test_new_refuses_a_default_needs_env_the_table_cannot_hold(tmp_path):
    transform, reports, _ = make_three_repos(tmp_path)
    p = prd_of(reports) / "testing.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| `pytest tests/system` | staging |", "| `pytest tests/system` | my staging |"), encoding="utf-8")
    r = new(transform, "../reports")
    assert (r.code, r.err.strip()) == (1, "refused: live in my staging cannot be written into the record table")


def test_writes_replace_the_file_whole(tmp_path, monkeypatch):
    import os

    from prdlint import changeset

    _, cs = started(tmp_path)
    mode = cs.stat().st_mode
    ok("set", cs, "transform", "ids=FR-001")
    assert sorted(p.name for p in cs.parent.iterdir()) == ["CS-001.md"]
    assert cs.stat().st_mode == mode
    before = cs.read_bytes()

    def boom(*_):
        raise OSError("disk full")

    monkeypatch.setattr(changeset.os, "replace", boom)
    with pytest.raises(OSError):
        changeset.log(cs, "lost")
    assert cs.read_bytes() == before
    assert sorted(p.name for p in cs.parent.iterdir()) == ["CS-001.md"]
    assert os.path.exists(cs)
