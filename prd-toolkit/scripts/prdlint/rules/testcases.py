"""Test-case rules: every test is fully specified by the PRD alone (spec 4.1, 4.2)."""
import csv
import io
import json
import re
from collections.abc import Iterator

from ..findings import Finding
from ..markdown import strip_code, tables
from ..model import Prd, TestCase
from ..registry import rule
from ..yamlload import yaml
from .contracts import event_names, operation_ids, schema_tables

TARGET_KINDS = {"op", "table", "event", "job", "component", "page", "code"}

_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.M)


def _ref_problem(prd: Prd, ref: object) -> str | None:
    """Why a `refs:` entry does not resolve, or None. An entry is a PRD-folder path, optionally
    followed by '#' and the exact text of a heading in that file."""
    if not isinstance(ref, str) or not ref.strip():
        return f"refs entry {ref!r} must be a path in the PRD folder, optionally with #heading"
    path, _, heading = ref.partition("#")
    target = (prd.root / path).resolve()
    if not target.is_relative_to(prd.root) or not target.is_file():
        return f"refs entry '{ref}': no file {path} in the PRD folder"
    if heading:
        headings = _HEADING.findall(strip_code(target.read_text(encoding="utf-8")))
        if heading not in headings:
            return f"refs entry '{ref}': {path} has no heading '{heading}'"
    return None

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_PHONE = re.compile(r"(?<!\d)\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}(?!\d)")  # not inside a longer digit run
_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_SYNTHETIC_DOMAINS = {"example.com", "example.org", "example.net"}
_SYNTHETIC_SUFFIXES = (".test", ".example", ".invalid")
_AC_NUMBER = re.compile(r"AC-(\d+)\.\d+")
_TID_NUMBER = re.compile(r"T-(\d+)\.\d+")


# ---------------------------------------------------------------- PII helpers (public)


def pii_values(text: str) -> list[str]:
    """Every email, SSN and phone-number-shaped value in `text`, synthetic or not."""
    out: list[str] = []
    for pattern in (_EMAIL, _SSN, _PHONE):  # most specific first; a match is blanked before the next pattern
        for m in pattern.finditer(text):
            out.append(m.group(0))
        text = pattern.sub(lambda m: " " * len(m.group(0)), text)
    return out


def is_synthetic(value: str) -> bool:
    """True when `value` is an allowed synthetic PII form. A value that is not PII-shaped counts as synthetic."""
    if _EMAIL.fullmatch(value):
        domain = value.rsplit("@", 1)[1].lower()
        return domain in _SYNTHETIC_DOMAINS or domain.endswith(_SYNTHETIC_SUFFIXES)
    if _SSN.fullmatch(value):
        area = value[:3]
        return area in ("000", "666") or area.startswith("9")
    if _PHONE.fullmatch(value):
        digits = re.sub(r"\D", "", value)
        return digits[3:6] == "555" and digits[6:8] == "01"  # line 0100 to 0199
    return True


# ---------------------------------------------------------------- shared helpers


def target_kinds(prd: Prd) -> set[str]:
    """Built-in target kinds plus the custom type names of prd.md section 7 (validator not `built-in`)."""
    kinds = set(TARGET_KINDS)
    sec = next((s for s in prd.sections if s.number == 7), None)
    for t in tables(sec.body) if sec else []:
        for r in t.rows:
            if len(r.cells) >= 3 and r.cells[2].strip("`").strip() != "built-in":
                kinds.add(r.cells[0].strip("`").strip())
    return kinds


def _cases(prd: Prd) -> Iterator[TestCase]:
    """Test cases that are mappings; the loader already reports the others under `sufficiency`."""
    bad = {(f.file, f.line) for f in prd.load_findings if f.rule == "sufficiency" and "must be a mapping" in f.message}
    for tc in prd.test_cases:
        if (tc.file, tc.line) not in bad:
            yield tc


def _line(tc: TestCase, key: str) -> int:
    return tc.data.key_lines.get(key, tc.line)


def _expect(tc: TestCase) -> dict:
    e = tc.data.get("expect")
    return e if isinstance(e, dict) else {}


def _blank(v) -> bool:
    return v is None or (isinstance(v, (str, list, dict)) and len(v) == 0)


