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

CASES: list[Case] = [
    Case("ac-has-test", "T-002.2 deleted", _both(_drop_case("test-cases/api.yaml", "T-002.2"), _edit("features/api.md", TESTS_002, "Tests: T-002.1 [integration]  (test-cases/api.yaml)"))),
    Case("test-cases-consistent", "level differs", _edit("features/api.md", "T-002.1 [integration]", "T-002.1 [unit]")),
    Case("test-cases-consistent", "Tests line cites an entry that is absent", _edit("features/api.md", TESTS_002, TESTS_002.replace("T-002.2 [integration]", "T-002.2 [integration], T-002.9 [unit]"))),
    Case("test-cases-consistent", "entry no Tests line cites", _append("test-cases/import.yaml", "\nT-001.9:\n  ac: AC-001.1\n  level: unit\n")),
    Case("test-cases-consistent", "named file missing", _edit("features/api.md", TESTS_003, TESTS_003.replace("api.yaml", "orders.yaml"))),
    Case("test-level", "level smoke", _edit("test-cases/import.yaml", "  ac: AC-001.3\n  level: unit", "  ac: AC-001.3\n  level: smoke")),
    Case("test-level", "level missing", _edit("test-cases/import.yaml", "  ac: AC-001.3\n  level: unit\n", "  ac: AC-001.3\n")),
    Case("sufficiency", "leaks deleted", _edit("test-cases/import.yaml", "    errors: [IMPORT_DUPLICATE]\n    leaks: none\n", "    errors: [IMPORT_DUPLICATE]\n")),
    Case("sufficiency", "signoff deleted", _edit("test-cases/import.yaml", "  signoff: Sample Owner\n", "")),
    Case("sufficiency", "steps not a list", _edit("test-cases/import.yaml", "  steps:\n    - Load the customers/two_customers fixture into staging.\n    - Upload orders/one_existing.csv through the import job.\n    - Open the order K-1000 and confirm it shows status open.\n", "  steps: Do it\n")),
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
