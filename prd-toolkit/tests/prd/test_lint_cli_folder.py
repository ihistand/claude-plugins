"""lint-cli FR-005 and FR-006: a folder without prd.md, and internal errors (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import in_process, run, s0  # noqa: E402


def test_t005_1_no_prd_md(tmp_path):
    """@prd T-005.1"""
    (tmp_path / "empty").mkdir()
    resolved = Path(tmp_path).resolve()
    r1 = run([str(tmp_path / "empty")], cwd=tmp_path)
    assert (r1.exit, r1.stdout, r1.stderr) == (2, "", f"prd_lint: {resolved}/empty: no prd.md\n")
    r2 = run([str(tmp_path / "missing")], cwd=tmp_path)
    assert (r2.exit, r2.stdout, r2.stderr) == (2, "", f"prd_lint: {resolved}/missing: no prd.md\n")


def test_t005_2_uppercase_prd_md(tmp_path, monkeypatch):
    """@prd T-005.2"""
    root = s0(tmp_path, monkeypatch)
    (root / "prd.md").rename(root / "prd.md.tmp-rename")
    (root / "prd.md.tmp-rename").rename(root / "PRD.md")
    resolved = Path(tmp_path).resolve()
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == (
        f"prd_lint: {resolved}/docs/prd/orders: no prd.md; found PRD.md; "
        "the file name is lowercase prd.md\n"
    )


def test_t005_3_prd_md_is_a_directory(tmp_path):
    """@prd T-005.3"""
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "prd.md").mkdir()
    resolved = Path(tmp_path).resolve()
    r = run([str(tmp_path / "p")], cwd=tmp_path)
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == f"prd_lint: {resolved}/p: prd.md must be a file\n"


def test_t006_1_load_error_no_traceback(tmp_path, monkeypatch):
    """@prd T-006.1"""
    root = s0(tmp_path, monkeypatch)
    with open(root / "prd.md", "ab") as fh:
        fh.write(b"\xff\xfe")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 2
    assert r.stdout == ""
    assert "Traceback" not in r.stderr
    lines = r.stderr_lines
    assert len(lines) == 1, r.stderr
    assert lines[0].startswith(
        "prd_lint: internal error: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff "
        "in position "
    ), r.stderr


def test_t006_2_rule_crash(tmp_path, monkeypatch, capsys):
    """@prd T-006.2"""
    s0(tmp_path, monkeypatch)
    # In-process call: the subprocess environment rules, through monkeypatch (testing.md, Harness).
    prd_lint = in_process(monkeypatch)
    import prdlint.registry

    def zz_crash(*args, **kwargs):
        return 1 / 0

    prdlint.registry.rule("zz-crash")(zz_crash)
    try:
        capsys.readouterr()
        rc = prd_lint.main([str(tmp_path / "docs" / "prd" / "orders")])
        out = capsys.readouterr()
    finally:
        # RULES and SEVERITY are dicts of rule name (T-001.4's setup).
        prdlint.registry.RULES.pop("zz-crash", None)
        prdlint.registry.SEVERITY.pop("zz-crash", None)
    assert rc == 2
    assert out.out == ""
    assert out.err == "prd_lint: internal error in rule zz-crash: ZeroDivisionError: division by zero\n"


def test_t006_3_md_directory_is_a_finding(tmp_path, monkeypatch):
    """@prd T-006.3"""
    root = s0(tmp_path, monkeypatch)
    (root / "notes.md").mkdir()
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1, (r.stdout, r.stderr)
    assert r.stdout == "docs/prd/orders/notes.md:0: sufficiency: a .md entry that is not a file\n"
    assert r.stderr == ""
