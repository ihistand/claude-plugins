"""The location reader and the links.md writers behind prd_links.py (prd-toolkit 0.7).

A Location is a links.md cell: a backticked path to another repository's root, or a backticked
`<git URL>#<PRD folder>`. `open_side` turns one into a Side, the other repository as git sees it: a
path on disk, or a bare partial clone of the URL under the cache. Every git call goes through `_git`,
with GIT_TERMINAL_PROMPT=0 and a timeout, so a location that cannot be read is Unreachable, never a
prompt or a hang. Reading a PRD at a ref copies its folder out of git into a temporary directory;
nothing is written under any `.git/` or inside a repository except the files a command names.
"""
import hashlib
import os
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import citations, model, snapshot
from .markdown import frontmatter, split_cells
from .rules.contracts import event_names
from .rules.links import _LOCATION, _LOCATION_MSG, _NEEDS, _URL, _VERSION

UPSTREAM_HEADER = "| Upstream | Location | Version | Commit | Needs |"
CONSUMER_HEADER = "| Consumer | Location |"
SKELETON = (f"# Links\n\n## Upstreams\n\n{UPSTREAM_HEADER}\n|---|---|---|---|---|\n\n"
            f"## Consumers\n\n{CONSUMER_HEADER}\n|---|---|\n")


class Unreachable(Exception):
    """A location the script cannot read or fetch."""


class Refused(Exception):
    """The command will not do it; nothing was written."""


class BadArgument(ValueError):
    """A malformed location or Needs value: a usage error."""


# ---------------------------------------------------------------- git

def _timeout() -> float:
    try:
        return float(os.environ.get("PRD_LINKS_TIMEOUT") or 60)
    except ValueError:
        return 60.0


def _git(cwd: Path, *args: str, input: bytes | None = None) -> subprocess.CompletedProcess:
    """Run git in `cwd`: no terminal prompt, no optional locks, bounded by the timeout. Raises Unreachable on a
    timeout or when git cannot start; a non-zero exit is the caller's to judge."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
    limit = _timeout()
    try:
        p = subprocess.Popen(["git", *args], cwd=cwd, env=env, stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError as e:
        raise Unreachable(f"git cannot run: {e}") from e
    try:
        out, err = p.communicate(input, timeout=limit)
    except subprocess.TimeoutExpired:
        try:  # the whole group: a transport helper or ssh holding the pipes would block the second communicate
            os.killpg(p.pid, signal.SIGKILL) if hasattr(os, "killpg") else p.kill()
        except (ProcessLookupError, PermissionError):
            p.kill()
        p.communicate()
        raise Unreachable(f"git {args[0]} timed out after {limit:g} s") from None
    return subprocess.CompletedProcess(["git", *args], p.returncode, out, err)


def _out(cwd: Path, *args: str, input: bytes | None = None, why: str = "") -> bytes:
    """git's stdout; Unreachable, prefixed with `why`, on a timeout or a non-zero exit."""
    try:
        r = _git(cwd, *args, input=input)
    except Unreachable as e:
        raise Unreachable(f"{why}: {e}" if why else str(e)) from None
    if r.returncode != 0:
        tail = r.stderr.decode("utf-8", "replace").strip().splitlines()
        msg = f"git {args[0]}: {tail[-1] if tail else f'exit {r.returncode}'}"
        raise Unreachable(f"{why}: {msg}" if why else msg)
    return r.stdout


def toplevel(path: Path) -> Path:
    """The repository root above `path`; `path` itself when git finds none."""
    try:
        r = _git(path, "rev-parse", "--show-toplevel")
    except Unreachable:
        return path
    out = r.stdout.decode("utf-8", "replace").strip()
    return Path(out) if r.returncode == 0 and out else path


# ---------------------------------------------------------------- locations

@dataclass
class Location:
    raw: str  # the cell as written, backticks included
    path: str | None  # a path location: the other repository's root, relative to this repository's root
    url: str | None  # a URL location: the git URL ...
    folder: str | None  # ... and the PRD folder it names


def parse_location(cell: str) -> Location:
    """A links.md Location cell; BadArgument (a ValueError) on anything links-format would reject."""
    raw = cell.strip()
    m = _LOCATION.fullmatch(raw)
    if not m:
        raise BadArgument(f"{cell!r}: {_LOCATION_MSG}")
    loc = m.group(1)
    if _URL.match(loc):
        url, _, folder = loc.partition("#")
        folder = folder.strip().strip("/")
        if not folder or not url.strip():
            raise BadArgument(f"{cell!r}: {_LOCATION_MSG}")
        return Location(raw, None, url.strip(), folder)
    return Location(raw, loc, None, None)


