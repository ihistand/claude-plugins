"""prd_hooks.py install and check vendor the packs, prd_judge.py, its grader prompt and the language tables (0.8.0)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from doc_fixture import document_prd
from packs_fixture import plugins_file, write_pack
from test_judge import BOTH, DOC, FAKE, TID

from prdlint import hooks, languages, model, packs

PLUGIN_ROOT = Path(__file__).parent.parent
PRD = "docs/prd/guide"
PACKS_DIR = PLUGIN_ROOT / "packs"
NAMED = "- Pack: document 1.0.0 (prd-toolkit)"
DEMO = "- Pack: demo 1.0.0 (demo@market)"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(tmp_path / "none.json"))
    document_prd(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def with_demo(repo, tmp_path, monkeypatch, description="one") -> Path:
    plugin = tmp_path / "plug"
    write_pack(plugin / "prd-packs", "demo", "1.0.0", description=description)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@market": plugin})))
    edit(repo / PRD, "prd.md", NAMED, DEMO)
    return plugin


def test_install_vendors_named_packs_and_service(repo):
    hooks.install(repo, PRD)
    v = repo / ".prd-toolkit"
    assert sorted(p.name for p in (v / "packs").iterdir()) == ["document", "service"]
    assert tree(v / "packs/document") == tree(PACKS_DIR / "document")
    assert tree(v / "packs/service") == tree(PACKS_DIR / "service")
    assert (v / "prd_judge.py").is_file() and os.access(v / "prd_judge.py", os.X_OK)
    assert (v / "judge/grader.md").read_bytes() == (PLUGIN_ROOT / "templates/judge/grader.md").read_bytes()
    assert tree(v / "languages") == tree(PLUGIN_ROOT / "references/languages")
    assert hooks.check(repo, PLUGIN_ROOT, model.load(repo / PRD), PRD) == []


def test_unresolvable_pack_refuses_and_vendors_nothing(repo):
    edit(repo / PRD, "prd.md", NAMED, DEMO)
    with pytest.raises(hooks.InstallRefused) as e:
        hooks.install(repo, PRD)
    assert "pack demo 1.0.0 (demo@market) not found; looked in:" in str(e.value)
    assert not (repo / ".prd-toolkit").exists()
    assert not (repo / ".gitignore").exists()


def test_cli_refusal_exits_2_naming_where_it_looked(repo):
    edit(repo / PRD, "prd.md", NAMED, DEMO)
    r = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_hooks.py"), "install", PRD], cwd=repo, capture_output=True, text=True,
                       env={**os.environ, "PRD_PLUGINS_FILE": str(repo / "none.json")})
    assert r.returncode == 2 and "looked in" in r.stderr and "internal error" not in r.stderr
    assert not (repo / ".prd-toolkit").exists()


def test_reinstall_replaces_the_copy_after_a_source_change(repo, tmp_path, monkeypatch):
    plugin = with_demo(repo, tmp_path, monkeypatch)
    hooks.install(repo, PRD)
    assert "description: one" in (repo / ".prd-toolkit/packs/demo/pack.yaml").read_text()
    (repo / ".prd-toolkit/packs/demo/stray.txt").write_text("x")
    write_pack(plugin / "prd-packs", "demo", "1.0.0", description="two")
    prd = model.load(repo / PRD)
    assert "packs/demo: differs from demo@market 1.0.0; run prd_hooks.py install" in hooks.check(repo, PLUGIN_ROOT, prd, PRD)
    hooks.install(repo, PRD)
    assert "description: two" in (repo / ".prd-toolkit/packs/demo/pack.yaml").read_text()
    assert not (repo / ".prd-toolkit/packs/demo/stray.txt").exists()
    assert hooks.check(repo, PLUGIN_ROOT, prd, PRD) == []


def test_check_reports_a_hand_edited_vendored_manifest(repo):
    hooks.install(repo, PRD)
    manifest = repo / ".prd-toolkit/packs/document/pack.yaml"
    manifest.write_text(manifest.read_text() + "# edited\n")
    out = hooks.check(repo, PLUGIN_ROOT, model.load(repo / PRD), PRD)
    assert "packs/document: differs from prd-toolkit 1.0.0; run prd_hooks.py install" in out


def test_gitignore_gains_prd_judge_once(repo):
    (repo / ".gitignore").write_text("build/")
    hooks.install(repo, PRD)
    hooks.install(repo, PRD)
    assert (repo / ".gitignore").read_text() == "build/\n.prd-judge/\n"


def test_gitignore_is_created(repo):
    hooks.install(repo, PRD)
    assert (repo / ".gitignore").read_text() == ".prd-judge/\n"


def test_a_pack_no_longer_named_is_removed_and_service_stays(repo, tmp_path, monkeypatch):
    with_demo(repo, tmp_path, monkeypatch)
    hooks.install(repo, PRD)
    assert sorted(p.name for p in (repo / ".prd-toolkit/packs").iterdir()) == ["demo", "service"]
    edit(repo / PRD, "prd.md", DEMO, NAMED)
    hooks.install(repo, PRD)
    assert sorted(p.name for p in (repo / ".prd-toolkit/packs").iterdir()) == ["document", "service"]


def test_vendored_prd_judge_runs_from_the_copy(repo, tmp_path):
    out = tmp_path / "docs/guide/install.md"
    out.parent.mkdir(parents=True)
    out.write_text(DOC, encoding="utf-8")
    hooks.install(repo, PRD)
    replies = tmp_path / "replies.json"
    replies.write_text(json.dumps([BOTH]), encoding="utf-8")
    env = {**os.environ, "PRD_JUDGE_CLAUDE": str(FAKE), "FAKE_CLAUDE_REPLY": str(replies), "PRD_PLUGINS_FILE": str(tmp_path / "none.json")}
    r = subprocess.run([sys.executable, "-B", str(repo / ".prd-toolkit/prd_judge.py"), str(repo / PRD), TID, str(out), "--runs", "1"],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr + r.stdout


def test_vendored_lint_accepts_a_spanish_prd(tmp_path, monkeypatch):
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")
    root = document_prd(tmp_path, language="es")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    hooks.install(tmp_path, PRD)
    r = subprocess.run([sys.executable, "-B", str(tmp_path / ".prd-toolkit/prd_lint.py"), str(root)], cwd=tmp_path,
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PRD_PLUGINS_FILE": str(tmp_path / "none.json")})
    assert "language-table" not in r.stdout + r.stderr


# --- R10: no built-in en fallback ---------------------------------------------------------------------------------

@pytest.fixture
def vendored_scripts(tmp_path, monkeypatch):
    """A vendored layout (no plugin.json) whose languages/ the test fills."""
    scripts = tmp_path / "vend"
    (scripts / "languages").mkdir(parents=True)
    monkeypatch.setattr(languages, "SCRIPTS", scripts)
    monkeypatch.setattr(languages, "PLUGIN_ROOT", scripts.parent)
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(tmp_path / "none.json"))
    return scripts


def _findings(root):
    from prdlint import registry
    return [f for f in registry.run(model.load(root), warnings=True) if f.rule in ("language-table", "ac-ears", "vague-word")]


def test_missing_languages_dir_is_a_language_table_finding(tmp_path, vendored_scripts):
    shutil.rmtree(vendored_scripts / "languages")
    found = _findings(document_prd(tmp_path))
    assert [f.rule for f in found] == ["language-table"]
    assert found[0].message == f"language table {vendored_scripts / 'languages/en.yaml'}: not found"


def test_malformed_en_table_is_a_finding_not_a_crash(tmp_path, vendored_scripts):
    (vendored_scripts / "languages/en.yaml").write_text("ears: {openers: [When]}\n", encoding="utf-8")  # no ubiquitous
    found = _findings(document_prd(tmp_path))
    assert [f.rule for f in found] == ["language-table"]
    assert found[0].message.startswith(f"language table {vendored_scripts / 'languages/en.yaml'}: ")


def test_broken_es_table_is_named_and_unknown_fr_keeps_its_message(tmp_path, vendored_scripts):
    shutil.copy(PLUGIN_ROOT / "references/languages/en.yaml", vendored_scripts / "languages/en.yaml")
    (vendored_scripts / "languages/es.yaml").write_text(": : [\n", encoding="utf-8")
    found = _findings(document_prd(tmp_path / "a", language="es"))
    assert [f.rule for f in found] == ["language-table"] and found[0].message.startswith(f"language table {vendored_scripts / 'languages/es.yaml'}: ")
    assert [f.message for f in _findings(document_prd(tmp_path / "b", language="fr"))] == ["language 'fr' has no table"]
