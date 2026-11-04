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


def test_approved_has_the_shipped_cli_verified_and_two_changes_to_build(tmp_path):
    """FR-001 is the CLI the repository ships, so it is verified; FR-002 and FR-010 are approved and unbuilt,
    so each area has a build to run (0.8.0 proof, P2: an approved requirement whose code predates it has no build)."""
    r = build(tmp_path, "approved")
    assert not (r / "docs/guide").exists()
    greet = read(r, "features/greet.md")
    assert "### FR-001 Print a greeting\nStatus: verified (since 1.0.0)" in greet
    assert "### FR-002 Print the version\nStatus: approved" in greet
    assert "Status: approved" in read(r, "features/guide.md")
    index = read(r, "prd.md")
    assert "| FR-001 | Print a greeting | verified |" in index and "| FR-002 | Print the version | approved |" in index
    run = subprocess.run(["uv", "run", "--directory", "src", "python", "-m", "greet", "--version"], cwd=r, capture_output=True, text=True)
    # FR-002 is not built: the CLI greets the flag as a name. A command that fails or prints nothing fails here.
    assert (run.returncode, run.stdout) == (0, "Hello, --version!\n"), run.stdout + run.stderr


@pytest.mark.parametrize("state", ["approved", "built"])
def test_the_prd_specifies_every_behaviour_the_cli_ships(tmp_path, state):
    """The CLI's usage line is in FR-001, so a build of FR-001 meets no code the PRD lacks (0.8.0 proof, P2)."""
    r = build(tmp_path, state)
    assert "it shall print `usage: greet <name>` and exit with code 2" in read(r, "features/greet.md")
    assert "T-001.3 [unit]" in read(r, "features/greet.md") and "T-001.3:" in read(r, "test-cases/greet.yaml")
    tests = (r / "tests/unit/test_greet.py").read_text(encoding="utf-8")
    assert tests.count("def test_") == tests.count('"""@prd T-'), tests
    assert '"usage: greet <name>\\n"' in tests


@pytest.mark.parametrize("state", ["approved", "built"])
def test_every_claim_of_ac_010_2_is_a_rubric_item_of_t_010_2(tmp_path, state):
    """AC-010.2 asked for one sentence per step, which no case checked; a tester stopped on it (0.8.0 proof, P2)."""
    r = build(tmp_path, state)
    assert "- AC-010.2 The guide shall give each step of Install as one action the reader performs, using only tools that Requirements lists." in read(r, "features/guide.md")
    assert "one sentence" not in read(r, "features/guide.md")
    cases = read(r, "test-cases/guide.yaml")
    assert "- Each step in Install names one action the reader performs" in cases
    assert "- No step relies on a tool that Requirements does not list" in cases


@pytest.mark.parametrize("state", ["approved", "built"])
def test_the_harness_says_a_section_heading_appears_once(tmp_path, state):
    """A tester asked whether a section heading may repeat and stopped the build (0.8.0 proof, P2 attempt 4)."""
    r = build(tmp_path, state)
    assert "Each `sections` entry heads exactly one section; a repeated one fails." in read(r, "testing.md")


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
