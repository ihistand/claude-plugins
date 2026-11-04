"""The change bookkeeping behind prd_change.py: next IDs, the PRD digest and the version bump (record and approve join them)."""
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import model, snapshot
from .markdown import sections, tables
from .deps import require
from .rules.contracts import custom_types

yaml = require("yaml", "pyyaml")

REVIEW_FILE = ".prd-review.json"
_NUM = re.compile(r"(?:UJ|FR|NFR)-(\d+)")
_KIND = re.compile(r"^(?:(UJ|FR|NFR)|(AC|T)-(\d+))$")
_FM_DROP = re.compile(r"^(?:version|updated):")


class ChangeError(Exception):
    """A change the script refuses; the CLI prints `refused: <message>` and exits 1."""


class UsageError(Exception):
    """A call the script cannot run (a ref with no PRD); the CLI prints the message as one line and exits 2."""


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


def _normalized_prd_md(prd: model.Prd, drop_lines: re.Pattern = _FM_DROP) -> str:
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
            if drop_lines.match(lines[i]):
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


# ---------------------------------------------------------------- bump

LEVELS = ("patch", "minor", "major")
JUDGMENT = "needs judgment"

# (item, level) per row of the spec's bump table, in spec order; `_rule(i)` is the one place a level is read
BUMP_RULES: tuple[tuple[str, str], ...] = (
    ("a new block or AC", "minor"),
    ("a new test case under a new AC", "minor"),
    ("a removed block or AC", "major"),
    ("a removed contract item", "major"),
    ("an AC whose text changed (not equal after lowercasing, removing punctuation and collapsing whitespace)", JUDGMENT),
    ("an AC whose text is equal after that normalization, a changed title, Flow, Edge cases or glossary meaning", "patch"),
    ("a changed test case or contract item under an unchanged AC", JUDGMENT),
    ("a changed test case under a changed AC", "major"),
    ("a new test case under an unchanged AC that cites an open errors.md entry", "patch"),
    ("any other new test case under an unchanged AC", JUDGMENT),
    ("any other changed file in the PRD folder", JUDGMENT),
)
_NEW, _NEW_TEST, _GONE, _GONE_ITEM, _AC_TEXT, _PROSE, _CHANGED_UNDER_SAME, _CHANGED_UNDER_CHANGED, _REGRESSION, _OTHER_TEST, _OTHER_FILE = range(11)
_BASE_FM_DROP = re.compile(r"^(?:version|updated|status):")
_FIELD = re.compile(r"^([A-Za-z][\w ()/-]*?):")
_PROSE_FIELDS = ("Flow", "Edge cases")
_IGNORED_FIELDS = ("Status", "Source", "Tests", "Acceptance (EARS)", "AC")


@dataclass
class BumpItem:
    id: str
    file: str
    line: int
    change: str  # added | removed | changed
    level: str
    reason: str


@dataclass
class Bump:
    level: str
    items: list[BumpItem] = field(default_factory=list)


def _rule(index: int, detail: str = "") -> tuple[str, str]:
    """(reason, level) of BUMP_RULES row `index`; the unclassified row names its file."""
    text, level = BUMP_RULES[index]
    return (f"unclassified change in {detail}" if index == _OTHER_FILE else text), level


def _ac_norm(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]|_", "", text.lower()).split())


def _canon(text: str) -> str:
    return " ".join(text.split())


def _dump(node) -> str:
    return _canon(yaml.safe_dump(json.loads(json.dumps(node, default=str)), sort_keys=True))


