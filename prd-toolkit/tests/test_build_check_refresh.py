"""prd_build_check.py --diff: an exact .prd-toolkit/ refresh is accepted, anything else under it is not."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import FIXTURE, PLUGINS_FILE

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from prdlint import buildcheck, model  # noqa: E402

REAL = Path(__file__).resolve().parent.parent
SCRIPT = REAL / "scripts/prd_build_check.py"
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
PRD = "docs/prd/orders"
OLD = ".prd-toolkit/x: the builder may not edit the vendored .prd-toolkit/ copy"


def git(root: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit(root: Path, msg: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


def vendor(root: Path, plugin: str = "prd-toolkit") -> None:
    subprocess.run([sys.executable, str(root / plugin / "scripts/prd_hooks.py"), "vendor", PRD], cwd=root, check=True, capture_output=True)


def copy_plugin(dest: Path) -> None:
    dest.mkdir(parents=True)
    for sub in (".claude-plugin", "scripts", "templates", "references/languages", "packs"):
        src = REAL / sub
        if src.is_dir():
            shutil.copytree(src, dest / sub, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


@pytest.fixture
def plugin_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    copy_plugin(tmp_path / "prd-toolkit")
    (tmp_path / "prd-toolkit/scripts/prdlint/zz_tmp.py").write_text("X = 1\n")
    shutil.copytree(FIXTURE, tmp_path / PRD)
    vendor(tmp_path)
    commit(tmp_path, "base")
    git(tmp_path, "tag", "base")
    return tmp_path


def diff(root: Path) -> list[str]:
    return buildcheck.diff_findings(model.load(root / PRD), root, "base..HEAD")


def append(path: Path, text: str = "# changed\n") -> None:
    path.write_text(path.read_text() + text)


def test_exact_refresh_passes(plugin_repo):
    append(plugin_repo / "prd-toolkit/scripts/prdlint/trace.py")
    vendor(plugin_repo)
    commit(plugin_repo, "refresh")
    assert diff(plugin_repo) == []


def test_hand_edit_of_the_vendored_copy_fails(plugin_repo):
    append(plugin_repo / ".prd-toolkit/prdlint/trace.py")
    commit(plugin_repo, "edit")
    assert diff(plugin_repo) == [".prd-toolkit/prdlint/trace.py: differs from the plugin; refresh it with prd_hooks.py vendor"]


def test_partial_refresh_reports_each_differing_path_in_order(plugin_repo):
    a, b = "prdlint/trace.py", "prdlint/zz_tmp.py"
    append(plugin_repo / "prd-toolkit/scripts" / a)
    append(plugin_repo / "prd-toolkit/scripts" / b)
    shutil.copy2(plugin_repo / "prd-toolkit/scripts" / a, plugin_repo / ".prd-toolkit" / a)
    commit(plugin_repo, "partial")
    assert diff(plugin_repo) == [f".prd-toolkit/{b}: differs from the plugin; refresh it with prd_hooks.py vendor"]


def test_refresh_that_drops_a_removed_script_passes(plugin_repo):
    git(plugin_repo, "rm", "-q", "prd-toolkit/scripts/prdlint/zz_tmp.py")
    vendor(plugin_repo)
    commit(plugin_repo, "drop")
    assert not (plugin_repo / ".prd-toolkit/prdlint/zz_tmp.py").exists()
    assert diff(plugin_repo) == []


def test_refresh_is_judged_at_head_not_the_working_tree(plugin_repo):
    append(plugin_repo / "prd-toolkit/scripts/prdlint/trace.py")
    vendor(plugin_repo)
    commit(plugin_repo, "refresh")
    append(plugin_repo / ".prd-toolkit/prdlint/trace.py")
    assert diff(plugin_repo) == []


@pytest.mark.parametrize("name", ["helper.py", "notes/x.txt"])
def test_hand_added_file_outside_the_pruned_folders_fails(plugin_repo, name):
    f = plugin_repo / ".prd-toolkit" / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x = 1\n")
    commit(plugin_repo, "add")
    assert diff(plugin_repo) == [f".prd-toolkit/{name}: differs from the plugin; refresh it with prd_hooks.py vendor"]


def test_without_the_plugin_the_old_refusal_stands(tmp_path):
    git(tmp_path, "init", "-q")
    shutil.copytree(FIXTURE, tmp_path / PRD)
    (tmp_path / ".prd-toolkit").mkdir()
    (tmp_path / ".prd-toolkit/x").write_text("1\n")
    commit(tmp_path, "base")
    git(tmp_path, "tag", "base")
    (tmp_path / ".prd-toolkit/x").write_text("2\n")
    commit(tmp_path, "edit")
    assert diff(tmp_path) == [OLD]


def test_two_plugin_directories_keep_the_old_refusal(plugin_repo):
    other = plugin_repo / "other"
    (other / "scripts").mkdir(parents=True)
    shutil.copytree(plugin_repo / "prd-toolkit/.claude-plugin", other / ".claude-plugin")
    shutil.copy2(plugin_repo / "prd-toolkit/scripts/prd_hooks.py", other / "scripts/prd_hooks.py")
    commit(plugin_repo, "second plugin")
    git(plugin_repo, "tag", "-f", "base")
    append(plugin_repo / "prd-toolkit/scripts/prdlint/trace.py")
    vendor(plugin_repo)
    commit(plugin_repo, "refresh")
    out = diff(plugin_repo)
    changed = git(plugin_repo, "diff", "--name-only", "base..HEAD", "--", ".prd-toolkit").splitlines()
    assert changed and out == [f"{p}: the builder may not edit the vendored .prd-toolkit/ copy" for p in changed if p.startswith(".prd-toolkit/")]


def test_cli_tool_error_is_exit_2(plugin_repo):
    (plugin_repo / "prd-toolkit/scripts/prd_hooks.py").write_text("raise SystemExit(1)\n")
    append(plugin_repo / ".prd-toolkit/prdlint/trace.py")
    commit(plugin_repo, "broken")
    p = subprocess.run([sys.executable, str(SCRIPT), PRD, "--diff", "base..HEAD"], cwd=plugin_repo, capture_output=True, text=True)
    assert p.returncode == 2
    assert p.stderr.startswith("prd_build_check: ")
    assert "internal error" not in p.stderr
