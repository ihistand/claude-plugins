"""lint-structure FR-028: a vague word without a number."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, symptom  # noqa: E402

D = "docs/prd/orders"
IMPORT_LINE_11 = "  and log `IMPORT_DUPLICATE` once for it"


def test_vague_on_continuation(tmp_path, monkeypatch):
    """@prd T-028.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(11, IMPORT_LINE_11 + " and shall be fast.")
    check(o.run(), exit=1, contains_line=f"{D}/features/import.md:10: vague-word: 'fast' with no measurable number on the line", stderr="")


def test_vague_any_case_ids_no_number(tmp_path, monkeypatch):
    """@prd T-028.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(11, IMPORT_LINE_11 + ", as Fast as AC-001.1 asks.")
    check(o.run(), exit=1, contains_line=f"{D}/features/import.md:10: vague-word: 'Fast' with no measurable number on the line", stderr="")


def test_vague_with_number(tmp_path, monkeypatch):
    """@prd T-028.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(11, IMPORT_LINE_11 + ", fast for up to 10 rows.")
    check(o.run(), exit=0, stdout_exact="", stderr="")


def test_vague_nfr_line(tmp_path, monkeypatch):
    """@prd T-028.4"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("nfr.md").replace(9, "Traces: UJ-01; FR-002; robust")
    check(o.run(), exit=1, contains_line=f"{D}/nfr.md:9: vague-word: 'robust' with no measurable number on the line", stderr="")


def test_vague_nfr_code_span(tmp_path, monkeypatch):
    """@prd T-028.5"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("nfr.md").replace(9, "Traces: UJ-01; FR-002; `robust`")
    check(o.run(), not_contains="vague-word", stderr="")


def test_vague_removed_ac(tmp_path, monkeypatch):
    """@prd T-028.6"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(
        12,
        "- AC-001.3 (removed in 1.1.0) If the import file is empty, the importer shall be fast and finish with status `empty`,",
    )
    check(o.run(), not_contains="vague-word", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-010")
def test_vague_in_code_span(tmp_path, monkeypatch):
    """@prd T-028.7 known-failing E-010"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(11, IMPORT_LINE_11 + ", with the flag `--secure`.")
    r = o.run()
    symptom(
        "vague-word: 'secure'" in r.stdout,
        "E-010",
        "vague-word reports 'secure' from inside a code span of the AC",
        r,
    )
    check(r, exit=0, not_contains="vague-word", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-010")
def test_digit_in_code_span_is_no_number(tmp_path, monkeypatch):
    """@prd T-028.8 known-failing E-010"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("features/import.md").replace(11, IMPORT_LINE_11 + " and be fast with `--limit 50`.")
    r = o.run()
    symptom(
        "vague-word" not in r.stdout,
        "E-010",
        "no vague-word finding, the digit inside the code span counted as a number",
        r,
    )
    check(r, exit=1, contains_line=f"{D}/features/import.md:10: vague-word: 'fast' with no measurable number on the line", stderr="")
