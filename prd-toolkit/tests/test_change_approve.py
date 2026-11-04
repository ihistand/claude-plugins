"""prd_change.py approve (0.8.1): the §14 record, the status and the approval commit, after every check."""
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from deploy_fixture import deploy_repo
from prd_change import main as change_main
from prdlint import change
from test_change_bump import PRD
from test_change_record import new_ac_with_test

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
REPLY = 'yes - "sí", then "no"\nship it  \n# not a comment'
DRY = "dry run T-002.3, 0 open questions, 1 dismissed by quote"
FILES = (".prd-review.json", "docs", "CLAUDE.md")


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = change_main(list(argv))
    return code, out.getvalue(), err.getvalue()


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8").stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    r = deploy_repo(tmp_path)
    git(r, "config", "user.name", "Ivan Histand")
    git(r, "config", "user.email", "ihistand@rotoplas.com")
    git(r, "config", "commit.gpgsign", "false")
    return r


def verdict(repo, **over):
    v = {"interface": 1, "kind": "review", "head": "x", "digest": change.digest(repo / PRD), "restate": "r", "touches": ["AC-002.3"],
         "impact": {"exit": 0, "lines": []}, "bump": {"level": "minor", "decided": []},
         "dry_run": {"tids": ["T-002.3"], "open": 0, "dismissed": 1, "record": DRY}, "ready": True, "blockers": []}
    v.update(over)
    (repo / PRD / ".prd-review.json").write_text(json.dumps(v), encoding="utf-8")


@pytest.fixture
def recorded(repo):
    """A recorded, reviewed change: a new AC with an integration case, status In review, §14 row `; pending`."""
    prd = repo / PRD
    new_ac_with_test(prd)
    edit(prd, "prd.md", "\nstatus: Approved\n", "\nstatus: In review\n")
    (repo / "tests/test_repeat.py").write_text('def test_repeat():\n    """@prd T-002.3"""\n', encoding="utf-8")
    git(repo, "add", "tests/test_repeat.py")
    git(repo, "commit", "-q", "-m", "test: T-002.3")
    change.record(repo, prd, "HEAD", "minor", "Repeat lookups", "2026-11-04")
    verdict(repo)
    return repo


def approve(repo, reply=REPLY, dry=DRY, *extra):
    return call("approve", str(repo / PRD), "--reply", reply, "--dry-run", dry, *extra)


def snapshot(repo):
    return {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".git/" not in p.as_posix()}


def refused(repo, why, **kw):
    before = snapshot(repo)
    code, out, err = approve(repo, **kw)
    assert code == 1 and err.strip() == f"refused: {why}", (code, err)
    assert snapshot(repo) == before  # byte-identical, .prd-review.json included


def test_an_empty_reply_is_refused(recorded):
    refused(recorded, "the owner's reply is empty", reply="  \n")


def test_a_missing_verdict_is_refused(recorded):
    (recorded / PRD / ".prd-review.json").unlink()
    refused(recorded, "there is no .prd-review.json; run the review first")


def test_a_verdict_not_ready_is_refused(recorded):
    verdict(recorded, ready=False, blockers=["lint fails"])
    refused(recorded, "the review is not ready: lint fails")


