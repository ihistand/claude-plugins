"""The doc_repo eval scaffold: three start states of a greet repo for the document-pack baselines (0.8.0)."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "evals/scaffolds/doc_repo.py"
LINT = ROOT / "scripts/prd_lint.py"
PRD = "docs/prd/greet"


def build(tmp_path: Path, state: str) -> Path:
    dst = tmp_path / state
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(dst), state], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return dst


def clean(repo: Path) -> str:
    return subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo, capture_output=True, text=True).stdout


def lint(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "--script", str(LINT), PRD], cwd=repo, capture_output=True, text=True)


def read(repo: Path, rel: str) -> str:
    return (repo / PRD / rel).read_text(encoding="utf-8")


@pytest.fixture(params=["empty", "approved", "built"])
def repo(request, tmp_path):
    return request.param, build(tmp_path, request.param)


def test_every_state_is_a_clean_repository_with_the_cli(repo):
    state, r = repo
    assert clean(r) == ""
    assert (r / "src/greet/cli.py").is_file() and (r / "README.md").is_file()
    assert list((r / "tests").rglob("test_*.py"))


def test_empty_has_no_prd(tmp_path):
    r = build(tmp_path, "empty")
    assert not (r / "docs/prd").exists() and not (r / ".prd-toolkit").exists()


@pytest.mark.parametrize("state", ["approved", "built"])
def test_approved_and_built_lint_clean_with_the_guide_area(tmp_path, state):
    r = build(tmp_path, state)
    out = lint(r)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "Pack:" not in read(r, "prd.md")
    feature = read(r, "features/guide.md")
    assert "Target: pack document 1.0.0 (prd-toolkit), output language en" in feature
    assert "### FR-010 Install guide" in feature
    cases = read(r, "test-cases/guide.yaml")
    assert "level: checks" in cases and "level: judged" in cases
    assert "install-guide:" in read(r, "contracts/outline.yaml") and "docs/guide/install.md" in read(r, "contracts/outline.yaml")
    assert sorted(p.name for p in (r / ".prd-toolkit/packs").iterdir()) == ["document", "service"]
    assert "prd-toolkit" in (r / "CLAUDE.md").read_text(encoding="utf-8")
    assert ".prd-judge/" in (r / ".gitignore").read_text(encoding="utf-8")


def test_approved_has_every_requirement_approved_and_no_guide(tmp_path):
    r = build(tmp_path, "approved")
    assert not (r / "docs/guide").exists()
    statuses = [l for l in (read(r, "features/guide.md") + read(r, "features/greet.md")).splitlines() if l.startswith("Status:")]
    assert statuses and all(s == "Status: approved" for s in statuses)


def test_built_has_the_guide_and_fr_010_verified(tmp_path):
    r = build(tmp_path, "built")
    guide = (r / "docs/guide/install.md").read_text(encoding="utf-8")
    assert [h for h in guide.splitlines() if h.startswith("## ")] == ["## Requirements", "## Install", "## First run", "## Common problems"]
    assert "Status: verified" in read(r, "features/guide.md")
    assert "| FR-010 | Install guide | verified |" in read(r, "prd.md")
    validate = subprocess.run(["uv", "run", "--quiet", "--script", str(ROOT / "packs/document/validate_outline.py"), "contracts/outline.yaml"],
                              cwd=r / PRD, capture_output=True, text=True)
    assert validate.returncode == 0, validate.stdout + validate.stderr


def test_refuses_a_non_empty_destination(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x/f").write_text("a")
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "x"), "empty"], capture_output=True, text=True)
    assert r.returncode != 0


def test_unknown_state_is_a_usage_error(tmp_path):
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "x"), "nope"], capture_output=True, text=True)
    assert r.returncode != 0
