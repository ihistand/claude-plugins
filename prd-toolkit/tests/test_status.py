"""prd_status.py: the read-only status report."""
import json
import subprocess
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, FIXTURE, edit
from prd_status import main
from prdlint import model, status
from prdlint.status import StatusItem

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
OPEN_ERROR = "\n### E-002 Duplicate check ignores case\nDetected: 2026-10-30, review\nClassification: code bug\nTouches: FR-001\nResolution: open\n"


def git(root: Path, *args: str) -> None:
    subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def prd_repo(tmp_path, monkeypatch):
    """The orders fixture in a git repo, with one test file citing T-001.1."""
    import shutil

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders")
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/unit/test_import.py").write_text('def test_a():\n    """@prd T-001.1"""\n')
    return tmp_path


@pytest.fixture
def cli(capsys):
    def run(path, *args):
        code = main([str(path), *args])
        out, err = capsys.readouterr()
        return code, out, err
    return run


@pytest.fixture
def items(prd_repo):
    return status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)


@pytest.fixture
def items_with_error(prd_repo):
    path = prd_repo / "docs/prd/orders/errors.md"
    path.write_text(path.read_text() + OPEN_ERROR)
    return status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)


def test_parts_in_order(prd_repo, cli):
    code, out, _ = cli(prd_repo / "docs/prd/orders")
    assert code == 0
    assert [h[3:] for h in out.splitlines() if h.startswith("## ")] == list(status.PARTS)


def test_counts_by_area(items):
    reqs = [i.text for i in items if i.part == "Requirements"]
    assert reqs == ["api: live 3", "import: live 1", "nfr: live 1"]


def test_matrix_row(items):
    row = next(i for i in items if i.part == "Matrix" and i.id == "FR-001")
    assert "T-001.1 integration build cited" in row.text and "missing" in row.text
    assert "T-001.4 acceptance deploy missing" in row.text and "; " in row.text


def test_no_adoption_map(items):
    assert StatusItem("Adoption map", None, "Not applicable: new project") in items


def test_header(items):
    head = next(i for i in items if i.part == "Header")
    assert "version 1.0.0" in head.text and "status Approved" in head.text


def test_not_built_and_not_verified(prd_repo):
    edit(prd_repo / "docs/prd/orders", "features/import.md", "Status: live (since 1.0.0)", "Status: approved")
    edit(prd_repo / "docs/prd/orders", "features/api.md", "### FR-002 Get an order\nStatus: live (since 1.0.0)", "### FR-002 Get an order\nStatus: built")
    out = status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)
    assert [i.id for i in out if i.part == "Not built"] == ["FR-001"]
    assert [i.id for i in out if i.part == "Not verified"] == ["FR-002"]


def test_open_errors_list_touches(items_with_error):
    assert any(i.part == "Open errors" and i.id == "E-002" and "Duplicate check ignores case" in i.text
               and "Touches: FR-001" in i.text for i in items_with_error)
    assert not any(i.id == "E-001" for i in items_with_error if i.part == "Open errors")


def test_json_matches_text_and_is_deterministic(prd_repo, cli):
    prd_dir = prd_repo / "docs/prd/orders"
    a, b = cli(prd_dir, "--json"), cli(prd_dir, "--json")
    expected = [(i.part, i.id) for i in status.build_status(model.load(prd_dir), prd_repo)]
    assert a[1] == b[1] and a[1].endswith("\n")
    assert [(x["part"], x["id"]) for x in json.loads(a[1])] == expected


def test_usage_error_prints_nothing(tmp_path, cli):
    code, out, err = cli(tmp_path / "missing")
    assert code == 2 and out == "" and err


def test_adoption_rows(prd_repo):
    prd_dir = prd_repo / "docs/prd/orders"
    (prd_dir / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n"
                                         "| api | adopted | `src/api/**` |\n| import | not started | |\n")
    edit(prd_dir, "prd.md", "Not applicable: new project.", "See adoption.md.")
    out = status.build_status(model.load(prd_dir), prd_repo)
    assert [(i.id, i.text) for i in out if i.part == "Adoption map"] == [
        ("api", "api | adopted | src/api/**"), ("import", "import | not started | -")]


def test_unmigrated_prd_exits_2_with_nothing_on_stdout(prd_repo, cli):
    prd_dir = prd_repo / "docs/prd/orders"
    edit(prd_dir, "prd.md", "Not applicable: new project.",
         "| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |")
    code, out, err = cli(prd_dir)
    assert code == 2 and out == "" and f"prd_status: {prd_dir.as_posix()}/prd.md: {model.UNMIGRATED}" in err
