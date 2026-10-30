"""Context packs: the slice of a PRD one task needs, and nothing else."""
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from itertools import groupby
from pathlib import Path

from .deps import require
from .markdown import Row, sections, tables
from .model import ADOPTION_FILE, UNMIGRATED, Prd, ReqBlock, _field_lines
from .rules.contracts import _custom_types

yaml = require("yaml", "pyyaml")

PARTS = ("Header", "Stack", "Glossary", "Requirements", "Code", "Levels", "Cited", "Known defects", "Open questions", "History")
PARTS_REPO = ("Header", "Stack", "Areas")
MODES = ("decide", "implement")

_NFR = re.compile(r"(?<![\w-])NFR-\d+(?![\w-])")
_UJ = re.compile(r"(?<![\w-])UJ-\d+(?![\w-])")
_ASSUMPTION = re.compile(r"\[ASSUMPTION\b(?: (A-\d+):)?")
_TYPED = re.compile(r"(?<![\w-])([A-Za-z][\w-]*):([^\s`'\",;()\[\]]+)")  # <type>:<name>
_FEATURE = re.compile(r"features/([^/]+)\.md")
_SUB_ID = re.compile(r"(?:AC|T)-\d+\.\d+|E-\d+")
_SOURCE_REF = re.compile(r"(?P<path>[^\s@]+):(?P<line>\d+)\s+@(?P<sha>[0-9a-fA-F]{4,40})")


@dataclass
class Item:
    part: str
    id: str | None
    file: str  # PRD-relative; repo-relative for Code items
    line: int | None
    text: str
    stale: bool = False


class ContextError(Exception):
    """A usage or input error: exit 2, nothing on stdout."""


def _word(term: str, flags: int = 0) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", flags)


def _trim(lines: list[str]) -> str:
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return "\n".join(lines)


def _lines(prd: Prd, rel: str) -> list[str]:
    return prd.docs[rel].split("\n")


def _section(prd: Prd, number: int):
    return next((s for s in prd.sections if s.number == number), None)


def _table_text(prd: Prd, rows: list[Row], first_row: int) -> str:
    """A prd.md table's header and separator (the two lines above `first_row`) followed by `rows`."""
    lines = _lines(prd, "prd.md")
    return "\n".join(lines[first_row - 3 : first_row - 1] + [lines[r.line - 1] for r in rows])


def _plain(v):
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    return v


def _dump(key, value) -> str:
    return yaml.safe_dump({key: _plain(value)}, sort_keys=False, allow_unicode=True).rstrip("\n")


def _none(part: str, file: str) -> Item:
    return Item(part, None, file, None, "None.")


def _block_text(prd: Prd, b: ReqBlock, area: str) -> str:
    heading = _lines(prd, b.file)[b.line - 1]
    m = _FEATURE.fullmatch(b.file)
    if m and m.group(1) != area:
        heading += f" (area: {m.group(1)})"
    return _trim([heading] + [t for _, t in b.lines])


def _areas_known(prd: Prd) -> list[str]:
    known = [r.area for r in prd.adoption or []]
    return known + [m.group(1) for rel in prd.docs if (m := _FEATURE.fullmatch(rel)) and m.group(1) not in known]


def _sub_id_hint(prd: Prd, sid: str) -> str:
    """For an AC, T or E ID passed to --req: name the requirement it belongs to."""
    if sid.startswith("E-"):
        e = prd.errors_ledger.get(sid)
        owners = list(dict.fromkeys(t for t, _ in e.touches)) if e else []
    else:
        owners = [b.id for b in prd.blocks if any(a.id == sid for a in b.acs) or any(t == sid for t, _, _ in b.tests)]
    return f"pass the requirement ID ({', '.join(owners) or 'UJ-, FR- or NFR-nnn'}), not {sid}"


def _select(prd: Prd, area: str, req: list[str] | None) -> list[ReqBlock]:
    if req is None:
        return [b for b in prd.blocks if b.file == f"features/{area}.md" and b.kind in ("UJ", "FR")]
    by_id = {}
    for b in prd.blocks:
        by_id.setdefault(b.id, b)
    unknown = [i for i in req if i not in by_id]
    if unknown:
        hints = [_sub_id_hint(prd, i) for i in unknown if _SUB_ID.fullmatch(i)]
        raise ContextError(f"no requirement block defines {', '.join(unknown)}" + "".join(f"; {h}" for h in hints))
    wanted = set(req)
    for i in req:
        for _, text in _field_lines(by_id[i].lines, "Traces"):
            wanted |= {u for u in _UJ.findall(text) if u in by_id}
    return [b for b in by_id.values() if b.id in wanted]


