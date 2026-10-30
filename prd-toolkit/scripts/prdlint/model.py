"""Load a PRD folder into a Prd model. Parsing only; rules live elsewhere."""
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .findings import Finding
from .markdown import Row, Section, frontmatter, sections, strip_code, tables
from .yamlload import LineDict, load_yaml


class NotAPrd(Exception):
    """The folder has no prd.md."""


@dataclass
class Ac:
    id: str
    text: str  # the criterion, without any "(removed in X.Y.Z)" prefix
    line: int
    removed: bool = False  # written "- AC-nnn.n (removed in X.Y.Z) <original text>"


@dataclass
class ReqBlock:
    id: str
    kind: str  # UJ | FR | NFR
    title: str
    file: str
    line: int
    status: str | None = None
    since: str | None = None
    acs: list[Ac] = field(default_factory=list)
    tests: list[tuple[str, str, int]] = field(default_factory=list)  # (T-id, level, line)
    tests_file: str | None = None
    source: str | None = None  # text after "Source:", the code location an as-built block was read from
    errors: list[tuple[str, int]] = field(default_factory=list)  # (code, line)
    lines: list[tuple[int, str]] = field(default_factory=list)  # body lines, heading excluded


@dataclass
class IndexRow:
    id: str
    title: str
    status: str
    file: str
    since: str
    line: int


@dataclass
class TestCase:
    __test__ = False  # not a pytest class
    id: str
    file: str
    line: int
    data: LineDict


ADOPTION_STATES = ("not started", "extracted", "confirmed", "adopted")


@dataclass
class AdoptionRow:
    area: str
    state: str
    boundary: list[str]  # the backticked globs of the Boundary cell
    line: int


@dataclass
class ErrorEntry:
    id: str
    line: int
    open: bool


@dataclass
class Harness:
    slots: list[tuple[str, int]] = field(default_factory=list)  # (slot name, line) in file order
    test_roots: list[str] | None = None  # the backticked list right after "Test roots:"; None when the text is absent
    test_roots_line: int = 0


@dataclass
class Testing:
    levels: dict[str, int] = field(default_factory=dict)
    environments: dict[str, int] = field(default_factory=dict)
    fixtures: dict[str, int] = field(default_factory=dict)
    signoffs: list[Row] = field(default_factory=list)
    harness: Harness = field(default_factory=Harness)


@dataclass
class Prd:
    root: Path
    frontmatter: dict[str, str]
    frontmatter_line: int
    docs: dict[str, str]
    sections: list[Section]
    blocks: list[ReqBlock]
    index: list[IndexRow]
    test_cases: list[TestCase]
    yaml: dict[str, Any]
    testing: Testing
    not_applicable: dict[str, tuple[str, int]]
    assumptions: list[Row]
    load_findings: list[Finding]
    adoption: list[AdoptionRow] | None = None  # None when section 8 has no table (Not applicable)
    errors_ledger: dict[str, ErrorEntry] = field(default_factory=dict)


_HEADING = re.compile(r"^#{1,3}\s")
_BLOCK = re.compile(r"^### ((?:UJ-\d+)|(?:FR-\d+)|(?:NFR-\d+))\s+(.*?)\s*$")
_STATUS = re.compile(r"^Status:\s*(.*?)\s*(?:\(since\s+([^)]*)\))?\s*$")
_AC = re.compile(r"^- (AC-\d+\.\d+)\s+(.*)$")
_AC_REMOVED = re.compile(r"^\(removed in \d+\.\d+\.\d+\)\s*")
_TEST = re.compile(r"(T-\d+\.\d+)\s*\[([^\]]+)\]")
_NA = re.compile(r"^\s*[-*]\s*Not applicable:\s*`([^`]+)`\s+[—–-]+\s+(.*?)\s*$")
_ERROR_HEAD = re.compile(r"^### (E-\d+)\b")
_RESOLUTION = re.compile(r"^Resolution:\s*(.*?)\s*$")
_SLOT = re.compile(r"^- \*\*([^*]+?)\.\*\*")
_MARKER = re.compile(r"\[NEEDS CLARIFICATION:[^\]]*\]")
_BACKTICKED = re.compile(r"`([^`]+)`")
_ITEM_LIST = re.compile(r"\s*(`[^`]+`(?:\s*,\s*`[^`]+`)*)")  # a comma-separated run of backticked items


