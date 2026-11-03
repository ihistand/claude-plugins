"""lint-cli FR-001 and FR-002: findings and their paths (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import append, m1, run, s0  # noqa: E402


def test_t001_1_clean_folder_prints_nothing(tmp_path, monkeypatch):
    """@prd T-001.1"""
    s0(tmp_path, monkeypatch)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert (r.exit, r.stdout, r.stderr) == (0, "", "")


def test_t001_2_finding_line_and_exit_1(tmp_path, monkeypatch):
    """@prd T-001.2"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert (
        "docs/prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 41)"
    ) in r.stdout_lines
    assert r.stderr == ""


def test_t001_3_findings_sorted(tmp_path, monkeypatch):
    """@prd T-001.3"""
    root = s0(tmp_path, monkeypatch)
    append(root / "test-cases" / "api.yaml", "T-002.1: {}\n")
    append(root / "contracts" / "errors.yaml", "IMPORT_EMPTY: {}\nFORBIDDEN: {}\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    expected = [
        "docs/prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key 'IMPORT_EMPTY' "
        "(first at line 9, again at line 41)",
        "docs/prd/orders/contracts/errors.yaml:42: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 42)",
        "docs/prd/orders/test-cases/api.yaml:68: id-unique: duplicate key 'T-002.1' "
        "(first at line 1, again at line 68)",
    ]
    lines = r.stdout_lines
    for line in expected:
        assert line in lines, f"missing line: {line!r}\nstdout:\n{r.stdout}"
    indexes = [lines.index(line) for line in expected]
    assert indexes == sorted(indexes), f"lines out of order:\n{r.stdout}"
    assert r.stderr == ""


def test_t002_1_folder_below_cwd(tmp_path, monkeypatch):
    """@prd T-002.1"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    r = run(["prd/orders"], cwd=tmp_path / "docs")
    assert r.exit == 1
    assert (
        "prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 41)"
    ) in r.stdout_lines


def test_t002_2_folder_is_cwd(tmp_path, monkeypatch):
    """@prd T-002.2"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    r = run(["."], cwd=root)
    assert r.exit == 1
    assert (
        "contracts/errors.yaml:41: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 41)"
    ) in r.stdout_lines


def test_t002_3_folder_outside_cwd(tmp_path, monkeypatch):
    """@prd T-002.3"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    r = run([str(tmp_path / "docs" / "prd" / "orders")], cwd=elsewhere)
    resolved = Path(tmp_path).resolve()
    assert r.exit == 1
    assert (
        f"{resolved}/docs/prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key "
        "'FORBIDDEN' (first at line 25, again at line 41)"
    ) in r.stdout_lines