def _exists_fixture(prd: Prd, name: str) -> bool:
    base = prd.root / "contracts/fixtures" / name
    return base.is_dir() or (base.parent.is_dir() and any(p.is_file() and p.stem == base.name for p in base.parent.iterdir()))



# ---------------------------------------------------------------- rules


@rule("ac-has-test")
def ac_has_test(prd: Prd):
    covered = {str(tc.data.get("ac")) for tc in _cases(prd)}
    for b in prd.blocks:
        if b.status == "removed":
            continue
        for ac in b.acs:
            if not ac.removed and ac.id not in covered:
                yield Finding(b.file, ac.line, "ac-has-test", f"{ac.id} has no test case whose ac: is {ac.id}")


@rule("test-cases-consistent")
def test_cases_consistent(prd: Prd):
    entries = {(tc.file, tc.id): tc for tc in prd.test_cases}
    cited: set[tuple[str | None, str]] = set()
    for b in prd.blocks:
        for tid, level, line in b.tests:
            cited.add((b.tests_file, tid))
            if b.tests_file is None:
                yield Finding(b.file, line, "test-cases-consistent", f"the Tests line of {b.id} names no test-cases file; end it with (test-cases/<area>.yaml)")
                continue
            if not (prd.root / b.tests_file).is_file():
                yield Finding(b.file, line, "test-cases-consistent", f"{tid}: the named file {b.tests_file} does not exist")
                continue
            tc = entries.get((b.tests_file, tid))
            if tc is None:
                yield Finding(b.file, line, "test-cases-consistent", f"{tid} has no entry in {b.tests_file}")
                continue
            actual = tc.data.get("level")
            if isinstance(actual, str) and actual != level:
                yield Finding(b.file, line, "test-cases-consistent", f"{tid} is [{level}] on the Tests line but level: {actual} in {tc.file}:{_line(tc, 'level')}")
    for tc in prd.test_cases:
        if (tc.file, tc.id) not in cited:
            yield Finding(tc.file, tc.line, "test-cases-consistent", f"{tc.id} is cited by no Tests line naming {tc.file}")


@rule("test-level")
def test_level(prd: Prd):
    for tc in _cases(prd):
        level = tc.data.get("level")
        if _blank(level):
            yield Finding(tc.file, tc.line, "test-level", f"{tc.id} has no level")
        elif str(level) not in prd.testing.levels:
            yield Finding(tc.file, _line(tc, "level"), "test-level", f"{tc.id}: level '{level}' is not a row of the Levels table in testing.md")


@rule("sufficiency")
def sufficiency(prd: Prd):
    # parse errors, non-mapping files and non-mapping cases are reported by the loader
    kinds = target_kinds(prd)
    for tc in _cases(prd):
        d = tc.data

        def miss(key: str, what: str, line: int | None = None):
            return Finding(tc.file, line or _line(tc, key), "sufficiency", f"{tc.id}: {what}")

        for key in ("ac", "level", "environment", "identity"):
            if not isinstance(d.get(key), str) or not d[key].strip():
                yield miss(key, f"{key} is missing", tc.line)
        target = d.get("target")
        if not isinstance(target, str) or not target.strip():
            yield miss("target", "target is missing", tc.line)
        else:
            kind, sep, name = target.partition(":")
            if not sep or not name.strip():
                yield miss("target", f"target '{target}' must be <kind>:<name>")
            elif kind not in kinds:
                yield miss("target", f"target kind '{kind}' is unknown (known: {', '.join(sorted(kinds))})")
        if not isinstance(d.get("preconditions"), list):
            yield miss("preconditions", "preconditions must be a list (use [] for none)", tc.line if "preconditions" not in d else None)
        if _blank(d.get("input")):
            yield miss("input", "input is missing or empty", tc.line if "input" not in d else None)
        expect = d.get("expect")
        if not isinstance(expect, dict):
            yield miss("expect", "expect is missing", tc.line if "expect" not in d else None)
            expect = {}
        eline = _line(tc, "expect")
        if _blank(expect.get("output")):
            yield miss("expect", "expect.output is missing", expect.key_lines.get("output", eline) if hasattr(expect, "key_lines") else eline)
        for key in ("effects", "errors"):
            if not isinstance(expect.get(key), list):
                yield miss("expect", f"expect.{key} must be a list (use [] for none)", getattr(expect, "key_lines", {}).get(key, eline))
        if _blank(expect.get("leaks")):
            yield miss("expect", "expect.leaks is missing (use 'none')", getattr(expect, "key_lines", {}).get("leaks", eline))
        if d.get("level") == "acceptance":
            steps = d.get("steps")
            if not (isinstance(steps, list) and steps and all(isinstance(s, str) and s.strip() for s in steps)):
                yield miss("steps", "an acceptance case needs steps: a non-empty list of strings", tc.line if "steps" not in d else None)
            if not isinstance(d.get("signoff"), str) or not d["signoff"].strip():
                yield miss("signoff", "an acceptance case needs signoff: the business owner", tc.line if "signoff" not in d else None)


