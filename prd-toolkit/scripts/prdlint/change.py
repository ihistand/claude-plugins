"""The change bookkeeping behind prd_change.py: next IDs and the PRD digest (bump, record and approve join them)."""
import hashlib
import re
from pathlib import Path

from . import model
from .markdown import tables

REVIEW_FILE = ".prd-review.json"
_NUM = re.compile(r"(?:UJ|FR|NFR)-(\d+)")
_KIND = re.compile(r"^(?:(UJ|FR|NFR)|(AC|T)-(\d+))$")
_FM_DROP = re.compile(r"^(?:version|updated):")


class ChangeError(Exception):
    """A change the script refuses; the CLI prints `refused: <message>` and exits 1."""


def _section(prd: model.Prd, number: int):
    return next((s for s in prd.sections if s.number == number), None)


def _table_cells(prd: model.Prd, number: int) -> list[list[str]]:
    s = _section(prd, number)
    return [r.cells for t in (tables(s.body) if s else []) for r in t.rows]


def _max(numbers) -> int:
    return max(numbers, default=0)


def next_id(prd: model.Prd, kind: str) -> str:
    """The next free ID of `kind` (FR, NFR, UJ, AC-<nnn> or T-<nnn>); reads only, never writes."""
    m = _KIND.match(kind)
    if not m:
        raise ChangeError(f"unknown kind {kind}; use FR, NFR, UJ, AC-<nnn> or T-<nnn>")
    changelog_ids = " ".join(c[3] for c in _table_cells(prd, 14) if len(c) > 3)
    if m.group(1) == "UJ":
        nums = [int(b.id[3:]) for b in prd.blocks if b.kind == "UJ"]
        nums += [int(r.id[3:]) for r in prd.index if r.id.startswith("UJ-") and r.id[3:].isdigit()]
        nums += [int(n) for n in re.findall(r"UJ-(\d+)", changelog_ids)]
        return f"UJ-{_max(nums) + 1:02d}"
    if m.group(1):  # FR or NFR: one sequence across both kinds
        nums = [int(b.id.split("-")[1]) for b in prd.blocks if b.kind in ("FR", "NFR")]
        nums += [int(r.id.split("-")[1]) for r in prd.index if r.id.startswith(("FR-", "NFR-")) and r.id.split("-")[1].isdigit()]
        nums += [int(n) for n in re.findall(r"(?:FR|NFR)-(\d+)", changelog_ids)]
        return f"{m.group(1)}-{_max(nums) + 1:03d}"
    nnn = m.group(3)
    block = next((b for b in prd.blocks if b.kind in ("FR", "NFR") and int(b.id.split("-")[1]) == int(nnn)), None)
    if block is None:
        raise ChangeError(f"no block FR-{nnn} or NFR-{nnn}")
    n = int(nnn)
    if m.group(2) == "AC":
        return f"AC-{n:03d}.{_max(int(a.id.split('.')[1]) for a in block.acs) + 1}"
    ids = [t[0] for t in block.tests] + [c.id for c in prd.test_cases] + re.findall(r"T-\d+\.\d+", changelog_ids)
    found = (re.fullmatch(r"T-(\d+)\.(\d+)", i) for i in ids)
    return f"T-{n:03d}.{_max(int(f.group(2)) for f in found if f and int(f.group(1)) == n) + 1}"


def _listed(root: Path) -> list[Path]:
    """Every file under root, found on disk; git is not asked, so an ignored folder still hashes and no repository is needed."""
    return [p for p in root.rglob("*") if p.is_file()]


def _skipped(rel: str) -> bool:
    parts = rel.split("/")
    if parts[-1] == REVIEW_FILE and len(parts) == 1:
        return True
    return any(p == "__pycache__" or (p.startswith(".") and p != ".gitkeep") for p in parts)


def _normalized_prd_md(prd: model.Prd) -> str:
    """prd.md without the frontmatter version: and updated: lines and the §11 and §14 table rows."""
    drop: set[int] = set()
    for number in (11, 14):
        s = _section(prd, number)
        for t in tables(s.body) if s else []:
            drop.update(r.line for r in t.rows)
    lines = prd.docs["prd.md"].split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                break
            if _FM_DROP.match(lines[i]):
                drop.add(i + 1)
    return "\n".join(ln for n, ln in enumerate(lines, 1) if n not in drop)


def digest(prd_root: Path) -> str:
    """SHA-256 hex over the PRD folder's files in sorted relative-path order (`path\\0content\\0`), prd.md normalized."""
    root = Path(prd_root).resolve()
    prd = model.load(root)
    h = hashlib.sha256()
    rels = {p.relative_to(root).as_posix(): p for p in _listed(root) if p.is_file()}
    for rel in sorted(r for r in rels if not _skipped(r)):
        content = _normalized_prd_md(prd).encode("utf-8") if rel == "prd.md" else rels[rel].read_bytes()
        h.update(rel.encode("utf-8") + b"\0" + content + b"\0")
    return h.hexdigest()
