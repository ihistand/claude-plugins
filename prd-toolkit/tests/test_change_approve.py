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


AUTHOR_NAME, AUTHOR_EMAIL = "Test Author", "test@example.com"  # the configured identity the commit must carry


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8").stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    r = deploy_repo(tmp_path)
    git(r, "config", "user.name", AUTHOR_NAME)
    git(r, "config", "user.email", AUTHOR_EMAIL)
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
    assert git(recorded, "log", "-1", "--format=%an <%ae>").strip() == f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>"
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


def test_refs_with_a_newline_is_a_usage_error(recorded):
    before = snapshot(recorded)
    code, _, err = approve(recorded, REPLY, DRY, "--refs", "FR-002\nFR-003")
    assert code == 2 and err.strip() == "approve: --refs must be one line" and snapshot(recorded) == before


def test_a_reply_line_that_looks_like_a_trailer_does_not_become_one(recorded):
    reply = "yes\nRefs: x\nmore"
    code, _, err = approve(recorded, reply)
    assert code == 0, err
    body = git(recorded, "log", "-1", "--format=%B").rstrip()
    assert 'Reply: "yes\n Refs: x\nmore"' in body  # one space keeps the line from reading as a trailer
    assert body.split("\n\n")[-1] == "Refs: none (no behaviour change)"
    assert git(recorded, "log", "-1", "--format=%(trailers:key=Refs,valueonly)").strip() == "none (no behaviour change)"
    traced = subprocess.run([sys.executable, str(SCRIPTS / "prd_trace.py"), str(recorded / PRD), "--range", "HEAD~1..HEAD"], cwd=recorded, capture_output=True, text=True)
    assert traced.returncode == 0, traced.stdout + traced.stderr


def test_the_commit_when_the_verdict_is_git_ignored(recorded):
    """F-1 (0.8.1 proof): prd_hooks.py ignores `.prd-review.json`; a literal exclude pathspec naming an ignored file made `git add` exit 1."""
    gi = recorded / ".gitignore"
    gi.write_text(gi.read_text(encoding="utf-8") + ".prd-review.json\n", encoding="utf-8")
    git(recorded, "add", ".gitignore")
    git(recorded, "commit", "-q", "-m", "chore: ignore the review verdict")
    code, out, err = approve(recorded)
    assert code == 0, err
    files = git(recorded, "show", "--name-only", "--format=", "HEAD").split()
    assert f"{PRD}/prd.md" in files and "CLAUDE.md" in files
    assert not any(f.endswith(".prd-review.json") for f in files)
    assert not (recorded / PRD / ".prd-review.json").exists()
    assert git(recorded, "status", "--porcelain").strip() == ""


def test_a_failed_add_leaves_the_index_and_the_tree_as_they_were(recorded, monkeypatch):
    """F-1 (0.8.1 proof): `git add` can stage some paths and still exit 1; approve must unstage them, as it does for a failed commit."""
    from prdlint import change_approve

    real = change_approve._git

    def add_then_fail(repo_root, *args):
        done = real(repo_root, *args)
        if args and args[0] == "add":
            return subprocess.CompletedProcess(done.args, 1, done.stdout, "fatal: simulated add failure")
        return done

    monkeypatch.setattr(change_approve, "_git", add_then_fail)
    staged = git(recorded, "diff", "--cached", "--name-only")
    before = snapshot(recorded)
    code, _, err = approve(recorded)
    assert code == 1 and err.startswith("refused: git add failed: fatal: simulated add failure"), err
    assert git(recorded, "diff", "--cached", "--name-only") == staged
    assert snapshot(recorded) == before


# --- R20: CLAUDE.md is committed only when prd_block changed it, and a dirty one is refused ---

def commit_claude_block(repo):
    """CLAUDE.md as prd_block writes it for the recorded version, committed: the next block run leaves it as it is."""
    from prdlint import change_approve

    change_approve._block(repo / PRD)
    git(repo, "add", "CLAUDE.md")
    git(repo, "commit", "-q", "-m", "docs: the PRD block")


def test_a_dirty_claude_md_is_refused_and_every_file_stays(recorded):
    claude = recorded / "CLAUDE.md"
    claude.write_text("# My notes\n", encoding="utf-8")  # untracked counts as uncommitted
    refused(recorded, "CLAUDE.md has uncommitted changes; commit or set them aside first")
    commit_claude_block(recorded)
    claude.write_text(claude.read_text(encoding="utf-8") + "\nMY UNRELATED NOTE\n", encoding="utf-8")
    refused(recorded, "CLAUDE.md has uncommitted changes; commit or set them aside first")


def test_a_clean_claude_md_that_prd_block_changes_is_committed(recorded):
    claude = recorded / "CLAUDE.md"
    claude.write_text("# Notes\n", encoding="utf-8")
    git(recorded, "add", "CLAUDE.md")
    git(recorded, "commit", "-q", "-m", "docs: notes")
    code, _, err = approve(recorded)
    assert code == 0, err
    assert "CLAUDE.md" in git(recorded, "show", "--name-only", "--format=", "HEAD").split()
    assert "## Product requirements" in git(recorded, "show", "HEAD:CLAUDE.md")
    assert git(recorded, "status", "--porcelain").strip() == ""


def test_a_clean_claude_md_that_prd_block_leaves_alone_is_not_in_the_commit(recorded):
    commit_claude_block(recorded)
    code, _, err = approve(recorded)
    assert code == 0, err
    files = git(recorded, "show", "--name-only", "--format=", "HEAD").split()
    assert "CLAUDE.md" not in files and f"{PRD}/prd.md" in files
    assert git(recorded, "status", "--porcelain").strip() == ""


# --- line endings ---

def test_approve_keeps_a_crlf_prd_md_crlf(recorded):
    md = recorded / PRD / "prd.md"
    md.write_bytes(md.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    verdict(recorded)
    code, _, err = approve(recorded)
    assert code == 0, err
    data = md.read_bytes()
    assert data.count(b"\n") == data.count(b"\r\n")
    assert b"\r\nstatus: Approved\r\n" in data and f"Repeat lookups; {DRY} | FR-002, AC-002.3, T-002.3 |\r\n".encode() in data and b"; pending" not in data
