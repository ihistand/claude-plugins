"""lint-structure FR-026 and FR-027: prose without code and quotations, and placeholders."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, finding_in, symptom, texts  # noqa: E402

D = "docs/prd/orders"


def test_fenced_block_is_not_prose(tmp_path, monkeypatch):
    """@prd T-026.1"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append(*t["q_fence_lines"])
    check(o.run(), not_contains=["placeholder", "glossary-synonym"], stderr="")


def test_errors_md_quotations_blanked(tmp_path, monkeypatch):
    """@prd T-026.2"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("errors.md").append(*t["e_quoted_lines"])
    check(
        o.run(),
        not_contains=[
            f"{D}/errors.md:13: glossary-synonym",
            f"{D}/errors.md:14: placeholder",
            f"{D}/errors.md:15: placeholder",
        ],
        stderr="",
    )


def test_errors_md_diagnosis_is_prose(tmp_path, monkeypatch):
    """@prd T-026.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("errors.md").append(
        "",
        "### E-002 quoted",
        "Detected: 2026-11-03, user report",
        "Classification: code bug",
        "Evidence: e",
        "Diagnosis: usage: greet <name>",
        "Resolution: -",
        "Recurrence of: -",
    )
    check(
        o.run(),
        exit=1,
        contains_line=f"{D}/errors.md:14: placeholder: placeholder '<name>' in prose; if this is literal text, put it in backticks",
        stderr="",
    )


def test_evidence_outside_errors_md_is_prose(tmp_path, monkeypatch):
    """@prd T-026.4"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append(t["q_evidence_line"])
    check(o.run(), exit=1, contains_line=t["p_tbd_expect"], stderr="")


def test_tbd(tmp_path, monkeypatch):
    """@prd T-027.1"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append(t["p_tbd_line"])
    check(o.run(), exit=1, contains_line=t["p_tbd_expect"], stderr="")


def test_angle_bracket_slot(tmp_path, monkeypatch):
    """@prd T-027.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append("Pick the <the data_state> now.")
    check(
        o.run(),
        exit=1,
        contains_line=f"{D}/operations.md:48: placeholder: placeholder '<the data_state>' in prose; if this is literal text, put it in backticks",
        stderr="",
    )


def test_template_slot(tmp_path, monkeypatch):
    """@prd T-027.3"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(10, t["p_slot_heading"])
    check(o.run(), exit=1, contains_line=t["p_slot_expect"], stderr="")


def test_question_marks(tmp_path, monkeypatch):
    """@prd T-027.4"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append(t["p_qqq_line"])
    check(o.run(), exit=1, contains_line=t["p_qqq_expect"], stderr="")


def test_not_placeholders(tmp_path, monkeypatch):
    """@prd T-027.5"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("operations.md").append(t["p_clean_line"])
    check(o.run(), not_contains="placeholder", stderr="")


def test_yaml_value(tmp_path, monkeypatch):
    """@prd T-027.6"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/config.yaml").replace(6, "    owner: " + t["p_yaml_value"])
    check(o.run(), exit=1, contains_line=t["p_yaml_expect"], stderr="")


def test_yaml_list_item(tmp_path, monkeypatch):
    """@prd T-027.7"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("test-cases/import.yaml").replace(15, "      - \"" + t["p_case_item"] + "\"")
    check(o.run(), exit=1, contains_line=t["p_case_expect"], stderr="")


def test_yaml_angle_and_comment(tmp_path, monkeypatch):
    """@prd T-027.8"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.lines("contracts/config.yaml").replace(6, "    owner: <Sample Owner>").append(t["p_yaml_comment"])
    check(o.run(), not_contains="placeholder", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-011")
def test_hidden_file(tmp_path, monkeypatch):
    """@prd T-027.9 known-failing E-011"""
    t = texts()
    o = Orders(tmp_path, monkeypatch)
    o.write(".notes.md", t["p_tbd_line"] + "\n")
    r = o.run()
    symptom(
        finding_in(r, ".notes.md", "placeholder"),
        "E-011",
        "placeholder reports a line of the hidden file .notes.md",
        r,
    )
    check(r, exit=0, not_contains="placeholder", stderr="")
