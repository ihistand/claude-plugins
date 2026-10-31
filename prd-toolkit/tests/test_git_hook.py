"""commit-msg and pre-commit hook logic, in a temp git repo with the orders fixture as a new project."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from prdlint import githook, model

CLI = Path(__file__).parent.parent / "scripts/prd_git_hook.py"


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def script(repo, name, body):
    path = repo / "bin" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)


@pytest.fixture
def repo(prd, monkeypatch):
    root = prd.parent.parent.parent
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "T")
    script(root, "ok-lint", 'for a in "$@"; do echo "$a" >> "$(dirname "$0")/../log"; done\n')
    script(root, "fail-lint", 'echo "bad thing"; exit 1\n')
    monkeypatch.setenv("PATH", f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}")
    edit(prd, "prd.md", "| `**/*.sql` | `python3 -m json.tool` |", "| `**/*.sql` | `fail-lint` |")
    edit(prd, "prd.md", "| code, schema.sql | enforced |\n", "| code, schema.sql | enforced |\n| `**/*.py` | `ok-lint` | none | code | enforced |\n")
    return root


def p(repo):
    return model.load(repo / "docs/prd/orders")


def log(repo):
    f = repo / "log"
    return f.read_text().splitlines() if f.exists() else []


def test_boundary_commit_without_refs_blocked(repo):
    assert githook.commit_msg(p(repo), repo, "Add x", ["src/app.py"], merging=False)


def test_boundary_commit_with_refs_passes(repo):
    assert githook.commit_msg(p(repo), repo, "Add x\n\nRefs: FR-001", ["src/app.py"], merging=False) == []


def test_comment_lines_stripped(repo):
    assert githook.commit_msg(p(repo), repo, "Add x\n# Refs: FR-001\n", ["src/app.py"], merging=False)


def test_prd_only_commit_passes(repo):
    assert githook.commit_msg(p(repo), repo, "PRD edit", ["docs/prd/orders/prd.md"], merging=False) == []


def test_merge_commit_passes(repo):
    assert githook.commit_msg(p(repo), repo, "Merge branch 'x'", ["src/app.py"], merging=True) == []


def run(repo, *args):
    return subprocess.run([sys.executable, str(CLI), *args], cwd=repo, capture_output=True, text=True, env=os.environ)


def stage(repo, rel):
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x\n")
    git(repo, "add", "--", rel)


def test_cli_reads_staged_and_merge_head(repo, tmp_path):
    stage(repo, "src/app.py")
    msg = tmp_path / "msg"
    msg.write_text("Add x\n")
    r = run(repo, "commit-msg", "docs/prd/orders", str(msg))
    assert r.returncode == 1
    assert "prd-toolkit: accepted forms: Refs: FR-001, E-002 | Refs: none (no behaviour change)" in r.stderr
    msg.write_text("Add x\n\nRefs: FR-001\n")
    assert run(repo, "commit-msg", "docs/prd/orders", str(msg)).returncode == 0
    msg.write_text("Merge x\n")
    (repo / ".git/MERGE_HEAD").write_text("0" * 40 + "\n")
    assert run(repo, "commit-msg", "docs/prd/orders", str(msg)).returncode == 0


def test_cli_not_a_prd_exits_2(repo, tmp_path):
    assert run(repo, "pre-commit", "nope").returncode == 2


def test_cli_pre_commit_blocks(repo):
    stage(repo, "db/x.sql")
    r = run(repo, "pre-commit", "docs/prd/orders")
    assert r.returncode == 1 and "`fail-lint`" in r.stderr


def test_pre_commit_runs_matching_rows_only(repo):
    assert githook.pre_commit(p(repo), repo, ["src/my file.py"]) == [] and log(repo) == ["src/my file.py"]


def test_pre_commit_blocks_on_failure(repo):
    out = githook.pre_commit(p(repo), repo, ["db/x.sql"])
    assert out and "`fail-lint`" in out[0] and "bad thing" in out[0]


def test_declined_rows_never_run(repo):
    edit(repo / "docs/prd/orders", "prd.md", "| code | enforced |\n", "| code | declined |\n")
    assert githook.pre_commit(p(repo), repo, ["src/a.py"]) == [] and log(repo) == []


def test_standards_rows(repo):
    from prdlint.rules import registries

    rows = registries.standards_rows(p(repo))
    assert [(r.glob, r.command, r.decision) for r in rows] == [
        ("**/*.sql", "fail-lint", "enforced"), ("**/*.py", "ok-lint", "enforced")]
    assert all(r.line > 0 for r in rows)


def _commit_app(repo):
    stage(repo, "src/app.py")
    git(repo, "commit", "-q", "-m", "seed", "--no-verify")


def test_cli_blocks_deletion_without_refs(repo, tmp_path):
    _commit_app(repo)
    git(repo, "rm", "-q", "src/app.py")
    msg = tmp_path / "msg"
    msg.write_text("Remove app\n")
    assert run(repo, "commit-msg", "docs/prd/orders", str(msg)).returncode == 1
    msg.write_text("Remove app\n\nRefs: FR-001\n")
    assert run(repo, "commit-msg", "docs/prd/orders", str(msg)).returncode == 0


def test_cli_blocks_rename_out_of_boundary(repo, tmp_path):
    _commit_app(repo)
    (repo / ".prd-toolkit").mkdir()
    git(repo, "mv", "src/app.py", ".prd-toolkit/moved.py")
    msg = tmp_path / "msg"
    msg.write_text("Move app\n")
    assert run(repo, "commit-msg", "docs/prd/orders", str(msg)).returncode == 1


def test_cli_pre_commit_skips_deleted_paths(repo):
    stage(repo, "src/gone.py")
    git(repo, "commit", "-q", "-m", "seed", "--no-verify")
    git(repo, "rm", "-q", "src/gone.py")
    assert run(repo, "pre-commit", "docs/prd/orders").returncode == 0 and log(repo) == []
