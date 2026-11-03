"""lint-cli FR-008, FR-009 and FR-010: CI runs, UTF-8 output, missing packages (test-cases/lint-cli.yaml)."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import PLUGINS_NONE, PRD_PUBLISH, run, s0, write_orders  # noqa: E402


def test_t008_1_ci_flag(tmp_path, monkeypatch):
    """@prd T-008.1"""
    write_orders(tmp_path)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_NONE))
    monkeypatch.delenv("PRD_LINT_CI", raising=False)
    r1 = run(["docs/prd/orders"], cwd=tmp_path, unset=("PRD_LINT_CI",))
    assert r1.exit == 1
    assert (
        "docs/prd/orders/prd.md:65: registries: required skill 'superpowers:writing-plans' is not "
        "installed; if it is built into Claude Code, mark the row 'recommended'"
    ) in r1.stdout_lines, r1.stdout
    r2 = run(["--ci", "docs/prd/orders"], cwd=tmp_path, unset=("PRD_LINT_CI",))
    assert (r2.exit, r2.stdout, r2.stderr) == (0, "", "")


def test_t008_2_ci_variable(tmp_path, monkeypatch):
    """@prd T-008.2"""
    write_orders(tmp_path)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_NONE))
    r = run(["docs/prd/orders"], cwd=tmp_path, env={"PRD_LINT_CI": "1"})
    assert (r.exit, r.stdout, r.stderr) == (0, "", "")


def test_t009_1_utf8_in_c_locale(tmp_path, monkeypatch):
    """@prd T-009.1"""
    root = s0(tmp_path, monkeypatch)
    (root / "contracts" / "config.yaml").unlink()
    r = run(
        ["docs/prd/orders"],
        cwd=tmp_path,
        env={"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"},
        unset=("PYTHONIOENCODING",),
    )
    assert r.exit == 1
    assert r.stderr_bytes == b""
    line = (
        "docs/prd/orders/prd.md:1: sections: 'contracts/config.yaml' is absent and section 1 has "
        "no 'Not applicable: `contracts/config.yaml` — reason' line"
    )
    assert line in r.stdout_bytes.decode("utf-8").splitlines(), r.stdout_bytes


def _bare_venv(tmp_path: Path) -> Path:
    subprocess.run(["python3", "-m", "venv", str(tmp_path / "venv")], check=True)
    return tmp_path / "venv" / "bin" / "python"


def test_t010_1_lint_missing_package(tmp_path):
    """@prd T-010.1"""
    py = _bare_venv(tmp_path)
    r = run(["--list-rules"], cwd=tmp_path, env={"LC_ALL": "C.UTF-8"},
            unset=("PYTHONPATH", "PYTHONHOME"), python=str(py))
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == (
        "prd_lint: missing Python package 'pyyaml'. Run with: uv run --script prd_lint.py …, "
        "or: pip install pyyaml sqlglot openapi-spec-validator\n"
    )


@pytest.mark.xfail(strict=True, reason="E-002")
def test_t010_2_publish_missing_package(tmp_path):
    """@prd T-010.2 known-failing E-002"""
    py = _bare_venv(tmp_path)
    r = run(["--help"], cwd=tmp_path, env={"LC_ALL": "C.UTF-8"},
            unset=("PYTHONPATH", "PYTHONHOME"), script=PRD_PUBLISH, python=str(py))
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == (
        "prd_publish: missing Python package 'pyyaml'. Run with: uv run --script prd_publish.py "
        "…, or: pip install pyyaml sqlglot openapi-spec-validator markdown-it-py\n"
    )
