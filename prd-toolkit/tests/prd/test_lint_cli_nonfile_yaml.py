"""lint-cli: a `.yaml` entry in test-cases/ or contracts/ that is not a regular file (AC-006.3).

Cases T-006.4 and T-006.5 of docs/prd/prd-toolkit/test-cases/lint-cli.yaml, the regression tests
of E-007. Their expected-failure markers were removed in the E-007 fixes build; the E-007 symptom,
if it is seen, now fails the test with E007Symptom.
"""
import os

import pytest

from lint_cli_support import run, s0


class E007Symptom(Exception):
    """The E-007 symptom was seen: lint exited 2 with the one-line internal error on stderr."""


def check_symptom(r, exc_type: str) -> None:
    """Raise E007Symptom when the run shows the case's `symptom:`.

    Symptom: lint exits 2 and its stderr is one line that starts with
    `prd_lint: internal error: <exc_type>: ` (stderr_single_line_starts, testing.md Assertions).
    """
    prefix = f"prd_lint: internal error: {exc_type}: "
    lines = r.stderr_lines
    if r.exit == 2 and len(lines) == 1 and lines[0].startswith(prefix):
        raise E007Symptom(lines[0])


def test_t006_4_yaml_directory_in_test_cases_is_a_finding(tmp_path, monkeypatch):
    """@prd T-006.4"""
    root = s0(tmp_path, monkeypatch)
    (root / "test-cases" / "sub.yaml").mkdir()
    r = run(["docs/prd/orders"], cwd=tmp_path)
    check_symptom(r, "IsADirectoryError")
    assert r.exit == 1
    assert r.stdout == "docs/prd/orders/test-cases/sub.yaml:0: sufficiency: a .yaml entry that is not a file\n"
    assert r.stderr == ""


def test_t006_5_broken_yaml_symlink_in_contracts_is_a_finding(tmp_path, monkeypatch):
    """@prd T-006.5"""
    root = s0(tmp_path, monkeypatch)
    target = tmp_path / "missing.yaml"
    assert not target.exists()
    os.symlink(str(target), str(root / "contracts" / "gone.yaml"))
    r = run(["docs/prd/orders"], cwd=tmp_path)
    check_symptom(r, "FileNotFoundError")
    assert r.exit == 1
    assert r.stdout == "docs/prd/orders/contracts/gone.yaml:0: sufficiency: a .yaml entry that is not a file\n"
    assert r.stderr == ""
