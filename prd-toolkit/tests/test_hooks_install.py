"""prd_hooks.py install | check | uninstall, in a temp git repo with the orders fixture."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from prdlint import hooks

PLUGIN_ROOT = Path(__file__).parent.parent
PLUGIN_VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text())["version"]
PRD = "docs/prd/orders"


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)
    return r.stdout.strip()


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "T")
    (root / "src").mkdir()
    (root / "src/app.py").write_text("x = 1\n")
    return root


def test_install_vendors_and_writes_shims(repo):
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/VERSION").read_text().strip() == PLUGIN_VERSION
    assert all((repo / ".prd-toolkit" / f).is_file() for f in hooks.VENDORED)
    assert (repo / ".prd-toolkit/prdlint/model.py").is_file()
    assert not list((repo / ".prd-toolkit").rglob("__pycache__"))
    shim = (repo / ".git/hooks/commit-msg").read_text()
    assert hooks.MARKER in shim and PRD in shim and os.access(repo / ".git/hooks/commit-msg", os.X_OK)
    assert os.access(repo / ".prd-toolkit/prd_hooks.py", os.X_OK)


def test_install_is_idempotent_and_refreshes(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/prdlint/stale.py").write_text("x\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    hooks.install(repo, PRD)
    assert not (repo / ".prd-toolkit/prdlint/stale.py").exists()
    assert hooks.check(repo, PLUGIN_ROOT) == []


def test_existing_hook_is_never_overwritten(repo):
    (repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\necho mine\n")
    lines = hooks.install(repo, PRD)
    assert (repo / ".git/hooks/pre-commit").read_text() == "#!/bin/sh\necho mine\n"
    assert any("add this line to .git/hooks/pre-commit" in x for x in lines)


def test_never_sets_hooks_path(repo):
    hooks.install(repo, PRD)
    assert git(repo, "config", "--get", "core.hooksPath", check=False) == ""


def test_check_flags_stale_version_and_changed_file(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    problems = hooks.check(repo, PLUGIN_ROOT)
    assert any("VERSION 0.0.1" in x for x in problems) and any("prd_lint.py differs" in x for x in problems)


def test_uninstall_removes_only_marked_hooks(repo):
    hooks.install(repo, PRD)
    (repo / ".git/hooks/post-commit").write_text("#!/bin/sh\necho mine\n")
    hooks.uninstall(repo)
    assert not (repo / ".git/hooks/commit-msg").exists() and (repo / ".git/hooks/post-commit").exists()
    assert (repo / ".prd-toolkit/VERSION").exists()


def commit_in(cwd, message):
    git(cwd, "add", "app.py")
    return subprocess.run(["git", "commit", "-q", "-m", message], cwd=cwd, capture_output=True, text=True)


def test_end_to_end_commit_refused_from_subdirectory(repo):
    hooks.install(repo, PRD)
    r = commit_in(repo / "src", "Add x")
    assert r.returncode != 0 and "Refs" in r.stderr
    assert commit_in(repo / "src", "Add x\n\nRefs: none (no behaviour change)").returncode == 0


def test_shim_blocks_without_uv(repo):
    assert not Path("/usr/bin/uv").exists() and not Path("/bin/uv").exists()
    hooks.install(repo, PRD)
    msg = repo / "msg"
    msg.write_text("x\n")
    r = subprocess.run([str(repo / ".git/hooks/commit-msg"), str(msg)], cwd=repo, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert r.returncode != 0 and "prd-toolkit: uv is not on PATH; install uv to run this hook" in r.stderr


def run_vendored(repo, *args):
    return subprocess.run([sys.executable, str(repo / ".prd-toolkit/prd_hooks.py"), *args], cwd=repo, capture_output=True, text=True)


def test_vendored_install_writes_shims_only(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    for h in ("commit-msg", "pre-commit"):
        (repo / ".git/hooks" / h).unlink()
    r = run_vendored(repo, "install", PRD)
    assert r.returncode == 0, r.stderr
    assert (repo / ".git/hooks/commit-msg").is_file() and (repo / ".git/hooks/pre-commit").is_file()
    assert (repo / ".prd-toolkit/VERSION").read_text() == "0.0.1\n"
    assert (repo / ".prd-toolkit/prd_lint.py").read_text() == "# changed\n"


def test_vendored_check_exits_2(repo):
    hooks.install(repo, PRD)
    r = run_vendored(repo, "check", PRD)
    assert r.returncode == 2 and "run check from the plugin, not the vendored copy" in r.stderr and r.stdout == ""