def _stack(prd: Prd) -> list[Item]:
    items = []
    for number in (1, 4):
        s = _section(prd, number)
        if s:
            heading = "#" + _lines(prd, "prd.md")[s.line - 1]  # demoted under the part heading
            items.append(Item("Stack", None, "prd.md", s.line, _trim([heading] + [t for _, t in s.body])))
    return items or [_none("Stack", "prd.md")]


def _glossary(prd: Prd, text: str) -> list[Item]:
    s3 = _section(prd, 3)
    ts = tables(s3.body) if s3 else []
    if not ts or not ts[0].rows:
        return [_none("Glossary", "prd.md")]
    hits = [r for r in ts[0].rows if r.cells and r.cells[0].strip("`").strip()
            and _word(r.cells[0].strip("`").strip(), re.I).search(text)]
    first = ts[0].rows[0].line
    return [Item("Glossary", None, "prd.md", first - 2, _table_text(prd, hits, first))] if hits else [_none("Glossary", "prd.md")]


def _cited(prd: Prd, area: str, blocks: list[ReqBlock], text: str) -> list[Item]:
    items: list[Item] = []
    chosen = {b.id for b in blocks}
    nfrs = set(_NFR.findall(text)) - chosen
    seen: set[str] = set()
    for b in prd.blocks:
        if b.id in nfrs and b.id not in seen:
            seen.add(b.id)
            items.append(Item("Cited", b.id, b.file, b.line, _block_text(prd, b, area)))

    codes = {c for b in blocks for c, _ in b.errors}
    errors = prd.yaml.get("contracts/errors.yaml")
    errors = errors if isinstance(errors, dict) else {}
    for code in [c for c in errors if c in codes] + sorted(codes - set(errors)):
        if code in errors:
            items.append(Item("Cited", code, "contracts/errors.yaml", errors.key_lines.get(code), _dump(code, errors[code])))
        else:
            items.append(Item("Cited", code, "contracts/errors.yaml", None, f"{code}: not in contracts/errors.yaml"))

    typed = {(m.group(1), m.group(2).rstrip(".:")) for m in _TYPED.finditer(text)}
    for kind, _, files, _ in _custom_types(prd):  # resolved as contracts-valid resolves custom_items
        for f in files:
            data = prd.yaml.get(f)
            for key in data if isinstance(data, dict) else []:
                tid = f"{kind}:{key}"
                if (kind, str(key)) in typed and tid not in seen:
                    seen.add(tid)
                    items.append(Item("Cited", tid, f, data.key_lines.get(key), _dump(key, data[key])))

    aids = {m.group(1) for m in _ASSUMPTION.finditer(text) if m.group(1)}
    if prd.assumptions:
        first = prd.assumptions[0].line
        for r in prd.assumptions:
            aid = r.cells[0].strip("`") if r.cells else ""
            if aid in aids and aid not in seen:
                seen.add(aid)
                items.append(Item("Cited", aid, "prd.md", r.line, _table_text(prd, [r], first)))
    return items or [_none("Cited", "prd.md")]


def _defects(prd: Prd, ids: set[str]) -> list[Item]:
    items, loose = [], 0
    lines = _lines(prd, "errors.md") if "errors.md" in prd.docs else []
    for e in prd.errors_ledger.values():
        if not e.open:
            continue
        if not e.touches:
            loose += 1
        elif any(t in ids for t, _ in e.touches):
            items.append(Item("Known defects", e.id, "errors.md", e.line, _trim(lines[e.line - 1 : e.end])))
    return items + [Item("Known defects", None, "errors.md", None, f"{loose} open errors.md entries name no requirement")]


