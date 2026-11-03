"""The items an adoption area asks its owner to confirm: requirements, bugs, questions and markers."""
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .model import _MARKER, Prd, ReqBlock, repo_root

SUMMARY_MAX = 400
CONTEXT_LINES = 10
_CITE = re.compile(r"([^\s,;`()]+):(\d+)(?:\s*@([0-9A-Za-z]+))?")
_BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
_ID = re.compile(r"\b(?:UJ|FR|NFR)-\d+\b")


class Refused(Exception):
    """Something the owner must fix before a form can be served."""


@dataclass
class Item:
    id: str
    kind: str  # requirement | bug | question | marker
    title: str
    text: str  # the item as served; its SHA-256 is the fingerprint
    acs: list[tuple[str, str]] = field(default_factory=list)
    excerpts: list[str] = field(default_factory=list)
    fingerprint: str = ""
    where: str = ""


def _fp(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _excerpt(root: Path, path: str, line: int, commit: str | None) -> str:
    ref = commit or "HEAD"
    try:
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=root, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return f"(code not available at {ref})"
    lines = out.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    lo, hi = max(1, line - CONTEXT_LINES), min(len(lines), line + CONTEXT_LINES)
    if lo > hi:
        return f"(code not available at {ref})"
    return "\n".join(f"{n:>4} | {lines[n - 1]}" for n in range(lo, hi + 1))


def _excerpts(root: Path, text: str) -> list[tuple[str, int, str | None, str]]:
    return [(p, int(n), sha or None, _excerpt(root, p, int(n), sha or None)) for p, n, sha in _CITE.findall(text)]


def _requirement(prd: Prd, root: Path, b: ReqBlock) -> Item:
    served = "\n".join([f"### {b.id} {b.title}"] + [t for _, t in b.lines])
    cites = _excerpts(root, b.source or "")
    where = f"{cites[0][0]}:{cites[0][1]}" if cites else b.file
    return Item(b.id, "requirement", b.title, served, [(a.id, a.text) for a in b.acs if not a.removed],
                [c[3] for c in cites], _fp(served), where)


def _name_re(name: str) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])")


def _bugs(prd: Prd, root: Path, area: str, ids: set[str]) -> list[Item]:
    lines = prd.docs.get("errors.md", "").split("\n")
    names_area = _name_re(area)
    out = []
    for e in prd.errors_ledger.values():
        if not e.open or not (any(t in ids for t, _ in e.touches) or names_area.search(e.detected)):
            continue
        served = "\n".join(lines[e.line - 1 : e.end]).rstrip()
        cites = _excerpts(root, e.detected)
        out.append(Item(e.id, "bug", e.title, served, [], [c[3] for c in cites], _fp(served), "errors.md"))
    return out


def _questions(prd: Prd, ids: set[str]) -> list[Item]:
    sec = next((s for s in prd.sections if s.number == 13), None)
    bullets: list[list[str]] = []
    for _, text in sec.body if sec else []:
        if _BULLET.match(text):
            bullets.append([text.rstrip()])
        elif bullets and text.startswith(" ") and text.strip():
            bullets[-1].append(text.rstrip())
    out = []
    for b in bullets:
        served = "\n".join(b)
        if not set(_ID.findall(served)) & ids:
            continue
        n = len(out) + 1
        title = _BULLET.match(b[0]).group(1).strip()
        out.append(Item(f"Q-{n:02d}", "question", title[:100], served, [], [], _fp(served), "prd.md §13"))
    return out


def _walk(node: Any, path: list[str], named: set[str], active: bool, hits: list[tuple[list[str], str, int]], line: int) -> None:
    """Collect markers under a key the area names; `path` runs from that key down."""
    if isinstance(node, dict):
        kl = getattr(node, "key_lines", {})
        for k, v in node.items():
            if active:
                _walk(v, path + [str(k)], named, True, hits, kl.get(k, line))
            else:
                _walk(v, [str(k)], named, str(k) in named, hits, kl.get(k, line))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, path + [str(i)] if active else path, named, active, hits, line)
    elif isinstance(node, str) and active and _MARKER.search(node):
        hits.append((path, _MARKER.search(node).group(0), line))


def _named(prd: Prd, blocks: list[ReqBlock]) -> set[str]:
    from .model import _field_lines  # noqa: PLC0415

    words: set[str] = set()
    for b in blocks:
        for _, text in _field_lines(b.lines, "Traces"):
            words |= set(re.findall(r"[A-Za-z_][\w.-]*", text))
    for tc in prd.test_cases:
        target = tc.data.get("target") if isinstance(tc.data, dict) else None
        if isinstance(target, str):
            words |= set(re.split(r"[:/\s]+", target))
    return {w for w in words if w}


def _markers(prd: Prd, blocks: list[ReqBlock]) -> list[Item]:
    named = _named(prd, blocks)
    out: dict[str, Item] = {}
    for rel, data in prd.yaml.items():
        hits: list[tuple[list[str], str, int]] = []
        _walk(data, [], named, False, hits, 0)
        src = (prd.root / rel).read_text(encoding="utf-8").split("\n")
        for path, marker, line in hits:
            key = ".".join(path)
            iid = f"{Path(rel).name}:{key}"
            served = src[line - 1].strip() if 0 < line <= len(src) and marker in src[line - 1] else marker
            out.setdefault(iid, Item(iid, "marker", key, served, [], [], _fp(served), f"{rel} {key}"))
    return list(out.values())


def build_items(prd: Prd, area: str) -> list[Item]:
    if not any(r.area == area for r in prd.adoption or []):
        raise Refused(f"area {area} is not in adoption.md")
    root = repo_root(prd.root)
    blocks = [b for b in prd.blocks if b.file == f"features/{area}.md"]
    ids = {b.id for b in blocks}
    items = [_requirement(prd, root, b) for b in blocks if b.status == "as-built"]
    items += _bugs(prd, root, area, ids)
    items += _questions(prd, ids)
    items += _markers(prd, blocks)
    if not items:
        raise Refused(f"area {area} has no item to confirm")
    return items


def load_summaries(path: Path, items: list[Item], area: str) -> dict[str, str]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"cannot read summaries {path}: {e}") from e
    if not isinstance(data, dict):
        raise Refused(f"summaries {path} must be a JSON object mapping item ID to text")
    known = {i.id for i in items}
    for key, text in data.items():
        if key not in known:
            raise Refused(f"summary for {key} names no item of {area}")
        if not isinstance(text, str) or key not in text:
            raise Refused(f"summary for {key} does not mention {key}")
        if len(text) > SUMMARY_MAX:
            raise Refused(f"summary for {key} is over {SUMMARY_MAX} characters")
    return dict(data)
