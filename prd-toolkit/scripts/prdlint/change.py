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
    rels = {p.relative_to(root).as_posix(): p for p in _listed(root)}
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
_IGNORED_FIELDS = ("Status", "Source", "Acceptance (EARS)", "AC")


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
        elif rel == "contracts/config.yaml" and isinstance(data, dict) and isinstance(data.get("settings"), dict):
            out[rel] = {str(k): _dump(v) for k, v in data["settings"].items()}
        elif rel in custom and isinstance(data, dict):
            out[rel] = {str(k): _dump(v) for k, v in data.items()}
        else:
            out[rel] = {rel: _canon((root / rel).read_text(encoding="utf-8", errors="replace"))}
    return out


def _contract_lines(prd: model.Prd, items: dict[str, dict[str, str]]) -> dict[str, dict[str, int]]:
    """file -> item name -> the line its definition starts on: the YAML key's line, else the first line naming it, else 1."""
    out: dict[str, dict[str, int]] = {}
    for file, names in items.items():
        data = prd.yaml.get(file)
        if isinstance(data, dict) and isinstance(data.get("settings"), dict) and file == "contracts/config.yaml":
            data = data["settings"]
        keyed = {str(k): n for k, n in getattr(data, "key_lines", {}).items()}
        text = (prd.root / file).read_text(encoding="utf-8", errors="replace").lower().split("\n")
        out[file] = {n: keyed.get(n) or next((i for i, ln in enumerate(text, 1) if n.lower() in ln), 1) for n in names}
    return out


def repo_root(prd_root: Path) -> Path:
    """The top of the git repository holding `prd_root`; UsageError when it is in none."""
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=prd_root, capture_output=True, text=True)
    if top.returncode != 0:
        raise UsageError(f"bump: {prd_root} is not in a git repository")
    return Path(top.stdout.strip())


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


def _ac_states(old: model.Prd, new: model.Prd) -> dict[str, str]:
    """AC id -> new | unchanged | changed | removed, from the two PRDs; a wording-only edit is unchanged."""
    old_acs = {a.id: a for b in old.blocks for a in b.acs}
    out: dict[str, str] = {}
    for b in new.blocks:
        for a in b.acs:
            before = old_acs.get(a.id)
            if a.removed:
                out[a.id] = "removed" if before and not before.removed else "unchanged"
            elif before is None or before.removed:
                out[a.id] = "new"
            else:
                out[a.id] = "unchanged" if _ac_norm(a.text) == _ac_norm(before.text) else "changed"
    for a in old_acs.values():
        if not a.removed and a.id not in out:
            out[a.id] = "removed"
    return out


@dataclass
class _Diff:
    """The two PRDs and the items found so far; the `_diff_*` helpers read it and add to `items`."""
    old: model.Prd
    new: model.Prd
    items: list[BumpItem] = field(default_factory=list)

    def __post_init__(self):
        self.old_blocks = {b.id: b for b in self.old.blocks}
        self.new_blocks = {b.id: b for b in self.new.blocks}
        self.gone = {i for i, b in self.old_blocks.items() if not _removed(b) and (i not in self.new_blocks or _removed(self.new_blocks[i]))}
        self.fresh = set(self.new_blocks) - set(self.old_blocks)
        self.ac_state = _ac_states(self.old, self.new)
        self.block_of_ac = {_block_id_of_ac(a.id): b.id for b in [*self.old.blocks, *self.new.blocks] for a in b.acs}

    def add(self, index: int, id_: str, file: str, line: int, change: str) -> None:
        reason, level = _rule(index, file)
        self.items.append(BumpItem(id_, file, line or 1, change, level, reason))

    def covered(self, ac_id: str) -> bool:
        """Is this AC inside a block that was added or removed, so the block's own item speaks for it?"""
        block = self.block_of_ac.get(_block_id_of_ac(ac_id))
        return block in self.gone or block in self.fresh


_TEST_REF = re.compile(r"T-\d+\.\d+\s*\[[^\]]+\]")


