"""The built-in service and document packs, the `pack` validator and pack target kinds (0.8.0)."""
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from conftest import edit, lint
from doc_fixture import document_prd
from packs_fixture import plugins_file

from prdlint import model, packs, registry
from prdlint.model import PackRef

TOOLKIT_PACKS = Path(packs.__file__).resolve().parents[2] / "packs"
VALIDATOR = TOOLKIT_PACKS / "document/validate_outline.py"
GOOD = {
    "path": "docs/guide/install.md",
    "audience": "first-time users on Windows or macOS",
    "purpose": "install the CLI and run it once",
    "sections": ["Requirements", "Install", "First run", "Common problems"],
    "terms": ["CLI", "token"],
    "length": {"min-words": 300, "max-words": 1200},
}


def _lint(root):
    return [f for f in registry.run(model.load(root))]


# --- manifests ---------------------------------------------------------------------------------------------------

def test_service_manifest_loads():
    p = packs.load_manifest(TOOLKIT_PACKS / "service", "prd-toolkit")
    assert (p.name, p.version, p.builder_tests) == ("service", "1.0.0", "unit")
    assert [c["type"] for c in p.contract_types] == [
        "openapi", "schema", "events", "errors", "permissions", "config", "classification", "dependencies", "fixtures"]
    assert {c["validator"] for c in p.contract_types} == {"built-in"}
    assert p.target_kinds == {} and p.levels == [] and p.harness == {} and p.vocabulary == []


def test_document_manifest_loads():
    p = packs.load_manifest(TOOLKIT_PACKS / "document", "prd-toolkit")
    assert (p.name, p.version, p.builder_tests) == ("document", "1.0.0", "none")
    assert p.contract_types == [{"type": "outline", "files": "contracts/outline.yaml",
                                 "validator": "uv run --quiet --script ${PACK}/validate_outline.py"}]
    assert p.target_kinds == {"doc": "outline"}
    assert [(x["level"], x["command"], x["gate"]) for x in p.levels] == [
        ("checks", "uv run pytest tests/checks", "build"), ("judged", "uv run pytest tests/judged", "build")]
    assert p.vocabulary == []
    assert len(p.standards) == 1 and p.standards[0]["linter"] == 'npx markdownlint-cli2 "docs/**/*.md"'
    for slot in ("HTTP requests", "Database access", "Browser identity", "Persistent environments", "Leaks"):
        assert p.harness[slot].startswith("Not applicable")
    assert "uv" in p.harness["Tools on the runner"] and "claude" in p.harness["Tools on the runner"]
    assert p.harness["Layout"] == "Test roots: `tests/`"
    assert "prd_judge.py" in p.harness["Assertions"]
    assert p.rubrics.is_file() and p.clarify.is_file()


# --- the document fixture ----------------------------------------------------------------------------------------

def test_document_prd_lints_clean_but_for_the_judged_case(tmp_path):
    found = _lint(document_prd(tmp_path))
    assert found == []


def test_doc_target_resolves_both_ways(tmp_path):
    root = document_prd(tmp_path)
    edit(root, "test-cases/install.yaml", "target: doc:install-guide\n  environment: local\n  identity: none\n  preconditions: []\n  input: {path",
         "target: doc:nope\n  environment: local\n  identity: none\n  preconditions: []\n  input: {path")
    msgs = [f.message for f in _lint(root) if f.rule == "test-refs"]
    assert msgs == ["T-001.1: target doc:nope: no outline entry 'nope'"]
    assert not [f for f in _lint(root) if f.rule == "sufficiency" and "kind" in f.message]


def test_pack_row_no_pack_declares(tmp_path):
    root = document_prd(tmp_path)
    edit(root, "prd.md", "| outline | `contracts/outline.yaml` | pack |",
         "| outline | `contracts/outline.yaml` | pack |\n| glossary | `contracts/outline.yaml` | pack |")
    found = [f for f in _lint(root) if f.rule == "contracts-valid"]
    assert [f.message for f in found] == ["custom type glossary: no named pack declares contract type glossary"]
    assert found[0].file == "prd.md"


def test_pack_row_with_no_pack_line_is_not_declared_by_service(tmp_path):
    """No Pack: line: the service default declares only built-in types, so a pack row for outline is not declared."""
    root = document_prd(tmp_path)
    edit(root, "prd.md", "- Pack: document 1.0.0 (prd-toolkit)\n", "")
    msgs = [f.message for f in _lint(root) if f.rule == "contracts-valid"]
    assert msgs == ["custom type outline: no named pack declares contract type outline"]


def test_0_7_prd_unaffected(prd):
    assert lint(prd) == []


# --- validate_outline.py -----------------------------------------------------------------------------------------

def _run(tmp: Path, data, name="outline.yaml", validator=VALIDATOR):
    root = tmp / "docs/prd/guide"  # the validator runs from the PRD root; the document lives outside it
    root.mkdir(parents=True, exist_ok=True)
    f = root / "contracts" / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(yaml.safe_dump(data, sort_keys=False) if not isinstance(data, str) else data, encoding="utf-8")
    return subprocess.run(["uv", "run", "--script", str(validator), f"contracts/{name}"], cwd=root,
                          capture_output=True, text=True)


def _without(key):
    return {k: v for k, v in GOOD.items() if k != key}