def contract_items(prd: model.Prd) -> dict[str, dict[str, str]]:
    """file (PRD-relative) -> item name -> canonical text: OpenAPI operations, events, SQL tables, errors.yaml codes,
    config.yaml keys and pack contract items; any other contracts file (fixtures excepted) is one item named after it."""
    root = prd.root
    out: dict[str, dict[str, str]] = {}
    c = snapshot.contracts_of(prd)
    found = snapshot.items(c)
    for kind, name in (("op", "openapi.yaml"), ("table", "schema.sql"), ("event", "events.md")):
        if name in c.files:
            out[f"contracts/{name}"] = {n: _canon(snapshot.item_text(c, kind, n) or "") for n in sorted(found[kind])}
    custom = {f for _, _, files, _ in custom_types(prd) for f in files}
    for rel in sorted(p.relative_to(root).as_posix() for p in (root / "contracts").rglob("*") if p.is_file()):
        if rel in out or rel.startswith("contracts/fixtures/"):
            continue
        data = prd.yaml.get(rel)
        if rel == "contracts/errors.yaml" and isinstance(data, dict):
            out[rel] = {str(k): _dump(v) for k, v in data.items()}
        elif rel == "contracts/config.yaml" and isinstance(data, dict):
            settings = data.get("settings")
            out[rel] = {str(k): _dump(v) for k, v in (settings if isinstance(settings, dict) else {}).items()}
        elif rel in custom and isinstance(data, dict):
            out[rel] = {str(k): _dump(v) for k, v in data.items()}
        else:
            out[rel] = {rel: _canon((root / rel).read_text(encoding="utf-8", errors="replace"))}
    return out


def _load_base(repo_root: Path, rel: str, base: str, into: Path) -> model.Prd:
    """The PRD folder `rel` as it was at `base`, extracted from `git archive` into `into`."""
    nope = UsageError(f"bump: {base} has no {rel}")
    sha = subprocess.run(["git", "rev-parse", "-q", "--verify", "--end-of-options", f"{base}^{{commit}}"], cwd=repo_root, capture_output=True)
    if sha.returncode != 0:
        raise nope
    arc = subprocess.run(["git", "archive", "--format=tar", sha.stdout.decode().strip(), "--", rel], cwd=repo_root, capture_output=True)
    if arc.returncode != 0:
        raise nope
    with tarfile.open(fileobj=io.BytesIO(arc.stdout)) as tar:
        for m in tar:
            dest = (into / m.name).resolve()
            if m.isfile() and dest.is_relative_to(into.resolve()):
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tar.extractfile(m).read())
    try:
        return model.load(into / rel)
    except model.NotAPrd:
        raise nope from None


def _files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in _listed(root) if not _skipped(p.relative_to(root).as_posix())}


def _fields(block: model.ReqBlock) -> dict[str, str]:
    """A block's body by field name (Flow, Edge cases, Errors, ...); AC lines and their continuations are the field AC."""
    out: dict[str, list[str]] = {}
    cur = ""
    for _, text in block.lines:
        if not text.strip():
            continue
        if text.startswith("- AC-"):
            cur = "AC"
        elif not text[0].isspace():
            m = _FIELD.match(text)
            cur = m.group(1) if m else "(text)"
        out.setdefault(cur, []).append(text.rstrip())
    return {k: "\n".join(v) for k, v in out.items()}


def _outside_blocks(prd: model.Prd, rel: str) -> str:
    """A features file's text with every requirement block (heading and body) removed."""
    inside = {b.line for b in prd.blocks if b.file == rel} | {n for b in prd.blocks if b.file == rel for n, _ in b.lines}
    return "\n".join(t.rstrip() for n, t in enumerate(prd.docs.get(rel, "").split("\n"), 1) if n not in inside).strip()


def _removed(b: model.ReqBlock) -> bool:
    return (b.status or "").lower().startswith("removed")


def _block_id_of_ac(ac_id: str) -> str:
    return "AC-" + ac_id[3:].split(".")[0]


