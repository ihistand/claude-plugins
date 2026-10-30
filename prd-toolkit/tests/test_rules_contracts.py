import pytest
from conftest import Case, edit, fired, lint
from prd_lint import main


def _edit(rel, old, new):
    return lambda root: edit(root, rel, old, new)


def _append(rel, text):
    def mutate(root):
        path = root / rel
        path.write_text(path.read_text().rstrip("\n") + "\n" + text + "\n")

    return mutate


def _write(rel, text):
    return lambda root: (root / rel).write_text(text)


VALIDATOR = 'python3 -c "import sys; sys.exit(0)"'
LKML_ROW = "| lookml | `contracts/custom/*.lkml` | "


def _validator(cmd):
    return _edit("prd.md", LKML_ROW + f"`{VALIDATOR}` |", LKML_ROW + f"`{cmd}` |")


UNUSED = """UNUSED_CODE:
  meaning: Nothing cites this.
  when: Never.
  status: 500
  message: Unused
  log_level: error
  retryable: false
  metric: unused_total"""

CASES: list[Case] = [
    Case("contracts-valid", "custom glob matches no file", _edit("prd.md", "`contracts/custom/*.lkml`", "`contracts/custom/*.nope`")),
    Case("contracts-valid", "errors-missing-metric", _edit("contracts/errors.yaml", "  metric: orders_forbidden_total\n", "")),
    Case("contracts-valid", "errors-bad-code-name", _edit("contracts/errors.yaml", "FORBIDDEN:\n", "forbidden:\n")),
    Case("contracts-valid", "errors-status-not-int", _edit("contracts/errors.yaml", "status: 403", "status: forbidden")),
    Case("contracts-valid", "openapi-no-example", _edit("contracts/openapi.yaml", "              example: {id: 1, order_key: K-1000, customer_id: 1, status: open}\n", "")),
    Case("contracts-valid", "openapi-no-operation-id", _edit("contracts/openapi.yaml", "      operationId: getOrder\n", "")),
    Case("contracts-valid", "openapi-unknown-prd-id", _edit("contracts/openapi.yaml", "[FR-003, AC-003.1, AC-003.2]", "[FR-003, AC-003.1, AC-003.9]")),
    Case("contracts-valid", "openapi-no-effects", _edit("contracts/openapi.yaml", "      x-effects: []\n", "")),
    Case("contracts-valid", "openapi-invalid-spec", _edit("contracts/openapi.yaml", "openapi: 3.1.0\n", "openapi: 9.9.9\n")),
    Case("contracts-valid", "asyncapi-no-key", _write("contracts/asyncapi.yaml", "channels: {}\n")),
    Case("contracts-valid", "events-missing-line", _edit("contracts/events.md", "Retries: 3 attempts", "Retried: 3 attempts")),
    Case("contracts-valid", "schema-typo", _edit("contracts/schema.sql", "CREATE TABLE customers", "CREAT TABLE customers")),
    Case("contracts-valid", "schema-no-column-comment", _edit("contracts/schema.sql", "COMMENT ON COLUMN orders.status IS 'open, shipped or cancelled.';\n", "")),
    Case("contracts-valid", "schema-no-table-comment", _edit("contracts/schema.sql", "COMMENT ON TABLE customers IS 'People and companies that place orders.';\n", "")),
    Case("contracts-valid", "permissions-role-in-no-list", _edit("contracts/permissions.yaml", "deny: [rep]", "deny: []")),
    Case("contracts-valid", "permissions-role-in-both", _edit("contracts/permissions.yaml", "allow: [admin], deny: [rep]", "allow: [admin, rep], deny: [rep]")),
    Case("contracts-valid", "permissions-row-rule-no-attribute", _edit("contracts/permissions.yaml", "    attribute: sales_rep_name\n", "")),
    Case("contracts-valid", "config-no-owner", _edit("contracts/config.yaml", "    owner: Sample Owner\n", "")),
    Case("contracts-valid", "classification-bad-class", _edit("contracts/data-classification.yaml", "email: pii", "email: secret")),
    Case("contracts-valid", "classification-no-masking", _edit("contracts/data-classification.yaml", "  errors: error bodies carry a code and a fixed message only\n", "")),
    Case("contracts-valid", "dependency-no-4xx", _edit("contracts/dependencies/geocoder.yaml", "  4xx: GEOCODER_TIMEOUT\n", "")),
    Case("contracts-valid", "dependency-no-mock", _edit("contracts/dependencies/geocoder.yaml", "mock: tests/mocks/geocoder.py replays recorded answers; tests never call the live service\n", "")),
    Case("contracts-valid", "custom-validator-fails", _validator('python3 -c "import sys; sys.exit(1)"')),
    Case("schema-refs", "unknown-column", _edit("features/import.md", "`orders.order_key` UNIQUE", "`orders.order_kee` UNIQUE")),
    Case("error-codes", "uncatalogued-in-block", _edit("features/api.md", "Errors: ORDER_NOT_FOUND (contracts", "Errors: ORDER_NOT_FOUND, ORDER_LOCKED (contracts")),
    Case("error-codes", "uncatalogued-in-openapi", _edit("contracts/openapi.yaml", "x-error-codes: [FORBIDDEN]", "x-error-codes: [FORBIDDEN, NOPE]")),
    Case("error-codes", "uncatalogued-in-dependency", _edit("contracts/dependencies/geocoder.yaml", "  outage: GEOCODER_TIMEOUT", "  outage: GEOCODER_GONE")),
    Case("error-codes", "catalogued-never-cited", _append("contracts/errors.yaml", UNUSED)),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


def test_clean_fixture_fires_none_of_the_contract_rules(prd):
    assert not {"contracts-valid", "schema-refs", "error-codes"} & fired(lint(prd))


def test_unknown_table_prefix_is_not_checked(prd):
    _edit("features/import.md", "`orders.order_key` UNIQUE", "`prd.md` and `nosuch.thing` UNIQUE")(prd)
    assert "schema-refs" not in fired(lint(prd))


def test_file_names_that_look_like_table_columns_are_not_checked(prd):
    _edit("features/import.md", "`orders.order_key` UNIQUE", "`orders.csv` and `customers.sql` UNIQUE")(prd)
    assert "schema-refs" not in fired(lint(prd))
    _edit("features/import.md", "`customers.sql` UNIQUE", "`orders.order_kee` UNIQUE")(prd)
    assert "schema-refs" in fired(lint(prd))


def test_schema_refs_ignores_fenced_blocks(prd):
    _append("features/import.md", "\n```\n`orders.order_kee`\n```")(prd)
    assert "schema-refs" not in fired(lint(prd))


def test_code_cited_only_by_a_test_case_is_not_unused(prd):
    _edit("features/api.md", "Errors: FORBIDDEN (contracts/errors.yaml)", "Errors: -")(prd)
    _edit("contracts/openapi.yaml", "x-error-codes: [FORBIDDEN]", "x-error-codes: []")(prd)
    assert "error-codes" not in fired(lint(prd))


def test_test_case_code_missing_from_catalogue_is_not_reported_by_error_codes(prd):
    _edit("test-cases/api.yaml", "errors: [FORBIDDEN]", "errors: [FORBIDDEN, GHOST]")(prd)
    assert "error-codes" not in fired(lint(prd))


def test_bigquery_options_description_counts(prd):
    _edit("prd.md", "sql-dialect: postgres", "sql-dialect: bigquery")(prd)
    sql = (
        'CREATE TABLE customers (id INT64 OPTIONS(description="k"), email STRING OPTIONS(description="e"), '
        'name STRING OPTIONS(description="n")) OPTIONS(description="t");\n'
        'CREATE TABLE orders (id INT64 OPTIONS(description="k"), order_key STRING OPTIONS(description="k"), '
        'customer_id INT64 OPTIONS(description="c"), status STRING OPTIONS(description="s"), '
        'sales_rep_name STRING OPTIONS(description="r")) OPTIONS(description="t");\n'
    )
    _write("contracts/schema.sql", sql)(prd)
    assert "contracts-valid" not in fired(lint(prd))
    _write("contracts/schema.sql", sql.replace('name STRING OPTIONS(description="n")', "name STRING"))(prd)
    assert "contracts-valid" in fired(lint(prd))


@pytest.mark.parametrize(
    "rel, text",
    [
        ("contracts/config.yaml", "- a\n- b\n"),
        ("contracts/errors.yaml", ""),
        ("contracts/permissions.yaml", "roles: 3\n"),
        ("contracts/errors.yaml", "FORBIDDEN: 3\nlower: [a]\n"),
        ("contracts/permissions.yaml", "roles: {rep: 4}\noperations: [x]\nrow_rules: {a: b}\n"),
        ("contracts/permissions.yaml", "roles: {rep: {identity: r}}\noperations: {op: {allow: 1, deny: {a: b}}}\nrow_rules: [3]\n"),
        ("contracts/config.yaml", "settings: [1]\n"),
        ("contracts/config.yaml", "settings: {A: {environments: [1]}}\n"),
        ("contracts/data-classification.yaml", "tables: [x]\nmasking: 4\n"),
        ("contracts/data-classification.yaml", "tables: {t: {columns: [a]}}\nmasking: {logs: a}\n"),
        ("contracts/dependencies/geocoder.yaml", "auth: 3\nfailures: [x]\n"),
        ("contracts/dependencies/geocoder.yaml", "failures: {timeout: [1, {a: b}], outage: {x: y}}\n"),
        ("contracts/openapi.yaml", "paths: [x]\n"),
        ("contracts/openapi.yaml", "openapi: 3.1.0\npaths: {/a: {get: 3}, /b: {get: {responses: [1]}}, /c: {get: {responses: {'200': 5}}}}\n"),
        ("contracts/openapi.yaml", "paths: {/a: {get: {operationId: 3, x-prd-ids: [[1]], x-error-codes: 4, responses: {'200': {content: 7}}}}}\n"),
        ("contracts/asyncapi.yaml", "- a\n"),
    ],
    ids=lambda v: v[:20].replace("\n", " ") if isinstance(v, str) else None,
)
def test_malformed_shapes_never_crash(prd, capsys, rel, text):
    (prd / rel).write_text(text)
    assert main([str(prd)]) == 1
    captured = capsys.readouterr()
    assert "contracts-valid" in captured.out
    assert "Traceback" not in captured.out + captured.err
    assert "internal error" not in captured.out + captured.err


def test_validator_timeout(prd, monkeypatch):
    monkeypatch.setenv("PRD_VALIDATOR_TIMEOUT", "1")
    _validator("python3 -c 'import time; time.sleep(5)'")(prd)
    msgs = [f.message for f in lint(prd) if f.rule == "contracts-valid"]
    assert any("timed out after 1s" in m for m in msgs)


def test_validator_missing(prd):
    _validator("no-such-validator-xyz")(prd)
    msgs = [f.message for f in lint(prd) if f.rule == "contracts-valid"]
    assert any("not found" in m for m in msgs)


def test_validator_failure_reports_first_stderr_line(prd):
    _validator("python3 -c 'import sys; print(\"bad one\\nsecond\", file=sys.stderr); sys.exit(3)'")(prd)
    msgs = [f.message for f in lint(prd) if f.rule == "contracts-valid"]
    assert any(m.endswith("validator failed: bad one") for m in msgs)


def test_validator_receives_files_and_runs_in_the_prd_root(prd):
    script = "import os, sys; sys.exit(0 if sys.argv[1:] == ['contracts/custom/sample.lkml'] and os.path.isfile('prd.md') else 1)"
    _validator(f"python3 -c \"{script}\"")(prd)
    assert "contracts-valid" not in fired(lint(prd))


@pytest.mark.parametrize("text", ["asyncapi: 3.0.0\nchannels: [x]\noperations: 4\n", "asyncapi: 2.6.0\nchannels: {a: {publish: 3}}\n"])
def test_malformed_asyncapi_never_crashes(prd, capsys, text):
    (prd / "contracts/asyncapi.yaml").write_text(text)
    main([str(prd)])
    assert "internal error" not in capsys.readouterr().err


def test_custom_glob_without_a_file_says_so(prd):
    _edit("prd.md", "`contracts/custom/*.lkml`", "`contracts/custom/*.nope`")(prd)
    msgs = [f.message for f in lint(prd) if f.rule == "contracts-valid"]
    assert any("lookml" in m and "glob matches no file" in m for m in msgs)
