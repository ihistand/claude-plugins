import pytest
from conftest import Case, edit, fired, lint


def _edit(rel, old, new):
    return lambda root: edit(root, rel, old, new)


def _append(rel, text):
    def mutate(root):
        path = root / rel
        path.write_text(path.read_text().rstrip("\n") + "\n" + text + "\n")

    return mutate


def _both(*mutations):
    def mutate(root):
        for m in mutations:
            m(root)

    return mutate


ADOPT_OLD = "## 8. Adoption map\n\nNot applicable: new project."
FR2_ROW = "| FR-002 | Get an order | live | features/api.md | 1.0.0 |"
FR2_HEAD = "### FR-002 Get an order\nStatus: live (since 1.0.0)"


def _adoption(*rows):
    body = "\n".join(["| Area | State | Boundary |", "|---|---|---|", *rows])
    return _edit("prd.md", ADOPT_OLD, f"## 8. Adoption map\n\n{body}")


def _as_built(root):
    _edit("features/api.md", FR2_HEAD, FR2_HEAD.replace("live (since 1.0.0)", "as-built"))(root)
    _edit("prd.md", FR2_ROW, FR2_ROW.replace("live", "as-built"))(root)


FR3_ROW = "| FR-003 | Delete an order | live | features/api.md | 1.0.0 |"
FR3_ROW_REMOVED = FR3_ROW.replace("live", "removed")
FR3_STATUS = "### FR-003 Delete an order\nStatus: live (since 1.0.0)"
FR3_STATUS_REMOVED = "### FR-003 Delete an order\nStatus: removed (since 1.0.0)"
FR3_ACCEPTANCE = """Acceptance (EARS):
- AC-003.1 When an admin deletes an existing order through `op:deleteOrder`, the API shall
  remove the order and respond 204.
- AC-003.2 If a rep calls `op:deleteOrder`, the API shall respond 403 with error FORBIDDEN
  and keep the order.
"""
FR2_STATUS = "### FR-002 Get an order\nStatus: live (since 1.0.0)"

