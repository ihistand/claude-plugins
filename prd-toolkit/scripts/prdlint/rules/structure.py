"""Structure rules: frontmatter, sections, placeholders, vague words, markers, assumptions, glossary."""
import re
from collections.abc import Iterator

from ..deps import require
from ..findings import Finding
from ..markdown import strip_code, tables
from ..model import Prd
from ..registry import rule

SECTION_TITLES = [
    "Metadata & stack", "Summary & goals", "Glossary", "Architecture", "Standards registry",
    "Skills registry", "Contract types", "Adoption map", "Versioning", "Design & UI",
    "Requirement index", "Assumptions index", "Open questions", "Changelog",
]
MANDATORY = ["features/", "test-cases/", "nfr.md", "testing.md", "operations.md", "errors.md", "contracts/errors.yaml"]
# slot name -> alternatives that fill it
OPTIONAL = {
    "contracts/openapi.yaml": ["contracts/openapi.yaml"],
    "contracts/schema.sql": ["contracts/schema.sql"],
    "contracts/events.md": ["contracts/events.md", "contracts/asyncapi.yaml"],
    "contracts/permissions.yaml": ["contracts/permissions.yaml"],
    "contracts/config.yaml": ["contracts/config.yaml"],
    "contracts/data-classification.yaml": ["contracts/data-classification.yaml"],
    "contracts/dependencies/": ["contracts/dependencies/"],
    "contracts/fixtures/": ["contracts/fixtures/"],
}
STATUSES = ("Draft", "In review", "Approved")


def prose(prd: Prd) -> Iterator[tuple[str, int, str]]:
    """Every markdown line of the PRD as (file, line, text), with code blocks and spans blanked."""
    for rel, text in prd.docs.items():
        for n, line in enumerate(strip_code(text).split("\n"), 1):
            yield rel, n, line


def _status(prd: Prd) -> str:
    return prd.frontmatter.get("status", "")


def _fm_line(prd: Prd, key: str) -> int:
    for n, line in enumerate(prd.docs["prd.md"].split("\n"), 1):
        if line.startswith(key + ":"):
            return n
    return max(prd.frontmatter_line, 1)


def _exists(prd: Prd, path: str) -> bool:
    p = prd.root / path
    if path.endswith("/"):
        if path == "features/":
            return any(prd.root.glob("features/*.md"))
        if path == "test-cases/":
            return any(prd.root.glob("test-cases/*.yaml"))
        return p.is_dir() and any(f.is_file() for f in p.rglob("*"))
    return p.is_file()


@rule("frontmatter")
def frontmatter(prd: Prd):
    fm = prd.frontmatter
    f = lambda key, msg: Finding("prd.md", _fm_line(prd, key), "frontmatter", msg)  # noqa: E731
    checks = {
        "prd": (lambda v: re.fullmatch(r"[a-z][a-z0-9-]*", v) and v == prd.root.name, f"must be a lowercase slug equal to the folder name '{prd.root.name}'"),
        "version": (lambda v: re.fullmatch(r"\d+\.\d+\.\d+", v), "must be X.Y.Z, digits only"),
        "status": (lambda v: v in STATUSES, "must be Draft, In review or Approved"),
        "owner": (lambda v: bool(v), "must not be empty"),
        "updated": (lambda v: re.fullmatch(r"\d{4}-\d{2}-\d{2}", v), "must be YYYY-MM-DD"),
    }
    for key, (ok, msg) in checks.items():
        if key not in fm:
            yield f(key, f"missing key '{key}'")
        elif not ok(fm[key]):
            yield f(key, f"'{key}: {fm[key]}' {msg}")
    if (prd.root / "contracts/schema.sql").is_file():
        dialect = fm.get("sql-dialect")
        if not dialect:
            yield f("sql-dialect", "missing key 'sql-dialect' (required because contracts/schema.sql exists)")
        else:
            sqlglot = require("sqlglot", "sqlglot")
            try:
                sqlglot.Dialect.get_or_raise(dialect)
            except Exception as exc:
                yield f("sql-dialect", f"'sql-dialect: {dialect}' is not a sqlglot dialect ({exc})")


@rule("sections")
def sections(prd: Prd):
    actual = [(s.number, s.title) for s in prd.sections]
    expected = list(enumerate(SECTION_TITLES, 1))
    line_of = {(s.number, s.title): s.line for s in prd.sections}
    for num, title in expected:
        if (num, title) not in actual:
            yield Finding("prd.md", 1, "sections", f"missing section '## {num}. {title}'")
    present = [e for e in expected if e in actual]
    if [a for a in actual if a in expected] != present:
        yield Finding("prd.md", 1, "sections", "sections are out of order")
    for a in actual:
        if a not in expected:
            yield Finding("prd.md", line_of[a], "sections", f"unexpected section '## {a[0]}. {a[1]}'")
    na = {k.rstrip("/") + ("/" if k.endswith("/") else ""): v for k, v in prd.not_applicable.items()}
    for path in MANDATORY:
        hit = na.get(path) or na.get(path.rstrip("/"))
        if hit:
            yield Finding("prd.md", hit[1], "sections", f"mandatory '{path}' cannot be marked not applicable")
        elif not _exists(prd, path):
            yield Finding(path.rstrip("/"), 0, "sections", f"mandatory '{path}' is missing")
    for slot, alts in OPTIONAL.items():
        if any(_exists(prd, a) for a in alts):
            continue
        if not any(a in na or a.rstrip("/") in na for a in alts):
            yield Finding("prd.md", 1, "sections", f"'{slot}' is absent and section 1 has no 'Not applicable: `{slot}` — reason' line")