def _questions(prd: Prd, patterns: list[re.Pattern]) -> list[Item]:
    s13 = _section(prd, 13)
    found: list[tuple[int, list[str]]] = []
    for n, text in s13.body if s13 else []:
        if text.startswith("- "):
            found.append((n, [text]))
        elif found and text.startswith((" ", "\t")) and text.strip() and found[-1][0] + len(found[-1][1]) == n:
            found[-1][1].append(text)
    items = [Item("Open questions", None, "prd.md", n, "\n".join(q)) for n, q in found
             if any(p.search("\n".join(q)) for p in patterns)]
    rest = len(found) - len(items)
    return items + [Item("Open questions", None, "prd.md", None, f"{rest} other open questions in prd.md §13")]


def _history(prd: Prd, area: str) -> list[Item]:
    s14 = _section(prd, 14)
    ts = tables(s14.body) if s14 else []
    lines = _lines(prd, "prd.md")
    slug = _word(area)
    rows = [r for r in (ts[0].rows if ts else []) if slug.search(lines[r.line - 1])][-3:]
    if not rows:
        return [_none("History", "prd.md")]
    first = ts[0].rows[0].line
    return [Item("History", None, "prd.md", first - 2, _table_text(prd, rows, first))]


def _areas(prd: Prd) -> list[Item]:
    if prd.adoption is not None:
        items = [Item("Areas", r.area, ADOPTION_FILE, r.line,
                      f"- {r.area} ({r.state}; Boundary: {', '.join(r.boundary)})" if r.boundary else f"- {r.area} ({r.state})")
                 for r in prd.adoption]
    else:
        items = [Item("Areas", m.group(1), rel, None, f"- {m.group(1)}") for rel in prd.docs if (m := _FEATURE.fullmatch(rel))]
    return items or [_none("Areas", ADOPTION_FILE if prd.adoption is not None else "prd.md")]


def _header(prd: Prd, area: str | None, mode: str, display: str, body: list[Item]) -> Item:
    n = len(render_text(body).encode())
    size = f"pack {n:,} bytes (~{n / 4 / 1000:.1f}k tokens, bytes / 4); prd.md {(prd.root / 'prd.md').stat().st_size:,}"
    lines = [f"PRD: {display or prd.root.as_posix()} version {prd.frontmatter.get('version', '-')} mode {mode}"]
    if area is not None:
        feature = prd.root / f"features/{area}.md"
        if feature.is_file():
            size += f"; features/{area}.md {feature.stat().st_size:,}"
        row = next((r for r in prd.adoption or [] if r.area == area), None)
        state = f"{row.state}; Boundary: {', '.join(row.boundary)}" if row and row.boundary else (row.state if row else "-")
        lines.append(f"Area: {area} ({state})")
    return Item("Header", None, "prd.md", None, "\n".join(lines + [size]))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    """A git call in `root`; None when git cannot run or times out."""
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None


def _stale_reason(root: Path, path: str, sha: str, target: Path) -> str | None:
    ok = _git(root, "cat-file", "-e", f"{sha}^{{commit}}")
    if ok is None or ok.returncode != 0:
        return f"unknown commit {sha}"
    if not target.is_file():
        return "file missing"
    log = _git(root, "log", "--format=%H", f"{sha}..HEAD", "--", path)
    if log is None or log.returncode != 0:
        return f"cannot compare with {sha}"
    if log.stdout.strip():
        return f"changed since {sha}"
    diff = _git(root, "diff", "--quiet", "HEAD", "--", path)
    if diff is None or diff.returncode not in (0, 1):
        return f"cannot compare with {sha}"
    return "uncommitted changes" if diff.returncode else None


def _excerpt(root: Path, block: ReqBlock, path: str, line: int, sha: str, context: int) -> Item:
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()):
        target = root / "<outside repository>"
    reason = _stale_reason(root, path, sha, target)
    shown: list[str] = []
    if target.is_file():
        rows = target.read_bytes().decode("utf-8", errors="replace").split("\n")
        rows = [r.rstrip("\r") for r in (rows[:-1] if rows and rows[-1] == "" else rows)]
        if reason is None and line > len(rows):
            reason = f"line {line} is past the end ({len(rows)} lines)"
        lo, hi = max(1, line - context), min(len(rows), line + context)
        shown = [f"{n:>5}  {rows[n - 1]}" for n in range(lo, hi + 1)]
    head = [f"### {path}:{line} @{sha}"]
    if reason:
        head.append(f"STALE: {reason}; the cited line may have moved")
    return Item("Code", block.id, path, line, "\n".join(head + shown), stale=bool(reason))


