"""prd_error.py check: every change to errors.md in a git range, and the commit gate for an unconfirmed entry."""
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE
from deploy_fixture import deploy_repo
from legacy import commit, git
from test_deploy import OPS, change, deploy_cli, run_id_of

from prdlint import deploy, errors, model, trace

PRD = "docs/prd/orders"
ERRORS = f"{PRD}/errors.md"
SCRIPT = Path(__file__).resolve().parent.parent / "scripts/prd_error.py"
LEGACY = """# Error ledger

### E-001 Empty import file crashed the importer
Detected: 2026-10-29, test failure in T-001.3
Classification: code bug
Diagnosis: the importer indexed the first row of an empty file
Resolution: the importer returns status `empty` before reading rows; T-001.3 passes
Recurrence of: -
"""
CONFIRMED = 'Confirmed: 2026-11-03, "yes, it is a code bug"'


def entry(n=2, title="Greeting drops a word", detected="2026-11-03, user report (/prd-error)", cls="code bug",
          confirmed=CONFIRMED, resolution="-"):
    lines = [f"### E-{n:03d} {title}", f"Detected: {detected}", f"Classification: {cls}"]
    if confirmed:
        lines.append(confirmed)
    lines += ["Diagnosis: AC-001.1 says otherwise", f"Resolution: {resolution}", "Recurrence of: -"]
    return "\n".join(lines) + "\n"


def ledger(*entries):
    return LEGACY + "".join("\n" + e for e in entries)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def sha(repo, rev="HEAD") -> str:
    return git(repo, "rev-parse", rev).strip()


def put(repo, text, msg="Edit the ledger") -> None:
    (repo / ERRORS).write_text(text, encoding="utf-8")
    commit(repo, msg, ERRORS)


def start(repo, *entries) -> str:
    """Commit a ledger holding `entries` and return its sha: the base of the range."""
    put(repo, ledger(*entries), "Base ledger")
    return sha(repo)


def check(repo, base) -> list[str]:
    return errors.check_findings(model.load(repo / PRD), repo, f"{base}..HEAD")


def pre(eid="E-002"):
    return f"errors.md: {eid}: "


def fix(t="T-001.1", version="1.0.0", commit_="{fix}") -> str:
    return f"{t} [integration], PRD {version}, fixed in {commit_}"


def resolved(repo, resolution, **kw) -> str:
    return entry(resolution=resolution.replace("{fix}", sha(repo)[:7]), **kw)


def test_clean_range(repo):
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix())))
    assert check(repo, base) == []


def test_legacy_resolved_entry_with_no_confirmed_is_fine(repo):
    base = start(repo, entry())
    (repo / "README.md").write_text("x\n")
    commit(repo, "Unrelated", "README.md")
    assert check(repo, base) == []


def test_deleted(repo):
    base = start(repo, entry(2), entry(3, title="Other"))
    put(repo, ledger(entry(3, title="Other")))
    assert check(repo, base) == [pre("E-002") + "deleted"]


def test_renumbered(repo):
    base = start(repo, entry(2))
    put(repo, ledger(entry(3)))
    assert check(repo, base) == [pre("E-002") + "renumbered to E-003"]


def test_moved_before(repo):
    base = start(repo, entry(2, title="A"), entry(3, title="B"), entry(4, title="C"))
    put(repo, ledger(entry(2, title="A"), entry(4, title="C"), entry(3, title="B")))
    assert check(repo, base) == [pre("E-004") + "moved before E-003"]


def test_detected_changed(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(detected="2026-11-04, user report (/prd-error)")))
    assert check(repo, base) == [pre() + "Detected: changed"]


def test_classification_changed_after_confirmed(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(cls="spec gap")))
    assert check(repo, base) == [pre() + "Classification: changed after Confirmed:"]


def test_confirmed_changed(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(confirmed='Confirmed: 2026-11-04, "ok"')))
    assert check(repo, base) == [pre() + "Confirmed: changed"]


