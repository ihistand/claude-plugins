"""snapshot.py: contract items, extraction into snapshot bodies, and the canonical text compared."""
import re

import pytest
import yaml
from conftest import edit

from prdlint import model, snapshot


def contracts(root):
    return snapshot.contracts_of(model.load(root))


def add_cli(root):
    (root / "contracts/cli.yaml").write_text("greet:\n  args: [name]\n  help: Say hello\nbye:\n  help: Say goodbye\n")
    edit(root, "prd.md", "| fixtures | `contracts/fixtures/**` | built-in |",
         "| fixtures | `contracts/fixtures/**` | built-in |\n| cli | `contracts/cli.yaml` | `true` |")


def round_trip(root, cited):
    c = contracts(root)
    out = snapshot.extract(c, cited)
    files = []
    for name, body in out.items():
        kind = "cli" if name == "cli.yaml" else None
        dialect = c.dialect if name == "schema.sql" else None
        h = snapshot.header(name, "orders", "1.0.0", "abc123", kind, dialect)
        raw = h + "\n" + body
        first, _, rest = raw.partition("\n")
        m = model._SNAP_HEADER.match(first)
        assert m, first
        files.append(model.SnapshotFile(f"contracts/upstream/orders/{name}", {k: v for k, v in m.groupdict().items() if v}, rest, None))
    return c, snapshot.contracts_of_snapshot(files)


def test_items(prd):
    i = snapshot.items(contracts(prd))
    assert i["table"] == {"customers", "orders"} and i["op"] == {"getOrder", "deleteOrder"} and "import_orders" in i["job"]


def test_extract_only_cited(prd):
    out = snapshot.extract(contracts(prd), {("table", "orders")})
    assert set(out) == {"schema.sql"} and "CREATE TABLE orders" in out["schema.sql"]
    assert "CREATE TABLE customers" not in out["schema.sql"] and "COMMENT ON TABLE orders" in out["schema.sql"]


def test_extract_op_closure(prd):
    out = snapshot.extract(contracts(prd), {("op", "getOrder")})
    assert set(out) == {"openapi.yaml"}
    data = yaml.safe_load(out["openapi.yaml"])
    assert data["info"]["title"] == "Orders API"
    ops = [m for item in data["paths"].values() for m in item if m in ("get", "delete")]
    assert ops == ["get"]
    assert set(data["components"]["schemas"]) == {"Order", "Error"}
    assert "deleteOrder" not in out["openapi.yaml"]


def test_ref_closure_is_transitive(prd):
    edit(prd, "contracts/openapi.yaml", "customer_id: {type: integer, format: int64}\n        status",
         "customer_id: {$ref: \"#/components/schemas/Cid\"}\n        status")
    edit(prd, "contracts/openapi.yaml", "    Error:\n", "    Cid: {type: integer}\n    Unused: {type: string}\n    Error:\n")
    data = yaml.safe_load(snapshot.extract(contracts(prd), {("op", "getOrder")})["openapi.yaml"])
    assert set(data["components"]["schemas"]) == {"Order", "Error", "Cid"}


def test_external_ref_is_noted_not_followed(prd):
    edit(prd, "contracts/openapi.yaml", 'schema: {$ref: "#/components/schemas/Order"}', 'schema: {$ref: "other.yaml#/Order"}')
    c = contracts(prd)
    assert "other.yaml#/Order" in snapshot.item_text(c, "op", "getOrder")
    assert set(yaml.safe_load(snapshot.extract(c, {("op", "getOrder")})["openapi.yaml"])["components"]["schemas"]) == {"Error"}


def test_extract_event(prd):
    out = snapshot.extract(contracts(prd), {("job", "import_orders")})
    assert set(out) == {"events.md"} and "### import_orders" in out["events.md"] and "Failure:" in out["events.md"]


def test_extract_custom_yaml(prd):
    add_cli(prd)
    c = contracts(prd)
    assert snapshot.items(c)["cli"] == {"greet", "bye"}
    out = snapshot.extract(c, {("cli", "greet")})
    assert set(out) == {"cli.yaml"} and yaml.safe_load(out["cli.yaml"]) == {"greet": {"args": ["name"], "help": "Say hello"}}


def test_extract_missing(prd):
    with pytest.raises(snapshot.Missing) as e:
        snapshot.extract(contracts(prd), {("table", "nope"), ("op", "gone")})
    assert sorted(e.value.items) == [("op", "gone"), ("table", "nope")]


def test_round_trip_same(prd):
    add_cli(prd)
    cited = {("table", "orders"), ("table", "customers"), ("op", "getOrder"), ("op", "deleteOrder"), ("job", "import_orders"), ("cli", "greet")}
    c, snap = round_trip(prd, cited)
    assert snap.dialect == c.dialect and snap.types == {"cli": "cli.yaml"}
    for kind, name in cited:
        assert snapshot.item_text(snap, kind, name) == snapshot.item_text(c, kind, name) is not None, (kind, name)


def test_item_text_absent(prd):
    c = contracts(prd)
    assert snapshot.item_text(c, "table", "nope") is None and snapshot.item_text(c, "op", "x") is None
    assert snapshot.item_text(c, "job", "x") is None and snapshot.item_text(c, "cli", "x") is None


