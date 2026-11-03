"""Helpers for the lint-cli black-box tests (docs/prd/prd-toolkit/test-cases/lint-cli.yaml).

Everything here follows docs/prd/prd-toolkit/testing.md (Harness, Fixtures) and the conventions
at the top of test-cases/lint-cli.yaml.
"""
import os
import subprocess
import sys
from pathlib import Path

import yaml

# <repo> is the repository root: prd-toolkit/tests/prd/<this file>.
REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "prd-toolkit" / "scripts"
PRD_LINT = SCRIPTS / "prd_lint.py"
PRD_PUBLISH = SCRIPTS / "prd_publish.py"
# Load paths are relative to contracts/fixtures/ (testing.md, Fixtures).
FIXTURES = REPO / "docs" / "prd" / "prd-toolkit" / "contracts" / "fixtures"
PLUGINS_SUPERPOWERS = FIXTURES / "lint-cli" / "plugins_superpowers.json"
PLUGINS_NONE = FIXTURES / "lint-cli" / "plugins_none.json"

# The nine sample lines of T-007.1.
NINE = [
    "T-001.1 test-cases/import.yaml",
    "T-001.2 test-cases/import.yaml",
    "T-001.4 test-cases/import.yaml",
    "T-002.1 test-cases/api.yaml",
    "T-002.2 test-cases/api.yaml",
    "T-003.1 test-cases/api.yaml",
    "T-003.2 test-cases/api.yaml",
    "T-004.1 test-cases/nfr.yaml",
    "T-004.2 test-cases/nfr.yaml",
]


def write_orders(tmp: Path) -> Path:
    """Load fixture lint-cli/orders: write each key's text to <tmp>/docs/prd/orders/<key>."""
    data = yaml.safe_load((FIXTURES / "lint-cli" / "orders.yaml").read_text(encoding="utf-8"))
    root = tmp / "docs" / "prd" / "orders"
    for rel, text in data.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(text.encode("utf-8"))
    return root


def s0(tmp: Path, monkeypatch) -> Path:
    """S0: the orders folder, and PRD_PLUGINS_FILE set to lint-cli/plugins_superpowers.json."""
    root = write_orders(tmp)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_SUPERPOWERS))
    return root


def append(path: Path, text: str) -> None:
    with open(path, "ab") as fh:
        fh.write(text.encode("utf-8"))


def m1(root: Path) -> None:
    """M1: append the line `FORBIDDEN: {}` to contracts/errors.yaml (it becomes line 41)."""
    append(root / "contracts" / "errors.yaml", "FORBIDDEN: {}\n")


class Run:
    def __init__(self, proc: subprocess.CompletedProcess):
        self.exit = proc.returncode
        self.stdout_bytes = proc.stdout
        self.stderr_bytes = proc.stderr
        self.stdout = proc.stdout.decode("utf-8")
        self.stderr = proc.stderr.decode("utf-8")

    @property
    def stdout_lines(self) -> list[str]:
        return self.stdout.splitlines()

    @property
    def stderr_lines(self) -> list[str]:
        return self.stderr.splitlines()


def run(args, cwd: Path, env: dict | None = None, unset=(), script: Path = PRD_LINT,
        python: str | None = None) -> Run:
    """Run `python <script> <args>` as a subprocess in `cwd`, capturing stdout and stderr as bytes.

    The environment is the test process's (with any monkeypatch changes) minus PYTHONIOENCODING,
    PYTHONPATH and PYTHONHOME (testing.md, Harness, Subprocess environment) and minus `unset`,
    plus `env`.
    """
    full_env = dict(os.environ)
    for name in ("PYTHONIOENCODING", "PYTHONPATH", "PYTHONHOME", *unset):
        full_env.pop(name, None)
    if env:
        full_env.update(env)
    proc = subprocess.run(
        [python or sys.executable, str(script), *[str(a) for a in args]],
        cwd=str(cwd),
        env=full_env,
        capture_output=True,
        timeout=300,
    )
    return Run(proc)
