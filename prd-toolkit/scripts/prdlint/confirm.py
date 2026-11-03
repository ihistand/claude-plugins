"""The items an adoption area asks its owner to confirm: requirements, bugs, questions and markers."""
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .model import _MARKER, Prd, ReqBlock, _field_lines, repo_root

SUMMARY_MAX = 400
CONTEXT_LINES = 10
_CITE = re.compile(r"([^\s,;`()]+):(\d+)(?:\s*@([0-9A-Za-z]+))?")
_BULLET = re.compile(r"^[-*]\s+(.*)$")  # a top-level bullet; an indented one continues the bullet above
_QID = re.compile(r"^(Q-\d+)\b\s*(.*)$")
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


def _excerpt(root: Path, path: str, line: int, commit: str | None, cache: dict) -> str:
    ref = commit or "HEAD"
    key = (ref, path)
    if key not in cache:
        try:
            out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=root, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=30, check=True).stdout
            cache[key] = out.split("\n")
            if cache[key][-1] == "":
                cache[key].pop()
        except (OSError, subprocess.SubprocessError):
            cache[key] = None
    lines = cache[key]
    if lines is None:
        return f"(code not available at {ref})"
    lo, hi = max(1, line - CONTEXT_LINES), min(len(lines), line + CONTEXT_LINES)
    if lo > hi:
        return f"(code not available at {ref})"
    return "\n".join(f"{n:>4} | {lines[n - 1]}" for n in range(lo, hi + 1))


def _excerpts(root: Path, text: str, cache: dict) -> list[tuple[str, int, str | None, str]]:
    out = []
    for p, n, sha in _CITE.findall(text):
        if "/" in p or re.search(r"\.\w+$", p):  # a path, not a time or a host:port
            out.append((p, int(n), sha or None, _excerpt(root, p, int(n), sha or None, cache)))
    return out


def _requirement(root: Path, b: ReqBlock, cache: dict) -> Item:
    served = "\n".join([f"### {b.id} {b.title}"] + [t for _, t in b.lines])
    cites = _excerpts(root, b.source or "", cache)
    where = f"{cites[0][0]}:{cites[0][1]}" if cites else b.file
    return Item(b.id, "requirement", b.title, served, [(a.id, a.text) for a in b.acs if not a.removed],
                [c[3] for c in cites], _fp(served), where)


def _name_re(name: str) -> re.Pattern:
    return re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])")


def _bugs(prd: Prd, root: Path, area: str, ids: set[str], cache: dict) -> list[Item]:
    lines = prd.docs.get("errors.md", "").split("\n")
    names_area = _name_re(area)
    out = []
    for e in prd.errors_ledger.values():
        if not e.open or not (any(t in ids for t, _ in e.touches) or names_area.search(e.detected)):
            continue
        served = "\n".join(lines[e.line - 1 : e.end]).rstrip()
        cites = _excerpts(root, e.detected, cache)
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
    for pos, b in enumerate(bullets, 1):
        served = "\n".join(b)
        if not set(_ID.findall(served)) & ids:
            continue
        head = _BULLET.match(b[0]).group(1).strip()
        qm = _QID.match(head)
        out.append(Item(qm.group(1) if qm else f"Q-{pos:02d}", "question", (qm.group(2) if qm else head)[:100],
                        served, [], [], _fp(served), "prd.md §13"))
    return out


Hit = tuple[list[str], int, str, int, int]  # (full key path, index of the named key, marker, line, nth in its string)


def _walk(node: Any, path: list[str], start: int | None, named: set[str], hits: list[Hit], line: int) -> None:
    """Collect markers under a key the area names; `start` is where that key sits in `path`."""
    if isinstance(node, dict):
        kl = getattr(node, "key_lines", {})
        for k, v in node.items():
            st = start if start is not None else (len(path) if str(k) in named else None)
            _walk(v, path + [str(k)], st, named, hits, kl.get(k, line))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, path + [str(i)], start, named, hits, line)
    elif isinstance(node, str) and start is not None:
        for n, m in enumerate(_MARKER.finditer(node)):
            hits.append((path, start, m.group(0), line, n))


def _named(prd: Prd, area: str, blocks: list[ReqBlock]) -> set[str]:
    words: set[str] = set()
    for b in blocks:
        for _, text in _field_lines(b.lines, "Traces"):
            for tok in re.findall(r"[A-Za-z_][\w.-]*", text):
                words.add(tok.strip(".").rsplit(".", 1)[-1])  # `settings.KEY` names KEY
    for tc in prd.test_cases:
        target = tc.data.get("target") if isinstance(tc.data, dict) else None
        if tc.file == f"test-cases/{area}.yaml" and isinstance(target, str):
            words |= set(re.split(r"[:/\s]+", target.strip()))
            words.add(target.strip().rsplit(".", 1)[-1])
    return {w for w in words if w}


def _markers(prd: Prd, area: str, blocks: list[ReqBlock]) -> list[Item]:
    named = _named(prd, area, blocks)
    found: list[dict] = []
    for rel, data in prd.yaml.items():
        hits: list[Hit] = []
        _walk(data, [], None, named, hits, 0)
        src = (prd.root / rel).read_text(encoding="utf-8").split("\n")
        name = rel[len("contracts/"):] if rel.startswith("contracts/") else rel
        for path, start, marker, line, nth in hits:
            text = src[line - 1].strip() if 0 < line <= len(src) and marker in src[line - 1] else marker
            found.append({"rel": rel, "name": name, "path": path, "start": start, "marker": marker, "nth": nth,
                          "text": text if nth == 0 else f"{text}\n{marker}"})

    def ident(f: dict) -> str:
        return f"{f['name']}:{'.'.join(f['path'][f['start']:])}" + (f"#{f['nth'] + 1}" if f["nth"] else "")

    while True:  # extend colliding IDs upward through their ancestor keys until unique
        groups: dict[str, list[dict]] = {}
        for f in found:
            groups.setdefault(ident(f), []).append(f)
        grew = False
        for g in groups.values():
            if len(g) > 1:
                for f in g:
                    if f["start"] > 0:
                        f["start"] -= 1
                        grew = True
        if not grew:
            break
    out: list[Item] = []
    seen: dict[str, int] = {}
    for f in found:  # a collision that cannot be extended still keeps every marker
        iid = ident(f)
        seen[iid] = seen.get(iid, 0) + 1
        if seen[iid] > 1:
            iid += f"~{seen[iid]}"
        key = ".".join(f["path"][f["start"]:])
        out.append(Item(iid, "marker", key, f["text"], [], [], _fp(f["text"]), f"{f['rel']} {key}"))
    return out


def build_items(prd: Prd, area: str) -> list[Item]:
    if not any(r.area == area for r in prd.adoption or []):
        raise Refused(f"area {area} is not in adoption.md")
    root = repo_root(prd.root)
    blocks = [b for b in prd.blocks if b.file == f"features/{area}.md"]
    ids = {b.id for b in blocks}
    cache: dict = {}
    items = [_requirement(root, b, cache) for b in blocks if b.status == "as-built"]
    items += _bugs(prd, root, area, ids, cache)
    items += _questions(prd, ids)
    items += _markers(prd, area, blocks)
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
        if not isinstance(text, str):
            raise Refused(f"summary for {key} must be text")
        if not _name_re(key).search(text):
            raise Refused(f"summary for {key} does not mention {key}")
        if len(text) > SUMMARY_MAX:
            raise Refused(f"summary for {key} is over {SUMMARY_MAX} characters")
    return dict(data)
