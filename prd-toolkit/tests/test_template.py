"""The PRD folder template lints clean as a Draft and still carries every unknown."""
import shutil
from pathlib import Path

from conftest import edit, fired, lint

TEMPLATE = Path(__file__).parent.parent / "templates/prd"


def fill(dst, **kw):
    """Copy TEMPLATE to dst and replace each {{slot}} in every file; sql_dialect defaults to postgres."""
    kw.setdefault("sql_dialect", "postgres")
    shutil.copytree(TEMPLATE, dst)
    for path in Path(dst).rglob("*"):
        if path.is_file() and path.name != ".gitkeep":
            text = path.read_text()
            for key, value in kw.items():
                text = text.replace("{{" + key + "}}", value)
            path.write_text(text)
    return Path(dst)


def test_template_lints_clean_as_draft(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    assert [str(f) for f in lint(d)] == []


def test_template_carries_markers(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    edit(d, "prd.md", "status: Draft", "status: Approved")
    assert {"markers-open", "open-questions-empty"} <= fired(lint(d))


def test_unfilled_template_fails_frontmatter(tmp_path):
    shutil.copytree(TEMPLATE, tmp_path / "x")
    assert "frontmatter" in fired(lint(tmp_path / "x"))


def test_approved_template_flags_markers_outside_markdown(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    edit(d, "prd.md", "status: Draft", "status: Approved")
    files = {f.file for f in lint(d) if f.rule == "markers-open"}
    assert {"contracts/data-classification.yaml", "contracts/openapi.yaml", "contracts/schema.sql"} <= files


def test_fill_leaves_no_slot(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    left = [p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and "{{" in p.read_text(encoding="utf-8")]
    assert left == []


# The conventions every dry run asked for in the 0.1 acceptance run (link-shortener, runs 1-11).
HARNESS_SLOTS = ["Lifecycle", "Environment switch", "Database access", "Tools on the runner",
                 "Clean state", "Persistent environments", "Layout", "HTTP requests", "Fixtures",
                 "Browser identity", "Assertions", "Waits", "Effects", "Leaks", "Acceptance"]


def _harness(text: str) -> str:
    return text.split("## Harness\n", 1)[1].split("\n## ", 1)[0]


def test_template_testing_md_has_every_harness_slot_marked():
    section = _harness((TEMPLATE / "testing.md").read_text(encoding="utf-8"))
    for slot in HARNESS_SLOTS:
        line = next((ln for ln in section.splitlines() if ln.startswith(f"- **{slot}.**")), None)
        assert line is not None, f"missing slot {slot}"
        assert "[NEEDS CLARIFICATION:" in line, f"slot {slot} has no marker"


def test_approved_template_flags_the_harness_slots(tmp_path):
    d = fill(tmp_path / "docs/prd/sample", project="sample", owner="Sample Owner", date="2026-10-29")
    edit(d, "prd.md", "status: Draft", "status: Approved")
    text = (d / "testing.md").read_text(encoding="utf-8").splitlines()
    start = text.index("## Harness") + 1
    end = next(i for i in range(start, len(text)) if text[i].startswith("## "))
    flagged = {f.line for f in lint(d) if f.rule == "markers-open" and f.file == "testing.md"}
    assert len([n for n in flagged if start < n <= end]) >= len(HARNESS_SLOTS)


def test_valid_fixture_fills_every_harness_slot():
    fixture = Path(__file__).parent / "fixtures/valid/orders/testing.md"
    section = _harness(fixture.read_text(encoding="utf-8"))
    for slot in HARNESS_SLOTS:
        assert f"- **{slot}.**" in section, f"fixture misses slot {slot}"
