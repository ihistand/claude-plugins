"""lint-structure FR-025: testing.md's Harness slots."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, symptom, texts  # noqa: E402

T = "docs/prd/orders/testing.md"
ROOTS = "Test roots: `tests/`."
ORDER = (
    "Lifecycle, Environment switch, Database access, Tools on the runner, Clean state, "
    "Persistent environments, Layout, HTTP requests, Fixtures, Browser identity, Assertions, "
    "Waits, Effects, Leaks, Acceptance"
)


def test_no_harness_section(tmp_path, monkeypatch):
    """@prd T-025.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").replace(15, "## Conventions")
    check(o.run(), exit=1, contains_line=f"{T}:1: sections: testing.md has no '## Harness' section with its slots", stderr="")


def test_slot_missing(tmp_path, monkeypatch):
    """@prd T-025.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").delete(28)
    check(o.run(), exit=1, contains_line=f"{T}:17: sections: Harness slot 'Waits' is missing", stderr="")


def test_slots_out_of_order(tmp_path, monkeypatch):
    """@prd T-025.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").swap(17, 23)
    check(o.run(), exit=1, contains_line=f"{T}:17: sections: Harness slots are out of order; the order is {ORDER}", stderr="")


def test_extra_slot_ignored(tmp_path, monkeypatch):
    """@prd T-025.4"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").insert_before(22, "- **Subprocess environment.** A script runs with the runner's environment.")
    check(o.run(), not_contains=["Harness slot", "Harness slots are out of order"], stderr="")


def test_layout_without_test_roots(tmp_path, monkeypatch):
    """@prd T-025.5"""
    o = Orders(tmp_path, monkeypatch)
    edit = o.lines("testing.md")
    assert edit.line(23).endswith(" " + ROOTS)
    edit.sub(23, " " + ROOTS, "")
    check(o.run(), exit=1, contains_line=f"{T}:23: sections: the Harness Layout slot has no 'Test roots:' text", stderr="")


def test_test_roots_not_backticked(tmp_path, monkeypatch):
    """@prd T-025.6"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").sub(23, ROOTS, "Test roots: tests/.")
    check(o.run(), exit=1, contains_line=f"{T}:23: sections: Test roots: lists no backticked directory", stderr="")


def test_test_roots_marker(tmp_path, monkeypatch):
    """@prd T-025.7"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").sub(23, ROOTS, t["m_roots_tail"])
    check(
        o.run(),
        exit=1,
        contains_line=t["m_roots_expect"],
        not_contains=["lists no backticked directory", "has no 'Test roots:' text"],
        stderr="",
    )


def test_no_testing_md(tmp_path, monkeypatch):
    """@prd T-025.8"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("testing.md")
    check(
        o.run(),
        exit=1,
        contains_line=f"{T}:0: sections: mandatory 'testing.md' is missing",
        not_contains=["has no '## Harness' section", "Harness slot", "Harness Layout slot"],
        stderr="",
    )


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-013")
def test_marker_elsewhere_on_layout(tmp_path, monkeypatch):
    """@prd T-025.9 known-failing E-013"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").sub(23, ROOTS, t["r_marker_elsewhere"])
    r = o.run()
    symptom(
        "Test roots: lists no backticked directory" not in r.stdout,
        "E-013",
        "no `Test roots: lists no backticked directory` finding while a marker sits elsewhere on the Layout line",
        r,
    )
    check(r, exit=1, contains_line=f"{T}:23: sections: Test roots: lists no backticked directory", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-014")
def test_slot_twice(tmp_path, monkeypatch):
    """@prd T-025.10 known-failing E-014"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("testing.md").insert_before(29, "- **Waits.** An expectation waits up to 5 s.")
    r = o.run()
    symptom(
        "Harness slots are out of order" in r.stdout and "appears twice" not in r.stdout,
        "E-014",
        "the repeated slot is reported as `Harness slots are out of order`, with no duplicate finding",
        r,
    )
    check(
        r,
        exit=1,
        contains_line=f"{T}:29: sections: Harness slot 'Waits' appears twice",
        not_contains="Harness slots are out of order",
        stderr="",
    )