def _cache_dir(url: str) -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "prd-toolkit/links" / hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _fetch(loc: Location) -> Path:
    """The URL's bare partial clone under the cache: cloned the first time, fetched after."""
    d = _cache_dir(loc.url)
    if (d / "HEAD").is_file():
        _out(d, "fetch", "-q", "--prune", "origin", "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*",
             why=f"{loc.raw} is unreachable")
        return d
    d.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{d.name}.", dir=d.parent))
    try:
        _out(d.parent, "clone", "-q", "--bare", "--filter=blob:none", "--", loc.url, str(tmp), why=f"{loc.raw} is unreachable")
        try:
            tmp.rename(d)
        except OSError:  # another run cloned it first
            if not (d / "HEAD").is_file():
                raise
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    return d


@dataclass
class Side:
    location: Location
    repo: Path  # the repository on disk, or the URL's cache clone
    prd_dir: Path  # repo / the PRD folder (for a URL, a path inside the bare clone that is never read from disk)
    slug: str = ""  # the `prd:` the location was found to hold
    _tmp: list = field(default_factory=list, repr=False, compare=False)

    @property
    def folder(self) -> str:
        return self.prd_dir.relative_to(self.repo).as_posix()

    def default_branch(self) -> str:
        """`origin/HEAD` (as the branch it names) when set, else main; a URL's clone follows the remote's HEAD."""
        r = _git(self.repo, "rev-parse", "--abbrev-ref", "-q", "--verify", "origin/HEAD")
        out = r.stdout.decode("utf-8", "replace").strip()
        if r.returncode == 0 and out and out != "origin/HEAD":
            return out
        if self.location.url:
            r = _git(self.repo, "symbolic-ref", "-q", "--short", "HEAD")
            out = r.stdout.decode("utf-8", "replace").strip()
            if r.returncode == 0 and out:
                return out
        return "main"

    def commit(self, ref: str) -> str:
        """The full hex commit `ref` names; Refused when it names none."""
        r = _git(self.repo, "rev-parse", "-q", "--verify", "--end-of-options", f"{ref}^{{commit}}")
        out = r.stdout.decode("utf-8", "replace").strip()
        if r.returncode != 0 or not out:
            raise Refused(f"{self.location.raw} has no ref {ref}")
        return out

    def is_ancestor(self, commit: str, ref: str) -> bool:
        return _git(self.repo, "merge-base", "--is-ancestor", commit, ref).returncode == 0

    def show(self, ref: str, rel: str) -> str | None:
        """A file's text at `ref` (path relative to the repository root), or None when absent."""
        r = _git(self.repo, "cat-file", "blob", f"{ref}:{rel}")
        return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None

    def load(self, ref: str | None) -> model.Prd:
        """The PRD at `ref` (copied out of git into a temporary directory), or the working tree for None (path locations only)."""
        if ref is None:
            if self.location.url:
                raise ValueError(f"{self.location.raw}: a URL location has no working tree")
            return model.load(self.prd_dir)
        commit = self.commit(ref)
        listing = _out(self.repo, "ls-tree", "--full-tree", "-r", "-z", commit, "--", self.folder,
                       why=f"{self.location.raw} is unreachable")
        blobs: list[tuple[bytes, str]] = []
        for entry in filter(None, listing.split(b"\0")):
            meta, _, path = entry.partition(b"\t")
            mode, kind, sha = meta.split()
            if kind == b"blob" and mode != b"120000":  # a symlink is not copied
                blobs.append((sha, path.decode("utf-8", "surrogateescape")))
        if not any(p == f"{self.folder}/prd.md" for _, p in blobs):
            raise Refused(f"{self.location.raw} holds no PRD at {self.folder} on {ref}")
        data = _out(self.repo, "cat-file", "--batch", input=b"".join(s + b"\n" for s, _ in blobs),
                    why=f"{self.location.raw} is unreachable")
        tmp = tempfile.TemporaryDirectory(prefix="prd-links-")
        self._tmp.append(tmp)
        root, pos = Path(tmp.name), 0
        for _, path in blobs:
            nl = data.index(b"\n", pos)
            size = int(data[pos:nl].split()[2])
            body = data[nl + 1:nl + 1 + size]
            pos = nl + 1 + size + 1
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
        return model.load(root / self.folder)


def _slug_of(text: str | None) -> str | None:
    """The `prd:` of a prd.md text ("" when it has none); None when there is no prd.md."""
    return None if text is None else frontmatter(text)[0].get("prd", "")


def _held(raw: str, found: list[str], expect: str | None) -> Refused:
    if not found:
        return Refused(f"{raw} holds no PRD")
    return Refused(f"{raw} holds PRD {', '.join(sorted(found))}, not {expect}" if expect else
                   f"{raw} holds PRDs {', '.join(sorted(found))}; a path location names a repository with one PRD")


