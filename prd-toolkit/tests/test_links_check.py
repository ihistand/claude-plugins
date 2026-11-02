"""prd_links.py check and impact, and the Side lifetime and git environment (prd-toolkit 0.7, Task 5)."""
import gc
import os
import shutil
import socket
import subprocess
import tempfile
import time
import warnings
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE
from legacy import commit, git
from linked import add_cases, make_linked_repos, run_links

CITED = ["table:orders/orders", "op:orders/getOrder", "op:orders/deleteOrder"]
ITEMS = ["op:deleteOrder", "op:getOrder", "table:orders"]


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def rp(reports: Path) -> Path:
    return reports / "docs/prd/reports"


def op(orders: Path) -> Path:
    return orders / "docs/prd/orders"


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, (path, old)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def synced(tmp_path: Path, cited: list[str] = CITED) -> tuple[Path, Path]:
    """orders and reports linked both ways (`add`), reports citing `cited` and synced; both sides committed."""
    orders, reports = make_linked_repos(tmp_path)
    r = run_links("add", rp(reports), "`../orders`")
    assert r.code == 0, r.err
    add_cases(rp(reports), cited)
    commit(orders, "Link reports", "docs")
    r = run_links("sync", rp(reports), "orders")
    assert r.code == 0, r.err
    commit(reports, "Link orders", "docs")
    return orders, reports


def lines(out: str) -> list[str]:
    return [x for x in out.split("\n") if x]


def change_orders(orders: Path) -> None:
    """A column type change in table orders and deleteOrder dropped, committed."""
    edit(op(orders) / "contracts/schema.sql", "order_key text NOT NULL UNIQUE", "order_key varchar(40) NOT NULL UNIQUE")
    api = op(orders) / "contracts/openapi.yaml"
    text = api.read_text(encoding="utf-8")
    start, end = text.index("    delete:\n"), text.index("components:\n")
    api.write_text(text[:start] + text[end:], encoding="utf-8")
    commit(orders, "Change orders, drop deleteOrder", "docs")


# ---------------------------------------------------------------- check

def test_check_clean_both_sides(tmp_path):
    orders, reports = synced(tmp_path)
    r = run_links("check", rp(reports))
    assert (r.code, r.err) == (0, "")
    assert lines(r.out) == [f"upstream orders {i}: same" for i in ITEMS]
    r = run_links("check", op(orders))
    assert (r.code, r.err) == (0, "")
    assert lines(r.out) == [f"consumer reports {i}: same" for i in ITEMS]


def test_check_changed_and_removed(tmp_path):
    orders, reports = synced(tmp_path)
    change_orders(orders)
    r = run_links("check", rp(reports))
    assert r.code == 1, r
    assert lines(r.out) == ["upstream orders op:deleteOrder: removed", "upstream orders op:getOrder: same",
                            "upstream orders table:orders: changed"]
    r = run_links("check", op(orders))
    assert r.code == 1, r
    assert lines(r.out) == ["consumer reports op:deleteOrder: removed", "consumer reports op:getOrder: same",
                            "consumer reports table:orders: changed"]


def test_check_reformatted_is_same(tmp_path):
    orders, reports = synced(tmp_path)
    edit(op(orders) / "contracts/schema.sql", "  order_key text NOT NULL UNIQUE,", "    order_key TEXT   not null UNIQUE,")
    commit(orders, "Reformat", "docs")
    r = run_links("check", rp(reports))
    assert r.code == 0, r
    assert "upstream orders table:orders: same" in lines(r.out)


def test_newer_than_lock_alone_is_clean(tmp_path):
    orders, reports = synced(tmp_path)
    edit(op(orders) / "prd.md", "version: 1.0.0", "version: 1.1.0")
    commit(orders, "Bump", "docs")
    r = run_links("check", rp(reports))
    assert r.code == 0, r
    assert "upstream orders: newer than lock" in lines(r.out)
    r = run_links("check", op(orders))
    assert r.code == 0, r
    assert "consumer reports: newer than lock" in lines(r.out)


def test_orphaned_lock_after_squash(tmp_path):
    orders, reports = synced(tmp_path)
    git(orders, "checkout", "-q", "-b", "cs-001-x")
    edit(op(orders) / "contracts/schema.sql", "sales_rep_name text NOT NULL\n", "sales_rep_name text NOT NULL,\n  region text\n")
    commit(orders, "Add region", "docs")
    git(orders, "checkout", "-q", "main")
    assert run_links("sync", rp(reports), "orders", "--ref", "cs-001-x").code == 0
    git(orders, "merge", "-q", "--squash", "cs-001-x")
    git(orders, "commit", "-q", "-m", "Squash cs-001-x")
    r = run_links("check", rp(reports))
    assert r.code == 1, r
    assert "upstream orders: orphaned lock" in lines(r.out)
    assert "upstream orders table:orders: same" in lines(r.out)
    assert run_links("sync", rp(reports), "orders").code == 0
    r = run_links("check", rp(reports))
    assert r.code == 0, r
    assert not any("orphaned" in x for x in lines(r.out))