def _field_lines(lines: list[tuple[int, str]], name: str) -> list[tuple[int, str]]:
    """The `name:` line of a block plus its indented continuation lines, as (line, text)."""
    out: list[tuple[int, str]] = []
    for i, (n, text) in enumerate(lines):
        if text.startswith(name + ":"):
            out.append((n, text[len(name) + 1 :].strip()))
            for n2, t2 in lines[i + 1 :]:
                if t2.startswith("  ") and t2.strip():
                    out.append((n2, t2.strip()))
                else:
                    break
            break
    return out


def _parse_block(m: re.Match, rel: str, n: int, body: list[tuple[int, str]]) -> ReqBlock:
    b = ReqBlock(m.group(1), m.group(1).split("-")[0], m.group(2), rel, n, lines=body)
    for _, text in _field_lines(body, "Status")[:1]:
        sm = _STATUS.match("Status: " + text)
        b.status, b.since = sm.group(1) or None, sm.group(2)
    # acceptance criteria: "- AC-nnn.n text" plus continuation lines indented two or more spaces
    cur: Ac | None = None
    for ln, text in body:
        am = _AC.match(text)
        if am:
            ac_text, n_removed = _AC_REMOVED.subn("", am.group(2).strip(), count=1)
            cur = Ac(am.group(1), ac_text, ln, removed=bool(n_removed))
            b.acs.append(cur)
        elif cur and text.startswith("  ") and text.strip():
            cur.text += " " + text.strip()
        else:
            cur = None
    for ln, text in _field_lines(body, "Errors"):  # continuation lines included
        head, paren, _ = text.partition("(")
        for code in (c.strip() for c in head.split(",")):
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", code):
                b.errors.append((code, ln))
        if paren:  # the parenthetical closes the code list
            break
    sl = _field_lines(body, "Source")
    b.source = " ".join(t for _, t in sl) or None
    tl = _field_lines(body, "Tests")
    for ln, text in tl:
        for tid, level in _TEST.findall(text):
            b.tests.append((tid, level.strip(), ln))
    fm = re.search(r"\((test-cases/[^)\s]+)\)", " ".join(t for _, t in tl))
    b.tests_file = fm.group(1) if fm else None
    return b


def _blocks_in(rel: str, text: str) -> list[ReqBlock]:
    lines = text.split("\n")
    stripped = strip_code(text).split("\n")
    blocks: list[ReqBlock] = []
    cur: tuple[re.Match, int] | None = None
    body: list[tuple[int, str]] = []

    def close():
        if cur:
            blocks.append(_parse_block(cur[0], rel, cur[1], body))

    for n, (orig, st) in enumerate(zip(lines, stripped), 1):
        if _HEADING.match(st):
            close()
            m = _BLOCK.match(orig) if _BLOCK.match(st) else None
            cur, body = ((m, n) if m else None), []
            continue
        if cur:
            body.append((n, orig))
    close()
    return blocks


def _table_under(secs: list[Section], title: str):
    for s in secs:
        if s.title.strip().lower() == title.lower():
            ts = tables(s.body)
            return ts[0] if ts else None
    return None


def _names(table) -> dict[str, int]:
    return {r.cells[0].strip("`"): r.line for r in table.rows} if table else {}


def _adoption(secs: list[Section]) -> list[AdoptionRow] | None:
    s8 = next((s for s in secs if s.number == 8), None)
    ts = tables(s8.body) if s8 else []
    if not ts:
        return None
    rows = []
    for r in ts[0].rows:
        c = r.cells + [""] * 3
        rows.append(AdoptionRow(c[0].strip("`"), c[1].strip("`"), _BACKTICKED.findall(c[2]), r.line))
    return rows


def _errors_ledger(text: str) -> dict[str, ErrorEntry]:
    """`### E-nnn` entries of errors.md; open unless a Resolution line carries a real value."""
    ledger: dict[str, ErrorEntry] = {}
    cur: ErrorEntry | None = None
    for n, (orig, st) in enumerate(zip(text.split("\n"), strip_code(text).split("\n")), 1):
        if _HEADING.match(st):
            m = _ERROR_HEAD.match(orig) if _ERROR_HEAD.match(st) else None
            cur = ErrorEntry(m.group(1), n, True) if m else None
            if cur:
                ledger.setdefault(cur.id, cur)
            continue
        rm = _RESOLUTION.match(orig) if cur else None
        if rm:
            v = rm.group(1).lower()
            cur.open = v in ("", "-") or v.startswith("open")
    return ledger