def _tests_rest(b: model.ReqBlock) -> str:
    """A block's `Tests:` text without its T-id [level] tags and its (test-cases/<file>) part."""
    text = " ".join(t for _, t in model._field_lines(b.lines, "Tests")).replace(b.tests_file or "\0", "")
    return re.sub(r"[\s,()]+", " ", _TEST_REF.sub("", text)).strip()


def _tests_line_follows_cases(d: _Diff, before: model.ReqBlock, now: model.ReqBlock) -> bool:
    """Is the edit of a block's `Tests:` line only the T-ids of cases added or removed for it in this diff, with every
    `[level]` tag and the `(test-cases/<file>)` part agreeing with the cases? Then the cases carry their own rule."""
    old_cases = {t.id: t for t in d.old.test_cases}
    new_cases = {t.id: t for t in d.new.test_cases}
    was, now_ids = {t for t, _, _ in before.tests}, {t for t, _, _ in now.tests}

    def mine(tc: model.TestCase) -> bool:
        return d.block_of_ac.get(_block_id_of_ac(_owner_ac(tc))) == now.id

    if not all(t in new_cases and t not in old_cases and mine(new_cases[t]) for t in now_ids - was):
        return False
    if not all(t in old_cases and t not in new_cases and mine(old_cases[t]) for t in was - now_ids):
        return False
    for tid, level, _ in now.tests:
        case = new_cases.get(tid)
        if case is None or case.data.get("level") != level or (now.tests_file and case.file != now.tests_file):
            return False
    return _tests_rest(before) == _tests_rest(now)


def _diff_blocks(d: _Diff) -> None:
    """New and removed blocks; for the rest, title, prose and other fields, and each AC."""
    for i, b in d.new_blocks.items():
        if i in d.fresh:
            d.add(_NEW, i, b.file, b.line, "added")
    for i in sorted(d.gone):
        d.add(_GONE, i, d.old_blocks[i].file, d.old_blocks[i].line, "removed")
    old_acs = {a.id: a for b in d.old.blocks for a in b.acs}
    for b in d.new.blocks:
        before = d.old_blocks.get(b.id)
        if before is None or b.id in d.gone or _removed(b):
            continue
        if b.title != before.title:
            d.add(_PROSE, b.id, b.file, b.line, "changed")
        was, now = _fields(before), _fields(b)
        for name in sorted(set(was) | set(now)):
            if name in _IGNORED_FIELDS or was.get(name) == now.get(name):
                continue
            if name == "Tests" and _tests_line_follows_cases(d, before, b):
                continue
            d.add(_PROSE if name in _PROSE_FIELDS else _OTHER_FILE, b.id, b.file, b.line, "changed")
        for a in b.acs:
            st = d.ac_state.get(a.id)
            if st == "new":
                d.add(_NEW, a.id, b.file, a.line, "added")
            elif st == "changed":
                d.add(_AC_TEXT, a.id, b.file, a.line, "changed")
            elif st == "removed":
                d.add(_GONE, a.id, b.file, a.line, "removed")
            elif st == "unchanged" and not a.removed and a.text != old_acs[a.id].text:
                d.add(_PROSE, a.id, b.file, a.line, "changed")
        kept = {x.id for x in b.acs}
        for a in before.acs:
            if not a.removed and a.id not in kept:
                d.add(_GONE, a.id, before.file, a.line, "removed")


def _owner_ac(tc: model.TestCase) -> str:
    ac = tc.data.get("ac")
    return ac if isinstance(ac, str) and ac.startswith("AC-") else f"AC-{tc.id[2:].split('.')[0]}.0"


def _case_json(tc: model.TestCase) -> str:
    return json.dumps(tc.data, sort_keys=True, default=str)