@rule("test-refs")
def test_refs(prd: Prd):
    all_acs = {ac.id for b in prd.blocks for ac in b.acs}
    errors_yaml = prd.yaml.get("contracts/errors.yaml")
    perms = prd.yaml.get("contracts/permissions.yaml")
    identities = {"none"}
    if isinstance(perms, dict) and isinstance(perms.get("roles"), dict):
        identities |= {r["identity"] for r in perms["roles"].values() if isinstance(r, dict) and isinstance(r.get("identity"), str)}
    ops, tables_, events = operation_ids(prd), {t.lower() for t in schema_tables(prd)}, event_names(prd)

    for tc in _cases(prd):
        d = tc.data

        def bad(key: str, msg: str):
            return Finding(tc.file, _line(tc, key), "test-refs", f"{tc.id}: {msg}")

        ac = d.get("ac")
        if isinstance(ac, str) and ac:
            if ac not in all_acs:
                yield bad("ac", f"{ac} is not an acceptance criterion in any requirement block")
            am, tm = _AC_NUMBER.fullmatch(ac), _TID_NUMBER.fullmatch(tc.id)
            if am and tm and am.group(1) != tm.group(1):
                yield bad("ac", f"{ac} belongs to requirement {am.group(1)}, but {tc.id} is numbered for requirement {tm.group(1)}")

        for pre in d.get("preconditions") if isinstance(d.get("preconditions"), list) else []:
            if not isinstance(pre, str):
                yield bad("preconditions", f"precondition {pre!r} must be a fixture name or mock:<service>")
            elif pre.startswith("mock:"):
                if not (prd.root / f"contracts/dependencies/{pre[5:]}.yaml").is_file():
                    yield bad("preconditions", f"{pre} has no contracts/dependencies/{pre[5:]}.yaml")
            else:
                if pre not in prd.testing.fixtures:
                    yield bad("preconditions", f"fixture '{pre}' is not in the Fixtures table of testing.md")
                if not _exists_fixture(prd, pre):
                    yield bad("preconditions", f"fixture '{pre}' has no file or directory at contracts/fixtures/{pre}")

        inp = d.get("input")
        if isinstance(inp, dict) and isinstance(inp.get("file"), str):
            if not (prd.root / "contracts/fixtures" / inp["file"]).is_file():
                yield bad("input", f"input.file '{inp['file']}' does not exist under contracts/fixtures/")

        codes = _expect(tc).get("errors")
        if isinstance(errors_yaml, dict) and isinstance(codes, list):
            for code in codes:
                if not isinstance(code, str):
                    yield bad("expect", f"expect.errors item {code!r} must be an error code string")
                elif code not in errors_yaml:
                    yield bad("expect", f"error code {code} is not in contracts/errors.yaml")

        refs = d.get("refs")
        if refs is not None:
            for ref in refs if isinstance(refs, list) else [refs]:
                problem = _ref_problem(prd, ref)
                if problem:
                    yield bad("refs", problem)

        env = d.get("environment")
        if isinstance(env, str) and env and env not in prd.testing.environments:
            yield bad("environment", f"environment '{env}' is not in the Environments table of testing.md")
        ident = d.get("identity")
        if isinstance(ident, str) and ident and ident not in identities:
            yield bad("identity", f"identity '{ident}' is neither none nor a test identity in contracts/permissions.yaml")

        target = d.get("target")
        if isinstance(target, str) and ":" in target:
            kind, _, name = target.partition(":")
            if kind == "op" and name not in ops:
                yield bad("target", f"target {target}: no operationId '{name}' in contracts/openapi.yaml")
            elif kind == "table" and name.lower() not in tables_:
                yield bad("target", f"target {target}: no table '{name}' in contracts/schema.sql")
            elif kind in ("event", "job") and name not in events:
                yield bad("target", f"target {target}: no '### {name}' heading in contracts/events.md and no such asyncapi channel or operation")


