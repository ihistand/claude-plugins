"""prd_build_check.py: --diff (builder touched the PRD or a tester's test) and --results (RESULTS lines)."""
import re
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
    (repo / "tests/test_x.py").write_text("# @" "prd T-099.1\n")
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


# --- --stale (spec section 15) ---

CASES = "docs/prd/orders/test-cases/import.yaml"
STALE_TEST = "tests/test_import.py"


@pytest.fixture
def srepo(repo):
    """The repo with one committed test citing T-001.1, committed after its case."""
    (repo / STALE_TEST).write_text("# @" "prd T-001.1\ndef test_i():\n    pass\n")
    commit(repo, "test for T-001.1")
    return repo


def stale(root: Path, *tids: str) -> list[str]:
    return buildcheck.stale_findings(model.load(root / "docs/prd/orders"), root, list(tids))


def edit_case(root: Path, n: int = 2) -> None:
    """Make T-001.1's expected output `inserted: n`."""
    p = root / CASES
    s = re.sub(r"output: \{status: ok, inserted: \d+, skipped: 0\}", f"output: {{status: ok, inserted: {n}, skipped: 0}}", s_ := p.read_text(), count=1)
    assert s != s_ or f"inserted: {n}, skipped: 0}}" in s_
    p.write_text(s)


def test_stale_case_edited_after_the_test_commit(srepo):
    edit_case(srepo)
    commit(srepo, "fix the case")
    sha = git(srepo, "log", "-1", "--format=%h", "--", STALE_TEST)
    assert stale(srepo, "T-001.1") == [
        f"stale T-001.1 {STALE_TEST}: its test case changed after the test (last changed in {sha})"]


def test_stale_working_tree_edit_of_the_case_counts(srepo):
    edit_case(srepo)
    assert len(stale(srepo, "T-001.1")) == 1


def test_stale_unchanged_is_not_stale(srepo):
    assert stale(srepo, "T-001.1") == []


def test_stale_layout_only_change_is_not_stale(srepo):
    p = srepo / CASES
    s = p.read_text()
    old = "  ac: AC-001.1\n  level: integration\n"
    assert s.count(old) == 1
    s = s.replace(old, "  level:    integration\n  ac:   AC-001.1\n")
    p.write_text(s.replace("{status: ok, inserted: 1, skipped: 0}", "{ skipped: 0,  status: ok, inserted: 1 }"))
    assert stale(srepo, "T-001.1") == []


def test_stale_tid_with_no_test_is_not_stale(srepo):
    edit_case(srepo, 3)
    p = srepo / "docs/prd/orders/test-cases/api.yaml"
    p.write_text(p.read_text().replace("status: 404", "status: 410", 1))
    assert stale(srepo, "T-002.2") == []


def test_stale_test_with_working_tree_edits_is_not_stale(srepo):
    edit_case(srepo)
    commit(srepo, "fix the case")
    (srepo / STALE_TEST).write_text("# @" "prd T-001.1\ndef test_i():\n    assert 1\n")
    assert stale(srepo, "T-001.1") == []


def test_stale_never_committed_test_is_not_stale(repo):
    edit_case(repo)
    commit(repo, "fix the case")
    (repo / STALE_TEST).write_text("# @" "prd T-001.1\ndef test_i():\n    pass\n")
    assert stale(repo, "T-001.1") == []
    git(repo, "add", STALE_TEST)  # staged, still no commit
    assert stale(repo, "T-001.1") == []


def test_stale_the_newer_of_two_citing_files_is_judged(repo):
    old = {"GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z", "GIT_AUTHOR_DATE": "2020-01-01T00:00:00Z"}
    (repo / "tests/test_old.py").write_text("# @" "prd T-001.1\n")
    subprocess.run([*GIT, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*GIT, "commit", "-qm", "old test"], cwd=repo, check=True, env={**__import__("os").environ, **old})
    edit_case(repo)
    commit(repo, "fix the case")
    (repo / "tests/test_new.py").write_text("# @" "prd T-001.1\n")  # written after the fix: current
    commit(repo, "new test")
    assert stale(repo, "T-001.1") == []
    edit_case(repo, 4)
    commit(repo, "fix the case again")
    found = stale(repo, "T-001.1")
    assert len(found) == 1 and "tests/test_new.py" in found[0]


def test_stale_case_moved_unchanged_to_another_file_is_not_stale(srepo):
    """Review Focus 9: the entry is looked up across every test-case file at the test's commit."""
    src, dst = srepo / CASES, srepo / "docs/prd/orders/test-cases/moved.yaml"
    s = src.read_text()
    head, rest = s.split("\nT-001.2:", 1)
    dst.write_text(head.rstrip("\n") + "\n")
    src.write_text("T-001.2:" + rest)
    commit(srepo, "move T-001.1")
    assert stale(srepo, "T-001.1") == []


def test_stale_entry_absent_at_the_test_commit_is_stale(repo):
    p = repo / CASES
    s = p.read_text()
    head, rest = s.split("\nT-001.2:", 1)
    p.write_text("T-001.2:" + rest)
    (repo / "docs/prd/orders/test-cases/new.yaml").write_text(head.rstrip("\n") + "\n")
    (repo / STALE_TEST).write_text("# @" "prd T-001.1\n")
    # the test is committed while the case is not in any file yet
    git(repo, "add", STALE_TEST, CASES)
    git(repo, "commit", "-qm", "test first", "--", STALE_TEST, CASES)
    commit(repo, "case arrives")
    assert len(stale(repo, "T-001.1")) == 1


