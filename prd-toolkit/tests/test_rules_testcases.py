import re

import pytest
from conftest import Case, edit, fired, lint


def _edit(rel, old, new):
    return lambda root: edit(root, rel, old, new)


def _both(*mutations):
    def mutate(root):
        for m in mutations:
            m(root)

    return mutate


def _drop_case(rel, tid):
    """Remove the `tid:` entry (through its trailing blank line) from a test-case file."""

    def mutate(root):
        path = root / rel
        text, n = re.subn(rf"(?m)^{re.escape(tid)}:\n(?:[ ].*\n|\n)*?(?=^\S|\Z)", "", path.read_text(), count=1)
        assert n == 1, tid
        path.write_text(text)

    return mutate


def _append(rel, text):
    def mutate(root):
        path = root / rel
        path.write_text(path.read_text().rstrip("\n") + "\n" + text + "\n")

    return mutate


def _write(rel, text):
    def mutate(root):
        (root / rel).write_text(text)

    return mutate


TESTS_002 = "Tests: T-002.1 [integration], T-002.2 [integration]  (test-cases/api.yaml)"
TESTS_003 = "Tests: T-003.1 [integration], T-003.2 [integration]  (test-cases/api.yaml)"
CUSTOMERS_CSV = "contracts/fixtures/customers/two_customers.csv"

LOOKER_ROW = "| looker | `contracts/looker/*.yaml` | `python3 -c \"import sys; sys.exit(0)\"` |"
LOOKML_ROW = "| lookml | `contracts/custom/*.lkml` | `python3 -c \"import sys; sys.exit(0)\"` |"
KPI_YAML = "orders_summary: {kind: explore, fields: [order_count]}\n"
T1_TARGET = "target: code:importer.import_file"


def _looker(root):
    _edit("prd.md", LOOKML_ROW, LOOKML_ROW + "\n" + LOOKER_ROW)(root)
    (root / "contracts/looker").mkdir()
    (root / "contracts/looker/kpi.yaml").write_text(KPI_YAML)


def _known_failing(eid):
    return _edit("test-cases/import.yaml", T1_TARGET, f"known-failing: {eid}\n  {T1_TARGET}")


