from pathlib import Path

from conftest import lint
from prdlint import model

ROOT = Path(__file__).parent.parent

OPEN = "\n### E-002 Duplicate check ignores case\nDetected: 2026-10-30, review\nClassification: code bug\nTouches: FR-001, NFR-004\nDiagnosis: keys compare case-sensitively\nResolution: open\nRecurrence of: -\n"


def test_touches_is_parsed(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    e = model.load(prd).errors_ledger["E-002"]
    assert [t for t, _ in e.touches] == ["FR-001", "NFR-004"] and e.open
    assert model.load(prd).errors_ledger["E-001"].touches == []


def test_entry_end_line(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    led = model.load(prd).errors_ledger
    assert led["E-001"].end < led["E-002"].line and led["E-002"].end == len((prd / "errors.md").read_text().rstrip("\n").split("\n"))


def test_dangling_touches_is_index_consistent(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN.replace("NFR-004", "FR-099"))
    found = [f for f in lint(prd) if f.rule == "index-consistent" and f.file == "errors.md"]
    assert [f.message for f in found] == ["E-002 Touches FR-099, which no block defines"]


def test_valid_touches_lints_clean(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    assert lint(prd) == []


def test_format_and_extract_prompt_document_touches():
    assert "Touches: <requirement IDs or ->" in (ROOT / "references/prd-format.md").read_text()
    assert "Touches:" in (ROOT / "skills/adopting-prds/SKILL.md").read_text().split("APPARENT BUGS", 1)[1][:400]
