"""The items an adoption area asks its owner to confirm: requirements, bugs, questions and markers."""
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

try:
    import fcntl
except ImportError:  # no cross-process lock off POSIX; the in-process lock and the atomic replace remain
    fcntl = None

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
    related: list[str] = field(default_factory=list)  # a requirement's open E-nnn entries that touch it


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


def _in_repo(root: Path, path: str, commit: str | None, cache: dict) -> bool:
    """An extensionless name (`Makefile`) is a file only when git has it at that commit."""
    key = ("exists", commit or "HEAD", path)
    if key not in cache:
        try:
            cache[key] = subprocess.run(["git", "cat-file", "-e", f"{commit or 'HEAD'}:{path}"], cwd=root,
                                        capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.SubprocessError):
            cache[key] = False
    return cache[key]


def _excerpts(root: Path, text: str, cache: dict) -> list[tuple[str, int, str | None, str]]:
    out = []
    for p, n, sha in _CITE.findall(text):
        # a path, not a time or a host:port
        if "/" in p or re.search(r"\.\w+$", p) or _in_repo(root, p, sha or None, cache):
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


def _bare_name(chunk: str) -> str | None:
    """The key a word outside backticks names, or None. Only an identifier with an underscore (NOTES_LIMIT)
    or in camelCase (maxSize) names one: a dotted or kind:name word names its last part, and a path part,
    an ID prefix (FR-001), an all-caps word (UNIQUE, POST) or a version (v2) names nothing. Quotes and a
    trailing colon or full stop are dropped, and the <kind>:<prd>/<name> form names <name>."""
    chunk = chunk.strip("'\"").rstrip(":.")
    if re.fullmatch(r"[a-z]+:[a-z][a-z0-9-]*/[^/\s]+", chunk):
        chunk = chunk.rsplit("/", 1)[1]
    elif "/" in chunk:
        return None
    name = re.split(r"[:.]", chunk.strip("."))[-1]
    if re.fullmatch(r"[A-Za-z_]\w*", name) and re.search(r"[A-Za-z]", name) and re.search(r"_|[a-z][A-Z]", name):
        return name
    return None


def _named(prd: Prd, area: str, blocks: list[ReqBlock]) -> set[str]:
    """Contract keys the area names: backticked spans and, outside backticks, underscore or camelCase
    identifiers on its Traces lines (see _bare_name), and its test cases' targets. Prose names nothing."""
    words: set[str] = set()
    for b in blocks:
        for _, text in _field_lines(b.lines, "Traces"):
            for span in re.findall(r"`([^`]+)`", text):
                for tok in re.findall(r"[A-Za-z_][\w.-]*", span):
                    words.add(tok.strip(".").rsplit(".", 1)[-1])  # `settings.KEY` names KEY
            for chunk in re.split(r"[\s;,()]+", re.sub(r"`[^`]*`", " ", text)):
                if name := _bare_name(chunk):
                    words.add(name)
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
    for i in items:
        i.related = [e.id for e in prd.errors_ledger.values() if e.open and any(t == i.id for t, _ in e.touches)]
    items += _bugs(prd, root, area, ids, cache)
    items += _questions(prd, ids)
    items += _markers(prd, area, blocks)
    if not items:
        raise Refused(f"area {area} has no item to confirm")
    seen: set[str] = set()
    for i in items:  # answers apply by ID, so two items under one ID could never both be answered
        if i.id in seen:
            raise Refused(f"item ID {i.id} appears twice in {i.where}")
        seen.add(i.id)
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


# --- the answers file and the local server -------------------------------------------------------------------

REQUIRES_TEXT = {"correct", "bug", "ask", "answer"}  # `correct` is also satisfied by a non-empty `acs`
ALLOWED = {"requirement": {"confirm", "correct", "bug", "ask"}, "bug": {"bug", "intended", "ask"},
           "question": {"intended", "fix", "answer"}, "marker": {"answer"}}
MAX_BODY = 1024 * 1024
CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'")
EXCLUDE_LINE = "/.prd-confirm-*.json"


def answers_path(repo_root: Path, area: str) -> Path:
    return Path(repo_root) / f".prd-confirm-{area}.json"


def load_answers(path: Path) -> dict:
    """The saved file; {} when it does not exist. A file that exists but is not an answers object is refused,
    so an accepted answer is never silently thrown away."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise Refused(f"answers file {path} cannot be read: {e}") from e
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise Refused(f"answers file {path} is not valid JSON; move it aside to start over")
    return data


def save_answers(path: Path, data: dict) -> None:
    """Rewrite the whole file through a temporary file in the same folder, then os.replace."""
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f"{path.stem}.tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def open_ids(items: list[Item], answers: dict) -> list[str]:
    """Items with no answer, or whose answer was given to a different text (its fingerprint differs)."""
    saved = answers.get("answers", {}) if isinstance(answers, dict) else {}
    return [i.id for i in items if not isinstance(saved.get(i.id), dict) or saved[i.id].get("fingerprint") != i.fingerprint]


def ensure_excluded(repo_root: Path) -> None:
    """Add `/.prd-confirm-*.json` to the common git dir's info/exclude, once."""
    try:
        out = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=repo_root, capture_output=True, text=True,
                             encoding="utf-8", timeout=30, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    common = Path(out)
    if not common.is_absolute():
        common = Path(repo_root) / common
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if EXCLUDE_LINE in text.splitlines():
        return
    with exclude.open("a", encoding="utf-8") as f:
        f.write(("" if not text or text.endswith("\n") else "\n") + EXCLUDE_LINE + "\n")


