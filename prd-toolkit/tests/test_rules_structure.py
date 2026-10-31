import pytest
from conftest import Case, edit, fired, lint

from prdlint.rules.structure import HARNESS_SLOTS


def _delete_line(rel, startswith):
    def mutate(root):
        path = root / rel
        lines = path.read_text().split("\n")
        keep = [x for x in lines if not x.startswith(startswith)]
        assert len(keep) == len(lines) - 1, f"{rel}: expected one line starting {startswith!r}"
        path.write_text("\n".join(keep))

    return mutate


def _append(rel, text):
    def mutate(root):
        path = root / rel
        path.write_text(path.read_text().rstrip("\n") + "\n" + text + "\n")

    return mutate


def _edit(rel, old, new):
    return lambda root: edit(root, rel, old, new)


def _delete_config(root):
    (root / "contracts/config.yaml").unlink()


ADOPT_OLD = "## 8. Adoption map\n\nNot applicable: new project."


def _adoption(table_rows, header="| Area | State | Boundary |"):
    body = "\n".join([header, "|---|---|---|", *table_rows])

    def mutate(root):
        _edit("prd.md", ADOPT_OLD, "## 8. Adoption map\n\nSee adoption.md.")(root)
        (root / "adoption.md").write_text(f"# Adoption map\n\n{body}\n")

    return mutate


def _swap_lines(rel, first, second):
    def mutate(root):
        path = root / rel
        lines = path.read_text().split("\n")
        i = next(k for k, x in enumerate(lines) if x.startswith(first))
        j = next(k for k, x in enumerate(lines) if x.startswith(second))
        lines[i], lines[j] = lines[j], lines[i]
        path.write_text("\n".join(lines))

    return mutate


NA_CONFIG = "- Not applicable: `contracts/config.yaml` — no settings\n"