def test_stale_lines_follow_the_tids_order(srepo):
    (srepo / "tests/test_a2.py").write_text("# @" "prd T-002.2\n")
    commit(srepo, "test for T-002.2")
    edit_case(srepo)
    p = srepo / "docs/prd/orders/test-cases/api.yaml"
    p.write_text(p.read_text().replace("status: 404", "status: 410", 1))
    out = stale(srepo, "T-002.2", "T-001.1")
    assert [line.split()[1] for line in out] == ["T-002.2", "T-001.1"]


def test_cli_stale_exit_codes(srepo):
    code, out, _ = run(srepo, "docs/prd/orders", "--stale", "--tids", "T-001.1")
    assert (code, out) == (0, "")
    edit_case(srepo)
    code, out, _ = run(srepo, "docs/prd/orders", "--stale", "--tids", "T-001.1,T-002.1")
    assert code == 1 and out.startswith("stale T-001.1 tests/test_import.py: its test case changed after the test (last changed in ")


@pytest.mark.parametrize("args", [["--stale"], ["--stale", "--diff", "base..HEAD", "--tids", "T-001.1"],
                                  ["--stale", "--results", "r", "--tids", "T-001.1"]])
def test_cli_stale_usage_exit_2(srepo, args):
    code, out, err = run(srepo, "docs/prd/orders", *args)
    assert code == 2 and out == "" and err


def test_stale_git_failure_raises_so_the_cli_exits_2(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders")  # no git repository
    (tmp_path / "tests").mkdir()
    (tmp_path / STALE_TEST).write_text("# @" "prd T-001.1\n")
    with pytest.raises(RuntimeError):
        stale(tmp_path, "T-001.1")


# --- 0.8.3 spec section 5 (E-009 to E-015) ---

def test_e009_stale_outside_git_exits_2(tmp_path, monkeypatch):
    # 0.8.3 spec §5, E-009
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    dest = tmp_path / "orders"
    shutil.copytree(FIXTURE, dest)
    rc, out, err = run(tmp_path, str(dest), "--stale", "--tids", "T-001.1")
    assert (rc, out) == (2, "")
    assert f"prd_build_check: {dest.as_posix()} is not in a git working tree" in err


def test_e010_blank_line_after_results_ends_the_block():
    # 0.8.3 spec §5, E-010
    assert buildcheck.results_findings("RESULTS\n\nT-001.1: pass\n\nT-001.2: pass", ["T-001.1", "T-001.2"]) == [
        "T-001.2 has no RESULTS line"]
    assert buildcheck.results_findings("RESULTS\n\n\nT-001.1: pass\nT-001.2: pass", ["T-001.1", "T-001.2"]) == []


def test_e011_duplicated_tid_key_keeps_the_first_value(srepo):
    # 0.8.3 spec §5, E-011
    p = srepo / CASES
    s = p.read_text()
    head = s.split("\nT-001.2:", 1)[0]
    assert "inserted: 1," in head
    p.write_text(s.rstrip("\n") + "\n" + head.replace("inserted: 1,", "inserted: 9,") + "\n")
    assert stale(srepo, "T-001.1") == []


def test_e012_subfolder_case_files_are_not_read_at_either_end(repo):
    # 0.8.3 spec §5, E-012
    sub = repo / "docs/prd/orders/test-cases/aaa"
    sub.mkdir()
    (sub / "x.yaml").write_text("T-001.1: {level: unit, input: 5}\n")
    (repo / STALE_TEST).write_text("# @" "prd T-001.1\ndef test_i():\n    pass\n")
    commit(repo, "test for T-001.1")
    (sub / "x.yaml").write_text("T-001.1: {level: unit, input: 6}\n")
    commit(repo, "edit the subfolder copy")
    assert stale(repo, "T-001.1") == []


def test_e013_non_file_yaml_entry_is_skipped(srepo):
    # 0.8.3 spec §5, E-013. The PRD is loaded before the directory exists: model.load's own handling of such an entry is E-007's.
    prd = model.load(srepo / "docs/prd/orders")
    (srepo / "docs/prd/orders/test-cases/bad.yaml").mkdir()
    assert buildcheck.stale_findings(prd, srepo, ["T-001.1"]) == []
    edit_case(srepo)
    assert len(buildcheck.stale_findings(prd, srepo, ["T-001.1"])) == 1


def test_e014_citation_split_across_lines_is_not_a_citation(repo):
    # 0.8.3 spec §5, E-014
    (repo / "tests/test_split.py").write_text("# @" "prd\nT-002.1\n")  # CITE's \s+ spans a newline; a trace per-line scan does not
    commit(repo, "split citation")
    assert diff(repo) == []


def test_e015_an_uncommitted_citing_test_silences_the_tid(srepo):
    # 0.8.3 spec §5, E-015
    edit_case(srepo)
    commit(srepo, "fix the case")
    assert len(stale(srepo, "T-001.1")) == 1
    (srepo / "tests/test_import2.py").write_text("# @" "prd T-001.1\ndef test_j():\n    pass\n")
    rc, out, err = run(srepo, "docs/prd/orders", "--stale", "--tids", "T-001.1")
    assert (rc, out) == (0, "")


def test_e012_non_ascii_case_file_name_is_read_at_the_commit_end(repo):
    # 0.8.3 spec §5, E-012 (review fix): ls-tree must not C-quote the name, or the commit end drops the file
    d = repo / "docs/prd/orders/test-cases"
    (d / "import.yaml").rename(d / "caf\u00e9.yaml")
    (repo / STALE_TEST).write_text("# @" "prd T-001.1\ndef test_i():\n    pass\n")
    commit(repo, "test for T-001.1")
    assert stale(repo, "T-001.1") == []