def test_missing_row_either_side(tmp_path):
    orders, reports = synced(tmp_path)
    edit(op(orders) / "links.md", "| reports | `../reports` |\n", "")
    commit(orders, "Drop the consumer row", "docs")
    r = run_links("check", rp(reports))
    assert r.code == 1, r
    assert "upstream orders: missing row" in lines(r.out)

    orders, reports = synced(tmp_path / "reverse")
    edit(rp(reports) / "links.md", "| orders | `../orders` |", "| billing | `../orders` |")
    commit(reports, "Drop the upstream row", "docs")
    r = run_links("check", op(orders))
    assert r.code == 1, r
    assert "consumer reports: missing row" in lines(r.out)


def test_needs_env_not_an_environment(tmp_path):
    _, reports = synced(tmp_path)
    links_md = rp(reports) / "links.md"
    row = next(x for x in links_md.read_text(encoding="utf-8").split("\n") if x.startswith("| orders |"))
    edit(links_md, row, row.rstrip().rstrip("|").rstrip().rsplit("|", 1)[0] + "| live in qa |")
    r = run_links("check", rp(reports))
    assert r.code == 1, r
    assert "upstream orders: needs env qa is not an environment of orders" in lines(r.out)
    edit(links_md, "| live in qa |", "| live in staging |")
    r = run_links("check", rp(reports))
    assert r.code == 0, r


def test_check_wrong_prd_at_location_refuses(tmp_path):
    orders, reports = synced(tmp_path)
    edit(op(orders) / "prd.md", "prd: orders", "prd: billing")
    git(orders, "mv", "docs/prd/orders", "docs/prd/billing")
    commit(orders, "Rename", "docs")
    r = run_links("check", rp(reports))
    assert (r.code, r.out) == (1, "") and "refused: `../orders` holds PRD billing, not orders" in r.err


def test_unreachable(tmp_path):
    orders, reports = synced(tmp_path)
    orders.rename(tmp_path / "elsewhere")
    r = run_links("check", rp(reports))
    assert r.code == 3, r
    out = lines(r.out)
    assert len(out) == 1 and out[0].startswith("upstream orders: unreachable")
    r2 = run_links("check", rp(reports), "--ci")
    assert r2.code == 0, r2
    assert lines(r2.out) == out


def test_unreachable_url_git_fails(tmp_path):
    """A URL git refuses (no such repository, or credentials it may not prompt for) is unreachable, not a crash."""
    _, reports = synced(tmp_path)
    edit(rp(reports) / "links.md", "`../orders`", f"`{(tmp_path / 'gone.git').as_uri()}#docs/prd/orders`")
    r = run_links("check", rp(reports))
    assert r.code == 3, r
    out = lines(r.out)
    assert len(out) == 1 and out[0].startswith("upstream orders: unreachable (`file://") and "is unreachable: git clone" in out[0], out


def test_drift_beats_unreachable():
    from prdlint import links

    L = links.CheckLine
    assert links.check_exit([]) == 0
    assert links.check_exit([L("upstream", "a", None, "unreachable")]) == 3
    assert links.check_exit([L("upstream", "a", None, "unreachable"), L("consumer", "b", "table:t", "changed")]) == 1
    assert links.check_exit([L("upstream", "a", None, "newer than lock"), L("upstream", "a", "op:x", "same")]) == 0
    for v in ("removed", "orphaned lock", "missing row", "needs env qa is not an environment of a"):
        assert links.check_exit([L("upstream", "a", None, v)]) == 1, v


def _fake_git(tmp_path: Path) -> tuple[Path, Path]:
    """A `git` on PATH that logs its environment and execs the real git (same pid, so the group kill reaches it)."""
    real = shutil.which("git")
    bindir, log = tmp_path / "bin", tmp_path / "git-env.log"
    bindir.mkdir()
    stub = bindir / "git"
    stub.write_text(f'#!/bin/sh\necho "$1 prompt=$GIT_TERMINAL_PROMPT ssh=$GIT_SSH_COMMAND" >> "{log}"\nexec "{real}" "$@"\n', encoding="utf-8")
    stub.chmod(0o755)
    return bindir, log


def test_unreachable_url_times_out(tmp_path):
    """Review Focus 4: a host that never answers is unreachable within the timeout, never a hang or a prompt."""
    _, reports = synced(tmp_path)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)  # connections complete in the backlog; nothing ever answers
    port = srv.getsockname()[1]
    try:
        loc = f"`http://127.0.0.1:{port}/orders.git#docs/prd/orders`"
        edit(rp(reports) / "links.md", "`../orders`", loc)
        bindir, log = _fake_git(tmp_path)
        env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "git_ssh_command")}
        env.update(PATH=f"{bindir}{os.pathsep}{env.get('PATH', '')}", PRD_LINKS_TIMEOUT="2", no_proxy="*", NO_PROXY="*",
                   XDG_CACHE_HOME=str(tmp_path / "cache"), PRD_PLUGINS_FILE=str(PLUGINS_FILE))
        t0 = time.monotonic()
        r = run_links("check", rp(reports), env=env, timeout=30)
        took = time.monotonic() - t0
    finally:
        srv.close()
    assert r.code == 3, r
    assert took < 10, took
    out = lines(r.out)
    assert len(out) == 1 and out[0].startswith("upstream orders: unreachable") and "timed out after 2 s" in out[0], out
    clones = [x for x in log.read_text(encoding="utf-8").split("\n") if x.startswith("clone ")]
    assert clones and all("prompt=0" in x and "ssh=ssh -o BatchMode=yes" in x for x in clones), clones
    assert not list((tmp_path / "cache/prd-toolkit/links").glob("*/HEAD"))  # no half clone left as a cache entry