def open_side(here_root: Path, loc: Location, expect: str | None = None) -> Side:
    """The other repository: a path resolved against `here_root` (read from disk), or a URL through the cache
    (read at its default branch). With `expect`, the PRD there must be `prd: <expect>`."""
    if loc.path is not None:
        repo = (Path(here_root) / loc.path).resolve()
        if not repo.is_dir():
            raise Unreachable(f"{loc.raw} is unreachable: no directory {repo}")
        prd_root = repo / "docs/prd"
        on_disk = {d: _slug_of((d / "prd.md").read_text(encoding="utf-8")) for d in sorted(prd_root.iterdir())
                   if (d / "prd.md").is_file()} if prd_root.is_dir() else {}
        if expect is not None and on_disk.get(prd_root / expect) == expect:
            return Side(loc, repo, prd_root / expect, expect)
        if expect is None and len(on_disk) == 1:
            (d, slug), = on_disk.items()
            return Side(loc, repo, d, slug)
        if expect is not None and prd_root / expect in on_disk:
            raise _held(loc.raw, [on_disk[prd_root / expect] or "(none)"], expect)
        raise _held(loc.raw, [s or "(none)" for s in on_disk.values()], expect)
    repo = _fetch(loc)
    side = Side(loc, repo, repo / loc.folder)
    slug = _slug_of(side.show(side.default_branch(), f"{loc.folder}/prd.md"))
    if slug is None:
        raise Refused(f"{loc.raw} holds no PRD")
    if expect is not None and slug != expect:
        raise _held(loc.raw, [slug or "(none)"], expect)
    side.slug = slug
    return side


# ---------------------------------------------------------------- links.md text

def _row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |"


def _heading(line: str) -> bool:
    return line.startswith("#") and line.lstrip("#").startswith(" ")


def _add_row(text: str, title: str, header: str, row: str) -> str:
    """`text` with `row` appended to the table under `## <title>`, adding the table or the section when absent."""
    lines = text.rstrip("\n").split("\n")
    sep = "|" + "---|" * len(split_cells(header))
    at = next((i for i, x in enumerate(lines) if x.strip() == f"## {title}"), None)
    if at is None:
        block = [f"## {title}", "", header, sep, row, ""]
        before = next((i for i, x in enumerate(lines) if x.strip() == "## Consumers"), None) if title == "Upstreams" else None
        if before is None:
            return "\n".join(lines + [""] + block).rstrip("\n") + "\n"
        return "\n".join(lines[:before] + block + lines[before:]).rstrip("\n") + "\n"
    end = next((i for i in range(at + 1, len(lines)) if _heading(lines[i])), len(lines))
    first = next((i for i in range(at + 1, end) if lines[i].lstrip().startswith("|")), None)
    if first is None:
        lines[at + 1:at + 1] = ["", header, sep, row]
    else:
        last = first
        while last + 1 < end and lines[last + 1].lstrip().startswith("|"):
            last += 1
        lines.insert(last + 1, row)
    return "\n".join(lines).rstrip("\n") + "\n"


def _set_lock(text: str, name: str, version: str, commit: str) -> str:
    """`text` with the Version and Commit cells of Upstreams row `name` replaced."""
    lines, section = text.split("\n"), ""
    for i, line in enumerate(lines):
        if _heading(line):
            section = line.strip()
        elif section == "## Upstreams" and line.lstrip().startswith("|"):
            cells = [c.strip() for c in split_cells(line)]
            if cells and cells[0].strip("`") == name:
                cells = (cells + [""] * 5)[:5]
                cells[2], cells[3] = version, commit
                lines[i] = _row(*cells)
                return "\n".join(lines)
    raise Refused(f"no Upstreams row '{name}'")


# ---------------------------------------------------------------- add and sync

def _here(prd: model.Prd) -> Path:
    return toplevel(prd.root)


def _my_url(here: Path, prd: model.Prd) -> str:
    r = _git(here, "remote", "get-url", "origin")
    url = r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else ""
    return f"{url or '<git URL of this repository>'}#{prd.root.relative_to(here).as_posix()}"