_PLACEHOLDER = re.compile(r"\b(?:TBD|TODO)\b|\?\?\?|<(?!https?://)[A-Za-z][^<>\n]*>")
_SCALAR_PLACEHOLDER = re.compile(r"\b(?:TBD|TODO)\b|\?\?\?")


def _scalars(node, line: int) -> Iterator[tuple[int, str]]:
    if isinstance(node, dict):
        for k, v in node.items():
            kl = getattr(node, "key_lines", {}).get(k, line)
            yield from _scalars(v, kl)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _scalars(v, line)
    elif isinstance(node, str):
        yield line, node


@rule("placeholder")
def placeholder(prd: Prd):
    for rel, n, text in prose(prd):
        m = _PLACEHOLDER.search(text)
        if m:
            yield Finding(rel, n, "placeholder", f"placeholder '{m.group(0)}' in prose")
    sources = [(rel, data) for rel, data in prd.yaml.items()] + [(tc.file, tc.data) for tc in prd.test_cases]
    for rel, data in sources:
        for n, value in _scalars(data, 1):
            m = _SCALAR_PLACEHOLDER.search(value)
            if m:
                yield Finding(rel, n, "placeholder", f"placeholder '{m.group(0)}' in a YAML value")


_VAGUE = re.compile(r"\b(fast|secure|scalable|robust|intuitive|seamless|user-friendly)\b", re.I)
_ID = re.compile(r"\b(?:AC|FR|NFR|UJ|T)-\d+(?:\.\d+)?\b")


def _removed_ac_lines(b) -> set[int]:
    """Line numbers of a block's removed ACs, continuation lines included."""
    out: set[int] = set()
    starts = {a.line for a in b.acs if a.removed}
    on = False
    for n, text in b.lines:
        if n in starts:
            on = True
        elif not (on and text.startswith("  ") and text.strip()):
            on = False
        if on:
            out.add(n)
    return out


@rule("vague-word")
def vague_word(prd: Prd):
    def check(file, n, text):
        m = _VAGUE.search(text)
        if m and not re.search(r"\d", _ID.sub("", text)):
            return Finding(file, n, "vague-word", f"'{m.group(1)}' with no measurable number on the line")

    for b in prd.blocks:
        if b.kind == "NFR":
            stripped = strip_code("\n".join(t for _, t in b.lines)).split("\n")
            retired = _removed_ac_lines(b)
            items = [(n, t) for (n, _), t in zip(b.lines, stripped) if n not in retired]
        else:
            items = [(a.line, a.text) for a in b.acs if not a.removed]
        for n, t in items:
            f = check(b.file, n, t)
            if f:
                yield f


@rule("markers-open")
def markers_open(prd: Prd):
    if _status(prd) not in ("In review", "Approved"):
        return
    for rel, n, text in prose(prd):
        if "[NEEDS CLARIFICATION" in text:
            yield Finding(rel, n, "markers-open", f"[NEEDS CLARIFICATION] left open while status is {_status(prd)}")


_MARKER = re.compile(r"\[ASSUMPTION\b(?: (A-\d+):)?")
_ASSUMPTION_STATUS = ("open", "confirmed", "corrected")


@rule("assumption-indexed")
def assumption_indexed(prd: Prd):
    rows = {r.cells[0].strip("`"): r for r in prd.assumptions if r.cells}
    for rel, n, text in prose(prd):
        for m in _MARKER.finditer(text):
            if not m.group(1):
                yield Finding(rel, n, "assumption-indexed", "[ASSUMPTION] marker has no A-nn id")
            elif m.group(1) not in rows:
                yield Finding(rel, n, "assumption-indexed", f"{m.group(1)} has no row in section 12")
    for aid, r in rows.items():
        status = r.cells[2].strip("`") if len(r.cells) > 2 else ""
        if status not in _ASSUMPTION_STATUS:
            yield Finding("prd.md", r.line, "assumption-indexed", f"{aid}: status '{status}' must be open, confirmed or corrected")
        elif status == "open" and _status(prd) == "Approved":
            yield Finding("prd.md", r.line, "assumption-indexed", f"{aid} is open while the PRD is Approved")


@rule("open-questions-empty")
def open_questions_empty(prd: Prd):
    if _status(prd) != "Approved":
        return
    sec = next((s for s in prd.sections if s.number == 13), None)
    for n, text in sec.body if sec else []:
        if text.strip() and text.strip() != "None.":
            yield Finding("prd.md", n, "open-questions-empty", "section 13 must be 'None.' when the PRD is Approved")
            return


@rule("glossary-synonym")
def glossary_synonym(prd: Prd):
    s3 = next((s for s in prd.sections if s.number == 3), None)
    if not s3:
        return
    skip = {s3.line} | {n for n, _ in s3.body}
    banned: list[tuple[str, re.Pattern]] = []
    for t in tables(s3.body):
        for r in t.rows:
            if len(r.cells) < 3:
                continue
            for word in (w.strip().strip("`") for w in r.cells[2].split(",")):
                if word and word.lower() not in ("-", "—", "none"):
                    banned.append((r.cells[0], re.compile(rf"\b{re.escape(word)}s?\b", re.I)))
    for rel, n, text in prose(prd):
        if rel == "prd.md" and n in skip:
            continue
        for term, pat in banned:
            m = pat.search(text)
            if m:
                yield Finding(rel, n, "glossary-synonym", f"'{m.group(0)}' is a banned synonym; use '{term}'")