CASES: list[Case] = [
    Case("test-refs", "known-failing names no entry", _known_failing("E-099")),
    Case("test-refs", "known-failing names a resolved entry", _known_failing("E-001")),
    Case("test-refs", "custom target not among the YAML items", _both(_looker, _edit("test-cases/import.yaml", T1_TARGET, "target: looker:no_such_explore"))),
    Case("ac-has-test", "T-002.2 deleted", _both(_drop_case("test-cases/api.yaml", "T-002.2"), _edit("features/api.md", TESTS_002, "Tests: T-002.1 [integration]  (test-cases/api.yaml)"))),
    Case("test-cases-consistent", "level differs", _edit("features/api.md", "T-002.1 [integration]", "T-002.1 [unit]")),
    Case("test-cases-consistent", "Tests line cites an entry that is absent", _edit("features/api.md", TESTS_002, TESTS_002.replace("T-002.2 [integration]", "T-002.2 [integration], T-002.9 [unit]"))),
    Case("test-cases-consistent", "entry no Tests line cites", _append("test-cases/import.yaml", "\nT-001.9:\n  ac: AC-001.1\n  level: unit\n")),
    Case("test-cases-consistent", "named file missing", _edit("features/api.md", TESTS_003, TESTS_003.replace("api.yaml", "orders.yaml"))),
    Case("test-level", "level smoke", _edit("test-cases/import.yaml", "  ac: AC-001.3\n  level: unit", "  ac: AC-001.3\n  level: smoke")),
    Case("test-level", "level missing", _edit("test-cases/import.yaml", "  ac: AC-001.3\n  level: unit\n", "  ac: AC-001.3\n")),
    Case("sufficiency", "leaks deleted", _edit("test-cases/import.yaml", "    errors: [IMPORT_DUPLICATE]\n    leaks: none\n", "    errors: [IMPORT_DUPLICATE]\n")),
    Case("sufficiency", "signoff deleted", _edit("test-cases/import.yaml", "  signoff: Sample Owner\n", "")),
    Case("sufficiency", "steps not a list", _edit("test-cases/import.yaml", "  steps:\n    - Make an import file with one order whose order_key is acc- plus today's date and time, for customer 1.\n    - Upload it through the import job and check the job reports 1 inserted, 0 skipped.\n    - Open that order and check it shows status open.\n", "  steps: Do it\n")),
    Case("sufficiency", "target without a kind", _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: importer")),
    Case("sufficiency", "target kind unknown", _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: widget:importer")),
    Case("sufficiency", "input empty", _edit("test-cases/api.yaml", "  input:\n    id: 999\n", "  input: {}\n")),
    Case("sufficiency", "errors not a list", _edit("test-cases/api.yaml", "    errors: [ORDER_NOT_FOUND]", "    errors: ORDER_NOT_FOUND")),
    Case("sufficiency", "output missing", _edit("test-cases/nfr.yaml", "    output: {status: 200, p95_ms_max: 300}\n", "")),
    Case("sufficiency", "unparseable file", _write("test-cases/nfr.yaml", ": : :\n")),
    Case("test-refs", "precondition fixture not registered", _edit("test-cases/api.yaml", "T-002.1:\n  ac: AC-002.1\n  level: integration\n  target: op:getOrder\n  environment: ci\n  identity: test-rep\n  preconditions: [customers/two_customers, orders/one_existing]", "T-002.1:\n  ac: AC-002.1\n  level: integration\n  target: op:getOrder\n  environment: ci\n  identity: test-rep\n  preconditions: [customers/two_customers, orders/missing]")),
    Case("test-refs", "fixture registered but no file", _both(
        _edit("testing.md", "| customers/two_customers |", "| customers/ghost | Nothing | `x` | `y` |\n| customers/two_customers |"),
        _edit("test-cases/import.yaml", "preconditions: [customers/two_customers, mock:geocoder]\n  input:\n    rows:", "preconditions: [customers/ghost, mock:geocoder]\n  input:\n    rows:"),
    )),
    Case("test-refs", "refs names a missing file", _edit("test-cases/import.yaml", '"testing.md#Harness"]', '"testing.md#Harness", "contracts/nowhere.md"]')),
    Case("test-refs", "refs names a missing heading", _edit("test-cases/import.yaml", '"contracts/events.md#import_orders"', '"contracts/events.md#export_orders"')),
    Case("test-refs", "refs escapes the PRD folder", _edit("test-cases/import.yaml", '"testing.md#Harness"]', '"testing.md#Harness", "../../README.md"]')),
    Case("test-refs", "identity unknown", _edit("test-cases/nfr.yaml", "identity: test-rep", "identity: test-nobody")),
    Case("test-refs", "op typo", _edit("test-cases/nfr.yaml", "target: op:getOrder", "target: op:getOrdr")),
    Case("test-refs", "table typo", _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: table:order")),
    Case("test-refs", "job typo", _edit("test-cases/import.yaml", "  ac: AC-001.2\n  level: integration\n  target: job:import_orders", "  ac: AC-001.2\n  level: integration\n  target: job:import_order")),
    Case("test-refs", "ac number differs", _edit("test-cases/api.yaml", "T-002.1:\n  ac: AC-002.1", "T-002.1:\n  ac: AC-001.1")),
    Case("test-refs", "ac does not exist", _edit("test-cases/api.yaml", "T-002.1:\n  ac: AC-002.1", "T-002.1:\n  ac: AC-002.7")),
    Case("test-refs", "mock without dependency file", _edit("test-cases/import.yaml", "mock:geocoder]\n  input:\n    rows:", "mock:payments]\n  input:\n    rows:")),
    Case("test-refs", "input file missing", _edit("test-cases/import.yaml", "file: orders/dup_key_in_file.csv", "file: orders/nope.csv")),
    Case("test-refs", "error code not in catalogue", _edit("test-cases/api.yaml", "errors: [ORDER_NOT_FOUND]", "errors: [ORDER_MISSING]")),
    Case("test-refs", "environment unknown", _edit("test-cases/nfr.yaml", "environment: staging", "environment: prod")),
    Case("deny-tested", "T-003.2 deleted", _both(_drop_case("test-cases/api.yaml", "T-003.2"), _edit("features/api.md", TESTS_003, "Tests: T-003.1 [integration]  (test-cases/api.yaml)"))),
    Case("deny-tested", "denied case lacks error codes", _edit("test-cases/api.yaml", "errors: [FORBIDDEN]", "errors: []")),
    Case("classified-fixtures", "real email in csv", _edit(CUSTOMERS_CSV, "ada@example.com", "jane@gmail.com")),
    Case("classified-fixtures", "real email in inline input", _edit("test-cases/api.yaml", "  input:\n    id: 999\n", "  input:\n    id: 999\n    email: bob@acme.io\n")),
]

PII_COLUMNS = _edit("contracts/data-classification.yaml", "columns: {id: internal, email: pii, name: pii}", "columns: {id: internal, email: pii, name: pii, phone: pii, ssn: pii}")


def _customers_csv(email, phone, ssn):
    return _write(CUSTOMERS_CSV, f'id,email,name,phone,ssn\n1,{email},Ada Example,"{phone}",{ssn}\n')


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


def test_synthetic_pii_is_clean(prd):
    _both(PII_COLUMNS, _customers_csv("jane@example.com", "(312) 555-0142", "900-12-3456"))(prd)
    findings = [f for f in lint(prd) if f.rule == "classified-fixtures"]
    assert findings == []


@pytest.mark.parametrize(
    "email, phone, ssn",
    [("jane@gmail.com", "(312) 555-0142", "900-12-3456"), ("jane@example.com", "(312) 555-0242", "900-12-3456"), ("jane@example.com", "(312) 555-0142", "123-45-6789")],
    ids=["email", "phone", "ssn"],
)
def test_each_real_looking_kind_fires(prd, email, phone, ssn):
    _both(PII_COLUMNS, _customers_csv(email, phone, ssn))(prd)
    assert "classified-fixtures" in fired(lint(prd))


def test_synthetic_forms_are_clean(prd):
    _both(PII_COLUMNS, _customers_csv("a@mail.test", "312-555-0199", "000-12-3456"))(prd)
    assert "classified-fixtures" not in fired(lint(prd))


def test_pii_in_unclassified_csv_column_is_ignored(prd):
    _edit(CUSTOMERS_CSV, "Ada Example", "ada@gmail.com")(prd)
    _edit("contracts/data-classification.yaml", "email: pii, name: pii", "email: pii, name: internal")(prd)
    assert "classified-fixtures" not in fired(lint(prd))


def test_yaml_fixture_rows_are_checked(prd):
    _write("contracts/fixtures/customers/more.yaml", "customers:\n  - {id: 3, email: real@gmail.com, name: Real}\n")(prd)
    _edit("testing.md", "| customers/two_customers |", "| customers/more | More | `x` | `y` |\n| customers/two_customers |")(prd)
    assert "classified-fixtures" in fired(lint(prd))


def test_removed_requirement_acs_need_no_test(prd):
    _both(
        _edit("prd.md", "| FR-003 | Delete an order | live |", "| FR-003 | Delete an order | removed |"),
        _edit("features/api.md", "### FR-003 Delete an order\nStatus: live (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed (since 1.0.0)"),
        _drop_case("test-cases/api.yaml", "T-003.1"),
        _drop_case("test-cases/api.yaml", "T-003.2"),
        _edit("features/api.md", TESTS_003, "Tests: -"),
    )(prd)
    assert "ac-has-test" not in fired(lint(prd))


def test_custom_type_is_a_target_kind(prd):
    _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: lookml:orders_explore")(prd)
    assert not [f for f in lint(prd) if f.rule == "sufficiency" and "kind" in f.message]


def test_builtin_type_name_is_not_a_target_kind(prd):
    _edit("test-cases/import.yaml", "target: code:importer.import_file", "target: openapi:orders")(prd)
    assert any(f.rule == "sufficiency" and "kind" in f.message for f in lint(prd))


def test_non_mapping_case_is_reported_once_by_the_loader(prd):
    _edit("test-cases/nfr.yaml", "T-004.1:\n  ac:", "T-004.1: oops\nT-004.2:\n  ac:")(prd)
    messages = [f.message for f in lint(prd) if f.rule == "sufficiency" and "T-004.1" in f.message]
    assert len(messages) == 1


def test_clean_fixture_fires_none_of_the_testcase_rules(prd):
    rules = {"ac-has-test", "test-cases-consistent", "test-level", "sufficiency", "test-refs", "deny-tested", "classified-fixtures"}
    assert not rules & fired(lint(prd))


@pytest.mark.parametrize("bad", ["[{code: ORDER_NOT_FOUND}]", "[[ORDER_NOT_FOUND]]"])
def test_non_string_error_code_is_a_finding_not_a_crash(prd, bad):
    _edit("test-cases/api.yaml", "errors: [ORDER_NOT_FOUND]", f"errors: {bad}")(prd)
    assert any(f.rule == "test-refs" and "expect.errors item" in f.message for f in lint(prd))


def test_non_string_deny_role_does_not_crash(prd):
    _edit("contracts/permissions.yaml", "deny: [rep]", "deny: [[rep]]")(prd)
    lint(prd)


def test_flat_csv_fixture_uses_its_stem_as_the_table(prd):
    _write("contracts/fixtures/customers.csv", "id,email,name\n1,jane@gmail.com,Jane\n")(prd)
    assert "classified-fixtures" in fired(lint(prd))


@pytest.mark.parametrize("value", ["550e8400-e29b-41d4-a716-446655440000", "ORD-20261029123456"])
def test_long_digit_runs_are_not_pii(prd, value):
    _edit("test-cases/api.yaml", "  input:\n    id: 999\n", f"  input:\n    id: 999\n    ref: {value}\n")(prd)
    assert "classified-fixtures" not in fired(lint(prd))


def test_refs_matches_a_heading_at_any_level(prd):
    edit(prd, "test-cases/import.yaml", '"testing.md#Harness"]', '"testing.md#Harness", "prd.md#7. Contract types", "nfr.md"]')
    assert "test-refs" not in fired(lint(prd))


def _ref_messages(prd):
    return [f.message for f in lint(prd) if f.rule == "test-refs"]


def test_known_failing_messages_say_why(prd):
    _known_failing("E-099")(prd)
    assert any("E-099" in m and "errors.md" in m for m in _ref_messages(prd))
    _edit("test-cases/import.yaml", "known-failing: E-099", "known-failing: E-001")(prd)
    assert any("E-001" in m and "resolved" in m for m in _ref_messages(prd))


def test_known_failing_on_an_open_entry_is_clean(prd):
    _edit("errors.md", "Resolution: the importer returns status `empty` before reading rows; T-001.3 passes", "Resolution: open")(prd)
    _known_failing("E-001")(prd)
    assert "test-refs" not in fired(lint(prd))


def test_custom_target_naming_a_yaml_item_is_clean(prd):
    _looker(prd)
    _edit("test-cases/import.yaml", T1_TARGET, "target: looker:orders_summary")(prd)
    assert "test-refs" not in fired(lint(prd))


def test_custom_target_outside_the_yaml_items_says_so(prd):
    _looker(prd)
    _edit("test-cases/import.yaml", T1_TARGET, "target: looker:no_such_explore")(prd)
    assert any("no_such_explore" in m and "looker" in m for m in _ref_messages(prd))


def test_custom_type_without_yaml_items_is_not_checked(prd):
    _edit("test-cases/import.yaml", T1_TARGET, "target: lookml:anything")(prd)
    assert "test-refs" not in fired(lint(prd))


def test_custom_items_maps_types_to_top_level_keys(prd):
    from prdlint import model
    from prdlint.rules.contracts import custom_items

    assert custom_items(model.load(prd)) == {}
    _looker(prd)
    assert custom_items(model.load(prd)) == {"looker": {"orders_summary"}}
