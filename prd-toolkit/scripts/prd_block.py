#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Write or refresh the managed prd-toolkit block in a repo's CLAUDE.md.
Exit 0 written or current, 1 stale or missing (--check), 2 usage or error."""
import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import model  # noqa: E402
from prdlint.markdown import tables  # noqa: E402

START = "<!-- prd-toolkit:start -->"
END = "<!-- prd-toolkit:end -->"
TEMPLATE = Path(__file__).resolve().parent.parent / "templates/claude-block.md"


class BlockError(Exception):
    pass


def _rows(prd: model.Prd, number: int):
    sec = next((s for s in prd.sections if s.number == number), None)
    if sec is None:
        return None, []
    return sec, [r for t in tables(sec.body) for r in t.rows]


def _required_skills(prd: model.Prd) -> str:
    _, rows = _rows(prd, 6)
    lines = []
    for r in rows:
        cells = [c.strip() for c in r.cells] + [""] * 3
        if cells[2].strip("`").strip() == "required":
            lines.append(f"- `{cells[1].strip('`').strip()}` for {cells[0]}")
    return "\n".join(lines) or "- none"


def _adopted_areas(prd: model.Prd) -> str:
    sec, rows = _rows(prd, 8)
    if not rows:
        body = " ".join(t for _, t in sec.body) if sec else ""
        if "Not applicable: new project" in body:
            return "all (new project)"
        return "none yet"
    adopted = []
    for r in rows:
        cells = [c.strip() for c in r.cells] + [""] * 2
        if cells[1].strip("`").strip() == "adopted":
            adopted.append(cells[0].strip("`").strip())
    return ", ".join(adopted) or "none yet"


def render_block(prd: model.Prd, prd_rel: str) -> str:
    text = TEMPLATE.read_text()
    slots = {
        "prd_path": prd_rel,
        "version": prd.frontmatter.get("version", "unknown").strip(),
        "required_skills": _required_skills(prd),
        "adopted_areas": _adopted_areas(prd),
    }
    for k, v in slots.items():
        text = text.replace("{{" + k + "}}", v)
    return text.rstrip("\n")


def _scan(lines: list[str], track_fences: bool) -> tuple[list[int], list[int], bool]:
    starts, ends, fence = [], [], None
    for i, ln in enumerate(lines):
        t = ln.strip()
        if fence:
            if t.startswith(fence) and t.strip(fence[0]) == "":
                fence = None
            continue
        if track_fences and (t.startswith("```") or t.startswith("~~~")):
            fence = t[0] * (len(t) - len(t.lstrip(t[0])))
            continue
        if t == START:
            starts.append(i)
        elif t == END:
            ends.append(i)
    return starts, ends, fence is not None


def _find_block(lines: list[str]) -> tuple[int, int] | None:
    starts, ends, unclosed = _scan(lines, True)
    if unclosed:  # an unclosed fence is not trusted as a fence
        starts, ends, _ = _scan(lines, False)
    if not starts and not ends:
        return None
    if len(starts) > 1 or len(ends) > 1:
        raise BlockError("more than one prd-toolkit block")
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise BlockError("prd-toolkit start and end markers are unbalanced")
    return starts[0], ends[0]


def _merged(claude_md: Path, block: str) -> tuple[str, str]:
    """(current text, new text); raises BlockError on bad markers."""
    current = claude_md.read_bytes().decode("utf-8") if claude_md.exists() else ""
    lines = current.splitlines(keepends=True)
    span = _find_block(lines)
    if span is None:
        if not current:
            return current, block + "\n"
        sep = "\n\n" if not current.endswith("\n") else "\n"
        return current, current + sep + block + "\n"
    s, e = span
    eol = lines[e][len(lines[e].rstrip("\r\n")):]
    return current, "".join(lines[:s]) + block + eol + "".join(lines[e + 1:])


def apply_block(claude_md: Path, block: str) -> bool:
    claude_md = claude_md.resolve()  # write through a symlink, never replace it
    current, new = _merged(claude_md, block)
    if new == current:
        return False
    claude_md.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=claude_md.parent, prefix=".CLAUDE.md.")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(new.encode("utf-8"))
        if claude_md.exists():
            os.chmod(tmp, claude_md.stat().st_mode & 0o7777)
        os.replace(tmp, claude_md)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_block.py", description="Write the managed CLAUDE.md block.")
    parser.add_argument("prd_dir")
    parser.add_argument("--claude-md")
    parser.add_argument("--check", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    try:
        prd = model.load(Path(args.prd_dir))
        root = model.repo_root(prd.root)
        claude_md = Path(args.claude_md) if args.claude_md else root / "CLAUDE.md"
        try:
            rel = prd.root.relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = prd.root.as_posix()
        block = render_block(prd, rel)
        if args.check:
            current, new = _merged(claude_md, block)
            if new != current:
                print(f"prd_block: {claude_md} is stale or has no prd-toolkit block", file=sys.stderr)
                return 1
            return 0
        apply_block(claude_md, block)
        return 0
    except model.NotAPrd as e:
        print(f"prd_block: {e}", file=sys.stderr)
        return 2
    except BlockError as e:
        print(f"prd_block: {claude_md}: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_block: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
