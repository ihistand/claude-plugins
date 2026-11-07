"""prd_hooks.py vendor writes .prd-toolkit/ exactly as install does, and nothing else (0.8.3)."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from doc_fixture import document_prd
from packs_fixture import plugins_file, write_pack

from prdlint import packs

PLUGIN_ROOT = Path(__file__).parent.parent
SCRIPT = PLUGIN_ROOT / "scripts/prd_hooks.py"
VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text())["version"]
PRD = "docs/prd/guide"
NAMED = "- Pack: document 1.0.0 (prd-toolkit)"
DEMO = "- Pack: demo 1.0.0 (demo@market)"


def make_repo(root: Path) -> Path:
    root.mkdir(parents=True)
    document_prd(root)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(tmp_path / "none.json"))


def run(script, repo, *args, env=None):
    return subprocess.run([sys.executable, "-B", str(script), *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, **(env or {})})


def tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git/" not in p.as_posix() + "/" and "__pycache__" not in p.parts}


def test_vendor_writes_install_s_tree_and_nothing_else(tmp_path):
    a, b = make_repo(tmp_path / "a"), make_repo(tmp_path / "b")
    before = files(a)
    r = run(SCRIPT, a, "vendor", PRD)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == f"vendored the toolkit into .prd-toolkit/ (version {VERSION})"
    assert run(SCRIPT, b, "install", PRD).returncode == 0
    assert tree(a / ".prd-toolkit") == tree(b / ".prd-toolkit")
    assert files(a) - before == {f".prd-toolkit/{k}" for k in tree(a / ".prd-toolkit")}
    assert not list((a / ".git/hooks").glob("pre-commit")) and not (a / ".git/hooks/commit-msg").exists()
    assert not (a / "CLAUDE.md").exists() and not (a / ".gitlab").exists() and not (a / ".github").exists()
    assert not (a / ".gitignore").exists()


def test_vendor_matches_install_with_a_named_pack(tmp_path, monkeypatch):
    plugin = tmp_path / "plug"
    write_pack(plugin / "prd-packs", "demo", "1.0.0", description="one")
    env = {"PRD_PLUGINS_FILE": str(plugins_file(tmp_path, {"demo@market": plugin}))}
    monkeypatch.setenv("PRD_PLUGINS_FILE", env["PRD_PLUGINS_FILE"])
    a, b = make_repo(tmp_path / "a"), make_repo(tmp_path / "b")
    for r in (a, b):
        edit(r / PRD, "prd.md", NAMED, DEMO)
    assert run(SCRIPT, a, "vendor", PRD, env=env).returncode == 0
    assert run(SCRIPT, b, "install", PRD, env=env).returncode == 0
    va, vb = a / ".prd-toolkit", b / ".prd-toolkit"
    assert (va / "packs/demo/pack.yaml").is_file()
    assert tree(va / "packs") == tree(vb / "packs")
    assert (va / "pack-sources.json").read_bytes() == (vb / "pack-sources.json").read_bytes()


def test_vendor_from_a_vendored_copy_exits_2(tmp_path):
    a = make_repo(tmp_path / "a")
    assert run(SCRIPT, a, "vendor", PRD).returncode == 0
    r = run(a / ".prd-toolkit/prd_hooks.py", a, "vendor", PRD)
    assert r.returncode == 2
    assert r.stderr.strip() == "prd_hooks: vendor runs from the plugin, not from .prd-toolkit/"


def test_vendor_rejects_ci_flags(tmp_path):
    a = make_repo(tmp_path / "a")
    r = run(SCRIPT, a, "vendor", PRD, "--force")
    assert r.returncode == 2
    assert "--gitlab, --github and --force belong to ci" in r.stderr
    assert not (a / ".prd-toolkit").exists()


def test_help_lists_vendor(tmp_path):
    # "vendored copy" appears in the help already: match the action choice itself
    assert re.search(r"[{,]vendor[,}]", run(SCRIPT, tmp_path, "--help").stdout)