def test_change_then_revert_inside_the_range_is_still_caught(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(cls="spec gap")))
    put(repo, ledger(entry()))
    assert check(repo, base) == [pre() + "Classification: changed after Confirmed:"]


def test_confirming_in_the_range_may_set_class(repo):
    base = start(repo, entry(cls="spec gap", confirmed=None))
    put(repo, ledger(entry(cls="code bug")))
    assert check(repo, base) == []


def test_resolved_without_confirmed(repo):
    base = start(repo, entry(confirmed=None))
    put(repo, ledger(resolved(repo, fix(), confirmed=None)))
    assert check(repo, base) == [pre() + "resolved without Confirmed:"]


def test_resolution_not_a_form(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(resolution="fixed it, T-001.1 passes")))
    assert check(repo, base) == [pre() + "resolution is not one of the three forms"]


def test_not_a_defect_and_run_without_t_are_forms(repo):
    run_id = failed(repo)
    good = good_run(repo)
    base = start(repo, entry(2), entry(3, title="B"))
    put(repo, ledger(entry(2, resolution="not a defect: the input was invalid"),
                     entry(3, title="B", resolution=f"-, PRD 1.0.0, run {good}")))
    assert check(repo, base) == [] and run_id != good


def test_t_id_without_a_test_case(repo):
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix("T-001.9"))))
    assert check(repo, base) == [pre() + "T-001.9 has no test case"]


def test_t_id_cited_by_no_test(repo):
    p = repo / "tests/test_cases.py"
    p.write_text(p.read_text().replace('@' 'prd T-001.1"""', 'no citation"""'))
    commit(repo, "Drop a citation", "tests")
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix())))
    assert check(repo, base) == [pre() + "T-001.1 is cited by no test"]


def test_still_known_failing_on_a_case(repo):
    change(repo, f"{PRD}/test-cases/import.yaml", "T-001.1:\n  ac: AC-001.1\n", "T-001.1:\n  ac: AC-001.1\n  known-failing: E-002\n")
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix())))
    assert pre() + "T-001.1 is still known-failing on E-002" in check(repo, base)


def test_still_known_failing_on_a_tag(repo):
    p = repo / "tests/test_cases.py"
    p.write_text(p.read_text().replace('@' 'prd T-001.1"""', '@' 'prd T-001.1  known-failing: E-002"""'))
    commit(repo, "Tag a test", "tests")
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix())))
    assert check(repo, base) == [pre() + "T-001.1 is still known-failing on E-002"]


def test_known_failing_on_another_entry_is_not_this_one(repo):
    p = repo / "tests/test_cases.py"
    p.write_text(p.read_text().replace('@' 'prd T-001.1"""', '@' 'prd T-001.1 known-failing E-009"""'))
    commit(repo, "Tag a test", "tests")
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix())))
    assert check(repo, base) == []


def test_version_above_the_prd(repo):
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix(version="9.9.9"))))
    assert check(repo, base) == [pre() + "PRD 9.9.9 is above the PRD version 1.0.0"]


def test_version_with_no_changelog_row(repo):
    change(repo, f"{PRD}/prd.md", "version: 1.0.0\n", "version: 1.0.5\n")
    base = start(repo, entry())
    put(repo, ledger(resolved(repo, fix(version="1.0.5"))))
    assert check(repo, base) == [pre() + "PRD 1.0.5 has no changelog row"]


def test_commit_not_an_ancestor_of_head(repo):
    git(repo, "checkout", "-q", "-b", "side")
    (repo / "side.txt").write_text("x\n")
    commit(repo, "On a side branch", "side.txt")
    side = sha(repo)[:7]
    git(repo, "checkout", "-q", "main")
    base = start(repo, entry())
    put(repo, ledger(entry(resolution=fix(commit_=side))))
    assert check(repo, base) == [pre() + f"commit {side} is not an ancestor of HEAD"]


def test_commit_that_does_not_exist(repo):
    base = start(repo, entry())
    put(repo, ledger(entry(resolution=fix(commit_="1234567"))))
    assert check(repo, base) == [pre() + "commit 1234567 is not an ancestor of HEAD"]