CASES: list[Case] = [
    Case("index-consistent", "adoption row without a feature file", _adoption("| ghost | extracted | `src/ghost/**` |")),
    Case("index-consistent", "as-built block without Source", _as_built),
    Case("index-consistent", "duplicate index row", _edit("prd.md", FR2_ROW, FR2_ROW + "\n" + FR2_ROW)),
    Case("id-format", "FR-12 on a Traces line", _edit("features/api.md", "Traces: UJ-01; `orders.id`", "Traces: UJ-01; FR-12; `orders.id`")),
    Case("id-format", "heading FR-0001", _edit("features/import.md", "### FR-001 Import", "### FR-0001 Import")),
    Case("id-format", "bad AC in a YAML value", _edit("test-cases/import.yaml", "ac: AC-001.3", "ac: AC-1.3")),
    Case("id-unique", "duplicate AC line", _edit("features/import.md", "- AC-001.3 If the import file", "- AC-001.2 When a row repeats, the importer shall skip it.\n- AC-001.3 If the import file")),
    Case("id-unique", "FR-004 shares NFR-004's number", _append("features/api.md", "\n### FR-004 Extra\nStatus: approved\nAcceptance (EARS):\n- AC-004.7 When asked, the API shall answer.\nErrors: -\nTests: -")),
    Case("id-unique", "T-002.1 repeated in another file", _append("test-cases/import.yaml", "\nT-002.1:\n  ac: AC-002.1")),
    Case("id-unique", "E-001 heading twice", _append("errors.md", "\n### E-001 Again\nRecurrence of: -")),
    Case("id-unique", "A-01 row twice", _edit("prd.md", "| A-01 | Reps see only their own orders | confirmed |", "| A-01 | Reps see only their own orders | confirmed |\n| A-01 | Another | open |")),
    Case("id-removed-reused", "index removed, block live", _edit("prd.md", FR3_ROW, FR3_ROW_REMOVED)),
    Case("id-removed-reused", "removed in both, T-003.x kept", _both(_edit("prd.md", FR3_ROW, FR3_ROW_REMOVED), _edit("features/api.md", FR3_STATUS, FR3_STATUS_REMOVED))),
    Case("id-removed-reused", "test case cites a removed AC", _edit("features/import.md", "- AC-001.3 If the import file", "- AC-001.3 (removed in 2.0.0) If the import file")),
    Case("index-consistent", "FR-002 index status built", _edit("prd.md", "| FR-002 | Get an order | live |", "| FR-002 | Get an order | built |")),
    Case("index-consistent", "UJ-01 index row deleted", _edit("prd.md", "| UJ-01 | Rep looks up an order | live | features/api.md | 1.0.0 |\n", "")),
    Case("index-consistent", "unknown status shipped", _edit("features/import.md", "Status: live (since 1.0.0)", "Status: shipped")),
    Case("index-consistent", "live without since", _edit("features/api.md", FR2_STATUS, "### FR-002 Get an order\nStatus: live")),
    Case("index-consistent", "title differs", _edit("prd.md", "| FR-002 | Get an order |", "| FR-002 | Fetch an order |")),
    Case("fr-has-ac", "FR-003 acceptance deleted", _edit("features/api.md", FR3_ACCEPTANCE, "")),
    Case("fr-has-ac", "every AC of NFR-004 removed", _edit("nfr.md", "- AC-004.1 The API", "- AC-004.1 (removed in 2.0.0) The API")),
    Case("ac-ears", "AC-001.1 not EARS", _edit("features/import.md", "When an imported row has a new order_key, the importer shall insert the row\n  into `orders`.", "Rows get inserted.")),
    Case("ac-ears", "no shall", _edit("features/import.md", "the importer shall insert the row", "the importer inserts the row")),
    Case("nfr-bound", "quickly", _edit("nfr.md", "answer getOrder within 300 ms at p95 under 50 requests/s.", "answer getOrder quickly.")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


def test_mismatched_removal_reports_removed_reused_only(prd):
    edit(prd, "prd.md", FR3_ROW, FR3_ROW_REMOVED)
    rules = fired(lint(prd))
    assert "id-removed-reused" in rules
    assert "index-consistent" not in rules


def test_removed_requirement_cited_by_test_case_and_traces(prd):
    edit(prd, "prd.md", FR3_ROW, FR3_ROW_REMOVED)
    edit(prd, "features/api.md", FR3_STATUS, FR3_STATUS_REMOVED)
    edit(prd, "features/api.md", "Traces: UJ-01; `orders.id`", "Traces: UJ-01; FR-003; `orders.id`")
    messages = [f.message for f in lint(prd) if f.rule == "id-removed-reused"]
    assert any("test case" in m for m in messages)
    assert any("Traces" in m for m in messages)
    assert any("x-prd-ids" in m for m in messages)


def test_the_shall_form_without_a_leading_word_is_ear(prd):
    assert "ac-ears" not in fired(lint(prd))


def test_clean_fixture_fires_none_of_the_id_rules(prd):
    ids = {"id-format", "id-unique", "id-removed-reused", "index-consistent", "fr-has-ac", "ac-ears", "nfr-bound"}
    assert not ids & fired(lint(prd))


def test_shared_number_is_reported_by_its_own_branch(prd):
    _append("features/api.md", "\n### FR-004 Extra\nStatus: approved\nAcceptance (EARS):\n- AC-004.7 When asked, the API shall answer.\nErrors: -\nTests: -")(prd)
    messages = [f.message for f in lint(prd) if f.rule == "id-unique"]
    assert any("FR-004 and NFR-004 share a number" in m for m in messages)


@pytest.mark.parametrize("bound", ["reach 99.9% availability", "reach 99.9 % of requests", "sustain 600 req/min"])
def test_nfr_bound_accepts_percent_and_per_minute(prd, bound):
    edit(prd, "nfr.md", "answer getOrder within 300 ms at p95 under 50 requests/s.", f"{bound}.")
    assert "nfr-bound" not in fired(lint(prd))


def _index_messages(prd):
    return [f.message for f in lint(prd) if f.rule == "index-consistent"]


def test_new_index_findings_say_why(prd):
    _adoption("| ghost | extracted | `src/ghost/**` |")(prd)
    assert any("features/ghost.md" in m for m in _index_messages(prd))


def test_as_built_without_source_says_so(prd):
    _as_built(prd)
    assert any("Source" in m for m in _index_messages(prd))


def test_duplicate_index_row_says_so(prd):
    _edit("prd.md", FR2_ROW, FR2_ROW + "\n" + FR2_ROW)(prd)
    assert any("FR-002" in m and "twice" in m for m in _index_messages(prd))


def test_as_built_with_source_is_clean(prd):
    _as_built(prd)
    _edit("features/api.md", FR2_HEAD.replace("live (since 1.0.0)", "as-built"),
          FR2_HEAD.replace("live (since 1.0.0)", "as-built") + "\nSource: src/api.py:10 @abc1234")(prd)
    assert "index-consistent" not in fired(lint(prd))


def test_adopted_row_with_its_feature_file_is_clean(prd):
    _adoption("| import | adopted | `features/import.md` |", "| later | not started | |")(prd)
    assert "index-consistent" not in fired(lint(prd))
