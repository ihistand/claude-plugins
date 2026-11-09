"""install refreshes the three managed blocks; check --ci reports stale ones; the vendored copy holds the templates and the home page."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from prdlint import hooks

PLUGIN_ROOT = Path(__file__).parent.parent
PRD = "docs/prd/orders"
HOMEPAGE = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text())["homepage"]


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def run(repo, script, *args):
    return subprocess.run([sys.executable, str(script), *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")


def check_ci(repo):
    return run(repo, PLUGIN_ROOT / "scripts/prd_hooks.py", "check", "--ci", PRD)


def test_vendored_copy_holds_templates_and_homepage(repo):
    hooks.install(repo, PRD)
    t = repo / ".prd-toolkit/templates"
    for name in ("claude-block.md", "readme-prd.md", "readme-prds.md"):
        assert (t / name).read_bytes() == (PLUGIN_ROOT / "templates" / name).read_bytes()
    assert (repo / ".prd-toolkit/HOMEPAGE").read_text() == HOMEPAGE + "\n"


def test_install_writes_the_three_blocks_and_says_so(repo):
    lines = hooks.install(repo, PRD)
    for rel in ("CLAUDE.md", f"{PRD}/README.md", "docs/prd/README.md"):
        assert (repo / rel).is_file() and f"refreshed {rel}" in lines
    assert "prd-toolkit:start" in (repo / "CLAUDE.md").read_text()
    again = hooks.install(repo, PRD)
    assert not any(x.startswith("refreshed ") for x in again)


def test_check_ci_names_a_stale_readme_and_a_stale_claude_block(repo):
    hooks.install(repo, PRD)
    assert check_ci(repo).returncode == 0
    readme = repo / PRD / "README.md"
    readme.write_text(readme.read_text().replace("# orders", "# edited", 1))
    r = check_ci(repo)
    assert r.returncode == 1 and f"stale: {PRD}/README.md; run prd_block.py {PRD}" in r.stdout
    assert run(repo, PLUGIN_ROOT / "scripts/prd_block.py", PRD).returncode == 0
    assert check_ci(repo).returncode == 0
    claude = repo / "CLAUDE.md"
    claude.write_text(claude.read_text().replace("Every behaviour change", "Any change", 1))
    r = check_ci(repo)
    assert r.returncode == 1 and f"stale: CLAUDE.md; run prd_block.py {PRD}" in r.stdout
    assert run(repo, PLUGIN_ROOT / "scripts/prd_block.py", PRD).returncode == 0
    assert check_ci(repo).returncode == 0


def test_vendored_prd_block_writes_the_same_bytes(repo, tmp_path):
    hooks.install(repo, PRD)
    want = {rel: (repo / rel).read_bytes() for rel in ("CLAUDE.md", f"{PRD}/README.md", "docs/prd/README.md")}
    for rel in want:
        (repo / rel).unlink()
    assert run(repo, repo / ".prd-toolkit/prd_block.py", PRD).returncode == 0
    assert {rel: (repo / rel).read_bytes() for rel in want} == want
    assert HOMEPAGE.encode() in want["docs/prd/README.md"]


def broken(repo):
    readme = repo / PRD / "README.md"
    readme.write_text("<!-- prd-toolkit:start -->\nhand text\n<!-- prd-toolkit:start -->\n")
    return readme


def test_check_ci_reports_a_broken_marker_as_stale_exit_1(repo):
    hooks.install(repo, PRD)
    broken(repo)
    r = check_ci(repo)
    assert r.returncode == 1 and r.stderr == ""
    assert f"stale: {PRD}/README.md: more than one prd-toolkit block; run prd_block.py {PRD}" in r.stdout


def test_install_with_a_broken_marker_refuses_and_writes_nothing(repo):
    readme = broken(repo)
    before = readme.read_text()
    r = run(repo, PLUGIN_ROOT / "scripts/prd_hooks.py", "install", PRD)
    assert r.returncode == 1 and "internal error" not in r.stderr
    assert f"install refused: {PRD}/README.md: more than one prd-toolkit block; fix the marker, then run prd_block.py {PRD}" in r.stderr
    assert readme.read_text() == before
    assert not (repo / ".prd-toolkit").exists() and not (repo / ".git/hooks/commit-msg").exists()
    assert not (repo / "CLAUDE.md").exists() and not (repo / ".gitignore").exists()


def test_check_ci_skips_a_git_ignored_claude_md_in_a_fresh_clone(repo, tmp_path):
    (repo / ".gitignore").write_text("CLAUDE.md\n")
    hooks.install(repo, PRD)
    assert (repo / "CLAUDE.md").exists()
    assert check_ci(repo).returncode == 0
    git = ["git", "-c", "core.hooksPath=/dev/null", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "x"], cwd=repo, check=True)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
    assert not (clone / "CLAUDE.md").exists()
    r = check_ci(clone)
    assert (r.returncode, r.stdout) == (0, "")
    (clone / ".gitignore").write_text("")
    r = check_ci(clone)
    assert r.returncode == 1 and f"stale: CLAUDE.md; run prd_block.py {PRD}" in r.stdout