def failed(repo) -> str:
    change(repo, OPS, "echo Hi > .deploy/staging/greeting", "echo Bad > .deploy/staging/greeting")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4, r.stdout + r.stderr
    return run_id_of(r)


def test_run_did_not_finish_the_failed_environment(repo):
    run_id = failed(repo)
    det = f"2026-11-03, deploy {run_id} step 1"
    base = start(repo, entry(detected=det, cls="environment"))
    put(repo, ledger(entry(detected=det, cls="environment", resolution=f"-, PRD 1.0.0, run {run_id}")))
    assert check(repo, base) == [pre() + "run " + run_id + " did not finish staging"]


def test_run_that_finished_the_environment(repo):
    run_id = failed(repo)
    det = f"2026-11-03, deploy {run_id} step 1"
    change(repo, OPS, "echo Bad > .deploy/staging/greeting", "echo Hi > .deploy/staging/greeting")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    good = run_id_of(r)
    base = start(repo, entry(detected=det, cls="environment"))
    put(repo, ledger(entry(detected=det, cls="environment", resolution=f"-, PRD 1.0.0, run {good}")))
    assert check(repo, base) == []


def good_run(repo) -> str:
    change(repo, OPS, "echo Bad > .deploy/staging/greeting", "echo Hi > .deploy/staging/greeting")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    return run_id_of(r)


def resolve_env(repo, base, det, run, cls="environment"):
    put(repo, ledger(entry(detected=det, cls=cls, resolution=f"-, PRD 1.0.0, run {run}")))
    return check(repo, base)


def test_run_without_a_log(repo):
    run_id = failed(repo)
    det = f"2026-11-03, deploy {run_id} step 1"
    base = start(repo, entry(detected=det, cls="environment"))
    gone = "20261101T000000Z-all"
    assert resolve_env(repo, base, det, gone) == [pre() + f"run {gone} has no log in {deploy.log_dir(repo)}"]


def test_failed_run_named_in_detected_without_a_log(repo):
    run_id = failed(repo)
    good = good_run(repo)
    gone = "20261031T000000Z-all"
    det = f"2026-11-03, deploy {gone} step 1"
    base = start(repo, entry(detected=det, cls="environment"))
    assert run_id != good
    assert resolve_env(repo, base, det, good) == [pre() + f"the failed run {gone} named in Detected: has no log in {deploy.log_dir(repo)}"]


def test_failed_environment_comes_from_the_log_when_detected_has_no_step(repo):
    run_id = failed(repo)
    det = f"2026-11-03, deploy {run_id}"
    base = start(repo, entry(detected=det, cls="environment"))
    assert resolve_env(repo, base, det, run_id) == [pre() + f"run {run_id} did not finish staging"]
    good = good_run(repo)
    assert resolve_env(repo, base, det, good) == []


def test_detected_naming_no_run_needs_the_run_to_finish_its_plan(repo):
    run_id = failed(repo)
    det = "2026-11-03, reported by a user"
    base = start(repo, entry(detected=det, cls="environment"))
    assert resolve_env(repo, base, det, run_id) == [pre() + f"run {run_id} did not finish staging", pre() + f"run {run_id} did not finish production"]
    good = good_run(repo)
    assert resolve_env(repo, base, det, good) == []


def code(repo, name, msg) -> str:
    (repo / name).write_text(name + "\n")
    commit(repo, msg, name)
    return sha(repo)[:8]


def test_code_commit_citing_an_entry_before_it_was_confirmed(repo):
    """Review Focus 5: head is confirmed, but the code commit before the confirmation is a finding."""
    base = start(repo, entry(confirmed=None))
    early = code(repo, "a.py", "Fix a\n\nRefs: E-002")
    put(repo, ledger(entry()), "Confirm")
    late = code(repo, "b.py", "Fix b\n\nRefs: E-002")
    assert check(repo, base) == [pre() + f"commit {early} changes code and cites E-002, which was not confirmed at that commit"]
    assert late != early


