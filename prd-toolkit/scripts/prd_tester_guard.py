#!/usr/bin/env python3
"""PreToolUse hook: confine the prd-tester agent to the PRD folder, the scratchpad and the test roots.

Reads the hook JSON on stdin. Exit 0 allows the call; exit 2 blocks it with one stderr line.
Acts only when agent_type is `prd-tester` or ends with `:prd-tester`; every other session exits 0
before any filesystem or git work. For the tester it never fails open: any error blocks.
Standard library only; it parses testing.md itself and does not import prdlint.
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

READ_TOOLS = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
KNOWN_TOOLS = READ_TOOLS | WRITE_TOOLS | {"Bash"}
SHELLS = {"cd", "env", "sh", "bash", "zsh", "eval", "exec"}
EXPANSIONS = ("$(", "`", "<(", ">(")
PY_COMPILE = ["uv", "run", "python", "-m", "py_compile"]

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_SLOT = re.compile(r"^- \*\*([^*]+?)\.\*\*")
_MARKER = re.compile(r"\[NEEDS CLARIFICATION:[^\]]*\]")
_BACKTICKED = re.compile(r"`([^`]+)`")
_ITEM_LIST = re.compile(r"\s*(`[^`]+`(?:\s*,\s*`[^`]+`)*)")
_OP_CHARS = set("();<>|&")
_TASK_OUTPUT = re.compile(r"^[A-Za-z0-9_-]+\.output$")
# A glob character the shell would expand (outside quotes, unescaped) is lexed as its mask, so a check can tell
# `grep 'T-0*' tests` from `grep s* tests`; every check but grep's reads the token with its glob characters back.
_GLOB_MASK = {"*": "\x01", "?": "\x02", "[": "\x03"}
_UNMASK = str.maketrans({v: k for k, v in _GLOB_MASK.items()})
# grep (0.8.4): the only options the tester may give it; `-R` and `--dereference-recursive` follow symbolic links.
GREP_FLAGS = set("rnlLciwxvoqsHhEF")
GREP_VALUE_FLAGS = set("efmABC")
GREP_GLOB_OPTS = ("--include=", "--exclude=")


class Block(Exception):
    """The call is not allowed; the message is the stderr line."""


# ---- testing.md (must agree with prdlint.model on the same input) ----

def _sections(text: str) -> list[tuple[str, list[str]]]:
    """(title, body lines) for each level-2 section; headings in code fences are ignored."""
    out: list[tuple[str, list[str]]] = []
    in_fence = False
    for line in text.split("\n"):
        if _FENCE.match(line):
            in_fence = not in_fence
            if out:
                out[-1][1].append(line)
            continue
        m = None if in_fence else _HEADING.match(line)
        if m and len(m.group(1)) <= 2:
            out.append((m.group(2) if len(m.group(1)) == 2 else "\0closer", []))
            continue
        if out:
            out[-1][1].append(line)
    return out


def _section(text: str, title: str) -> list[str] | None:
    for t, body in _sections(text):
        if t.strip().lower() == title:
            return body
    return None


def parse_test_roots(text: str) -> list[str] | None:
    """The backticked list after `Test roots:` in the Harness Layout bullet; None when absent."""
    body = _section(text, "harness")
    roots: list[str] | None = None
    in_fence = False
    for line in body or []:
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        m = _SLOT.match(line)
        if in_fence or not m or m.group(1) != "Layout" or "Test roots:" not in line:
            continue
        tail = _MARKER.sub("", line.split("Test roots:", 1)[1])
        lst = _ITEM_LIST.match(tail)
        roots = _BACKTICKED.findall(lst.group(1)) if lst else []
    return roots


def _cells(line: str) -> list[str]:
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    cells, cur, in_code, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if c == "`":
            in_code = not in_code
        if c == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def parse_harness_commands(text: str) -> list[list[str]]:
    """Token lists of the backticked Harness command cells of the Levels table."""
    body = _section(text, "levels") or []
    cmds: list[list[str]] = []
    in_table = False
    for line in body:
        if not line.lstrip().startswith("|"):
            if in_table:
                break
            continue
        in_table = True
        cells = _cells(line)
        if len(cells) < 2:
            continue
        m = _BACKTICKED.search(cells[1])
        if m:
            try:
                toks = shlex.split(m.group(1))
            except ValueError:
                continue
            if toks:
                cmds.append(toks)
    return cmds


# ---- roots ----

class Context:
    """Read roots are PRD + scratch + test roots + the vendored packs (outside degraded mode); write roots are scratch + test roots only, so the
    tester can never edit the PRD (and with it its own policy)."""

    def __init__(self, data: dict):
        cwd = data.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            raise Block("prd-tester: hook input has no cwd")
        self.cwd = Path(cwd).resolve()
        self.top = self._toplevel()
        self.prd_roots: list[Path] = []
        self.test_roots: list[Path] = []
        self.harness: list[list[str]] = []
        self.scratch: Path | None = None
        self.problems: list[str] = []
        self._load_prds()
        sp = data.get("scratchpad_dir")
        if isinstance(sp, str) and sp:
            p = (self.cwd / sp).resolve()
            if len(p.parts) > 1:
                self.scratch = p
        # Claude Code writes a background task's output in the `tasks` folder beside the scratchpad; a symlink is no tasks folder.
        tasks = self.scratch.parent / "tasks" if self.scratch else None
        self.tasks_dir: Path | None = tasks if tasks and tasks.is_dir() and not tasks.is_symlink() else None
        # The vendored packs are part of the PRD's harness; a symlinked `.prd-toolkit` or `packs` is no pack folder,
        # even one that points inside the repository.
        packs = self.top / ".prd-toolkit" / "packs"
        self.packs_root: Path | None = packs if packs.is_dir() and packs.resolve() == packs else None

    def _toplevel(self) -> Path:
        try:
            out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=self.cwd, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=10, check=True).stdout.strip()
            return Path(out).resolve() if out else self.cwd
        except (OSError, subprocess.SubprocessError):
            return self.cwd

    def _load_prds(self) -> None:
        base = (self.top / "docs" / "prd").resolve()
        prds: list[Path] = []
        if base.is_dir():
            for d in sorted(base.iterdir()):
                r = d.resolve()
                # the exact name: a PRD.md folder is not a PRD, even where the filesystem ignores case
                if d.is_dir() and r.parent == base and any(p.name == "prd.md" and p.is_file() for p in r.iterdir()):
                    prds.append(r)
        if not prds:
            self.problems.append("no docs/prd/*/ folder")
            return
        self.prd_roots = prds
        for r in prds:
            name = r.name
            try:
                text = (r / "testing.md").read_text(encoding="utf-8")
            except OSError:
                self.problems.append(f"{name}/testing.md is missing")
                continue
            roots = parse_test_roots(text)
            if not roots:
                self.problems.append(f"{name}/testing.md has no `Test roots:` entries")
                continue
            valid = False
            for entry in roots:
                p = (self.top / entry).resolve()
                if p == self.top or not p.is_relative_to(self.top):
                    self.problems.append(f"{name}/testing.md test root {entry!r} is not inside the repo")
                elif any(p.is_relative_to(q) or q.is_relative_to(p) for q in prds):
                    self.problems.append(f"{name}/testing.md test root {entry!r} overlaps a PRD folder")
                else:
                    self.test_roots.append(p)
                    valid = True
            if valid:
                self.harness += parse_harness_commands(text)

    @property
    def degraded(self) -> bool:
        """No PRD yields a valid test root: the tester may only read the PRD folders."""
        return not self.test_roots

    def read_roots(self) -> list[Path]:
        if self.degraded:
            return self.prd_roots
        return (self.prd_roots + ([self.scratch] if self.scratch else []) + self.test_roots
                + ([self.packs_root] if self.packs_root else []))

    def write_roots(self) -> list[Path]:
        if self.degraded:
            return []
        return ([self.scratch] if self.scratch else []) + self.test_roots

    def inside(self, raw: str, roots: list[Path], base: Path | None = None) -> bool:
        p = ((base or self.cwd) / raw).resolve()
        return any(p.is_relative_to(r) for r in roots)

    def can_read(self, raw: str) -> bool:
        return self.inside(raw, self.read_roots())

    def can_read_task_output(self, raw: str) -> bool:
        """Read (and only Read) of `<id>.output` directly in the tasks folder: a symlink or `..` that leaves
        the folder resolves to another parent and fails."""
        if self.degraded or self.tasks_dir is None:
            return False
        p = (self.cwd / raw).resolve()
        return p.parent == self.tasks_dir and bool(_TASK_OUTPUT.match(p.name))

    def can_write(self, raw: str, base: Path | None = None) -> bool:
        """`raw` resolved from `base` (default: cwd) is inside a write root."""
        return self.inside(raw, self.write_roots(), base)

    def deny(self, verb: str) -> Block:
        roots = self.read_roots() if verb == "read" else self.write_roots()
        msg = f"prd-tester may only {verb} under: {', '.join(str(r) for r in roots) or '(none)'}"
        if self.problems:
            msg += f" (testing.md is missing or has no Test roots: {'; '.join(self.problems)})"
        return Block(" ".join(msg.split("\n")))


# ---- tools ----

def check_path(ctx: Context, raw: object, verb: str) -> None:
    ok = ctx.can_read if verb == "read" else ctx.can_write
    if not isinstance(raw, str) or not raw or not ok(raw):
        raise ctx.deny(verb)


def has_glob(s: str) -> bool:
    return any(c in s for c in "*?[")


def check_bash(ctx: Context, cmd: object) -> None:
    deny = ctx.deny("run")
    if ctx.degraded or not isinstance(cmd, str) or not cmd.strip():
        raise deny
    if any(x in cmd for x in EXPANSIONS):
        raise deny
    for line in cmd.split("\n"):
        for seg in _segments(line, deny):
            _check_segment(ctx, seg, deny)


def _mask_globs(line: str, deny: Block) -> str:
    """`line` with each glob character the shell would expand replaced by its mask; quotes and escapes are kept as
    they are, so the lexer splits the masked line exactly as the original one."""
    if any(m in line for m in _GLOB_MASK.values()):
        raise deny
    out, quote, i = [], None, 0
    while i < len(line):
        c = line[i]
        if quote == "'":
            quote = None if c == "'" else quote
        elif c == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2])
            i += 2
            continue
        elif quote == '"':
            quote = None if c == '"' else quote
        elif c in "'\"":
            quote = c
        elif c in _GLOB_MASK:
            c = _GLOB_MASK[c]
        out.append(c)
        i += 1
    return "".join(out)


def _segments(line: str, deny: Block) -> list[list[str]]:
    """The line's command segments, each a token list in which an unquoted glob character is still masked."""
    line = _mask_globs(line, deny)
    try:
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        lex.commenters = ""
        toks = list(lex)
    except ValueError:
        raise deny
    segs: list[list[str]] = [[]]
    for t in toks:
        if set(t) <= _OP_CHARS and t in ("&&", "||", ";", "|", "&", "|&", ";;"):
            segs.append([])
        else:
            segs[-1].append(t)
    return [s for s in segs if s]