def test_an_edit_after_the_verdict_is_refused_on_the_digest(recorded):
    edit(recorded / PRD, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order")
    refused(recorded, "the PRD changed after its review; review it again")


def test_lint_failing_is_refused(recorded):
    edit(recorded / PRD, "features/api.md", "T-002.3 [integration]", "T-002.3 [integration], T-099.1 [unit]")
    verdict(recorded)
    before = snapshot(recorded)
    code, _, err = approve(recorded)
    assert code == 1 and err.startswith("refused: lint exits ") and snapshot(recorded) == before


def test_pending_dry_run_with_a_non_unit_test_is_refused(recorded):
    refused(recorded, "the change adds or revises a non-unit test (T-002.3) and has no dry-run record", dry="no dry run: it is a typo")


PENDING = 'the dry-run record is pending; give the record or "no dry run (<why>)"'


@pytest.mark.parametrize("record", ["pending", "  pending \t", "", "   "])
def test_an_empty_or_pending_record_is_always_refused(recorded, record):
    refused(recorded, PENDING, dry=record)


def test_a_unit_only_pending_record_is_refused(recorded):
    edit(recorded / PRD, "test-cases/api.yaml", "T-002.3:\n  ac: AC-002.3\n  level: integration", "T-002.3:\n  ac: AC-002.3\n  level: unit")
    edit(recorded / PRD, "features/api.md", "T-002.3 [integration]", "T-002.3 [unit]")
    verdict(recorded)
    refused(recorded, PENDING, dry="pending")


def test_a_unit_test_alone_may_have_no_dry_run(recorded):
    edit(recorded / PRD, "test-cases/api.yaml", "T-002.3:\n  ac: AC-002.3\n  level: integration", "T-002.3:\n  ac: AC-002.3\n  level: unit")
    edit(recorded / PRD, "features/api.md", "T-002.3 [integration]", "T-002.3 [unit]")
    verdict(recorded)
    code, _, err = approve(recorded, dry="no dry run (unit only)")
    assert code == 0, err
    assert "; pending" not in (recorded / PRD / "prd.md").read_text(encoding="utf-8")


def test_a_removed_t_id_in_the_row_is_skipped(recorded):
    prd = recorded / PRD
    md = (prd / "prd.md").read_text(encoding="utf-8")
    (prd / "prd.md").write_text(md.replace("| AC-002.3, T-002.3 |", "| AC-002.3, T-002.3, T-002.9 |"), encoding="utf-8")
    verdict(recorded)
    code, _, err = approve(recorded)
    assert code == 0, err


def test_a_first_approval_is_refused(recorded):
    prd = recorded / PRD
    md = (prd / "prd.md").read_text(encoding="utf-8")
    rows = [ln for ln in md.splitlines() if ln.startswith("| 1.") and "|" in ln]
    for ln in rows:
        if not ln.startswith("| 1.1.0 |"):
            md = md.replace(ln + "\n", "")
    (prd / "prd.md").write_text(md.replace("| 1.1.0 |", "| 0.9.0 |").replace("\nversion: 1.1.0\n", "\nversion: 0.9.0\n"), encoding="utf-8")
    verdict(recorded)
    refused(recorded, "a first approval is authoring's, not a change's")


def test_an_unrecorded_change_is_refused(recorded):
    prd = recorded / PRD
    md = (prd / "prd.md").read_text(encoding="utf-8")
    (prd / "prd.md").write_text(md.replace("; pending |", " |"), encoding="utf-8")
    verdict(recorded)
    refused(recorded, "the last §14 row is not recorded and pending; run record first")


def test_the_commit(recorded):
    code, out, err = approve(recorded)
    assert code == 0, err
    sha = git(recorded, "rev-parse", "--short", "HEAD").strip()
    assert out == f"approved orders 1.1.0 {sha}\n"
    assert git(recorded, "log", "-1", "--format=%an <%ae>").strip() == "Ivan Histand <ihistand@rotoplas.com>"
    assert git(recorded, "log", "-1", "--format=%s").strip() == "docs(prd): approve orders 1.1.0"
    body = git(recorded, "log", "-1", "--format=%B")
    assert f'Reply: "{REPLY}"\n' in body, body
    assert f"Dry run: {DRY}\n" in body
    assert body.rstrip().endswith("Refs: none (no behaviour change)")
    files = git(recorded, "show", "--name-only", "--format=", "HEAD").split()
    assert "CLAUDE.md" in files and f"{PRD}/prd.md" in files
    assert not any(f.endswith(".prd-review.json") for f in files)
    assert not (recorded / PRD / ".prd-review.json").exists()
    md = (recorded / PRD / "prd.md").read_text(encoding="utf-8")
    assert "\nstatus: Approved\n" in md and f"Repeat lookups; {DRY} |" in md and "; pending" not in md
    assert git(recorded, "status", "--porcelain").strip() == ""
    traced = subprocess.run([sys.executable, str(SCRIPTS / "prd_trace.py"), str(recorded / PRD), "--range", "HEAD~1..HEAD"], cwd=recorded, capture_output=True, text=True)
    assert traced.returncode == 0, traced.stdout + traced.stderr


def test_refs_replace_the_trailer(recorded):
    code, _, err = approve(recorded, REPLY, DRY, "--refs", "FR-002, E-004")
    assert code == 0, err
    assert git(recorded, "log", "-1", "--format=%B").rstrip().endswith("Refs: FR-002, E-004")


def test_json_output(recorded):
    code, out, err = approve(recorded, REPLY, DRY, "--json")
    assert code == 0, err
    doc = json.loads(out)
    assert doc["kind"] == "change.approve" and doc["commit"] == git(recorded, "rev-parse", "HEAD").strip()


def test_a_dry_run_record_with_a_newline_is_refused(recorded):
    refused(recorded, "the dry-run record must be one non-empty line without |", dry="a\nb")
