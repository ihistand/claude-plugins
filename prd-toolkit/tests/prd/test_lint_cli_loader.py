"""lint-cli FR-011 and FR-012: loading test-case and contract YAML (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import NINE, append, run, s0  # noqa: E402


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_t011_1_duplicate_test_case_key(tmp_path, monkeypatch):
    """@prd T-011.1"""
    root = s0(tmp_path, monkeypatch)
    append(root / "test-cases" / "api.yaml", "T-002.1: {}\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout == (
        "docs/prd/orders/test-cases/api.yaml:68: id-unique: duplicate key 'T-002.1' "
        "(first at line 1, again at line 68)\n"
    )
    assert r.stderr == ""


def test_t011_2_yaml_parse_error(tmp_path, monkeypatch):
    """@prd T-011.2"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "test-cases" / "broken.yaml", b"T-009.1: a: b\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout == (
        "docs/prd/orders/test-cases/broken.yaml:1: sufficiency: YAML parse error: "
        "mapping values are not allowed here\n"
    )
    assert r.stderr == ""


def test_t011_3_top_level_not_a_mapping(tmp_path, monkeypatch):
    """@prd T-011.3"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "test-cases" / "list.yaml", b"- a\n- b\n")
    _write(root / "test-cases" / "empty.yaml", b"")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout == (
        "docs/prd/orders/test-cases/empty.yaml:1: sufficiency: top level must be a mapping\n"
        "docs/prd/orders/test-cases/list.yaml:1: sufficiency: top level must be a mapping\n"
    )
    assert r.stderr == ""


def test_t011_4_case_not_a_mapping(tmp_path, monkeypatch):
    """@prd T-011.4"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "test-cases" / "scalar.yaml", b"T-009.1: plain text\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    for line in (
        "docs/prd/orders/test-cases/scalar.yaml:1: sufficiency: T-009.1: a test case must be a mapping",
        "docs/prd/orders/test-cases/scalar.yaml:1: test-cases-consistent: T-009.1 is cited by no "
        "Tests line naming test-cases/scalar.yaml",
    ):
        assert line in r.stdout_lines, (line, r.stdout)
    assert r.stderr == ""


def test_t011_5_only_yaml_directly_in_test_cases(tmp_path, monkeypatch):
    """@prd T-011.5"""
    root = s0(tmp_path, monkeypatch)
    text = b"T-002.1: {}\nT-002.1: {}\n"
    _write(root / "test-cases" / "sub" / "c.yaml", text)
    _write(root / "test-cases" / "d.yml", text)
    r1 = run(["docs/prd/orders"], cwd=tmp_path)
    assert (r1.exit, r1.stdout, r1.stderr) == (0, "", "")
    r2 = run(["--sample-tids", "99", "docs/prd/orders"], cwd=tmp_path)
    assert r2.exit == 0
    assert r2.stderr == ""
    assert sorted(r2.stdout_lines) == sorted(NINE), r2.stdout


def test_t011_6_unhashable_key_in_test_cases(tmp_path, monkeypatch):
    """@prd T-011.6"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "test-cases" / "keys.yaml", b"? [a, b]\n: x\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1, (r.stdout, r.stderr)
    assert r.stdout == (
        "docs/prd/orders/test-cases/keys.yaml:1: sufficiency: YAML parse error: found unhashable key\n"
    )
    assert r.stderr == ""


def test_t012_1_contract_yaml_findings(tmp_path, monkeypatch):
    """@prd T-012.1"""
    root = s0(tmp_path, monkeypatch)
    append(root / "contracts" / "errors.yaml", "FORBIDDEN: {}\n")
    _write(root / "contracts" / "extra" / "a.yaml", b"K: 1\nL: 2\nK: 3\n")
    _write(root / "contracts" / "extra" / "b.yaml", b"- a\n")
    _write(root / "contracts" / "extra" / "c.yaml", b"k: v: w\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout == (
        "docs/prd/orders/contracts/errors.yaml:41: contracts-valid: duplicate key 'FORBIDDEN' "
        "(first at line 25, again at line 41)\n"
        "docs/prd/orders/contracts/extra/a.yaml:3: contracts-valid: duplicate key 'K' "
        "(first at line 1, again at line 3)\n"
        "docs/prd/orders/contracts/extra/b.yaml:1: contracts-valid: top level must be a mapping\n"
        "docs/prd/orders/contracts/extra/c.yaml:1: contracts-valid: YAML parse error: "
        "mapping values are not allowed here\n"
    )
    assert r.stderr == ""


def test_t012_2_fixtures_not_read(tmp_path, monkeypatch):
    """@prd T-012.2"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "contracts" / "fixtures" / "extra" / "dup.yaml", b"K: 1\nK: 2\n")
    _write(root / "contracts" / "fixtures" / "extra" / "notes.md", b"\xff\xfe")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert (r.exit, r.stdout, r.stderr) == (0, "", ""), (r.stdout, r.stderr)


def test_t012_3_unhashable_key_in_contracts(tmp_path, monkeypatch):
    """@prd T-012.3"""
    root = s0(tmp_path, monkeypatch)
    _write(root / "contracts" / "extra" / "keys.yaml", b"? [a, b]\n: x\n")
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1, (r.stdout, r.stderr)
    assert r.stdout == (
        "docs/prd/orders/contracts/extra/keys.yaml:1: contracts-valid: YAML parse error: "
        "found unhashable key\n"
    )
    assert r.stderr == ""
