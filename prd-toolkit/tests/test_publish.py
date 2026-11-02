"""prd_publish.py: the self-contained page, its summaries and its refusals."""
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from conftest import edit
from prdlint import model, publish

TODAY = date(2026, 11, 1)
GOLDEN = Path(__file__).parent / "fixtures/publish/orders.html"
SCRIPT = Path(__file__).resolve().parent.parent / "scripts/prd_publish.py"


def render(prd, summaries=None):
    return publish.render_page(model.load(prd), prd.parent.parent.parent, summaries, TODAY)


def problems(prd, summaries):
    return publish.summary_problems(model.load(prd), summaries)


def test_golden(prd):
    assert render(prd) == GOLDEN.read_text(encoding="utf-8")


def test_loads_nothing(prd):
    page = render(prd, {"version": "1.0.0", "areas": {"import": {"text": "Files come in.", "ids": ["FR-001"]}}})
    for s in ("<script", "<link", "@import", "url("):
        assert s not in page


def test_markup_in_prd_is_text(prd):
    edit(prd, "features/import.md", "- AC-001.1 When an imported row has a new order_key,",
         "- AC-001.1 <script>alert(1)</script> $title {{x}} When an imported row has a new order_key,")
    page = render(prd)
    assert "&lt;script&gt;" in page and "<script" not in page
    assert "$title" in page and "{{x}}" in page


def test_markup_in_glossary_and_summary_is_text(prd):
    edit(prd, "prd.md", "| customer |", "| </div>$title |")
    page = render(prd, {"version": "1.0.0", "areas": {"api": {"text": "<b>x</b> $header", "ids": ["FR-002"]}}})
    assert "&lt;/div&gt;$title" in page and "&lt;b&gt;x&lt;/b&gt; $header" in page


def test_no_evidence(prd):
    edit(prd, "errors.md", "Diagnosis: the importer",
         "Evidence: SECRET-TRACE-LINE\n  and a second SECRET-TRACE-LINE\nDiagnosis: the importer")
    page = render(prd)
    assert "SECRET-TRACE-LINE" not in page
    assert "E-001 Empty import file crashed the importer" in page


def test_tabs_and_header(prd):
    page = render(prd)
    assert ">Business<" in page and ">Technical<" in page
    head = page.split("</header>")[0]
    for s in ("orders", "1.0.0", "Approved", "2026-11-01", "no commit"):
        assert s in head


def test_unapproved_status_is_prominent(prd):
    assert "status-flag" not in render(prd).split("</style>")[1]
    edit(prd, "prd.md", "status: Approved", "status: Draft")
    assert "status-flag" in render(prd).split("</style>")[1]


def test_summary_box(prd):
    page = render(prd, {"version": "1.0.0", "areas": {"api": {"text": "Reps look orders up.", "ids": ["UJ-01", "FR-002", "FR-003"]}}})
    assert "Summary by Claude of UJ-01, FR-002, FR-003, PRD 1.0.0" in page
    assert 'href="#FR-002"' in page and 'id="FR-002"' in page and "Reps look orders up." in page


def test_label_id_list():
    assert publish.id_label(["FR-001", "FR-002"]) == "FR-001, FR-002"
    assert publish.id_label(["FR-001", "FR-002", "FR-003", "FR-005", "NFR-004"]) == "FR-001–FR-003, FR-005, NFR-004"
    assert publish.id_label(["FR-001", "UJ-02", "FR-002", "FR-003"]) == "FR-001, UJ-02, FR-002, FR-003"


def test_summary_problems(prd):
    ok = {"version": "1.0.0", "areas": {"import": {"text": "x", "ids": ["FR-001"]}}}
    assert problems(prd, ok) == []
    assert problems(prd, {**ok, "version": "0.9.0"}) == ["summaries: version 0.9.0 is not the PRD's 1.0.0"]
    assert problems(prd, {"version": "1.0.0", "areas": {"nope": {"text": "x", "ids": []}}}) == ["summaries: area 'nope' does not exist"]
    assert problems(prd, {"version": "1.0.0", "areas": {"import": {"text": "x", "ids": ["FR-999"]}}}) == ["summaries: import: FR-999 is not defined"]
    assert problems(prd, {"version": "1.0.0", "areas": {"import": {"text": "x", "ids": ["FR-002"]}}}) == ["summaries: import: FR-002 belongs to area 'api'"]
    assert problems(prd, {"version": "1.0.0", "areas": {"import": {"text": "y" * 600, "ids": []}}}) == []
    assert problems(prd, {"version": "1.0.0", "areas": {"import": {"text": "y" * 601, "ids": []}}}) == ["summaries: import: text is 601 characters; at most 600"]


def test_summary_malformed(prd):
    assert problems(prd, []) == ["summaries: must be an object with version and areas"]
    assert problems(prd, {"version": "1.0.0", "areas": {"import": "text"}}) == ["summaries: import: must be an object with text and ids"]


def test_render_refuses_bad_summaries(prd):
    with pytest.raises(publish.Refused):
        render(prd, {"version": "0.1.0", "areas": {}})


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def test_cli(prd, tmp_path):
    inside = run("render", prd, "--out", prd / "page.html")
    assert inside.returncode == 1 and "refused: --out is inside the PRD folder" in inside.stderr
    assert not (prd / "page.html").exists()
    out = tmp_path / "out.html"
    summ = tmp_path / "s.json"
    summ.write_text('{"version": "0.9.0", "areas": {}}')
    bad = run("render", prd, "--out", out, "--summaries", summ)
    assert bad.returncode == 1 and "summaries: version 0.9.0 is not the PRD's 1.0.0" in bad.stderr and not out.exists()
    summ.write_text('{"version": "1.0.0", "areas": {"import": {"text": "Files load.", "ids": ["FR-001"]}}}')
    good = run("render", prd, "--out", out, "--summaries", summ)
    assert good.returncode == 0 and good.stdout.strip() == f"wrote {out}"
    assert "Files load." in out.read_text(encoding="utf-8")
    assert run("render", tmp_path / "nowhere", "--out", out).returncode == 2
    summ.write_text("{not json")
    assert run("render", prd, "--out", out, "--summaries", summ).returncode == 2