def _check_segment(ctx: Context, masked: list[str], deny: Block) -> None:
    toks = [t.translate(_UNMASK) for t in masked]
    args: list[str] = []
    margs: list[str] = []  # args as lexed, an unquoted glob character still masked
    i = 0
    while i < len(toks):
        t = toks[i]
        if set(t) <= _OP_CHARS:
            if t not in (">", ">>", "<", ">&", ">|") or i + 1 >= len(toks):
                raise deny
            target = toks[i + 1]
            if args and args[-1].isdigit():
                args.pop()  # a file descriptor, as in 2>&1
                margs.pop()
            if not (t == ">&" and (target.isdigit() or target == "-")) and target != "/dev/null":
                if t == "<":
                    if has_glob(target) or not ctx.can_read(target):
                        raise ctx.deny("read")
                elif has_glob(target) or not ctx.can_write(target):
                    raise ctx.deny("write")
            i += 2
            continue
        if "$" in t or "{" in t or t.startswith("~"):
            raise deny
        args.append(t)
        margs.append(masked[i])
        i += 1
    if not args or args[0] in SHELLS:
        raise deny
    for h in ctx.harness:
        if args[: len(h)] == h:
            _check_harness_args(ctx, args[len(h):], _harness_base(ctx, h))
            return
    if args[0] == "grep":
        _check_grep(ctx, margs[1:], deny)
        return
    if args[: len(PY_COMPILE)] == PY_COMPILE:
        paths, verb = _non_flags(args[len(PY_COMPILE):]), "write"
    elif args[0] == "mkdir":
        paths, verb = _non_flags(args[1:]), "write"
    elif args[0] == "ls":
        paths, verb = _non_flags(args[1:]), "read"
    else:
        raise deny
    ok = ctx.can_read if verb == "read" else ctx.can_write
    if not paths or not all(not has_glob(p) and ok(p) for p in paths):
        raise ctx.deny(verb)