class _Bad(Exception):
    def __init__(self, status: int, why: str):
        super().__init__(why)
        self.status, self.why = status, why


class _State:
    """Everything a request needs; every write to the answers file goes through `change`."""

    def __init__(self, prd: Prd, area: str, items: list[Item], summaries: dict, page: str, token: str,
                 idle_minutes: float, request_timeout: float):
        self.prd, self.area, self.items, self.summaries, self.page, self.token = prd, area, items, summaries, page, token
        self.request_timeout = request_timeout
        self.by_id = {i.id: i for i in items}
        self.root = repo_root(prd.root)
        self.path = answers_path(self.root, area)
        self.idle_seconds = idle_minutes * 60
        self.last = time.monotonic()
        self.end: str | None = None
        self.lock = threading.Lock()
        self.head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True,
                                   encoding="utf-8", timeout=30).stdout.strip()
        load_answers(self.path)  # a corrupt file refuses the server before anything is served

    def snapshot(self) -> dict:
        with self.lock:
            return load_answers(self.path)

    def change(self, apply) -> dict:
        """Under one lock (and a directory lock across processes): re-read the disk, apply one change, save."""
        with self.lock:
            dirfd = None
            if fcntl is not None:
                try:
                    dirfd = os.open(self.root, os.O_RDONLY)
                    try:
                        fcntl.flock(dirfd, fcntl.LOCK_EX)
                    except OSError:
                        os.close(dirfd)
                        dirfd = None
                except OSError:
                    dirfd = None
            try:
                answers = load_answers(self.path).get("answers")
                data = {"prd": self.prd.frontmatter.get("prd", ""), "area": self.area,
                        "commit": self.head, "answers": answers if isinstance(answers, dict) else {}}
                apply(data["answers"])
                save_answers(self.path, data)
                return data
            finally:
                if dirfd is not None:
                    os.close(dirfd)

    def answer(self, body: dict) -> dict:
        iid, decision = body.get("id"), body.get("decision")
        if not isinstance(iid, str) or iid not in self.by_id:
            raise _Bad(400, f"unknown item {iid!r}")
        item = self.by_id[iid]
        if not isinstance(decision, str) or decision not in {d for ds in ALLOWED.values() for d in ds}:
            raise _Bad(400, f"unknown decision {decision!r}")
        if decision not in ALLOWED[item.kind]:
            raise _Bad(400, f"decision {decision} is not allowed for a {item.kind}")
        text, acs = body.get("text"), body.get("acs")
        if text is not None and not isinstance(text, str):
            raise _Bad(400, "text must be a string")
        text = (text or "").strip()
        if acs is not None and not (isinstance(acs, dict) and all(isinstance(v, str) for v in acs.values())):
            raise _Bad(400, "acs must map an AC ID to text")
        if acs is not None and decision != "correct":
            raise _Bad(400, "acs is allowed only with correct")
        known = {a for a, _ in item.acs}
        for k in acs or {}:
            if k not in known:
                raise _Bad(400, f"{k} is not an AC of {item.id}")
        acs = {k: v.strip() for k, v in (acs or {}).items() if v.strip()}
        if decision == "correct":
            if not text and not acs:
                raise _Bad(400, "correct needs text or an edited AC")
        elif decision in REQUIRES_TEXT and not text:
            raise _Bad(400, f"{decision} needs text")
        entry: dict[str, Any] = {"decision": decision}
        if text:
            entry["text"] = text
        if acs:
            entry["acs"] = acs
        entry["fingerprint"] = item.fingerprint
        entry["where"] = item.where  # with `served`, how the session finds the item again
        entry["served"] = item.text
        entry["at"] = datetime.now(timezone.utc).isoformat()
        return self.change(lambda a: a.__setitem__(item.id, entry))

    def undo(self, body: dict) -> dict:
        iid = body.get("id")
        if not isinstance(iid, str) or iid not in self.by_id:
            raise _Bad(400, f"unknown item {iid!r}")
        return self.change(lambda a: a.pop(iid, None))

    def finish(self) -> list[str]:
        """The open IDs; when there are none, mark the run done. Check and mark share the write lock."""
        with self.lock:
            pending = open_ids(self.items, load_answers(self.path))
            if not pending:
                self.end = "done"
            return pending

    def listing(self) -> dict:
        data = self.snapshot()
        saved = data.get("answers", {}) if isinstance(data.get("answers"), dict) else {}
        shown = [{**asdict(i), "summary": self.summaries.get(i.id)} for i in self.items]
        changed = [i.id for i in self.items if isinstance(saved.get(i.id), dict)
                   and saved[i.id].get("fingerprint") != i.fingerprint]
        return {"area": self.area, "items": shown, "answers": saved, "open": open_ids(self.items, data),
                "changed": changed}


