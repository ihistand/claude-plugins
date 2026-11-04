"""Helpers for the lint-cli black-box tests (docs/prd/prd-toolkit/test-cases/lint-cli.yaml).

Everything here follows docs/prd/prd-toolkit/testing.md (Harness, Fixtures) and the conventions
at the top of test-cases/lint-cli.yaml.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
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


class VendoredFixtureMismatch(RuntimeError):
    """The repo/vendored fixture differs from what testing.md's Fixtures table says it holds."""


def load_vendored(tmp: Path) -> Path:
    """Load fixture repo/vendored (testing.md, Fixtures) and run its check.

    Copies <repo>/.prd-toolkit to <tmp>/.prd-toolkit as plain files (a symlink is followed and its
    target copied), leaving out every __pycache__ folder. Then checks that the only entry of
    <tmp>/.prd-toolkit/packs/ whose name does not start with `.` is a folder named `service`, and
    that pack-sources.json, parsed as JSON, equals {"service": "prd-toolkit"}; raises
    VendoredFixtureMismatch when either differs. Returns <tmp>/.prd-toolkit.
    """
    dest = tmp / ".prd-toolkit"
    shutil.copytree(
        REPO / ".prd-toolkit",
        dest,
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    packs = dest / "packs"
    visible = sorted(p for p in packs.iterdir() if not p.name.startswith(".")) if packs.is_dir() else []
    if [p.name for p in visible] != ["service"] or not visible[0].is_dir():
        raise VendoredFixtureMismatch(
            f"repo/vendored: packs/ holds {[p.name for p in visible]}, not only the folder 'service'"
        )
    try:
        sources = json.loads((dest / "pack-sources.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise VendoredFixtureMismatch(f"repo/vendored: pack-sources.json unreadable: {exc}") from exc
    if sources != {"service": "prd-toolkit"}:
        raise VendoredFixtureMismatch(
            f"repo/vendored: pack-sources.json is {sources!r}, not {{'service': 'prd-toolkit'}}"
        )
    return dest


@pytest.fixture(name="vendored")
def vendored_fixture(tmp_path) -> Path:
    """Fixture repo/vendored, loaded into <tmp>/.prd-toolkit with its check.

    Its check runs in pytest's setup phase, so a mismatch ends the test as an error, not a failure
    (testing.md, Fixtures). Returns <tmp>/.prd-toolkit.
    """
    return load_vendored(tmp_path)


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
    PYTHONPATH, PYTHONHOME and PRD_LINT_CI (testing.md, Harness, Subprocess environment) and minus
    `unset`, plus `env`.
    """
    full_env = dict(os.environ)
    for name in ("PYTHONIOENCODING", "PYTHONPATH", "PYTHONHOME", "PRD_LINT_CI", *unset):
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


def in_relative_order(lines: list[str], expected: list[str]) -> bool:
    """stdout_lines_in_this_relative_order (testing.md, Assertions): each expected line is found,
    whole, after the one before it, with other lines allowed between."""
    pos = 0
    for want in expected:
        try:
            pos = lines.index(want, pos) + 1
        except ValueError:
            return False
    return True


def in_process(monkeypatch):
    """Prepare an in-process call (testing.md, Harness, In-process calls).

    Applies the subprocess environment rules through monkeypatch (drops PYTHONIOENCODING,
    PYTHONPATH, PYTHONHOME and PRD_LINT_CI), puts prd-toolkit/scripts on sys.path, and returns
    the imported prd_lint module.
    """
    for name in ("PYTHONIOENCODING", "PYTHONPATH", "PYTHONHOME", "PRD_LINT_CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import importlib

    return importlib.import_module("prd_lint")


def register_zz_warn():
    """Register the rule zz-warn of T-001.4 and return a function that removes it.

    The rule takes the loaded PRD and returns
    [prdlint.findings.Finding("prd.md", 1, "zz-warn", "a warning", severity="warn")].
    """
    import importlib

    registry = importlib.import_module("prdlint.registry")
    findings = importlib.import_module("prdlint.findings")

    @registry.rule("zz-warn", severity="warn")
    def zz_warn(prd):
        return [findings.Finding("prd.md", 1, "zz-warn", "a warning", severity="warn")]

    def remove():
        registry.RULES.pop("zz-warn", None)
        registry.SEVERITY.pop("zz-warn", None)

    return remove
