"""Model additions of 0.2: adoption map, errors ledger, Source lines, Harness."""
import re

from conftest import edit

from prdlint.model import ADOPTION_STATES, load

TESTING = "testing.md"


def _set_adoption(prd, *rows):
    text = (prd / "prd.md").read_text()
    new = "| Area | State | Boundary |\n|---|---|---|\n" + "\n".join(rows) + "\n"
    assert text.count("Not applicable: new project.\n") == 1
    (prd / "prd.md").write_text(text.replace("Not applicable: new project.\n", new))


def _append_errors(prd, text):
    path = prd / "errors.md"
    path.write_text(path.read_text().rstrip("\n") + "\n\n" + text)


def _set_roots(prd, tail):
    path = prd / TESTING
    text = path.read_text()
    new, n = re.subn(r"(- \*\*Layout\.\*\*[^\n]*?)\s*Test roots:[^\n]*|(- \*\*Layout\.\*\*[^\n]*)", lambda m: (m.group(1) or m.group(2)) + (" " + tail if tail else ""), text, count=1)
    assert n == 1
    path.write_text(new)


def test_adoption_states_constant():
    assert ADOPTION_STATES == ("not started", "extracted", "confirmed", "adopted")


def test_adoption_none_when_not_applicable(prd):
    assert load(prd).adoption is None


def test_adoption_rows_parse_boundary_globs(prd):
    _set_adoption(prd, "| import | adopted | `features/import.md`, `src/importer/**` |")
    row = load(prd).adoption[0]
    assert (row.area, row.state, row.boundary) == ("import", "adopted", ["features/import.md", "src/importer/**"])
    assert row.line > 0


def test_adoption_row_without_boundary_cell(prd):
    text = (prd / "prd.md").read_text()
    (prd / "prd.md").write_text(text.replace("Not applicable: new project.\n", "| Area | State |\n|---|---|\n| import | extracted |\n"))
    row = load(prd).adoption[0]
    assert (row.area, row.state, row.boundary) == ("import", "extracted", [])


def test_errors_ledger_open_and_resolved(prd):
    _append_errors(prd, "### E-002 Open one\nDetected: 2026-10-29, test\nResolution: -\n\n### E-003 Fixed\nResolution: AC-001.4 in 1.1.0\n")
    led = load(prd).errors_ledger
    assert led["E-002"].open and not led["E-003"].open
    assert not led["E-001"].open
    assert led["E-003"].line > led["E-002"].line


def test_errors_ledger_open_variants(prd):
    _append_errors(
        prd,
        "### E-002 No resolution line\nDetected: x\n\n### E-003 Empty\nResolution:\n\n"
        "### E-004 Open word\nResolution: Open - waiting on the owner\n",
    )
    led = load(prd).errors_ledger
    assert all(led[k].open for k in ("E-002", "E-003", "E-004"))


def test_errors_ledger_skips_fenced_code(prd):
    _append_errors(prd, "```\n### E-009 Example\n```\n")
    assert "E-009" not in load(prd).errors_ledger


def test_block_source_line(prd):
    edit(prd, "features/import.md", "Status: live (since 1.0.0)", "Status: live (since 1.0.0)\nSource: src/importer.py:12 @abc1234")
    blocks = load(prd).blocks
    assert next(b for b in blocks if b.id == "FR-001").source == "src/importer.py:12 @abc1234"
    assert all(b.source is None for b in blocks if b.id != "FR-001")


def test_harness_slots_and_test_roots(prd):
    h = load(prd).testing.harness
    assert [s for s, _ in h.slots][:3] == ["Lifecycle", "Environment switch", "Database access"]
    assert len(h.slots) == 15
    assert h.test_roots == ["tests/"]
    assert h.test_roots_line > 0


def test_harness_test_roots_several_and_absent(prd):
    _set_roots(prd, "Test roots: `tests/`, `e2e/`.")
    assert load(prd).testing.harness.test_roots == ["tests/", "e2e/"]
    _set_roots(prd, "")
    assert load(prd).testing.harness.test_roots is None


def test_harness_test_roots_ignores_marker_contents(prd):
    _set_roots(prd, "Test roots: [NEEDS CLARIFICATION: the test directories, e.g. `tests/`]")
    assert load(prd).testing.harness.test_roots == []
    _set_roots(prd, "Test roots: [NEEDS CLARIFICATION: dirs] `tests/`")
    assert load(prd).testing.harness.test_roots == ["tests/"]


def test_harness_test_roots_stop_at_first_non_item_text(prd):
    _set_roots(prd, "Test roots: `tests/` (not `src/`).")
    assert load(prd).testing.harness.test_roots == ["tests/"]
    _set_roots(prd, "Test roots: `tests/`, `z_tests/`.")
    assert load(prd).testing.harness.test_roots == ["tests/", "z_tests/"]


def test_template_harness_has_empty_test_roots(tmp_path):
    from test_template import TEMPLATE

    (tmp_path / "prd.md").write_text("# x\n")
    (tmp_path / "testing.md").write_text((TEMPLATE / "testing.md").read_text(encoding="utf-8"))
    h = load(tmp_path).testing.harness
    assert h.test_roots == []
    assert len(h.slots) == 15


def test_no_testing_md_gives_empty_harness(prd):
    (prd / "testing.md").unlink()
    h = load(prd).testing.harness
    assert h.slots == [] and h.test_roots is None