def _handler(state: _State) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"
        timeout = state.request_timeout  # a stalled client frees its thread

        def log_message(self, *args) -> None:  # no per-request log
            pass

        def _send(self, status: int, body: bytes, ctype: str, csp: bool = False) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            if csp:
                self.send_header("Content-Security-Policy", CSP)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, obj: Any) -> None:
            self._send(status, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

        def _authorized(self, query: dict, header: bool) -> bool:
            given = (query.get("token") or [""])[0]
            if not given and header:
                given = self.headers.get("X-Prd-Token", "")
            return hmac.compare_digest(given.encode("utf-8"), state.token.encode("utf-8"))

        def _body(self) -> dict:
            raw = self.headers.get("Content-Length")
            try:
                n = int(raw) if raw is not None else -1
            except ValueError:
                n = -1
            if n < 0:
                raise _Bad(400, "a POST needs a Content-Length")
            if n > MAX_BODY:
                left = n
                try:
                    while left > 0:  # read it off the wire so the client sees the reply, not a reset
                        chunk = self.rfile.read(min(65536, left))
                        if not chunk:
                            break
                        left -= len(chunk)
                except OSError:
                    pass
                raise _Bad(413, "request body is over 1 MB")
            try:
                data = self.rfile.read(n)
            except OSError:  # timed out waiting for the rest of the body
                raise _Bad(408, "request timed out") from None
            if len(data) < n:
                raise _Bad(400, "body is shorter than its Content-Length")
            try:
                obj = json.loads(data.decode("utf-8") or "{}")
            except ValueError:
                raise _Bad(400, "body is not JSON") from None
            if not isinstance(obj, dict):
                raise _Bad(400, "body must be a JSON object")
            return obj

        def _route(self, method: str, route: str) -> None:
            if method == "GET" and route == "/":
                self._send(200, state.page.encode("utf-8"), "text/html; charset=utf-8", csp=True)
            elif method == "GET" and route == "/items":
                self._json(200, state.listing())
            elif method == "POST" and route in ("/answer", "/undo"):
                body = self._body()
                data = state.answer(body) if route == "/answer" else state.undo(body)
                self._json(200, {"open": open_ids(state.items, data)})
            elif method == "POST" and route == "/done":
                self._body()
                pending = state.finish()
                if pending:
                    self._json(409, {"open": pending})
                else:
                    self._json(200, {"open": []})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                raise _Bad(404, "no such request")

        def _handle(self, method: str) -> None:
            parts = urlsplit(self.path)
            query = parse_qs(parts.query)
            route = parts.path
            try:
                if not self._authorized(query, header=route != "/"):
                    raise _Bad(403, "missing or wrong token")
                state.last = time.monotonic()  # only an authorized request keeps the server alive
                self._route(method, route)
            except _Bad as e:
                self._json(e.status, {"error": e.why})
            except Refused as e:
                self._json(500, {"error": str(e)})
            except (BrokenPipeError, ConnectionError):
                pass
            except Exception:  # noqa: BLE001 - nothing may reset the connection or print a traceback
                self._json(500, {"error": "internal error"})

        def do_GET(self) -> None:
            self._handle("GET")

        def do_POST(self) -> None:
            self._handle("POST")

    return Handler


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128  # a burst of browser requests must not be reset

    def handle_error(self, request, client_address) -> None:  # never a traceback on the owner's terminal
        pass

    def __init__(self, address: tuple[str, int], state: _State):
        self.state = state
        super().__init__(address, _handler(state))


def make_server(prd: Prd, area: str, items: list[Item], summaries: dict, page: str, port: int = 0,
                idle_minutes: float = 120, request_timeout: float = 30) -> tuple[ThreadingHTTPServer, str]:
    """A server bound to 127.0.0.1 only, and its token. Raises OSError when `port` is in use, and Refused
    when the answers file exists but is not valid."""
    token = secrets.token_hex(32)
    state = _State(prd, area, items, summaries, page, token, idle_minutes, request_timeout)
    return _Server(("127.0.0.1", port), state), token


def run(server: ThreadingHTTPServer) -> int:
    """Serve until Done (0), Ctrl-C or the idle timeout (3)."""
    if not isinstance(server, _Server):
        raise TypeError("run() takes a server made by make_server")
    state = server.state
    stop = threading.Event()

    def watch() -> None:
        while not stop.wait(0.05):
            if time.monotonic() - state.last > state.idle_seconds:
                state.end = "idle"
                server.shutdown()
                return

    state.last = time.monotonic()
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        server.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        state.end = "interrupted"
    finally:
        stop.set()
        watcher.join(5)
    return 0 if state.end == "done" else 3


def page_path() -> Path:
    """The form page: the plugin's template, or the copy vendored beside the scripts."""
    from . import hooks
    return hooks.PLUGIN_ROOT / "templates" / hooks.CONFIRM_PAGE if hooks.is_plugin() else hooks.SCRIPTS / hooks.CONFIRM_PAGE
