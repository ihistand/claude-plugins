import pytest

from conftest import edit

from prdlint.markdown import frontmatter, sections, strip_code, tables
from prdlint.model import NotAPrd, load
from prdlint.yamlload import LineDict, load_yaml


def test_loads_blocks_and_ids(prd):
    p = load(prd)
    assert [b.id for b in p.blocks] == ["UJ-01", "FR-002", "FR-003", "FR-001", "NFR-004"]
    fr1 = next(b for b in p.blocks if b.id == "FR-001")
    assert [a.id for a in fr1.acs] == ["AC-001.1", "AC-001.2", "AC-001.3"]
    assert ("T-001.4", "acceptance") in [(t, l) for t, l, _ in fr1.tests]
    assert {t.id for t in p.test_cases} >= {"T-001.1", "T-003.2", "T-004.1"}


def test_strip_code_keeps_line_numbers():
    assert strip_code("a\n```\nTODO\n```\nb `<x>`").splitlines()[4] == "b " + " " * 5


def test_duplicate_yaml_key_reports_both_lines(tmp_path):
    f = tmp_path / "test-cases/a.yaml"
    f.parent.mkdir()
    f.write_text("T-001.1: {}\nT-001.1: {}\n")
    _, findings = load_yaml(f, rel="test-cases/a.yaml")
    assert [(x.rule, x.line) for x in findings] == [("id-unique", 2)] and "line 1" in findings[0].message


def test_not_a_prd(tmp_path):
    with pytest.raises(NotAPrd):
        load(tmp_path)


def test_fixture_loads_without_findings(prd):
    p = load(prd)
    assert p.load_findings == []
    assert p.frontmatter["prd"] == "orders" and p.frontmatter["sql-dialect"] == "postgres"
    assert [s.number for s in p.sections] == list(range(1, 15))
    assert sorted(r.id for r in p.index) == sorted(b.id for b in p.blocks)
    assert all(r.status == "live" and r.since == "1.0.0" for r in p.index)
    assert all(b.status == "live" and b.since == "1.0.0" for b in p.blocks)
    assert "contracts/errors.yaml" in p.yaml and "contracts/dependencies/geocoder.yaml" in p.yaml
    assert "features/import.md" in p.docs and "contracts/events.md" in p.docs
    assert set(p.testing.levels) == {"unit", "integration", "component", "system", "e2e", "acceptance"}
    assert set(p.testing.environments) == {"local", "ci", "staging"}
    assert len(p.testing.fixtures) == 3 and p.testing.signoffs
    assert [r.cells[0] for r in p.assumptions] == ["A-01"]


def test_block_fields(prd):
    p = load(prd)
    fr1 = next(b for b in p.blocks if b.id == "FR-001")
    assert fr1.kind == "FR" and fr1.title == "Import an orders file" and fr1.file == "features/import.md"
    assert fr1.tests_file == "test-cases/import.yaml"
    assert [c for c, _ in fr1.errors] == ["IMPORT_DUPLICATE", "IMPORT_EMPTY"]
    nfr = next(b for b in p.blocks if b.id == "NFR-004")
    assert nfr.kind == "NFR" and nfr.file == "nfr.md" and nfr.tests_file == "test-cases/nfr.yaml"
    assert p.blocks[0].kind == "UJ" and p.blocks[0].acs == []


def test_ac_continuation_lines_are_joined(prd):
    p = load(prd)
    ac = next(a for b in p.blocks for a in b.acs if a.id == "AC-001.2")
    assert "IMPORT_DUPLICATE" in ac.text and "\n" not in ac.text


def test_test_cases_are_line_dicts(prd):
    p = load(prd)
    tc = next(t for t in p.test_cases if t.id == "T-003.2")
    assert isinstance(tc.data, LineDict)
    assert tc.data["identity"] == "test-rep" and tc.line == 51
    assert tc.file == "test-cases/api.yaml"


def test_not_applicable_files_are_collected(prd):
    text = (prd / "prd.md").read_text()
    marker = "## 2. Summary & goals"
    (prd / "prd.md").write_text(
        text.replace(marker, "- Not applicable: `contracts/asyncapi.yaml` — no queues\n\n" + marker, 1)
    )
    p = load(prd)
    reason, line = p.not_applicable["contracts/asyncapi.yaml"]
    assert reason == "no queues" and line > 0


def test_yaml_parse_error_rules(prd):
    (prd / "test-cases/api.yaml").write_text("T-002.1: [unclosed\n")
    (prd / "contracts/errors.yaml").write_text("- just\n- a list\n")
    p = load(prd)
    rules = {(f.file, f.rule) for f in p.load_findings}
    assert ("test-cases/api.yaml", "sufficiency") in rules
    assert ("contracts/errors.yaml", "contracts-valid") in rules


def test_frontmatter_and_sections_helpers():
    fm, line = frontmatter("---\nprd: x\nversion: 1.0.0\n---\n# t\n")
    assert fm == {"prd": "x", "version": "1.0.0"} and line == 1
    text = "## 1. One\na\n```\n## 2. fake\n```\n## 2. Two\n| A | B |\n|---|---|\n| `x|y` | 2 |\n"
    secs = sections(text)
    assert [(s.number, s.title) for s in secs] == [(1, "One"), (2, "Two")]
    t = tables(secs[1].body)[0]
    assert t.header == ["A", "B"] and t.rows[0].cells == ["`x|y`", "2"] and t.rows[0].line == 9


def test_wrapped_errors_line_keeps_all_codes(prd):
    edit(prd, "features/import.md",
         "Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)",
         "Errors: IMPORT_DUPLICATE,\n  IMPORT_EMPTY (contracts/errors.yaml)")
    fr1 = next(b for b in load(prd).blocks if b.id == "FR-001")
    assert [c for c, _ in fr1.errors] == ["IMPORT_DUPLICATE", "IMPORT_EMPTY"]
    assert fr1.errors[1][1] == fr1.errors[0][1] + 1


def test_flow_style_test_case_line_is_the_key_line(prd):
    (prd / "test-cases/api.yaml").write_text("# c\nT-002.1: {}\n")
    tc = next(t for t in load(prd).test_cases if t.id == "T-002.1")
    assert tc.line == 2
