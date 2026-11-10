"""lint-structure FR-031 and FR-032: open questions and banned glossary synonyms."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, finding_in, symptom  # noqa: E402

D = "docs/prd/orders"
P = f"{D}/prd.md"
MSG = "open-questions-empty: section 13 must be 'None.' when the PRD is Approved"


def test_open_question_approved(tmp_path, monkeypatch):
    """@prd T-031.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(116, "- Q-01 Who owns refunds?", "- Q-02 Who approves deletes?")
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:116: {MSG}",
        not_contains=f"{P}:117: open-questions-empty",
        stderr="",
    )


def test_open_question_in_review(tmp_path, monkeypatch):
    """@prd T-031.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: In review").replace(116, "- Q-01 Who owns refunds?")
    check(o.run(), not_contains="open-questions-empty", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-015")
def test_section_13_empty(tmp_path, monkeypatch):
    """@prd T-031.3 known-failing E-015"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").delete(116)
    r = o.run()
    symptom(
        "open-questions-empty" not in r.stdout,
        "E-015",
        "no open-questions-empty finding for a section 13 with no text",
        r,
    )
    check(r, exit=1, contains_line=f"{P}:114: {MSG}", stderr="")


def test_synonym_in_flow(tmp_path, monkeypatch):
    """@prd T-032.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(
        5,
        "Flow: 0. a purchase arrives → 1. Importer reads a file → 2. validates each row's postal code with the geocoder",
    )
    check(o.run(), exit=1, contains_line=f"{D}/features/import.md:5: glossary-synonym: 'purchase' is a banned synonym; use 'order'", stderr="")


def test_synonym_plural_any_case(tmp_path, monkeypatch):
    """@prd T-032.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append("Clients call the API.")
    check(o.run(), exit=1, contains_line=f"{D}/operations.md:48: glossary-synonym: 'Clients' is a banned synonym; use 'customer'", stderr="")


def test_synonym_in_code_span(tmp_path, monkeypatch):
    """@prd T-032.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append("Each `purchase` is an order.")
    check(o.run(), exit=0, stdout_exact="", stderr="")


def test_empty_synonym_parts(tmp_path, monkeypatch):
    """@prd T-032.4"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(40, "| order | A customer's request for goods, stored once per order_key | — |").replace(
        41, "| customer | The person or company an order belongs to | none |"
    )
    o.lines("operations.md").append("A purchase by a client: none lost.")
    check(o.run(), not_contains="glossary-synonym", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-011")
def test_synonym_hidden_file(tmp_path, monkeypatch):
    """@prd T-032.5 known-failing E-011"""
    o = Orders(tmp_path, monkeypatch)
    o.write(".notes.md", "a purchase arrives\n")
    r = o.run()
    symptom(
        finding_in(r, ".notes.md", "glossary-synonym"),
        "E-011",
        "glossary-synonym reports a line of the hidden file .notes.md",
        r,
    )
    check(r, exit=0, not_contains="glossary-synonym", stderr="")
