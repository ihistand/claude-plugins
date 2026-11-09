"""lint-cli black-box tests for FR-015: the PRD folder's root README.md is left out of the lint.

Cases T-015.1 and T-015.2 of docs/prd/prd-toolkit/test-cases/lint-cli.yaml.
"""
import shutil
from pathlib import Path

from lint_cli_support import FIXTURES, run, s0

# Fixture lint-cli/readme_markers (testing.md, Fixtures): copied byte for byte to each path a case names.
README_MARKERS = FIXTURES / "lint-cli" / "readme_markers.md"


def copy_readme_markers(dest: Path) -> None:
    """Load fixture lint-cli/readme_markers: copy the file byte for byte to `dest`, creating parent folders."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(README_MARKERS, dest)


def test_root_readme_gives_no_finding(tmp_path, monkeypatch):
    """@prd T-015.1"""
    root = s0(tmp_path, monkeypatch)
    copy_readme_markers(root / "README.md")

    r = run(["docs/prd/orders"], cwd=tmp_path)

    assert r.exit == 0
    assert r.stdout_bytes == b""
    assert r.stderr_bytes == b""


def test_nested_readme_is_linted(tmp_path, monkeypatch):
    """@prd T-015.2"""
    root = s0(tmp_path, monkeypatch)
    copy_readme_markers(root / "README.md")
    copy_readme_markers(root / "contracts" / "dependencies" / "README.md")

    r = run(["docs/prd/orders"], cwd=tmp_path)

    assert r.exit == 1
    assert "docs/prd/orders/contracts/dependencies/README.md:1: markers-open: " in r.stdout
    assert r.stderr_bytes == b""