def _harness(body: list[tuple[int, str]]) -> Harness:
    h = Harness()
    for n, text in body:
        m = _SLOT.match(text)
        if not m:
            continue
        h.slots.append((m.group(1), n))
        if m.group(1) == "Layout" and "Test roots:" in text:
            tail = _MARKER.sub("", text.split("Test roots:", 1)[1])
            lst = _ITEM_LIST.match(tail)  # stops at the first text that is not another ", `item`"
            h.test_roots, h.test_roots_line = (_BACKTICKED.findall(lst.group(1)) if lst else []), n
    return h


def load(prd_dir: Path) -> Prd:
    prd_dir = Path(prd_dir).resolve()
    # the exact name: on a case-insensitive filesystem `prd.md` also "exists" as PRD.md
    names = {p.name: p for p in prd_dir.iterdir()} if prd_dir.is_dir() else {}
    if "prd.md" not in names or not names["prd.md"].is_file():
        other = next((n for n in names if n.lower() == "prd.md"), None)
        hint = f"; found {other}; the file name is lowercase prd.md" if other else ""
        raise NotAPrd(f"{prd_dir}: no prd.md{hint}")
    findings: list[Finding] = []
    docs = {p.relative_to(prd_dir).as_posix(): p.read_text(encoding="utf-8") for p in sorted(prd_dir.rglob("*.md"))}
    fm, fm_line = frontmatter(docs["prd.md"])
    secs = sections(docs["prd.md"])

    blocks: list[ReqBlock] = []
    for rel in [r for r in docs if re.fullmatch(r"features/[^/]+\.md", r)] + (["nfr.md"] if "nfr.md" in docs else []):
        blocks += _blocks_in(rel, docs[rel])

    def sec(num: int):
        return next((s for s in secs if s.number == num), None)

    index: list[IndexRow] = []
    s11 = sec(11)
    for t in tables(s11.body) if s11 else []:
        for r in t.rows:
            c = [x.strip("`") for x in r.cells] + [""] * 5
            index.append(IndexRow(c[0], c[1], c[2], c[3], c[4], r.line))
    assumptions: list[Row] = []
    s12 = sec(12)
    for t in tables(s12.body) if s12 else []:
        assumptions += t.rows
    na: dict[str, tuple[str, int]] = {}
    s1 = sec(1)
    for n, text in s1.body if s1 else []:
        m = _NA.match(text)
        if m:
            na[m.group(1)] = (m.group(2), n)

    test_cases: list[TestCase] = []
    for p in sorted((prd_dir / "test-cases").glob("*.yaml")):
        rel = p.relative_to(prd_dir).as_posix()
        data, fs = load_yaml(p, rel)
        findings += fs
        for tid, val in (data or {}).items():
            if not isinstance(val, LineDict):
                findings.append(Finding(rel, data.key_lines[tid], "sufficiency", f"{tid}: a test case must be a mapping"))
                val = LineDict()
                val.line = data.key_lines[tid]
            test_cases.append(TestCase(str(tid), rel, data.key_lines[tid], val))

    yml: dict[str, Any] = {}
    for p in sorted((prd_dir / "contracts").rglob("*.yaml")):
        rel = p.relative_to(prd_dir).as_posix()
        data, fs = load_yaml(p, rel)
        findings += fs
        if data is not None:
            yml[rel] = data

    testing = Testing()
    if "testing.md" in docs:
        tsecs = sections(docs["testing.md"])
        testing.levels = _names(_table_under(tsecs, "Levels"))
        testing.environments = _names(_table_under(tsecs, "Environments"))
        testing.fixtures = _names(_table_under(tsecs, "Fixtures"))
        so = _table_under(tsecs, "Sign-offs")
        testing.signoffs = so.rows if so else []
        hs = next((x for x in tsecs if x.title.strip().lower() == "harness"), None)
        testing.harness = _harness(hs.body) if hs else Harness()

    return Prd(prd_dir, fm, fm_line, docs, secs, blocks, index, test_cases, yml, testing, na, assumptions, findings,
               adoption=_adoption(secs), errors_ledger=_errors_ledger(docs.get("errors.md", "")))


def repo_root(path: Path) -> Path:
    """`git rev-parse --show-toplevel` from `path`; `path` itself on any failure (including no git)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=10, check=True
        ).stdout.strip()
        return Path(out) if out else path
    except (OSError, subprocess.SubprocessError):
        return path