def _diff_cases(d: _Diff) -> None:
    """New, changed and removed test cases, each judged by the state of the AC it tests."""
    old_cases = {t.id: t for t in d.old.test_cases}
    new_ids = {t.id for t in d.new.test_cases}
    open_touches = {t for e in d.new.errors_ledger.values() if e.open for t, _ in e.touches}
    for tc in d.new.test_cases:
        ac = _owner_ac(tc)
        if d.covered(ac):
            continue
        st = d.ac_state.get(ac, "unchanged")
        before = old_cases.get(tc.id)
        if before is None:
            if st == "new":
                d.add(_NEW_TEST, tc.id, tc.file, tc.line, "added")
                continue
            entry = d.new.errors_ledger.get(str(tc.data.get("known-failing")))
            cites = (entry is not None and entry.open) or d.block_of_ac.get(_block_id_of_ac(ac)) in open_touches
            d.add(_REGRESSION if cites and st == "unchanged" else _OTHER_TEST, tc.id, tc.file, tc.line, "added")
        elif _case_json(tc) != _case_json(before):
            d.add(_CHANGED_UNDER_CHANGED if st in ("changed", "removed") else _CHANGED_UNDER_SAME, tc.id, tc.file, tc.line, "changed")
    for tid, tc in old_cases.items():
        if tid not in new_ids and not d.covered(_owner_ac(tc)):
            d.add(_OTHER_FILE, tid, tc.file, tc.line, "removed")


def _diff_contracts(d: _Diff, was: dict[str, dict[str, str]], was_lines: dict[str, dict[str, int]]) -> None:
    """Removed, changed and new contract items; `was` is the base side, read while its folder still existed."""
    now = contract_items(d.new)
    now_lines = _contract_lines(d.new, now)
    for file in sorted(set(was) | set(now)):
        old_items, new_items = was.get(file, {}), now.get(file, {})
        for name in sorted(set(old_items) | set(new_items)):
            if name not in new_items:
                d.add(_GONE_ITEM, name, file, was_lines[file][name], "removed")
            elif name not in old_items:
                d.add(_OTHER_FILE, name, file, now_lines[file][name], "added")
            elif old_items[name] != new_items[name]:
                d.add(_CHANGED_UNDER_SAME, name, file, now_lines[file][name], "changed")


def _preamble(text: str) -> str:
    return text[: text.find("\n## ")] if "\n## " in text else text


def _diff_prd_md(d: _Diff, old_md: str) -> None:
    """prd.md outside the ignored lines: the glossary is prose; the preamble and any other section are unclassified."""
    new_md = _normalized_prd_md(d.new, _BASE_FM_DROP)
    if new_md == old_md:
        return
    if _preamble(old_md) != _preamble(new_md):
        d.add(_OTHER_FILE, "prd.md", "prd.md", 1, "changed")
    was = {s.number: s for s in sections(old_md) if s.number is not None}
    now = {s.number: s for s in sections(new_md) if s.number is not None}
    for n in sorted(set(was) | set(now)):
        body = [("\n".join(t for _, t in s.body).strip() if s else None) for s in (was.get(n), now.get(n))]
        if body[0] == body[1]:
            continue
        line = next((x.line for x in d.new.sections if x.number == n), 1)
        if n == 3 and n in was and n in now:
            d.add(_PROSE, "glossary", "prd.md", line, "changed")
        else:
            d.add(_OTHER_FILE, f"section {n}", "prd.md", line, "changed")


def _diff_files(d: _Diff, old_files: dict[str, bytes], new_files: dict[str, bytes]) -> None:
    """Every other changed file, and the text a features or nfr file keeps outside its blocks."""
    for rel in sorted(set(old_files) | set(new_files)):
        if re.fullmatch(r"features/[^/]+\.md", rel) or rel == "nfr.md":
            if _outside_blocks(d.old, rel) != _outside_blocks(d.new, rel):
                d.add(_OTHER_FILE, rel, rel, 1, "changed")
        elif _is_classified(rel):
            continue
        elif old_files.get(rel) != new_files.get(rel):
            d.add(_OTHER_FILE, rel, rel, 1, "changed")


