"""Load a PRD folder into a Prd model. Parsing only; rules live elsewhere."""
import re
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
    text: str
    line: int


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


@dataclass
class Testing:
    levels: dict[str, int] = field(default_factory=dict)
    environments: dict[str, int] = field(default_factory=dict)
    fixtures: dict[str, int] = field(default_factory=dict)
    signoffs: list[Row] = field(default_factory=list)


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


_HEADING = re.compile(r"^#{1,3}\s")
_BLOCK = re.compile(r"^### ((?:UJ-\d+)|(?:FR-\d+)|(?:NFR-\d+))\s+(.*?)\s*$")
_STATUS = re.compile(r"^Status:\s*(.*?)\s*(?:\(since\s+([^)]*)\))?\s*$")
_AC = re.compile(r"^- (AC-\d+\.\d+)\s+(.*)$")
_TEST = re.compile(r"(T-\d+\.\d+)\s*\[([^\]]+)\]")
_NA = re.compile(r"^\s*[-*]\s*Not applicable:\s*`([^`]+)`\s+[—–-]+\s+(.*?)\s*$")
_FIELD = re.compile(r"^(Status|Flow|Acceptance \(EARS\)|Errors|Edge cases|Tests|Traces):")


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
            cur = Ac(am.group(1), am.group(2).strip(), ln)
            b.acs.append(cur)
        elif cur and text.startswith("  ") and text.strip():
            cur.text += " " + text.strip()
        else:
            cur = None
    for ln, text in _field_lines(body, "Errors")[:1]:
        head = text.split("(")[0]
        for code in (c.strip() for c in head.split(",")):
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", code):
                b.errors.append((code, ln))
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


def load(prd_dir: Path) -> Prd:
    prd_dir = Path(prd_dir)
    if not (prd_dir / "prd.md").is_file():
        raise NotAPrd(f"{prd_dir}: no prd.md")
    findings: list[Finding] = []
    docs = {p.relative_to(prd_dir).as_posix(): p.read_text() for p in sorted(prd_dir.rglob("*.md"))}
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

    return Prd(prd_dir, fm, fm_line, docs, secs, blocks, index, test_cases, yml, testing, na, assumptions, findings)
