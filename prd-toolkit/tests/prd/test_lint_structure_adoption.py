"""lint-structure FR-024: section 8 and adoption.md."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, symptom, texts  # noqa: E402

D = "docs/prd/orders"
P = f"{D}/prd.md"


def test_table_in_section_8(tmp_path, monkeypatch):
    """@prd T-024.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "| Area | State | Boundary |", "|---|---|---|", "| import | adopted | `features/import.md` |")
    check(
        o.run(),
        exit=1,
        contains_line=f'{P}:82: sections: section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there and leave "See adoption.md."',
        stderr="",
    )


def test_points_at_missing_adoption(tmp_path, monkeypatch):
    """@prd T-024.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "See adoption.md.")
    check(o.run(), exit=1, contains_line=f"{P}:82: sections: section 8 points at adoption.md but adoption.md does not exist", stderr="")


def test_new_project_but_adoption_exists(tmp_path, monkeypatch):
    """@prd T-024.3"""
    o = Orders(tmp_path, monkeypatch)
    o.a1()
    assert o.lines("prd.md").line(84) == "Not applicable: new project."
    check(o.run(), exit=1, contains_line=f'{P}:82: sections: section 8 says "Not applicable: new project" but adoption.md exists', stderr="")


def test_other_body(tmp_path, monkeypatch):
    """@prd T-024.4"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "Adopted.")
    check(o.run(), exit=1, contains_line=f'{P}:82: sections: section 8 body must be "See adoption.md." or "Not applicable: new project."', stderr="")


def test_marker_in_section_8(tmp_path, monkeypatch):
    """@prd T-024.5"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, t["m_s8_line"])
    check(o.run(), exit=1, contains_line=t["m_s8_expect"], not_contains="sections: section 8", stderr="")


def test_adoption_without_table(tmp_path, monkeypatch):
    """@prd T-024.6"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "See adoption.md.")
    o.write_lines("adoption.md", ["# Adoption map", "", "No areas yet."])
    check(o.run(), exit=1, contains_line=f"{D}/adoption.md:1: sections: adoption.md holds no '| Area | State | Boundary |' table", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-016")
def test_adoption_bad_header(tmp_path, monkeypatch):
    """@prd T-024.7 known-failing E-016"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "See adoption.md.")
    o.write_lines("adoption.md", ["# Adoption map", "", "| Area | State |", "|---|---|", "| import | adopted |"])
    r = o.run()
    message = "sections: adoption.md table header must be '| Area | State | Boundary |', not '| Area | State |'"
    symptom(
        f"{D}/adoption.md:1: {message}" in r.stdout.splitlines(),
        "E-016",
        "the header finding is reported at adoption.md:1, not at the header's line",
        r,
    )
    check(r, exit=1, contains_line=f"{D}/adoption.md:3: {message}", stderr="")


def test_adoption_bad_state(tmp_path, monkeypatch):
    """@prd T-024.8"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "See adoption.md.")
    o.a1().replace(5, "| import | done | `features/import.md` |")
    check(
        o.run(),
        exit=1,
        contains_line=f"{D}/adoption.md:5: sections: adoption state 'done' for import must be one of not started, extracted, confirmed, adopted",
        stderr="",
    )


def test_adoption_clean(tmp_path, monkeypatch):
    """@prd T-024.9"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(84, "See adoption.md")
    o.a1().append("| legacy | not started | |")
    check(o.run(), not_contains="sections:", stderr="")
