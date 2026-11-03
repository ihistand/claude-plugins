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


def assert_loads_nothing(page):
    import re
    for tag in ("<img", "<iframe", "<object", "<embed", "<script", "<link", "@import"):
        assert tag not in page, tag
    assert "url(" not in page.split("</style>")[0]
    assert " src=" not in page
    for href in re.findall(r'href="([^"]*)"', page):
        assert href.startswith(("#", "http://", "https://", "mailto:")), href


def test_loads_nothing(prd):
    page = render(prd, {"version": "1.0.0", "areas": {"import": {"text": "Files come in.", "ids": ["FR-001"]}}})
    assert_loads_nothing(page)


def test_images_are_text(prd):
    edit(prd, "features/import.md", "- AC-001.1 When", "- AC-001.1 ![x](https://evil.example/a.png) ![d](data:image/png;base64,AAAA) When")
    edit(prd, "prd.md", "| customer |", "| ![x](https://evil.example/a.png) |")
    page = render(prd)
    assert_loads_nothing(page)
    assert '!<a href="https://evil.example/a.png">x</a>' in page  # a plain link, not an image


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


def test_summary_ids_not_strings(prd):
    for ids in ([["FR-001"]], [1], "FR-001"):
        assert problems(prd, {"version": "1.0.0", "areas": {"import": {"text": "x", "ids": ids}}}) == [
            "summaries: import: ids must be a list of requirement IDs"]


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


def test_spanish_chrome_and_english_fallback(tmp_path):
    from doc_fixture import document_prd
    root = document_prd(tmp_path, language="es")
    page = publish.render_page(model.load(root), tmp_path, None, TODAY)
    assert "<label for=\"tab-business\">Negocio</label>" in page and "<label for=\"tab-technical\">Técnico</label>" in page
    assert '<html lang="es">' in page and "Versión del PRD" in page and "Matriz de requisitos y pruebas" in page
    assert "<th>Business</th>" not in page and ">Business<" not in page
    # PRD text is never translated
    assert "Install section" in page
    publish._LABELS.pop("business")  # a key missing from the language falls back to en
    assert publish.L("business") == "Business"


def test_every_label_key_is_in_both_tables():
    from prdlint import languages
    en, es = languages.load("en").labels, languages.load("es").labels
    assert set(en) == set(es) and {"business", "technical", "requirement", "status", "test", "level", "gate", "in_code",
                                   "diagnosis", "resolution", "recurrence_of"} <= set(en)
    import re
    src = (Path(publish.__file__).read_text() + (publish.TEMPLATE.read_text()))
    used = set(re.findall(r"""L\(["'](\w+)["']""", src))
    assert used <= set(en), used - set(en)


def test_no_commit_cell_follows_the_page_language(tmp_path):
    from doc_fixture import document_prd
    root = document_prd(tmp_path, language="es")  # tmp_path is not a git repository
    page = publish.render_page(model.load(root), tmp_path, None, TODAY)
    assert "<dd>sin commit</dd>" in page and "no commit" not in page