def test_code_commit_after_confirmation_is_fine(repo):
    base = start(repo, entry(confirmed=None))
    put(repo, ledger(entry()), "Confirm")
    code(repo, "b.py", "Fix b\n\nRefs: E-002")
    assert check(repo, base) == []


def test_a_prd_only_commit_may_cite_an_unconfirmed_entry(repo):
    base = start(repo, entry(confirmed=None))
    (repo / PRD / "notes.txt").write_text("x\n")
    commit(repo, "PRD only\n\nRefs: E-002", PRD)
    assert check(repo, base) == []


def run_cli(repo, *args):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8", cwd=repo)


def test_cli_findings_exit_1(repo):
    base = start(repo, entry())
    put(repo, ledger())
    r = run_cli(repo, "check", str(repo / PRD), f"{base}..HEAD")
    assert (r.returncode, r.stdout, r.stderr) == (1, pre("E-002") + "deleted\n", "")


def test_cli_clean_exit_0(repo):
    base = start(repo, entry())
    r = run_cli(repo, "check", str(repo / PRD), f"{base}..HEAD")
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


def test_cli_bad_range_exit_2_with_empty_stdout(repo):
    r = run_cli(repo, "check", str(repo / PRD), "nope")
    assert r.returncode == 2 and r.stdout == "" and r.stderr


def test_refs_problems_gate_unit(repo):
    base = start(repo, entry(confirmed=None))
    prd = model.load(repo / PRD)
    msg = "x\n\nRefs: E-002"
    assert trace.refs_problems(prd, msg) == []
    assert trace.refs_problems(prd, msg, code_commit=True) == [
        "E-002 is not confirmed; a commit that changes code may cite it only after prd_error.py confirm"]
    assert base


# --- fix round 1 ---

@pytest.mark.parametrize("bad, finding", [
    ("garbage ???", "resolution is not one of the three forms"),
    ("T-001.1 [integration], PRD 1.0.0, fixed in 1234567", "commit 1234567 is not an ancestor of HEAD"),
    ("T-001.1 [integration], PRD 9.9.9, fixed in {fix}", "PRD 9.9.9 is above the PRD version 1.0.0"),
    ("T-001.9 [integration], PRD 1.0.0, fixed in {fix}", "T-001.9 has no test case"),
])
def test_rewriting_a_resolved_resolution_is_checked(repo, bad, finding):
    base = start(repo, resolved(repo, fix()))
    put(repo, ledger(resolved(repo, bad)))
    assert check(repo, base) == [pre() + finding]


def test_rewritten_resolution_needs_confirmed(repo):
    base = start(repo, entry(confirmed=None, resolution="old free text"))
    put(repo, ledger(resolved(repo, fix(), confirmed=None)))
    assert check(repo, base) == [pre() + "resolved without Confirmed:"]


def side_branch(repo, ledger_text=None):
    git(repo, "checkout", "-q", "-b", "side")
    if ledger_text:
        put(repo, ledger_text, "On the side")
    else:
        code(repo, "side.txt", "On the side")
    git(repo, "checkout", "-q", "main")
    (repo / "README.md").write_text("main\n")
    commit(repo, "Unrelated on main", "README.md")


def test_merged_side_branch_is_clean(repo):
    base = start(repo, entry(2))
    side_branch(repo, ledger(entry(2), entry(3, title="B")))
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge side", "side")
    assert check(repo, base) == []


def test_deletion_inside_a_merge(repo):
    base = start(repo, entry(2))
    side_branch(repo)
    git(repo, "merge", "-q", "--no-ff", "--no-commit", "side")
    put(repo, ledger(), "Merge side")
    assert check(repo, base) == [pre() + "deleted"]


def test_merge_that_changes_code_and_cites_an_unconfirmed_entry(repo):
    base = start(repo, entry(2, confirmed=None))
    side_branch(repo)
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge side\n\nRefs: E-002", "side")
    merge = sha(repo)[:8]
    assert check(repo, base) == [pre() + f"commit {merge} changes code and cites E-002, which was not confirmed at that commit"]
