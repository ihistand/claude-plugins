"""prd_build_check.py: --diff (builder touched the PRD or a tester's test) and --results (RESULTS lines)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import FIXTURE, PLUGINS_FILE

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from prdlint import buildcheck, model  # noqa: E402

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/prd_build_check.py"
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
UNIT, NONUNIT = "T-001.3", "T-002.1"


def git(root: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit(root: Path, msg: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders")
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders-old")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests/test_api.py").write_text(f"# @prd {NONUNIT}\ndef test_a():\n    pass\n")
    (tmp_path / "tests/test_unit.py").write_text(f"# @prd {UNIT}\ndef test_u():\n    pass\n")
    (tmp_path / "src/app.py").write_text("x = 1\n")
    commit(tmp_path, "base")
    git(tmp_path, "tag", "base")
    return tmp_path


def diff(root: Path) -> list[str]:
    prd = model.load(root / "docs/prd/orders")
    return buildcheck.diff_findings(prd, root, "base..HEAD")


def test_prd_edit_fails(repo):
    p = repo / "docs/prd/orders/prd.md"
    p.write_text(p.read_text() + "\nmore\n")
    commit(repo, "edit")
    assert any("docs/prd/orders/prd.md: the builder may not edit the PRD folder" in f for f in diff(repo))


def test_sibling_prefix_is_not_under_the_prd(repo):
    p = repo / "docs/prd/orders-old/prd.md"
    p.write_text(p.read_text() + "\nmore\n")
    commit(repo, "edit")
    assert diff(repo) == []


def test_tester_file_edit_fails(repo):
    (repo / "tests/test_api.py").write_text(f"# @prd {NONUNIT}\ndef test_a():\n    assert 1\n")
    commit(repo, "edit")
    assert any("tests/test_api.py cites T-" in f and "a tester's test" in f for f in diff(repo))


def test_tester_file_renamed_fails(repo):
    git(repo, "mv", "tests/test_api.py", "tests/test_api2.py")
    commit(repo, "rename")
    assert diff(repo)


def test_unit_test_and_code_pass(repo):
    (repo / "tests/test_unit.py").write_text(f"# @prd {UNIT}\ndef test_u():\n    assert 1\n")
    (repo / "src/app.py").write_text("x = 2\n")
    commit(repo, "code")
    assert diff(repo) == []


def test_uncovered_tid_is_treated_as_non_unit(repo):
    (repo / "tests/test_x.py").write_text("# @prd T-099.1\n")
    commit(repo, "new")
    assert any("tests/test_x.py cites T-099.1" in f for f in diff(repo))


def run(root: Path, *args: str):
    p = subprocess.run([str(SCRIPT), *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_cli_diff_findings_exit_1(repo):
    (repo / "tests/test_api.py").write_text("changed\n")
    commit(repo, "edit")
    code, out, _ = run(repo, "docs/prd/orders", "--diff", "base..HEAD")
    assert code == 1 and "tests/test_api.py cites T-002.1" in out


def test_cli_diff_clean_exit_0(repo):
    code, out, _ = run(repo, "docs/prd/orders", "--diff", "base..HEAD")
    assert (code, out) == (0, "")


def test_cli_bad_range_exit_2(repo):
    code, out, err = run(repo, "docs/prd/orders", "--diff", "nope..HEAD")
    assert code == 2 and out == "" and err


@pytest.mark.parametrize("args", [[], ["--diff", "a..b", "--results", "r"], ["--results", "r"]])
def test_cli_usage_exit_2(repo, args):
    code, out, err = run(repo, "docs/prd/orders", *args)
    assert code == 2 and out == "" and err


def test_cli_results(repo, tmp_path):
    rep = tmp_path / "report.md"
    rep.write_text("## RESULTS\n- T-001.2: pass\n")
    code, out, _ = run(repo, "docs/prd/orders", "--results", str(rep), "--tids", "T-001.2,T-002.1")
    assert code == 1 and "T-002.1 has no RESULTS line" in out
    code, out, _ = run(repo, "docs/prd/orders", "--results", str(rep), "--tids", "T-001.2")
    assert (code, out) == (0, "")


def test_results_clean():
    assert buildcheck.results_findings("RESULTS\nT-001.2: pass\nT-002.1: known-failing E-001\n", ["T-001.2", "T-002.1"]) == []


@pytest.mark.parametrize("report,needle", [
    ("RESULTS\nT-001.2: pass\n", "T-002.1 has no RESULTS line"),
    ("RESULTS\nT-001.2: pass\nT-002.1: pass\nT-009.1: pass\n", "T-009.1 was not dispatched"),
    ("RESULTS\nT-001.2: ok\nT-002.1: pass\n", "T-001.2: not one of pass, fail: <reason>, known-failing E-nnn")])
def test_results_problems(report, needle):
    assert any(needle in f for f in buildcheck.results_findings(report, ["T-001.2", "T-002.1"]))


TIDS = ["T-001.2", "T-002.1"]


def test_tid_line_before_heading_is_ignored():
    r = "T-001.2: pass\nT-002.1: pass\n\nRESULTS\nT-001.2: pass\n"
    assert buildcheck.results_findings(r, TIDS) == ["T-002.1 has no RESULTS line"]


def test_notes_after_prose_line_are_ignored_and_do_not_hide_a_missing_one():
    r = "RESULTS\nT-001.2: pass\nNotes follow.\nT-002.1: pass\n"
    assert buildcheck.results_findings(r, TIDS) == ["T-002.1 has no RESULTS line"]


def test_see_results_below_does_not_start_the_block():
    r = "Summary: see RESULTS below\nT-001.2: pass\n\n## RESULTS\n\nT-001.2: pass\nT-002.1: pass\n"
    assert buildcheck.results_findings(r, TIDS) == []


def test_duplicate_tid_line_is_a_finding():
    r = "RESULTS\nT-001.2: pass\nT-001.2: fail: x\nT-002.1: pass\n"
    assert "T-001.2: more than one RESULTS line" in buildcheck.results_findings(r, TIDS)


@pytest.mark.parametrize("heading", ["RESULTS", "## RESULTS", "3. RESULTS", "**RESULTS**", "## 3. **RESULTS**"])
def test_heading_forms_and_star_bullets(heading):
    assert buildcheck.results_findings(f"{heading}\n* T-001.2: pass\n- T-002.1: pass\n", TIDS) == []


def test_no_heading_reports_all_missing():
    assert buildcheck.results_findings("T-001.2: pass\n", TIDS) == [f"{t} has no RESULTS line" for t in TIDS]


def test_triple_dot_range_exits_2(repo):
    code, out, err = run(repo, "docs/prd/orders", "--diff", "base...HEAD")
    assert code == 2 and out == "" and err


def test_deleted_tester_file_is_reported(repo):
    git(repo, "rm", "-q", "tests/test_api.py")
    commit(repo, "delete")
    assert any("tests/test_api.py cites T-002.1" in f for f in diff(repo))


def test_renamed_and_modified_tester_file_is_reported(repo):
    git(repo, "mv", "tests/test_api.py", "tests/test_api2.py")
    (repo / "tests/test_api2.py").write_text(f"# @prd {NONUNIT}\ndef test_a():\n    assert 1\n    assert 2\n")
    commit(repo, "rename+modify")
    assert any("tests/test_api" in f and "a tester's test" in f for f in diff(repo))


def test_tester_file_with_space_is_reported(repo):
    (repo / "tests/test api.py").write_text(f"# @prd {NONUNIT}\n")
    commit(repo, "space")
    assert any("tests/test api.py cites T-002.1" in f for f in diff(repo))


def test_head_side_unreadable_rev_is_not_silently_absent(repo):
    prd = model.load(repo / "docs/prd/orders")
    with pytest.raises(Exception):
        buildcheck.diff_findings(prd, repo, "base..deadbeef")


def test_vendored_toolkit_edit_fails(repo):
    """Minor 5: the builder may not change the vendored .prd-toolkit/ copy."""
    (repo / ".prd-toolkit").mkdir()
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    commit(repo, "edit")
    assert diff(repo) == [".prd-toolkit/prd_lint.py: the builder may not edit the vendored .prd-toolkit/ copy"]


DEPLOY_GATE = "T-004.1"  # level system, Gate deploy in the fixture's Levels


def test_r28_builder_edit_of_a_deploy_gate_test_fails(repo):
    (repo / "tests/system").mkdir()
    (repo / "tests/system/test_sys.py").write_text(f"# @prd {DEPLOY_GATE}\ndef test_s():\n    pass\n")
    commit(repo, "tester's deploy-gate test")
    git(repo, "tag", "-f", "base")
    (repo / "tests/system/test_sys.py").write_text(f"# @prd {DEPLOY_GATE}\ndef test_s():\n    assert 1\n")
    commit(repo, "builder edit")
    assert any(f"tests/system/test_sys.py cites {DEPLOY_GATE}, a tester's test" in f for f in diff(repo))


def test_r28_results_check_takes_only_the_dispatched_build_gate_tids():
    report = f"RESULTS\n{NONUNIT}: pass\n"
    assert buildcheck.results_findings(report, [NONUNIT]) == []
    assert buildcheck.results_findings(report + f"{DEPLOY_GATE}: pass\n", [NONUNIT]) == [f"{DEPLOY_GATE} was not dispatched"]