@rule("deny-tested")
def deny_tested(prd: Prd):
    perms = prd.yaml.get("contracts/permissions.yaml")
    if not isinstance(perms, dict):
        return
    roles = perms.get("roles") if isinstance(perms.get("roles"), dict) else {}
    ops = perms.get("operations") if isinstance(perms.get("operations"), dict) else {}
    for op, cell in ops.items():
        if not isinstance(cell, dict):
            continue
        line = getattr(cell, "key_lines", {}).get("deny") or getattr(ops, "key_lines", {}).get(op, 1)
        deny = cell.get("deny")
        for role in deny if isinstance(deny, list) else []:
            if not isinstance(role, str):
                continue  # contracts-valid reports the shape
            ident = (roles.get(role) or {}).get("identity") if isinstance(roles.get(role), dict) else None
            if not ident:
                yield Finding("contracts/permissions.yaml", line, "deny-tested", f"deny cell ({op}, {role}): role '{role}' has no test identity")
                continue
            tested = any(
                tc.data.get("target") == f"op:{op}" and tc.data.get("identity") == ident and _expect(tc).get("errors")
                for tc in _cases(prd)
            )
            if not tested:
                yield Finding("contracts/permissions.yaml", line, "deny-tested", f"deny cell ({op}, {role}) has no test case with target op:{op}, identity {ident} and expect.errors")


# ---- classified-fixtures


def _pii_columns(prd: Prd) -> dict[str, set[str]]:
    data = prd.yaml.get("contracts/data-classification.yaml")
    out: dict[str, set[str]] = {}
    for table, spec in (data.get("tables") if isinstance(data, dict) and isinstance(data.get("tables"), dict) else {}).items():
        cols = spec.get("columns") if isinstance(spec, dict) else None
        if isinstance(cols, dict):
            out[str(table)] = {str(c) for c, kind in cols.items() if kind == "pii"}
    return out


def _strings(node) -> Iterator[str]:
    if isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)
    elif isinstance(node, str):
        yield node


def _line_of(text: str, value: str, default: int = 1) -> int:
    i = text.find(value)
    return text.count("\n", 0, i) + 1 if i >= 0 else default


@rule("classified-fixtures")
def classified_fixtures(prd: Prd):
    pii = _pii_columns(prd)

    def real(value) -> list[str]:
        return [v for v in pii_values(str(value)) if not is_synthetic(v)]

    base = prd.root / "contracts/fixtures"
    for path in sorted(base.rglob("*")) if base.is_dir() else []:
        if not path.is_file():
            continue
        rel = path.relative_to(prd.root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        suffix = path.suffix.lower()
        if suffix == ".csv":
            table = path.parent.name if path.parent != base else path.stem
            cols = pii.get(table, set())
            reader = csv.reader(io.StringIO(text))
            header = next(reader, [])
            for row in reader:
                for col, value in zip(header, row):
                    if col in cols:
                        for v in real(value):
                            yield Finding(rel, reader.line_num, "classified-fixtures", f"{table}.{col} is classified pii but holds the real-looking value '{v}'")
        elif suffix in (".yaml", ".yml", ".json"):
            try:
                data = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
            except Exception:
                continue  # contracts-valid reports YAML that does not parse
            for table, rows in (data.items() if isinstance(data, dict) else []):
                for row in rows if isinstance(rows, list) else []:
                    for col, value in (row.items() if isinstance(row, dict) else []):
                        if col in pii.get(str(table), set()):
                            for v in real(value if not isinstance(value, (dict, list)) else " ".join(_strings(value))):
                                yield Finding(rel, _line_of(text, v), "classified-fixtures", f"{table}.{col} is classified pii but holds the real-looking value '{v}'")
    for tc in _cases(prd):
        inp = tc.data.get("input")
        for s in _strings(inp):
            for v in real(s):
                yield Finding(tc.file, _line(tc, "input"), "classified-fixtures", f"{tc.id}: inline input holds the real-looking PII value '{v}'; use a synthetic form")
