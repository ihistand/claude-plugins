"""0.8.4: the PRD folder's root README.md is generated, so the digest and the bump skip it (FR-015)."""
import contextlib
import io
import json

import pytest
from deploy_fixture import deploy_repo
from prd_change import main as change_main
from prd_context import main as context_main
from prd_publish import main as publish_main
from prd_trace import main as trace_main
from prdlint import change

PRD = "docs/prd/orders"
README_TEXT = "# Orders\n\nGenerated guide. Mentions FR-999.\n"


def run(main, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def test_skipped_only_at_the_root():
    assert change.README == "README.md"
    assert change._skipped("README.md")
    assert not change._skipped("features/README.md")
    assert not change._skipped("contracts/dependencies/README.md")


def test_digest_ignores_a_root_readme(repo):
    prd = repo / PRD
    before = change.digest(prd)
    (prd / "README.md").write_text(README_TEXT, encoding="utf-8")
    assert change.digest(prd) == before
    (prd / "README.md").write_text(README_TEXT + "edited\n", encoding="utf-8")
    assert change.digest(prd) == before


def test_digest_counts_a_nested_readme(repo):
    prd = repo / PRD
    before = change.digest(prd)
    (prd / "features/README.md").write_text(README_TEXT, encoding="utf-8")
    assert change.digest(prd) != before


def test_bump_reports_nothing_for_a_root_readme(repo):
    (repo / PRD / "README.md").write_text(README_TEXT, encoding="utf-8")
    code, out, err = run(change_main, "bump", str(repo / PRD), "--base", "HEAD", "--json")
    assert code == 0, err
    data = json.loads(out)
    assert "README" not in out
    assert not data.get("items")


def test_bump_still_sees_a_nested_readme(repo):
    (repo / PRD / "features/README.md").write_text(README_TEXT, encoding="utf-8")
    code, out, err = run(change_main, "bump", str(repo / PRD), "--base", "HEAD", "--json")
    assert code == 0, err
    assert "README" in out


@pytest.mark.parametrize("main,args", [
    (context_main, ["--for", "implement"]),
    (trace_main, []),
])
def test_other_readers_unchanged_by_a_root_readme(repo, main, args):
    prd = str(repo / PRD)
    before = run(main, prd, *args)
    (repo / PRD / "README.md").write_text(README_TEXT, encoding="utf-8")
    assert run(main, prd, *args) == before


def test_publish_unchanged_by_a_root_readme(repo, tmp_path):
    prd = str(repo / PRD)
    a, b = tmp_path / "a.html", tmp_path / "b.html"
    code, _, err = run(publish_main, "render", prd, "--out", str(a))
    assert code == 0, err
    (repo / PRD / "README.md").write_text(README_TEXT, encoding="utf-8")
    code, _, err = run(publish_main, "render", prd, "--out", str(b))
    assert code == 0, err
    assert a.read_bytes() == b.read_bytes()
