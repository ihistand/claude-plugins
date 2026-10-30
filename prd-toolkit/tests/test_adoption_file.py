"""adoption.md holds the adoption map; section 8 only points at it."""
from pathlib import Path

import prd_block
from conftest import edit, lint
from prdlint import model

ROOT = Path(__file__).resolve().parent.parent


def adopt(prd, rows):
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n" + rows)
    edit(prd, "prd.md", "Not applicable: new project.", "See adoption.md.")


def test_new_project_fixture_stays_clean(prd):
    assert lint(prd) == []


def test_adoption_file_is_read_into_the_model(prd):
    adopt(prd, "| import | adopted | `src/import/**` |\n| api | not started | `src/api/**` |\n")
    rows = model.load(prd).adoption
    assert [(r.area, r.state, r.boundary) for r in rows] == [("import", "adopted", ["src/import/**"]), ("api", "not started", ["src/api/**"])]
    assert rows[0].line == 5


def test_no_adoption_file_means_none(prd):
    assert model.load(prd).adoption is None


def test_table_left_in_section_8_names_the_migration(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |")
    msgs = [f.message for f in lint(prd) if f.rule == "sections"]
    assert 'section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there and leave "See adoption.md."' in msgs


def test_pointer_without_file(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "See adoption.md.")
    assert any(f.file == "prd.md" and "adoption.md does not exist" in f.message for f in lint(prd))


def test_not_applicable_with_file(prd):
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |\n")
    assert any('says "Not applicable: new project" but adoption.md exists' in f.message for f in lint(prd))


def test_other_section_8_body(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "Areas are listed elsewhere.")
    assert any('section 8 body must be "See adoption.md." or "Not applicable: new project."' in f.message for f in lint(prd))


def test_bad_header_and_state_report_adoption_md(prd):
    adopt(prd, "| import | half-done | `src/**` |\n")
    found = [f for f in lint(prd) if f.rule == "sections" and f.file == "adoption.md"]
    assert [f.line for f in found] == [5]
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | Status | Files |\n|---|---|---|\n| import | adopted | `src/**` |\n")
    assert any(f.file == "adoption.md" and "header must be '| Area | State | Boundary |'" in f.message for f in lint(prd))


def test_adoption_file_without_table(prd):
    adopt(prd, "")
    (prd / "adoption.md").write_text("# Adoption map\n\nnothing\n")
    assert any(f.file == "adoption.md" and "adoption.md holds no '| Area | State | Boundary |' table" in f.message for f in lint(prd))


def test_index_consistent_reports_adoption_md(prd):
    adopt(prd, "| billing | adopted | `src/billing/**` |\n")
    assert any(f.rule == "index-consistent" and f.file == "adoption.md" and f.line == 5 for f in lint(prd))


def test_block_lists_adopted_areas_from_adoption_md(prd):
    adopt(prd, "| import | adopted | `src/**` |\n| api | confirmed | `src/api/**` |\n")
    assert "Adopted areas: import" in prd_block.render_block(model.load(prd), "docs/prd/orders")


def test_format_reference_has_the_tasks_table():
    text = (ROOT / "references/prd-format.md").read_text()
    assert "## Tasks" in text and "| New sub-project |" in text and "| Bug fix |" in text
    assert "A toolkit format migration, such as moving the adoption map, is a patch." in text


def test_adopting_skill_names_adoption_md_not_section_8_table():
    text = (ROOT / "skills/adopting-prds/SKILL.md").read_text()
    assert "`adoption.md`" in text and "See adoption.md." in text
    assert "replace §8's marker with the" not in text
