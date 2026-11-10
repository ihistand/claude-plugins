"""lint-structure FR-029 and FR-030: open clarification markers and assumption markers."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, finding_in, symptom, texts  # noqa: E402

D = "docs/prd/orders"
P = f"{D}/prd.md"
ROW = "| A-01 | Reps see only their own orders | {} |"


def test_marker_approved(tmp_path, monkeypatch):
    """@prd T-029.1"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    assert o.lines("prd.md").line(4) == "status: Approved"
    o.lines("nfr.md").append(t["m_line"])
    check(o.run(), exit=1, contains_line=t["m_expect_approved"], stderr="")


def test_marker_in_review(tmp_path, monkeypatch):
    """@prd T-029.2"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: In review")
    o.lines("nfr.md").append(t["m_line"])
    check(o.run(), exit=1, contains_line=t["m_expect_review"], stderr="")


def test_marker_yaml_value(tmp_path, monkeypatch):
    """@prd T-029.3"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/config.yaml").replace(6, t["m_yaml_value_line"])
    check(o.run(), exit=1, contains_line=t["m_yaml_value_expect"], stderr="")


def test_marker_yaml_comment(tmp_path, monkeypatch):
    """@prd T-029.4"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/config.yaml").append(t["m_yaml_comment"])
    check(o.run(), exit=1, contains_line=t["m_yaml_comment_expect"], stderr="")


def test_marker_sql_comment(tmp_path, monkeypatch):
    """@prd T-029.5"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/schema.sql").append(t["m_sql_comment"])
    check(o.run(), exit=1, contains_line=t["m_sql_expect"], stderr="")


def test_marker_in_code_span(tmp_path, monkeypatch):
    """@prd T-029.6"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("nfr.md").append(t["m_code_span_line"])
    check(o.run(), not_contains="markers-open", stderr="")


def test_unscanned_raw_files(tmp_path, monkeypatch):
    """@prd T-029.7"""
    t = texts()
    m = t["m_line"]
    o = Orders(tmp_path, monkeypatch)
    o.write("contracts/fixtures/notes.json", m + "\n")
    o.write(".notes.yaml", m + "\n")
    o.write("prd.md~", m + "\n")
    o.write("contracts/custom/notes.lkml", m + "\n")
    o.write("contracts/blob.json", b"\x00" + m.encode("utf-8"))
    o.write("contracts/latin.json", b"\xff" + m.encode("utf-8"))
    check(o.run(), not_contains="markers-open", stderr="")


def test_upstream_skipped_with_links(tmp_path, monkeypatch):
    """@prd T-029.8"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.write_lines(
        "links.md",
        [
            "# Links",
            "",
            "## Upstreams",
            "",
            "| Upstream | Location | Version | Commit | Needs |",
            "|---|---|---|---|---|",
            "| greet | `../greet` | | | verified |",
        ],
    )
    o.write("contracts/upstream/greet/notes.yaml", t["m_upstream_file"])
    check(o.run(), not_contains="markers-open", stderr="")


def test_upstream_scanned_without_links(tmp_path, monkeypatch):
    """@prd T-029.9"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.write("contracts/upstream/greet/notes.yaml", t["m_upstream_file"])
    assert not (o.root / "links.md").exists()
    check(o.run(), exit=1, contains_line=t["m_upstream_expect"], stderr="")


def test_marker_draft(tmp_path, monkeypatch):
    """@prd T-029.10"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: Draft")
    o.lines("nfr.md").append(t["m_line"])
    check(o.run(), not_contains="markers-open", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-011")
def test_marker_hidden_markdown(tmp_path, monkeypatch):
    """@prd T-029.11 known-failing E-011"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    assert o.lines("prd.md").line(4) == "status: Approved"
    o.write(".notes.md", t["m_line"] + "\n")
    r = o.run()
    symptom(
        finding_in(r, ".notes.md", "markers-open"),
        "E-011",
        "markers-open reports a line of the hidden file .notes.md",
        r,
    )
    check(r, exit=0, not_contains="markers-open", stderr="")


def test_assumption_without_id(tmp_path, monkeypatch):
    """@prd T-030.1"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("nfr.md").append(t["a_noid_line"])
    check(o.run(), exit=1, contains_line=t["a_noid_expect"], stderr="")


def test_assumption_not_indexed(tmp_path, monkeypatch):
    """@prd T-030.2"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("nfr.md").append(t["a_a09_line"])
    check(o.run(), exit=1, contains_line=f"{D}/nfr.md:23: assumption-indexed: A-09 has no row in section 12", stderr="")


def test_assumption_yaml_comment_draft(tmp_path, monkeypatch):
    """@prd T-030.3"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: Draft")
    o.lines("contracts/config.yaml").append(t["a_a09_yaml"])
    check(o.run(), exit=1, contains_line=f"{D}/contracts/config.yaml:7: assumption-indexed: A-09 has no row in section 12", stderr="")


def test_assumption_indexed(tmp_path, monkeypatch):
    """@prd T-030.4"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/config.yaml").append(t["a_a01_yaml"])
    check(o.run(), not_contains="assumption-indexed", stderr="")


def test_assumption_bad_status(tmp_path, monkeypatch):
    """@prd T-030.5"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(112, ROW.format("maybe"))
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:112: assumption-indexed: A-01: status 'maybe' must be open, confirmed, corrected or awaiting <who>",
        stderr="",
    )


def test_assumption_bare_awaiting(tmp_path, monkeypatch):
    """@prd T-030.6"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(112, ROW.format("awaiting"))
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:112: assumption-indexed: A-01: status 'awaiting' must be open, confirmed, corrected or awaiting <who>",
        stderr="",
    )


def test_assumption_open_approved(tmp_path, monkeypatch):
    """@prd T-030.7"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(112, ROW.format("open"))
    check(o.run(), exit=1, contains_line=f"{P}:112: assumption-indexed: A-01 is open while the PRD is Approved", stderr="")


def test_assumption_awaiting_name(tmp_path, monkeypatch):
    """@prd T-030.8"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(112, ROW.format("awaiting Sam Rivera"))
    check(o.run(), not_contains="assumption-indexed", stderr="")


def test_assumption_open_in_review(tmp_path, monkeypatch):
    """@prd T-030.9"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: In review").replace(112, ROW.format("open"))
    check(o.run(), not_contains="assumption-indexed", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-011")
def test_assumption_hidden_markdown(tmp_path, monkeypatch):
    """@prd T-030.10 known-failing E-011"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.write(".notes.md", t["a_a09_line"] + "\n")
    r = o.run()
    symptom(
        finding_in(r, ".notes.md", "assumption-indexed"),
        "E-011",
        "assumption-indexed reports a line of the hidden file .notes.md",
        r,
    )
    check(r, exit=0, not_contains="assumption-indexed", stderr="")