def _non_flags(args: list[str]) -> list[str]:
    out, ended = [], False
    for a in args:
        if not ended and a == "--":
            ended = True
        elif ended or not a.startswith("-"):
            out.append(a)
    return out


# Long options whose value is a path.
PATH_OPTS = {"--junitxml", "--junit-xml", "--basetemp", "--rootdir", "--confcutdir", "--config-file", "-c",
             "--log-file", "--report-log", "--resultlog", "--cache-dir", "--ignore", "--ignore-glob", "--deselect",
             "--html", "--cov-report"}
# Short options that take a value (`c` and `o` are paths/ini overrides; the rest are expressions or names).
SHORT_VALUE_OPTS = "ockmpnWr"


def _looks_like_path(v: str) -> bool:
    v = v.split("::", 1)[0]
    return "/" in v or v.endswith(".py")


def _harness_base(ctx: Context, harness: list[str]) -> Path:
    """Where the harness reads its path arguments from: uv's `--directory <d>` (or `--directory=<d>`), resolved from
    cwd, when the harness is a uv command that holds one; else cwd."""
    if harness and harness[0] == "uv":
        for n, t in enumerate(harness):
            if t == "--directory" and n + 1 < len(harness):
                return (ctx.cwd / harness[n + 1]).resolve()
            if t.startswith("--directory="):
                return (ctx.cwd / t.partition("=")[2]).resolve()
    return ctx.cwd