def test_git_ssh_batch_mode(tmp_path, monkeypatch):
    from prdlint import links

    seen = []
    real = subprocess.Popen

    def spy(cmd, *a, **kw):
        seen.append(kw.get("env"))
        return real(cmd, *a, **kw)

    monkeypatch.setattr(subprocess, "Popen", spy)
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    links._git(tmp_path, "--version")
    assert seen[-1]["GIT_SSH_COMMAND"] == "ssh -o BatchMode=yes" and seen[-1]["GIT_TERMINAL_PROMPT"] == "0"
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i /k")
    links._git(tmp_path, "--version")
    assert seen[-1]["GIT_SSH_COMMAND"] == "ssh -i /k"


def test_no_main_names_the_way_out(tmp_path):
    orders, reports = synced(tmp_path)
    git(orders, "branch", "-m", "main", "master")
    r = run_links("sync", rp(reports), "orders")
    assert (r.code, r.out) == (1, "") and "refused: `../orders` has no ref main; pass --ref <branch>" in r.err
    r = run_links("check", rp(reports))
    assert r.code == 3, r
    assert lines(r.out) == ["upstream orders: unreachable (`../orders` has no ref main; pass --ref <branch>)"]
    r = run_links("check", rp(reports), "--ref", "master")
    assert r.code == 0, r
    assert lines(r.out) == [f"upstream orders {i}: same" for i in ITEMS]
    git(reports, "branch", "-m", "main", "master")
    r = run_links("check", op(orders))
    assert r.code == 3, r
    assert lines(r.out) == ["consumer reports: unreachable (`../reports` has no ref main; pass --ref <branch>)"]


def test_sides_are_closed(tmp_path, monkeypatch):
    """check and sync remove every temporary directory they make, with no finalizer left to do it."""
    from prdlint import links, model

    orders, reports = synced(tmp_path)
    tmp = tmp_path / "tmpdirs"
    tmp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("error", ResourceWarning)
        assert links.check_exit(links.check(model.load(rp(reports)))) == 0
        assert links.check_exit(links.check(model.load(op(orders)))) == 0
        assert list(tmp.iterdir()) == []
        warnings.simplefilter("always", ResourceWarning)
        links.sync(model.load(rp(reports)), "orders")
        assert list(tmp.iterdir()) == []
        gc.collect()
    assert [w for w in caught if issubclass(w.category, ResourceWarning)] == []
    side = links.open_side(reports, links.parse_location("`../orders`"), expect="orders")
    with side:
        side.load("main")
        assert len(list(tmp.iterdir())) == 1
    assert list(tmp.iterdir()) == []


# ---------------------------------------------------------------- impact

def test_impact_lists_cited_consumers(tmp_path):
    orders, _ = synced(tmp_path)
    schema = op(orders) / "contracts/schema.sql"
    edit(schema, "order_key text NOT NULL UNIQUE", "order_key varchar(40) NOT NULL UNIQUE")
    r = run_links("impact", op(orders))
    assert r.code == 1, r
    assert lines(r.out) == ["changed: table:orders", "consumer reports: table:orders"]
    git(orders, "checkout", "-q", "--", "docs")
    edit(schema, "email text NOT NULL,", "email varchar(200) NOT NULL,")
    r = run_links("impact", op(orders))
    assert r.code == 0, r
    assert lines(r.out) == ["changed: table:customers"]
    git(orders, "checkout", "-q", "--", "docs")
    r = run_links("impact", op(orders))
    assert (r.code, r.out) == (0, "")


def test_impact_base(tmp_path):
    orders, _ = synced(tmp_path)
    edit(op(orders) / "contracts/schema.sql", "order_key text NOT NULL UNIQUE", "order_key varchar(40) NOT NULL UNIQUE")
    commit(orders, "Change orders", "docs")
    assert run_links("impact", op(orders)).code == 0
    r = run_links("impact", op(orders), "--base", "HEAD~1")
    assert r.code == 1, r
    assert lines(r.out) == ["changed: table:orders", "consumer reports: table:orders"]


def test_impact_unreachable_consumer(tmp_path):
    orders, reports = synced(tmp_path)
    reports.rename(tmp_path / "elsewhere")
    r = run_links("impact", op(orders))
    assert r.code == 3, r
    assert lines(r.out) == ["consumer reports: unreachable"]


def test_check_impact_usage(tmp_path):
    _, reports = synced(tmp_path)
    for args in (("check",), ("impact",), ("check", rp(reports), "--bogus"), ("check", tmp_path / "nope")):
        r = run_links(*args)
        assert r.code == 2 and r.out == "", args