def _code(blocks: list[ReqBlock], area: str, root: Path, context: int) -> list[Item]:
    items, seen = [], set()
    for b in blocks:
        if b.source and not _SOURCE_REF.search(b.source):
            line = _field_lines(b.lines, "Source")[0][0]
            items.append(Item("Code", b.id, b.file, line,
                              f"### {b.id} Source: {b.source}\nSTALE: Source not in <path>:<line> @<sha> form", stale=True))
        for m in _SOURCE_REF.finditer(b.source or ""):
            ref = (m["path"], int(m["line"]), m["sha"])
            if ref not in seen:
                seen.add(ref)
                items.append(_excerpt(root, b, *ref[:2], ref[2], context))
    return items or [_none("Code", f"features/{area}.md")]


def _levels(prd: Prd) -> list[Item]:
    if "testing.md" not in prd.docs:
        return [_none("Levels", "testing.md")]
    sec = next((s for s in sections(prd.docs["testing.md"]) if s.title.strip().lower() == "levels"), None)
    ts = tables(sec.body) if sec else []
    if not ts or not ts[0].rows:
        return [_none("Levels", "testing.md")]
    lines = _lines(prd, "testing.md")
    first = ts[0].rows[0].line
    text = "\n".join(lines[first - 3 : first - 1] + [lines[r.line - 1] for r in ts[0].rows])
    return [Item("Levels", None, "testing.md", first - 2, text)]


def _in_git_work_tree(path: Path) -> bool:
    r = _git(path, "rev-parse", "--is-inside-work-tree")
    return r is not None and r.returncode == 0 and r.stdout.strip() == "true"


def build_pack(prd: Prd, area: str | None, req: list[str] | None, mode: str = "decide",
               context: int = 20, repo_root: Path | None = None, display: str = "") -> list[Item]:
    """The pack's items, in part order. Raises ContextError for every exit-2 condition."""
    if prd.adoption_unmigrated:
        raise ContextError(f"{prd.root.as_posix()}/prd.md: {UNMIGRATED}")
    if mode not in MODES:
        raise ContextError(f"--for must be one of {', '.join(MODES)}")
    if req is not None and not req:
        raise ContextError("--req names no ID")
    if area is None:
        if req is not None:
            raise ContextError("--req needs --area")
        if mode == "implement":
            raise ContextError("--for implement needs --area")
        body = _stack(prd) + _areas(prd)
        return [_header(prd, None, mode, display, body)] + body
    known = _areas_known(prd)
    if area not in known:
        raise ContextError(f"unknown area '{area}'; areas: {', '.join(known) or 'none'}")

    if mode == "implement" and not _in_git_work_tree(prd.root):
        raise ContextError("--for implement needs the PRD inside a git work tree")
    blocks = _select(prd, area, req)
    texts = [_block_text(prd, b, area) for b in blocks]
    text = "\n".join(texts)
    ids = {b.id for b in blocks}
    requirements = [Item("Requirements", b.id, b.file, b.line, t) for b, t in zip(blocks, texts)]
    patterns = [_word(i) for i in sorted(ids | {ac.id for b in blocks for ac in b.acs})] + [_word(area)]
    implement = (_code(blocks, area, repo_root or prd.root, context) + _levels(prd)) if mode == "implement" else []
    body = (_stack(prd) + _glossary(prd, text) + (requirements or [_none("Requirements", f"features/{area}.md")])
            + implement + _cited(prd, area, blocks, text) + _defects(prd, ids) + _questions(prd, patterns) + _history(prd, area))
    return [_header(prd, area, mode, display, body)] + body


def render_text(items: list[Item]) -> str:
    """Each part under a `## <part>` heading, its items separated by a blank line (Areas: one line each)."""
    return "\n".join(f"## {part}\n\n" + ("\n" if part == "Areas" else "\n\n").join(i.text for i in group) + "\n"
                     for part, group in groupby(items, key=lambda i: i.part))


def render_json(items: list[Item]) -> str:
    return json.dumps([asdict(i) for i in items], indent=2, ensure_ascii=False) + "\n"