CASES: list[Case] = [
    Case("frontmatter", "missing owner", _delete_line("prd.md", "owner:")),
    Case("frontmatter", "bad version", _edit("prd.md", "version: 1.0.0", "version: 1.0")),
    Case("frontmatter", "bad status", _edit("prd.md", "status: Approved", "status: Done")),
    Case("frontmatter", "missing sql-dialect", _delete_line("prd.md", "sql-dialect:")),
    Case("sections", "missing section 9", _edit("prd.md", "## 9. Versioning", "")),
    Case("sections", "optional file absent", _delete_config),
    Case("sections", "mandatory file marked n/a", _edit("prd.md", "- Not used:", "- Not applicable: `errors.md` — none\n- Not used:")),
    Case("sections", "adoption table without a Boundary column", _adoption(["| import | adopted |"], "| Area | State |")),
    Case("sections", "adoption state outside the list", _adoption(["| import | done | `features/import.md` |"])),
    Case("sections", "harness slot missing", _delete_line("testing.md", "- **Waits.**")),
    Case("sections", "harness slots out of order", _swap_lines("testing.md", "- **Lifecycle.**", "- **Layout.**")),
    Case("sections", "layout without test roots", _edit("testing.md", " Test roots: `tests/`.", "")),
    Case("sections", "test roots with no backticked directory", _edit("testing.md", "Test roots: `tests/`.", "Test roots: tests/.")),
    Case("sections", "testing.md without a Harness section", _edit("testing.md", "## Harness", "## Conventions")),
    Case("placeholder", "TBD in operations", _append("operations.md", "Owner: TBD")),
    Case("placeholder", "angle placeholder in prd", _edit("prd.md", "Personas:", "Personas for <owner-name>:")),
    Case("placeholder", "TODO in yaml scalar", _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: code:TODO")),
    Case("vague-word", "fast in AC", _edit("features/import.md", "log `IMPORT_DUPLICATE` once for it.", "log `IMPORT_DUPLICATE` once for it and shall be fast.")),
    Case("markers-open", "marker in approved", _append("nfr.md", "[NEEDS CLARIFICATION: retention?]")),
    Case("markers-open", "marker in yaml value", _edit("contracts/openapi.yaml", "title: Orders API", 'title: "[NEEDS CLARIFICATION: API title]"')),
    Case("markers-open", "marker in yaml comment", _append("contracts/data-classification.yaml", "# [NEEDS CLARIFICATION: retention for logs]")),
    Case("markers-open", "marker in sql comment", _append("contracts/schema.sql", "-- [NEEDS CLARIFICATION]")),
    Case("placeholder", "slot in frontmatter", _edit("prd.md", "owner: Sample Owner", "owner: {{owner}}")),
    Case("placeholder", "slot in heading", _edit("prd.md", "# Orders service", "# {{project}}")),
    Case("placeholder", "slot in yaml scalar", _edit("contracts/openapi.yaml", "title: Orders API", 'title: "{{project}} API"')),
    Case("assumption-indexed", "row open while approved", _edit("prd.md", "| confirmed |", "| open |")),
    Case("assumption-indexed", "marker without row", _append("nfr.md", "[ASSUMPTION A-09: x]")),
    Case("assumption-indexed", "yaml marker without row", _append("contracts/config.yaml", "# [ASSUMPTION A-09: batch size fits memory]")),
    Case("assumption-indexed", "marker without id", _append("nfr.md", "[ASSUMPTION: x]")),
    Case("assumption-indexed", "bad row status", _edit("prd.md", "| confirmed |", "| maybe |")),
    Case("assumption-indexed", "awaiting names nobody", _edit("prd.md", "| confirmed |", "| awaiting |")),
    Case("open-questions-empty", "question while approved", _edit("prd.md", "## 13. Open questions\n\nNone.", "## 13. Open questions\n\n- Q-01 Who owns refunds?")),
    Case("glossary-synonym", "purchase in prose", _edit("features/import.md", "Flow: 1. Importer reads a file", "Flow: 0. a purchase arrives → 1. Importer reads a file")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


def test_placeholder_ignores_code(prd):
    _append("operations.md", "Run `<project>` now.\n\n```\nTODO <x>\n```")(prd)
    assert "placeholder" not in fired(lint(prd))


def test_placeholder_ignores_autolinks(prd):
    _append("operations.md", "See <https://example.com/x>.")(prd)
    assert "placeholder" not in fired(lint(prd))


def test_markers_allowed_in_draft(prd):
    edit(prd, "prd.md", "status: Approved", "status: Draft")
    _append("nfr.md", "[NEEDS CLARIFICATION: retention?]")(prd)
    edit(prd, "prd.md", "## 13. Open questions\n\nNone.", "## 13. Open questions\n\n- Q-01 Who owns refunds?")
    assert not {"markers-open", "open-questions-empty"} & fired(lint(prd))


def test_not_applicable_satisfies_sections(prd):
    _delete_config(prd)
    edit(prd, "prd.md", "- Not used:", NA_CONFIG + "- Not used:")
    assert "sections" not in fired(lint(prd))


def test_vague_word_with_number_is_clean(prd):
    edit(prd, "nfr.md", "- AC-004.1 The API", "- AC-004.1 fast: The API")
    assert "vague-word" not in fired(lint(prd))


def test_frontmatter_accepts_relative_dot_path(prd, monkeypatch):
    from prdlint import model, registry

    monkeypatch.chdir(prd)
    findings = registry.run(model.load(__import__("pathlib").Path(".")), only={"frontmatter"})
    assert findings == []


def test_vague_word_ignores_inline_code_and_fences(prd):
    edit(prd, "nfr.md", "- AC-004.1 The API", "- AC-004.9 Cookies use `--secure` flag\n- AC-004.1 The API")
    _append("nfr.md", "")(prd)
    edit(prd, "nfr.md", "Traces: UJ-01; FR-002", "```\nbe fast and secure\n```\nTraces: UJ-01; FR-002")
    assert "vague-word" not in fired(lint(prd))


def test_markers_in_contracts_report_their_file(prd):
    edit(prd, "contracts/openapi.yaml", "title: Orders API", 'title: "[NEEDS CLARIFICATION: API title]"')
    edit(prd, "contracts/schema.sql", "CREATE TABLE customers (", "-- [NEEDS CLARIFICATION: owner of customers]\nCREATE TABLE customers (")
    hits = {(f.file, f.line) for f in lint(prd) if f.rule == "markers-open"}
    assert hits == {("contracts/openapi.yaml", 3), ("contracts/schema.sql", 1)}


def test_an_awaiting_assumption_is_clean_while_approved(prd):
    # intent only a named person can confirm: allowed through approval (spec 0.2 §1)
    edit(prd, "prd.md", "| confirmed |", "| awaiting Sam Rivera |")
    assert "Approved" in (prd / "prd.md").read_text()
    assert "assumption-indexed" not in fired(lint(prd))


def test_yaml_assumption_with_a_row_is_clean(prd):
    (prd / "contracts/config.yaml").write_text((prd / "contracts/config.yaml").read_text() + "# [ASSUMPTION A-01: reps see only their own orders]\n")
    assert "assumption-indexed" not in fired(lint(prd))


def test_binary_and_gitkeep_files_are_not_scanned(prd):
    (prd / "contracts/fixtures/.gitkeep").write_text("[NEEDS CLARIFICATION: ignored]")
    (prd / "contracts/fixtures/blob.bin").write_bytes(b"\x00\xff[NEEDS CLARIFICATION\x00")
    assert "markers-open" not in fired(lint(prd))


# Parked minors from the final review.

def test_mustache_in_a_yaml_value_is_not_a_placeholder(prd):
    edit(prd, "contracts/errors.yaml", "message: Row skipped because the order already exists.",
         "message: Row {{order_key}} skipped because the order already exists.")
    assert "placeholder" not in fired(lint(prd))


def test_an_unfilled_template_slot_is_still_a_placeholder(prd):
    edit(prd, "contracts/errors.yaml", "message: Row skipped because the order already exists.",
         "message: Row skipped for {{owner}}.")
    assert "placeholder" in fired(lint(prd))


def test_markers_in_fixture_data_and_backups_are_ignored(prd):
    with open(prd / "contracts/fixtures/customers/two_customers.csv", "a", encoding="utf-8") as f:
        f.write("# [NEEDS CLARIFICATION: not a real question]\n")
    (prd / "prd.md~").write_text("[NEEDS CLARIFICATION: editor backup]\n[ASSUMPTION A-77: stale]\n", encoding="utf-8")
    (prd / ".prd.md.swp").write_text("[NEEDS CLARIFICATION: swap file]\n", encoding="utf-8")
    rules = fired(lint(prd))
    assert "markers-open" not in rules and "assumption-indexed" not in rules


def _sections_messages(prd):
    return [f.message for f in lint(prd) if f.rule == "sections"]


def test_harness_slots_are_the_template_list():
    import test_template

    assert test_template.HARNESS_SLOTS is HARNESS_SLOTS and len(HARNESS_SLOTS) == 15


@pytest.mark.parametrize("case_name, fragment", [
    ("harness slot missing", "Waits"),
    ("harness slots out of order", "order"),
    ("layout without test roots", "Test roots"),
    ("test roots with no backticked directory", "Test roots: lists no backticked directory"),
    ("testing.md without a Harness section", "## Harness"),
    ("adoption table without a Boundary column", "Area | State | Boundary"),
    ("adoption state outside the list", "done"),
])
def test_new_sections_findings_say_why(prd, case_name, fragment):
    case = next(c for c in CASES if c.rule == "sections" and c.name == case_name)
    case.mutate(prd)
    assert any(fragment in m for m in _sections_messages(prd))


def test_valid_adoption_table_is_clean(prd):
    _adoption(["| import | adopted | `features/import.md`, `src/importer/**` |", "| legacy | not started | |"])(prd)
    assert "sections" not in fired(lint(prd))


def test_test_roots_still_a_marker_is_left_to_markers_open(prd):
    """An unfilled Layout says so with its marker; `sections` does not pile on (the template stays one finding)."""
    edit(prd, "testing.md", "Test roots: `tests/`.", "Test roots: [NEEDS CLARIFICATION: the test directories, each in backticks]")
    assert not any("Test roots" in m for m in _sections_messages(prd))


def _placeholder_messages(prd):
    return [f.message for f in lint(prd) if f.rule == "placeholder"]


def test_prose_placeholder_message_says_how_to_mark_literal_text(prd):
    _append("operations.md", "Pick the <the data_state> now.")(prd)
    msgs = _placeholder_messages(prd)
    assert msgs and all(m.endswith("; if this is literal text, put it in backticks") for m in msgs)


def test_angle_text_in_a_code_span_lints_clean(prd):
    _append("operations.md", "Pick the `<the data_state>` now.")(prd)
    assert "placeholder" not in fired(lint(prd))


def test_bare_angle_text_in_prose_still_fires(prd):
    _append("operations.md", "Pick the <the data_state> now.")(prd)
    assert "placeholder" in fired(lint(prd))