def add(prd: model.Prd, location: str, needs: str = "") -> list[str]:
    """Write the Upstreams row here and the Consumers row there (or print it, for a URL location)."""
    cell = location.strip()
    loc = parse_location(cell if cell.startswith("`") else f"`{cell}`")
    needs = needs.strip()
    if needs and not _NEEDS.fullmatch(needs):
        raise BadArgument(f"--needs {needs!r}: must be verified or live in <env>")
    me = prd.frontmatter.get("prd", "")
    here = _here(prd)
    side = open_side(here, loc)
    other = side.slug
    if other == me or (loc.path is not None and side.prd_dir == prd.root):
        raise Refused("a PRD cannot link to itself")
    if prd.links and any(r.name == other for r in prd.links.upstreams):
        raise Refused(f"links.md already has an Upstreams row '{other}'")
    ours = prd.root / model.LINKS_FILE
    our_text = _add_row(ours.read_text(encoding="utf-8") if ours.is_file() else SKELETON, "Upstreams", UPSTREAM_HEADER,
                        _row(other, loc.raw, "", "", needs))
    report = [f"{model.LINKS_FILE}: added Upstreams row {other} {loc.raw}"]
    writes = [(ours, our_text)]
    if loc.path is not None:
        theirs = side.prd_dir / model.LINKS_FILE
        back = f"`{Path(os.path.relpath(here, side.repo)).as_posix()}`"
        shown = f"{loc.path.rstrip('/')}/{side.folder}/{model.LINKS_FILE}"
        their_links = model.load(side.prd_dir).links
        if their_links and any(r.name == me for r in their_links.consumers):
            report.append(f"{shown}: already has a Consumers row {me}")
        else:
            writes.append((theirs, _add_row(theirs.read_text(encoding="utf-8") if theirs.is_file() else SKELETON, "Consumers",
                                            CONSUMER_HEADER, _row(me, back))))
            report.append(f"{shown}: added Consumers row {me} {back}")
    else:
        report.append(f"{other} is not on disk: add this row to the Consumers table of its links.md "
                      f"({loc.url}#{loc.folder}): {_row(me, '`' + _my_url(here, prd) + '`')}")
    for path, text in writes:
        path.write_text(text, encoding="utf-8")
    return report


def _missing(up: model.Prd, kind: str, name: str, upstream: str, ref: str) -> str:
    if kind in ("event", "job") and "contracts/asyncapi.yaml" in up.yaml and name in event_names(up):
        return f"{kind}:{name}: asyncapi items cannot be cited across repositories"
    return f"{kind}:{name}: not in {upstream} at {ref}"


def sync(prd: model.Prd, upstream: str, ref: str | None = None) -> list[str]:
    """Copy every item this PRD cites from `upstream` at `ref` (default: its default branch) into the snapshot,
    remove snapshot files no longer needed, and write the lock. Refused, writing nothing, when an item is missing."""
    row = next((r for r in (prd.links.upstreams if prd.links else []) if r.name == upstream), None)
    if row is None:
        raise Refused(f"no Upstreams row '{upstream}'")
    try:
        loc = parse_location(row.location)
    except BadArgument as e:
        raise Refused(f"Upstreams row '{upstream}': {e}") from None
    side = open_side(_here(prd), loc, expect=upstream)
    at = ref or side.default_branch()
    commit = side.commit(at)
    up = side.load(commit)
    held = up.frontmatter.get("prd", "")
    if held != upstream:
        raise Refused(f"{loc.raw} holds PRD {held or '(none)'}, not {upstream}")
    version = up.frontmatter.get("version", "")
    if not _VERSION.fullmatch(version):
        raise Refused(f"{upstream} at {at} has no X.Y.Z version (found {version!r})")
    cited = set(citations.collect(prd).get(upstream, {}))
    contracts = snapshot.contracts_of(up)
    try:
        bodies = snapshot.extract(contracts, cited)
    except snapshot.Missing as e:
        raise Refused("; ".join(_missing(up, k, n, upstream, at) for k, n in e.items)) from None
    kinds = {fname: kind for kind, fname in contracts.types.items()}
    files = {name: snapshot.header(name, upstream, version, commit, kinds.get(name), contracts.dialect if name == "schema.sql" else None)
             + "\n" + body for name, body in bodies.items()}
    links_path = prd.root / model.LINKS_FILE
    links_text = _set_lock(links_path.read_text(encoding="utf-8"), upstream, version, commit)

    base = prd.root / model.UPSTREAM_DIR / upstream
    rel = f"{model.UPSTREAM_DIR}/{upstream}"
    old = sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
                 and not any(part.startswith(".") for part in p.relative_to(base).parts)) if base.is_dir() else []
    report = []
    for name, text in sorted(files.items()):
        dest = base / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        report.append(f"wrote {rel}/{name}")
    for name in old:
        if name not in files:
            (base / name).unlink()
            report.append(f"removed {rel}/{name}")
    for d in sorted((p for p in base.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True) if base.is_dir() else []:
        if not any(d.iterdir()):
            d.rmdir()
    if base.is_dir() and not any(base.iterdir()):
        base.rmdir()
    links_path.write_text(links_text, encoding="utf-8")
    report.append(f"{model.LINKS_FILE}: locked {upstream} {version} at {commit} ({at})")
    if not cited:
        report.append(f"note: nothing in this PRD cites {upstream}/; the snapshot is empty")
    return report