def _check_harness_args(ctx: Context, rest: list[str], base: Path) -> None:
    """Arguments after a harness command may only point at scratch or test roots, each resolved from `base`."""
    def need(v: str) -> None:
        v = v.split("::", 1)[0]
        if has_glob(v) or not ctx.can_write(v, base):
            raise ctx.deny("write")

    def check_ini(kv: str) -> None:
        key, _, val = kv.partition("=")
        if val and (_looks_like_path(val) or key == "cache_dir" or any(w in key for w in ("dir", "path", "file"))):
            need(val)

    i = 0
    while i < len(rest):
        a = rest[i]
        i += 1
        if a == "--override-ini" or a.startswith("--override-ini="):
            if a == "--override-ini":
                if i >= len(rest):
                    raise ctx.deny("write")
                check_ini(rest[i])
                i += 1
            else:
                check_ini(a.partition("=")[2])
        elif a.startswith("--") and "=" in a:
            opt, _, val = a.partition("=")
            if opt in PATH_OPTS or _looks_like_path(val):
                need(val)
        elif a in PATH_OPTS:
            if i >= len(rest):
                raise ctx.deny("write")
            need(rest[i])
            i += 1
        elif a.startswith("-") and not a.startswith("--") and len(a) >= 2:
            # A cluster of short flags: the first option that takes a value swallows the rest of the token,
            # or the next token when nothing follows it.
            j = next((n for n, ch in enumerate(a) if n and ch in SHORT_VALUE_OPTS), 0)
            if not j:
                continue
            val = a[j + 1:]
            if not val:
                if i >= len(rest):
                    raise ctx.deny("write")
                val, i = rest[i], i + 1
            if a[j] == "c":
                need(val)
            elif a[j] == "o":
                check_ini(val)
        elif not a.startswith("-") and _looks_like_path(a):
            need(a)