def test_reformat_is_same(prd):
    before = contracts(prd)
    base = {(k, n): snapshot.item_text(before, k, n) for k, n in [("table", "orders"), ("op", "getOrder"), ("job", "import_orders")]}
    sql = (prd / "contracts/schema.sql").read_text()
    sql = sql.replace("CREATE TABLE orders (\n  id bigint PRIMARY KEY,\n  order_key text NOT NULL UNIQUE,",
                      "create table orders (\n\n        id bigint primary key,\n\n        order_key text not null unique,")
    assert sql != (prd / "contracts/schema.sql").read_text()
    (prd / "contracts/schema.sql").write_text(sql)
    spec = yaml.safe_load((prd / "contracts/openapi.yaml").read_text())
    op = spec["paths"]["/orders/{id}"]["get"]
    spec["paths"]["/orders/{id}"]["get"] = dict(reversed(list(op.items())))
    spec["components"]["schemas"]["Order"] = dict(reversed(list(spec["components"]["schemas"]["Order"].items())))
    (prd / "contracts/openapi.yaml").write_text(yaml.safe_dump(spec, sort_keys=False, indent=4))
    edit(prd, "contracts/events.md", "Failure: after 3", "Failure: after 3")  # no-op, guards the anchor
    (prd / "contracts/events.md").write_text((prd / "contracts/events.md").read_text() + "\n\n\n")
    after = contracts(prd)
    assert {(k, n): snapshot.item_text(after, k, n) for k, n in base} == base


def test_real_change_differs(prd):
    before = contracts(prd)
    t, o = snapshot.item_text(before, "table", "orders"), snapshot.item_text(before, "op", "getOrder")
    edit(prd, "contracts/schema.sql", "order_key text NOT NULL UNIQUE", "order_key varchar(40) NOT NULL UNIQUE")
    edit(prd, "contracts/openapi.yaml", "required: [id, order_key, customer_id, status]", "required: [id, order_key, customer_id, status, sales_rep_name]")
    after = contracts(prd)
    assert snapshot.item_text(after, "table", "orders") != t and snapshot.item_text(after, "op", "getOrder") != o
    assert snapshot.item_text(after, "table", "customers") == snapshot.item_text(before, "table", "customers")


def test_comment_change_differs(prd):
    before = snapshot.item_text(contracts(prd), "table", "orders")
    edit(prd, "contracts/schema.sql", "One row per imported order.", "One row per order.")
    assert snapshot.item_text(contracts(prd), "table", "orders") != before


def test_header_forms():
    h = "Snapshot of orders 1.2.0 at abc123, written by prd_links.py sync. Do not edit."
    assert snapshot.header("schema.sql", "orders", "1.2.0", "abc123", dialect="postgres") == f"-- {h} Dialect: postgres."
    assert snapshot.header("cli.yaml", "orders", "1.2.0", "abc123", kind="cli") == f"# {h} Type: cli."
    assert snapshot.header("openapi.yaml", "orders", "1.2.0", "abc123") == f"# {h}"
    assert snapshot.header("events.md", "orders", "1.2.0", "abc123") == f"<!-- {h} -->"
    assert re.fullmatch(model._SNAP_HEADER.pattern, snapshot.header("events.md", "orders", "1.2.0", "abc123"))


def test_table_extracted_verbatim(prd):
    edit(prd, "contracts/schema.sql", "  email text NOT NULL,\n",
         "  email   text NOT NULL, -- contact address\n\t\t")
    src = (prd / "contracts/schema.sql").read_text()
    c = contracts(prd)
    out = snapshot.extract(c, {("table", "customers")})["schema.sql"]
    create = src[src.index("CREATE TABLE customers"):src.index(");", src.index("CREATE TABLE customers")) + 2]
    assert create in out and "-- contact address" in out and "COMMENT ON COLUMN customers.email IS 'Contact email. PII.';" in out
    assert "CREATE TABLE orders" not in out
    c2, snap = round_trip(prd, {("table", "customers")})
    assert snapshot.item_text(snap, "table", "customers") == snapshot.item_text(c, "table", "customers") is not None


def test_mixed_key_reorder_is_same(prd):
    spec = yaml.safe_load((prd / "contracts/openapi.yaml").read_text())
    get = spec["paths"]["/orders/{id}"]["get"]
    get["responses"]["default"] = {"description": "Any other."}
    (prd / "contracts/openapi.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    a = snapshot.item_text(contracts(prd), "op", "getOrder")
    get["responses"] = dict(reversed(list(get["responses"].items())))
    (prd / "contracts/openapi.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    assert snapshot.item_text(contracts(prd), "op", "getOrder") == a


def sql_contracts(text):
    return snapshot.Contracts({"schema.sql": text}, {}, None)


def test_uncited_text_does_not_leak():
    c = sql_contracts("-- file header\nCREATE TABLE a (id int); -- SECRET about a\nCREATE TABLE b (id int);\n")
    assert snapshot.extract(c, {("table", "b")})["schema.sql"] == "CREATE TABLE b (id int);\n"


def test_trailing_comment_on_uncited_comment_line_does_not_leak():
    c = sql_contracts("CREATE TABLE a (id int);\nCOMMENT ON TABLE a IS 'x'; -- SECRET\nCREATE TABLE b (id int);\n")
    out = snapshot.extract(c, {("table", "b")})["schema.sql"]
    assert out == "CREATE TABLE b (id int);\n"


def test_trailing_and_leading_comments_stay_with_cited():
    c = sql_contracts("CREATE TABLE a (id int);\n\n-- unrelated\n\n-- about b\nCREATE TABLE b (id int); -- mine\n")
    out = snapshot.extract(c, {("table", "b")})["schema.sql"]
    assert out == "-- about b\nCREATE TABLE b (id int); -- mine\n"


def test_extract_raises_on_untokenizable_schema():
    c = sql_contracts("CREATE TABLE a (id int); SELECT 'unterminated\n")
    with pytest.raises(Exception):
        snapshot._chunks(c)
