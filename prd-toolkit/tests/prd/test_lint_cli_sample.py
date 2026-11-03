"""lint-cli FR-007: --sample-tids (test-cases/lint-cli.yaml)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import NINE, m1, run, s0  # noqa: E402


def test_t007_1_sample_all_non_unit(tmp_path, monkeypatch):
    """@prd T-007.1"""
    s0(tmp_path, monkeypatch)
    r = run(["--sample-tids", "99", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 0
    assert r.stderr == ""
    assert sorted(r.stdout_lines) == sorted(NINE), r.stdout


def test_t007_2_sample_three_and_zero(tmp_path, monkeypatch):
    """@prd T-007.2"""
    s0(tmp_path, monkeypatch)
    r1 = run(["--sample-tids", "3", "docs/prd/orders"], cwd=tmp_path)
    assert r1.exit == 0
    assert r1.stderr == ""
    lines = r1.stdout_lines
    assert len(lines) == 3, r1.stdout
    assert len(set(lines)) == 3, r1.stdout
    assert all(line in NINE for line in lines), r1.stdout
    r2 = run(["--sample-tids", "0", "docs/prd/orders"], cwd=tmp_path)
    assert (r2.exit, r2.stderr, r2.stdout) == (0, "", "")


def test_t007_3_sample_runs_no_rule(tmp_path, monkeypatch):
    """@prd T-007.3"""
    root = s0(tmp_path, monkeypatch)
    m1(root)
    r = run(["--sample-tids", "99", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 0
    assert r.stderr == ""
    assert sorted(r.stdout_lines) == sorted(NINE), r.stdout
    assert not any("contracts-valid" in line for line in r.stdout_lines), r.stdout


def test_t007_4_no_non_unit_case(tmp_path, monkeypatch):
    """@prd T-007.4"""
    root = s0(tmp_path, monkeypatch)
    for path in sorted((root / "test-cases").glob("*.yaml")):
        text = path.read_bytes().decode("utf-8")
        path.write_bytes(re.sub(r"level: \w+", "level: unit", text).encode("utf-8"))
    r = run(["--sample-tids", "3", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout == ""
    assert r.stderr == "prd_lint: no non-unit T-ids to sample\n"


@pytest.mark.xfail(strict=True, reason="E-006")
def test_t007_5_no_level_or_uppercase_level_not_sampled(tmp_path, monkeypatch):
    """@prd T-007.5 known-failing E-006"""
    root = s0(tmp_path, monkeypatch)
    (root / "test-cases" / "odd.yaml").write_bytes(b"T-009.1: plain text\nT-009.2: {level: Unit}\n")
    r = run(["--sample-tids", "99", "docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 0
    assert r.stderr == ""
    assert sorted(r.stdout_lines) == sorted(NINE), r.stdout
    assert not any("T-009.1" in line or "T-009.2" in line for line in r.stdout_lines), r.stdout