def _check_grep(ctx: Context, margs: list[str], deny: Block) -> None:
    """`grep` with options from GREP_FLAGS, GREP_VALUE_FLAGS and GREP_GLOB_OPTS only (short flags may cluster, a value
    is the rest of its token or the next token), the pattern the first operand unless `-e` or `-f` gives it, `-f`'s
    file readable, and at least one file operand, none with a glob character, each readable. `margs` still holds each
    unquoted glob character masked: one in the pattern or an option value would be expanded by the shell into more
    operands, so it is refused; only an `--include=` or `--exclude=` value may hold one. Every option comes before the
    first operand, so GNU and BSD grep read the same tokens as operands."""
    def unquoted_glob(t: str) -> bool:
        return t != t.translate(_UNMASK)

    def readable(m: str) -> None:
        p = m.translate(_UNMASK)
        if not p or has_glob(p) or not ctx.can_read(p):
            raise ctx.deny("read")

    operands: list[str] = []
    pattern_given, ended, i = False, False, 0
    while i < len(margs):
        a = margs[i]
        i += 1
        if ended or not a.startswith("-") or a == "-":
            operands.append(a)
        elif operands:
            # GNU grep reads an option after an operand as an option, BSD grep as a file (`--` too): neither is checked
            raise deny
        elif a == "--":
            ended = True
        elif a.startswith(GREP_GLOB_OPTS):
            continue
        elif a.startswith("--"):
            raise deny
        else:
            for j, ch in enumerate(a[1:], 1):
                if ch in GREP_FLAGS:
                    continue
                if ch not in GREP_VALUE_FLAGS:
                    raise deny
                value = a[j + 1:]
                if not value:
                    if i >= len(margs):
                        raise deny
                    value, i = margs[i], i + 1
                if unquoted_glob(value):
                    raise deny
                if ch in "ef":
                    pattern_given = True
                if ch == "f":
                    readable(value)
                break
    if not pattern_given:
        if not operands:
            raise deny
        pattern, operands = operands[0], operands[1:]
        if unquoted_glob(pattern):
            raise deny
    if not operands:
        raise ctx.deny("read")
    for m in operands:
        readable(m)


def check(data: dict) -> None:
    tool, ti = data.get("tool_name"), data.get("tool_input")
    ctx = Context(data)
    if tool not in KNOWN_TOOLS or not isinstance(ti, dict):
        raise Block(f"prd-tester: cannot check tool {tool!r}")
    if ctx.degraded and tool not in READ_TOOLS:
        raise ctx.deny("run" if tool == "Bash" else "write")
    if tool == "Bash":
        check_bash(ctx, ti.get("command"))
    elif tool == "NotebookEdit":
        check_path(ctx, ti.get("notebook_path"), "write")
    elif tool in ("Glob", "Grep"):
        check_path(ctx, ti.get("path"), "read")
        pat = ti.get("pattern") if tool == "Glob" else None
        if isinstance(pat, str) and (pat.startswith(("/", "~")) or ".." in pat.split("/")):
            raise ctx.deny("read")
    elif tool == "Read":
        fp = ti.get("file_path")
        if not (isinstance(fp, str) and fp and ctx.can_read_task_output(fp)):
            check_path(ctx, fp, "read")
    else:
        check_path(ctx, ti.get("file_path"), "write")


def is_tester(agent_type: object) -> bool:
    return isinstance(agent_type, str) and (agent_type == "prd-tester" or agent_type.endswith(":prd-tester"))


def main() -> int:
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
        if sys.version_info < (3, 9):
            # Path.is_relative_to and friends need 3.9: an older python3 blocks the tester, never anyone else.
            if "prd-tester" in raw:
                print("prd-tester guard error: python3 is older than 3.9 (blocked)", file=sys.stderr)
                return 2
            return 0
        try:
            data = json.loads(raw)
        except ValueError:
            # Without valid JSON we cannot read agent_type. Exit 0 unless the raw input mentions
            # prd-tester, so garbage never blocks the user's own session but a tester's never slips through.
            if "prd-tester" in raw:
                print("prd-tester guard error: unreadable hook input (blocked)", file=sys.stderr)
                return 2
            return 0
        if not isinstance(data, dict) or not is_tester(data.get("agent_type")):
            return 0
        check(data)
    except Block as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:  # the tester never gets a fail-open path
        msg = " ".join(f"{e}".split())
        print(f"prd-tester guard error: {type(e).__name__}: {msg} (blocked)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
