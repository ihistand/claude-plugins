"""lint-cli FR-014: --json and --interface (test-cases/lint-cli.yaml)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import m1, run, s0  # noqa: E402

CLEAN = {"interface": 1, "kind": "lint", "prd": "orders", "version": "1.0.0",
         "dir": "docs/prd/orders", "findings": [], "errors": 0, "warnings": 0}
PACK_DOC = ("document 1.0.0 (prd-toolkit) — Markdown documents written for people: "
            "a user guide, a runbook for humans, a policy.")


def one_json(stdout: str):
    """stdout_json: the whole stdout is one line ending in a newline, parsed as one JSON object."""
    assert stdout.endswith("\n"), stdout
    assert stdout.count("\n") == 1, stdout
    obj = json.loads(stdout)
    assert isinstance(obj, dict)
    return obj


def test_t014_1_json_findings(tmp_path, monkeypatch):
    """@prd T-014.1"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    r = run(["--json", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stderr == ""
    obj = one_json(r.stdout)
    assert list(obj)[:2] == ["interface", "kind"]
    assert obj == {
        "interface": 1, "kind": "lint", "prd": "orders", "version": "1.0.0",
        "dir": "docs/prd/orders",
        "findings": [{"file": "contracts/errors.yaml", "line": 41, "rule": "contracts-valid",
                      "severity": "error",
                      "message": "duplicate key 'FORBIDDEN' (first at line 25, again at line 41)"}],
        "errors": 1, "warnings": 0,
    }


def test_t014_2_json_errors(tmp_path, monkeypatch):
    """@prd T-014.2"""
    s0(tmp_path, monkeypatch)
    r1 = run(["--json", "--bogus", "docs/prd/orders"], cwd=tmp_path)
    assert r1.exit == 2
    assert one_json(r1.stdout) == {"interface": 1, "kind": "lint",
                                   "error": "unrecognized arguments: --bogus"}
    lines = r1.stderr_lines
    assert lines and lines[0].startswith("usage: prd_lint.py"), r1.stderr
    assert lines[-1] == "prd_lint.py: error: unrecognized arguments: --bogus"

    missing = tmp_path.resolve() / "missing"
    r2 = run(["--json", tmp_path / "missing"], cwd=tmp_path)
    assert r2.exit == 2
    assert one_json(r2.stdout) == {"interface": 1, "kind": "lint",
                                   "error": f"{missing}: no prd.md"}
    assert r2.stderr == f"prd_lint: {missing}: no prd.md\n"


def test_t014_3_json_equals_form(tmp_path, monkeypatch):
    """@prd T-014.3"""
    s0(tmp_path, monkeypatch)
    r = run(["--json=1", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 0
    assert r.stderr == ""
    assert one_json(r.stdout) == CLEAN


def test_t014_4_unsupported_interface(tmp_path):
    """@prd T-014.4"""
    r = run(["--json=2", tmp_path / "missing"], cwd=tmp_path)
    assert r.exit == 2
    msg = "unsupported interface 2; this toolkit speaks 1"
    assert one_json(r.stdout) == {"interface": 1, "kind": "lint", "error": msg}
    assert r.stderr == f"prd_lint: {msg}\n"


def test_t014_5_interface(tmp_path):
    """@prd T-014.5"""
    for args in (["--interface"], ["--interface", tmp_path / "missing"]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stdout == "1\n", args
        assert r.stderr == "", args


def test_t014_6_json_with_other_options(tmp_path, monkeypatch):
    """@prd T-014.6"""
    s0(tmp_path, monkeypatch)
    r1 = run(["--json", "--list-rules"], cwd=tmp_path)
    assert r1.exit == 0 and r1.stderr == ""
    l1 = r1.stdout_lines
    assert l1[0] == "ac-ears error"
    assert "platform-word warn" in l1

    r2 = run(["--json", "--sample-tids", "99", "docs/prd/orders"], cwd=tmp_path)
    assert r2.exit == 0 and r2.stderr == ""
    assert "T-001.1 test-cases/import.yaml" in r2.stdout_lines

    r3 = run(["--json", "--list-packs"], cwd=tmp_path)
    assert r3.exit == 0 and r3.stderr == ""
    assert r3.stdout_lines[0] == PACK_DOC


def test_t014_7_json_before_or_after_folder(tmp_path, monkeypatch):
    """@prd T-014.7"""
    s0(tmp_path, monkeypatch)
    for args in (["--json", "docs/prd/orders"], ["docs/prd/orders", "--json"]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stderr == "", args
        obj = one_json(r.stdout)
        assert list(obj)[:2] == ["interface", "kind"]
        assert obj == CLEAN


def test_t014_8_interface_wins(tmp_path):
    """@prd T-014.8"""
    for args in (["--interface", "--json=2"], ["--json=2", "--interface", tmp_path / "missing"]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stdout == "1\n", args
        assert r.stderr == "", args
