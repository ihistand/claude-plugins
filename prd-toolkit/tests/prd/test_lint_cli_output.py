"""lint-cli FR-001 and FR-002: findings and their paths (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import (  # noqa: E402
    append, in_process, in_relative_order, m1, register_zz_warn, run, s0,
)


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
    assert in_relative_order(r.stdout_lines, expected), f"lines missing or out of order:\n{r.stdout}"
    assert r.stderr == ""


def test_t001_4_warn_finding_sorted_with_errors(tmp_path, monkeypatch, capsys):
    """@prd T-001.4"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    prd_lint = in_process(monkeypatch)
    remove = register_zz_warn()
    try:
        monkeypatch.chdir(tmp_path)
        capsys.readouterr()
        ret = prd_lint.main(["docs/prd/orders"])
        out, err = capsys.readouterr()
    finally:
        remove()
    assert ret == 1
    assert out == (
        "docs/prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 41)\n"
        "docs/prd/orders/prd.md:1: warn: zz-warn: a warning\n"
    )
    assert err == ""


def test_t001_5_only_warnings_exit_0(tmp_path, monkeypatch, capsys):
    """@prd T-001.5"""
    s0(tmp_path, monkeypatch)
    prd_lint = in_process(monkeypatch)
    remove = register_zz_warn()
    try:
        monkeypatch.chdir(tmp_path)
        capsys.readouterr()
        ret = prd_lint.main(["docs/prd/orders"])
        out, err = capsys.readouterr()
    finally:
        remove()
    assert ret == 0
    assert out == "docs/prd/orders/prd.md:1: warn: zz-warn: a warning\n"
    assert err == ""


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
