import pytest
from conftest import Case, edit, fired, lint


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


NA_CONFIG = "- Not applicable: `contracts/config.yaml` — no settings\n"

CASES: list[Case] = [
    Case("frontmatter", "missing owner", _delete_line("prd.md", "owner:")),
    Case("frontmatter", "bad version", _edit("prd.md", "version: 1.0.0", "version: 1.0")),
    Case("frontmatter", "bad status", _edit("prd.md", "status: Approved", "status: Done")),
    Case("frontmatter", "missing sql-dialect", _delete_line("prd.md", "sql-dialect:")),
    Case("sections", "missing section 9", _edit("prd.md", "## 9. Versioning", "")),
    Case("sections", "optional file absent", _delete_config),
    Case("sections", "mandatory file marked n/a", _edit("prd.md", "- Not used:", "- Not applicable: `errors.md` — none\n- Not used:")),
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