def _is_classified(rel: str) -> bool:
    """Files the item-level diffs already cover: prd.md, test cases and the contracts (fixtures excepted)."""
    return rel == "prd.md" or rel.startswith("test-cases/") or (rel.startswith("contracts/") and not rel.startswith("contracts/fixtures/"))


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
        old_contracts = contract_items(old)
        old_lines = _contract_lines(old, old_contracts)
        old_md = _normalized_prd_md(old, _BASE_FM_DROP)
    d = _Diff(old, new)
    _diff_blocks(d)
    _diff_cases(d)
    _diff_contracts(d, old_contracts, old_lines)
    _diff_prd_md(d, old_md)
    _diff_files(d, old_files, _files(new.root))
    return Bump(_combine(d.items), d.items)


def _combine(items: list[BumpItem]) -> str:
    if any(i.level == JUDGMENT for i in items):
        return JUDGMENT
    return max((i.level for i in items), key=LEVELS.index, default="patch")


# ---------------------------------------------------------------- record

RECORD_LEVELS = (*LEVELS, "needs-judgment")
_REQ_ID = re.compile(r"(?:(UJ|FR|NFR)-(\d+)|AC-(\d+)\.(\d+)|T-(\d+)\.(\d+))")
_ID_RANK = {"UJ": 0, "FR": 1, "NFR": 2, "AC": 3, "T": 4}
_BLOCK_ID = re.compile(r"(?:UJ|FR|NFR)-\d+")
_VERSION_LINE = re.compile(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$", re.M)


@dataclass
class Recorded:
    version: str
    row: str


def _id_order(id_: str) -> tuple:
    m = _REQ_ID.fullmatch(id_)
    kind = id_.split("-")[0]
    return (_ID_RANK[kind], *(int(g) for g in m.groups()[1:] if g and g.isdigit()))


def _record_ids(items: list[BumpItem], *prds: model.Prd) -> list[str]:
    """Every requirement ID the items name, and the FR or NFR each AC and T-id belongs to, once each, in the PRD's
    natural order (UJ, FR, NFR, AC, T); a parent is looked up by number in `prds` (the working tree, then the base)."""
    ids = {i.id for i in items if _REQ_ID.fullmatch(i.id)}
    blocks = {int(b.id.split("-")[1]): b.id for p in reversed(prds) for b in p.blocks if b.kind in ("FR", "NFR")}
    for id_ in list(ids):
        m = re.fullmatch(r"(?:AC|T)-(\d+)\.\d+", id_)
        if m and int(m.group(1)) in blocks:
            ids.add(blocks[int(m.group(1))])
    return sorted(ids, key=_id_order)


def _decided(result: Bump, given: str) -> None:
    """Refuse a `given` level the diff does not allow; judgment items are taken as decided by the caller."""
    if result.level == JUDGMENT:
        need = max((i.level for i in result.items if i.level != JUDGMENT), key=LEVELS.index, default="patch")
    else:
        need = result.level
    if LEVELS.index(given) < LEVELS.index(need):
        raise ChangeError(f"the diff needs {need}, not {given}")


def _bumped(base_md: str, level: str) -> str:
    m = _VERSION_LINE.search(base_md[: base_md.find("\n---", 4)] if base_md.startswith("---") else base_md)
    if not m:
        raise UsageError("record: the base prd.md has no frontmatter version")
    major, minor, patch = (int(g) for g in m.groups())
    return {"major": f"{major + 1}.0.0", "minor": f"{major}.{minor + 1}.0", "patch": f"{major}.{minor}.{patch + 1}"}[level]


def _table_of(text: str, number: int):
    s = next((s for s in sections(text) if s.number == number), None)
    return next(iter(tables(s.body)), None) if s else None


def _cells_line(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _index_rows(base_md: str, prd: model.Prd, items: list[BumpItem]) -> list[str]:
    """The §11 rows: the base's rows, with each block the diff names added, retitled or set to removed, and every row's
    status taken from its block's `Status:` line in the working tree."""
    t = _table_of(base_md, 11)
    rows = [list(r.cells) + [""] * (5 - len(r.cells)) for r in (t.rows if t else [])]
    by_id = {r[0].strip("`"): r for r in rows}
    blocks = {b.id: b for b in prd.blocks}
    for id_ in sorted({i.id for i in items if _BLOCK_ID.fullmatch(i.id)}, key=_id_order):
        removed = next(i for i in items if i.id == id_).change == "removed"
        b = blocks.get(id_)
        if id_ in by_id and removed:
            by_id[id_][2] = "removed"
        elif id_ in by_id and b:
            by_id[id_][1], by_id[id_][3] = b.title, b.file
        elif b and not removed:
            rows.append([id_, b.title, b.status or "approved", b.file, ""])
            by_id[id_] = rows[-1]
    for row in rows:
        b = blocks.get(row[0].strip("`"))
        if b is not None and b.status:
            row[2] = b.status
    return [_cells_line(r) for r in rows]


def _replace_rows(lines: list[str], table, new_rows: list[str]) -> None:
    """Replace a table's body rows in `lines` (0-based list of file lines) with `new_rows`; an empty table gets them after its separator."""
    if table.rows:
        lines[table.rows[0].line - 1 : table.rows[-1].line] = new_rows
    else:
        lines[table.line + 1 : table.line + 1] = new_rows


def _write_prd_md(path: Path, version: str, today: str, row: str, index_rows: list[str]) -> None:
    """Write the row, the §11 rows, `version` and `updated`; the file's line ending (LF or CRLF) is kept."""
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    lines = text.split("\n")
    log = _table_of(text, 14)
    if log is None:
        raise ChangeError("§14 has no changelog table")
    last = log.rows[-1] if log.rows else None
    if last is not None and len(last.cells) > 2 and last.cells[0] == version and last.cells[2].endswith("; pending"):
        lines[last.line - 1] = row
    elif last is not None:
        lines.insert(last.line, row)
    else:
        lines.insert(log.line + 1, row)
    idx = _table_of(text, 11)
    if idx is not None:
        _replace_rows(lines, idx, index_rows)
    end = lines.index("---", 1) if lines and lines[0].strip() == "---" and "---" in lines[1:] else 0
    for key, value in (("version", version), ("updated", today)):
        at = next((n for n in range(1, end) if lines[n].startswith(f"{key}:")), None)
        if at is None:
            raise ChangeError(f"prd.md frontmatter has no {key}:")
        lines[at] = f"{key}: {value}"
    path.write_bytes(eol.join(lines).encode("utf-8"))


def record(repo_root: Path, prd_root: Path, base: str, level: str, text: str, today: str) -> Recorded:
    """Write the version bumped from `base`'s, `updated`, the §14 row (`<text>; pending`) and the §11 rows; run again, it gives the same file."""
    repo_root, prd_root = Path(repo_root).resolve(), Path(prd_root).resolve()
    if level == "needs-judgment":
        raise ChangeError("a needs-judgment bump must be decided first")
    if "\n" in text or "|" in text or not text.strip():
        raise ChangeError("the change text must be one non-empty line without |")
    result = bump(repo_root, prd_root, base)
    _decided(result, level)
    rel = prd_root.relative_to(repo_root).as_posix()
    with tempfile.TemporaryDirectory(prefix="prd-record-") as tmp:
        old = _load_base(repo_root, rel, base, Path(tmp))
        base_md = old.docs["prd.md"]
    version = _bumped(base_md, level)
    now = model.load(prd_root)
    ids = ", ".join(_record_ids(result.items, now, old)) or "-"
    row = f"| {version} | {today} | {text.strip()}; pending | {ids} |"
    _write_prd_md(prd_root / "prd.md", version, today, row, _index_rows(base_md, now, result.items))
    return Recorded(version, row)


from .change_approve import Approved, approve  # noqa: E402,F401  (the approve step lives in its own module)
