"""Shared helper for the lint-structure black-box tests (testing.md Harness, Layout).

Everything here follows docs/prd/prd-toolkit/testing.md and the conventions at the top of
docs/prd/prd-toolkit/test-cases/lint-structure.yaml:

- S0 writes fixture lint-cli/orders to <tmp>/docs/prd/orders and sets PRD_PLUGINS_FILE to
  fixture lint-cli/plugins_superpowers.json.
- "line N of F" is line N of F as written before any other step of the case, so every edit
  of a file is addressed by its original line numbers.
- The lint command runs as `python <repo>/prd-toolkit/scripts/prd_lint.py docs/prd/orders`
  with the test's own interpreter, cwd <tmp>, and the runner's environment minus
  PYTHONIOENCODING, PYTHONPATH, PYTHONHOME and PRD_LINT_CI.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "docs" / "prd" / "prd-toolkit" / "contracts" / "fixtures"
LINT = REPO / "prd-toolkit" / "scripts" / "prd_lint.py"
DROPPED_ENV = ("PYTHONIOENCODING", "PYTHONPATH", "PYTHONHOME", "PRD_LINT_CI")

A1_LINES = [
    "# Adoption map",
    "",
    "| Area | State | Boundary |",
    "|---|---|---|",
    "| import | adopted | `features/import.md` |",
]


def texts() -> dict:
    """Fixture lint-structure/texts, read with yaml.safe_load."""
    return yaml.safe_load((FIXTURES / "lint-structure" / "texts.yaml").read_text(encoding="utf-8"))


@dataclass
class Result:
    exit: int
    stdout: str
    stderr: str


class Lines:
    """A text file edited by its original line numbers (1-based)."""

    def __init__(self, path: Path, text: str | None = None):
        self.path = path
        if text is None:
            text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        self.original = list(lines)
        self.entries: list[list[str]] = [[line] for line in lines]
        self.tail: list[str] = []

    def line(self, n: int) -> str:
        return self.original[n - 1]

    def replace(self, n: int, *new: str) -> "Lines":
        self.entries[n - 1] = list(new)
        return self

    def delete(self, n: int, to: int | None = None) -> "Lines":
        for i in range(n, (to or n) + 1):
            self.entries[i - 1] = []
        return self

    def insert_before(self, n: int, *new: str) -> "Lines":
        self.entries[n - 1] = list(new) + self.entries[n - 1]
        return self

    def append(self, *new: str) -> "Lines":
        self.tail.extend(new)
        return self

    def swap(self, a: int, b: int) -> "Lines":
        self.entries[a - 1], self.entries[b - 1] = self.entries[b - 1], self.entries[a - 1]
        return self

    def sub(self, n: int, old: str, new: str) -> "Lines":
        """Replace the text `old` on original line n with `new`; the line must hold it."""
        line = self.original[n - 1]
        assert old in line, f"setup: line {n} of {self.path.name} does not hold {old!r}: {line!r}"
        self.entries[n - 1] = [line.replace(old, new, 1)]
        return self

    def text(self) -> str:
        out = [line for entry in self.entries for line in entry] + self.tail
        return "".join(line + "\n" for line in out)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.text(), encoding="utf-8")


class Orders:
    """The orders PRD folder of setup step S0, in the test's own tmp_path."""

    def __init__(self, tmp_path: Path, monkeypatch):
        self.tmp = tmp_path
        self.root = tmp_path / "docs" / "prd" / "orders"
        files = yaml.safe_load((FIXTURES / "lint-cli" / "orders.yaml").read_text(encoding="utf-8"))
        for key, text in files.items():
            target = self.root / key
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        monkeypatch.setenv("PRD_PLUGINS_FILE", str((FIXTURES / "lint-cli" / "plugins_superpowers.json").resolve()))
        self._edits: dict[str, Lines] = {}

    def lines(self, rel: str) -> Lines:
        """The file `rel` (relative to the PRD folder) for edits by original line number."""
        if rel not in self._edits:
            self._edits[rel] = Lines(self.root / rel)
        return self._edits[rel]

    def write_lines(self, rel: str, lines: list[str]) -> Lines:
        """Write `rel` as `lines`, each ending in a newline; later edits use these line numbers."""
        edit = Lines(self.root / rel, "".join(line + "\n" for line in lines))
        self._edits[rel] = edit
        return edit

    def write(self, rel: str, content: str | bytes) -> None:
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")

    def delete(self, rel: str) -> None:
        (self.root / rel).unlink()

    def a1(self) -> Lines:
        return self.write_lines("adoption.md", A1_LINES)

    def run(self) -> Result:
        for edit in self._edits.values():
            if edit.path.exists() or edit.entries or edit.tail:
                edit.save()
        env = dict(os.environ)
        for name in DROPPED_ENV:
            env.pop(name, None)
        proc = subprocess.run(
            [sys.executable, str(LINT), "docs/prd/orders"],
            cwd=self.tmp,
            env=env,
            capture_output=True,
            text=True,
        )
        return Result(proc.returncode, proc.stdout, proc.stderr)


def _show(r: Result) -> str:
    return f"\nexit: {r.exit}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"


class KnownFailure(Exception):
    """The symptom a known-failing case names (its `symptom:`), seen in a run.

    A known-failing test's marker is `pytest.mark.xfail(strict=True, raises=KnownFailure)`, so
    only this exception counts as the expected failure; any other failure fails the test.
    """


def symptom(seen: bool, entry: str, text: str, r: Result) -> None:
    """Raise KnownFailure when the case's symptom is seen in the run."""
    if seen:
        raise KnownFailure(f"{entry}: {text}" + _show(r))


def finding_in(r: Result, rel: str, rule: str) -> bool:
    """Whether stdout holds a finding line of rule `rule` for the file `rel` of the PRD folder."""
    prefix = f"docs/prd/orders/{rel}:"
    return any(line.startswith(prefix) and f": {rule}: " in line for line in r.stdout.splitlines())


def check(
    r: Result,
    *,
    exit: int | None = None,
    contains_line: str | None = None,
    contains: str | list[str] | None = None,
    not_contains: str | list[str] | None = None,
    in_order: list[str] | None = None,
    count_of_line: tuple[str, int] | None = None,
    stdout_exact: str | None = None,
    stderr: str | None = None,
) -> None:
    """Assert a case's expect.output keys, as testing.md's Assertions slot defines them."""
    if exit is not None:
        assert r.exit == exit, f"exit {r.exit}, expected {exit}" + _show(r)
    lines = r.stdout.splitlines()
    if contains_line is not None:
        assert contains_line in lines, f"stdout lacks the line {contains_line!r}" + _show(r)
    if contains is not None:
        for s in [contains] if isinstance(contains, str) else contains:
            assert s in r.stdout, f"stdout lacks {s!r}" + _show(r)
    if not_contains is not None:
        for s in [not_contains] if isinstance(not_contains, str) else not_contains:
            assert s not in r.stdout, f"stdout holds {s!r}" + _show(r)
    if in_order is not None:
        pos = 0
        for want in in_order:
            try:
                pos = lines.index(want, pos) + 1
            except ValueError:
                raise AssertionError(f"stdout lacks the line {want!r} after line {pos}" + _show(r))
    if count_of_line is not None:
        line, count = count_of_line
        got = lines.count(line)
        assert got == count, f"{got} stdout lines equal {line!r}, expected {count}" + _show(r)
    if stdout_exact is not None:
        assert r.stdout == stdout_exact, f"stdout is not {stdout_exact!r}" + _show(r)
    if stderr is not None:
        assert r.stderr == stderr, f"stderr is not {stderr!r}" + _show(r)