def bump(repo_root: Path, prd_root: Path, base: str) -> Bump:
    """Compare the PRD folder at `base` with the working tree and propose a version level, item by item."""
    repo_root, prd_root = Path(repo_root).resolve(), Path(prd_root).resolve()
    try:
        rel = prd_root.relative_to(repo_root).as_posix()
    except ValueError:
        raise UsageError(f"bump: {prd_root} is not inside {repo_root}") from None
    new = model.load(prd_root)
    with tempfile.TemporaryDirectory(prefix="prd-bump-") as tmp:
        old = _load_base(repo_root, rel, base, Path(tmp))
        old_files = _files(old.root)
        old_cases = {t.id: t for t in old.test_cases}
        old_contracts = contract_items(old)
        old_md = _normalized_prd_md(old, _BASE_FM_DROP)
    new_files = _files(new.root)
    items: list[BumpItem] = []

    def add(index: int, id_: str, file: str, line: int, change: str, detail: str = "") -> None:
        reason, level = _rule(index, detail or file)
        items.append(BumpItem(id_, file, line, change, level, reason))

    old_blocks = {b.id: b for b in old.blocks}
    new_blocks = {b.id: b for b in new.blocks}
    gone_blocks = {i for i, b in old_blocks.items() if not _removed(b) and (i not in new_blocks or _removed(new_blocks[i]))}
    fresh_blocks = {i for i in new_blocks if i not in old_blocks}
    for i, b in new_blocks.items():
        if i in fresh_blocks:
            add(_NEW, i, b.file, b.line, "added")
    for i in sorted(gone_blocks):
        add(_GONE, i, old_blocks[i].file, old_blocks[i].line, "removed")
    # blocks in both: title, prose fields, unclassified fields; then their ACs
    old_acs = {a.id: a for b in old.blocks for a in b.acs}
    ac_state: dict[str, str] = {}
    for b in new.blocks:
        for a in b.acs:
            before = old_acs.get(a.id)
            if a.removed:
                ac_state[a.id] = "removed" if before and not before.removed else "unchanged"
            elif before is None or before.removed:
                ac_state[a.id] = "new"
            else:
                ac_state[a.id] = "unchanged" if _ac_norm(a.text) == _ac_norm(before.text) else "changed"
    for a in old_acs.values():
        if not a.removed and a.id not in ac_state:
            ac_state[a.id] = "removed"
    for b in new.blocks:
        before = old_blocks.get(b.id)
        if before is None or b.id in gone_blocks or _removed(b):
            continue
        if b.title != before.title:
            add(_PROSE, b.id, b.file, b.line, "changed")
        was, now = _fields(before), _fields(b)
        for name in sorted(set(was) | set(now)):
            if name in _IGNORED_FIELDS or was.get(name) == now.get(name):
                continue
            if name in _PROSE_FIELDS:
                add(_PROSE, b.id, b.file, b.line, "changed")
            else:
                add(_OTHER_FILE, b.id, b.file, b.line, "changed")
        for a in b.acs:
            st = ac_state.get(a.id)
            if st == "new":
                add(_NEW, a.id, b.file, a.line, "added")
            elif st == "changed":
                add(_AC_TEXT, a.id, b.file, a.line, "changed")
            elif st == "removed":
                add(_GONE, a.id, b.file, a.line, "removed")
            elif st == "unchanged" and not a.removed and a.text != old_acs[a.id].text:
                add(_PROSE, a.id, b.file, a.line, "changed")
        for a in before.acs:
            if not a.removed and a.id not in {x.id for x in b.acs}:
                add(_GONE, a.id, before.file, a.line, "removed")
    # test cases
    def owner(tc: model.TestCase) -> str:
        ac = tc.data.get("ac")
        return ac if isinstance(ac, str) and ac.startswith("AC-") else f"AC-{tc.id[2:].split('.')[0]}.0"

    def covered(ac_id: str) -> bool:
        block = {"AC-" + b.id.split("-")[1]: b.id for b in new.blocks + old.blocks}.get(_block_id_of_ac(ac_id))
        return block in gone_blocks or block in fresh_blocks

    open_touches = {t for e in new.errors_ledger.values() if e.open for t, _ in e.touches}
    for tc in new.test_cases:
        ac = owner(tc)
        st = ac_state.get(ac, "unchanged")
        before = old_cases.get(tc.id)
        if covered(ac):
            continue
        if before is None:
            if st == "new":
                add(_NEW_TEST, tc.id, tc.file, tc.line, "added")
                continue
            ledger = new.errors_ledger.get(str(tc.data.get("known-failing")))
            block = {"AC-" + b.id.split("-")[1]: b.id for b in new.blocks}.get(_block_id_of_ac(ac))
            cites = (ledger is not None and ledger.open) or block in open_touches
            add(_REGRESSION if cites and st == "unchanged" else _OTHER_TEST, tc.id, tc.file, tc.line, "added")
        elif json.dumps(tc.data, sort_keys=True, default=str) != json.dumps(before.data, sort_keys=True, default=str):
            add(_CHANGED_UNDER_CHANGED if st in ("changed", "removed") else _CHANGED_UNDER_SAME, tc.id, tc.file, tc.line, "changed")
    for tid, tc in old_cases.items():
        if tid not in {t.id for t in new.test_cases} and not covered(owner(tc)):
            add(_OTHER_FILE, tid, tc.file, tc.line, "removed")
    # contracts
    new_contracts = contract_items(new)
    for file in sorted(set(old_contracts) | set(new_contracts)):
        was, now = old_contracts.get(file, {}), new_contracts.get(file, {})
        for name in sorted(set(was) | set(now)):
            if name not in now:
                add(_GONE_ITEM, name, file, 0, "removed")
            elif name not in was:
                add(_OTHER_FILE, name, file, 0, "added")
            elif was[name] != now[name]:
                add(_CHANGED_UNDER_SAME, name, file, 0, "changed")
    # prd.md: glossary is prose, everything else outside the ignored lines is unclassified
    new_md = _normalized_prd_md(new, _BASE_FM_DROP)
    if new_md != old_md:
        was_s, now_s = {s.number: s for s in sections(old_md)}, {s.number: s for s in sections(new_md)}
        body = lambda s: "\n".join(t for _, t in s.body).strip() if s else None  # noqa: E731
        first = lambda text: text[: text.find("\n## ")] if "\n## " in text else text  # noqa: E731
        if first(old_md) != first(new_md):
            add(_OTHER_FILE, "prd.md", "prd.md", 1, "changed")
        for n in sorted(k for k in set(was_s) | set(now_s) if k is not None):
            if body(was_s.get(n)) == body(now_s.get(n)):
                continue
            sec = next((x for x in new.sections if x.number == n), None)
            line = sec.line if sec else 1
            if n == 3 and n in was_s and n in now_s:
                add(_PROSE, "glossary", "prd.md", line, "changed")
            else:
                add(_OTHER_FILE, f"section {n}", "prd.md", line, "changed", "prd.md")
    # every other changed file, and the text a features file keeps outside its blocks
    handled = lambda r: r == "prd.md" or r.startswith(("test-cases/", "contracts/")) and not r.startswith("contracts/fixtures/")  # noqa: E731
    for rel_file in sorted(set(old_files) | set(new_files)):
        if rel_file.endswith(".md") and (re.fullmatch(r"features/[^/]+\.md", rel_file) or rel_file == "nfr.md"):
            if _outside_blocks(old, rel_file) != _outside_blocks(new, rel_file):
                add(_OTHER_FILE, rel_file, rel_file, 1, "changed")
        elif not handled(rel_file) and old_files.get(rel_file) != new_files.get(rel_file):
            add(_OTHER_FILE, rel_file, rel_file, 1, "changed")
    return Bump(_combine(items), items)


def _combine(items: list[BumpItem]) -> str:
    if any(i.level == JUDGMENT for i in items):
        return JUDGMENT
    return max((i.level for i in items), key=LEVELS.index, default="patch")
