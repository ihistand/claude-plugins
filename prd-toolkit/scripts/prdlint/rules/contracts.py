"""Contract lookups shared by rules: schema tables, operationIds, event and job names. No rules here."""
import re

from ..deps import require
from ..model import Prd

sqlglot = require("sqlglot", "sqlglot")
from sqlglot import exp  # noqa: E402

_EVENT_HEADING = re.compile(r"^###\s+`?([^`\s]+)`?\s*$")
_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def schema_tables(prd: Prd) -> dict[str, set[str]]:
    """Table name -> column names from contracts/schema.sql; {} when it is absent or does not parse."""
    path = prd.root / "contracts/schema.sql"
    if not path.is_file():
        return {}
    dialect = prd.frontmatter.get("sql-dialect") or None
    try:
        statements = sqlglot.parse(path.read_text(), read=dialect)
    except Exception:  # sqlglot raises ParseError, TokenError or ValueError (unknown dialect)
        return {}
    tables: dict[str, set[str]] = {}
    for stmt in statements:
        if isinstance(stmt, exp.Create) and (stmt.args.get("kind") or "").upper() == "TABLE":
            table = stmt.find(exp.Table)
            if table is not None:
                tables.setdefault(table.name, set()).update(c.name for c in stmt.find_all(exp.ColumnDef))
    return tables


def operation_ids(prd: Prd) -> set[str]:
    """Every operationId in contracts/openapi.yaml (paths and webhooks)."""
    data = prd.yaml.get("contracts/openapi.yaml")
    out: set[str] = set()
    if not isinstance(data, dict):
        return out
    for section in ("paths", "webhooks"):
        for item in (data.get(section) or {}).values():
            if not isinstance(item, dict):
                continue
            for method in _METHODS:
                op = item.get(method)
                if isinstance(op, dict) and isinstance(op.get("operationId"), str):
                    out.add(op["operationId"])
    return out


def event_names(prd: Prd) -> set[str]:
    """`### name` headings of contracts/events.md plus asyncapi channels and operations."""
    out: set[str] = set()
    for line in prd.docs.get("contracts/events.md", "").split("\n"):
        m = _EVENT_HEADING.match(line)
        if m:
            out.add(m.group(1))
    data = prd.yaml.get("contracts/asyncapi.yaml")
    if isinstance(data, dict):
        for name, channel in (data.get("channels") or {}).items():
            out.add(str(name))
            if isinstance(channel, dict):
                if isinstance(channel.get("address"), str):
                    out.add(channel["address"])
                for verb in ("publish", "subscribe"):  # AsyncAPI 2.x operations live under the channel
                    op = channel.get(verb)
                    if isinstance(op, dict) and isinstance(op.get("operationId"), str):
                        out.add(op["operationId"])
        out.update(str(k) for k in (data.get("operations") or {}))  # AsyncAPI 3.x
    return out