DEFECTS = [
    ("no-path", {"g": _without("path")}, "g: missing path"),
    ("no-audience", {"g": _without("audience")}, "g: missing audience"),
    ("no-purpose", {"g": _without("purpose")}, "g: missing purpose"),
    ("no-sections", {"g": _without("sections")}, "g: sections must be a non-empty list"),
    ("empty-sections", {"g": {**GOOD, "sections": []}}, "g: sections must be a non-empty list"),
    ("absolute-path", {"g": {**GOOD, "path": "/etc/guide.md"}}, "g: path must be a relative .md path"),
    ("not-md", {"g": {**GOOD, "path": "docs/guide/install.txt"}}, "g: path must be a relative .md path"),
    ("min-gt-max", {"g": {**GOOD, "length": {"min-words": 900, "max-words": 100}}}, "g: length: min-words must not exceed max-words"),
    ("length-not-int", {"g": {**GOOD, "length": {"min-words": "many", "max-words": 100}}}, "g: length: min-words must be an integer"),
    ("terms-not-strings", {"g": {**GOOD, "terms": ["CLI", 7]}}, "g: terms must be a list of strings"),
    ("sections-not-strings", {"g": {**GOOD, "sections": ["Install", ["x"]]}}, "g: sections must be a non-empty list of strings"),
    ("entry-not-mapping", {"g": "text"}, "g: must be a mapping"),
]


def test_validator_passes_good_file(tmp_path):
    r = _run(tmp_path, {"install-guide": GOOD, "other": {**GOOD, "path": "docs/other.md"}})
    assert r.returncode == 0
    assert not [x for x in r.stderr.splitlines() if x.startswith("contracts/")]


@pytest.mark.parametrize("name,data,message", DEFECTS, ids=[d[0] for d in DEFECTS])
def test_validator_fails_defect(tmp_path, name, data, message):
    r = _run(tmp_path, data)
    assert r.returncode == 1, r.stderr
    assert message in r.stderr.splitlines()[0]


def test_validator_fails_path_inside_prd_folder(tmp_path):
    r = _run(tmp_path, {"g": {**GOOD, "path": "docs/prd/guide/features/install.md"}})
    assert r.returncode == 1
    assert "g: path must be outside the PRD folder" in r.stderr
    r = _run(tmp_path, {"g": {**GOOD, "path": "docs/prd/guide/../../guide/install.md"}})
    assert r.returncode == 0, r.stderr


def test_validator_fails_non_mapping_file(tmp_path):
    r = _run(tmp_path, "- a\n- b\n")
    assert r.returncode == 1 and "must be a mapping" in r.stderr


def test_validator_runs_from_a_pack_folder_with_a_space(tmp_path):
    spaced = tmp_path / "My Plugins/demo/prd-packs"
    spaced.mkdir(parents=True)
    shutil.copytree(TOOLKIT_PACKS / "document", spaced / "document")
    pack = packs.load_manifest(spaced / "document", "demo@test")
    argv = packs.expand(pack.contract_types[0]["validator"], pack)
    root = document_prd(tmp_path)
    done = subprocess.run(argv + ["contracts/outline.yaml"], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_contracts_valid_runs_a_plugin_pack_under_a_spaced_path(tmp_path, monkeypatch):
    install = tmp_path / "My Plugins/demo"
    (install / "prd-packs").mkdir(parents=True)
    shutil.copytree(TOOLKIT_PACKS / "document", install / "prd-packs/document")
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@test": install})))
    root = document_prd(tmp_path)
    edit(root, "prd.md", "(prd-toolkit)", "(demo@test)")
    assert [f for f in _lint(root) if f.rule in ("contracts-valid", "pack-resolves")] == []
    (root / "contracts/outline.yaml").write_text("g: {path: docs/x.md}\n", encoding="utf-8")
    msgs = [f.message for f in _lint(root) if f.rule == "contracts-valid"]
    assert msgs == ["custom type outline: validator failed: contracts/outline.yaml: g: missing audience"]


# --- the repository root of a document path ------------------------------------------------------------------------

def _run_in(root: Path, path: str):
    f = root / "o.yaml"
    f.write_text(yaml.safe_dump({"g": {**GOOD, "path": path}}), encoding="utf-8")
    return subprocess.run(["uv", "run", "--quiet", "--script", str(VALIDATOR), "o.yaml"], cwd=root, capture_output=True, text=True)


def test_root_from_the_layout_before_any_git(tmp_path):
    (tmp_path / ".git").mkdir()
    root = tmp_path / "sub/docs/prd/guide"
    root.mkdir(parents=True)
    assert _run_in(root, "sub/docs/prd/guide/x.md").returncode == 0  # git-first would read this as inside the PRD
    r = _run_in(root, "docs/prd/guide/x.md")
    assert r.returncode == 1 and "path must be outside the PRD folder" in r.stderr


def test_root_from_git_when_not_in_the_layout(tmp_path):
    (tmp_path / ".git").mkdir()
    root = tmp_path / "specs/guide"
    root.mkdir(parents=True)
    assert _run_in(root, "docs/x.md").returncode == 0
    r = _run_in(root, "specs/guide/x.md")
    assert r.returncode == 1 and "path must be outside the PRD folder" in r.stderr


def test_no_root_known_skips_only_the_inside_check(tmp_path):
    root = tmp_path / "loose/guide"
    root.mkdir(parents=True)
    assert _run_in(root, "docs/x.md").returncode == 0
    assert _run_in(root, "specs/guide/x.md").returncode == 0
    r = _run_in(root, "x.txt")  # the other checks still run
    assert r.returncode == 1 and "path must be a relative .md path" in r.stderr
