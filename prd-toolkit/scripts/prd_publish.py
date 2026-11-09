#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7", "markdown-it-py>=3.0", "mermaidx==0.11.3"]
# ///
"""Render a PRD folder as one self-contained HTML page. Exit 0 written, 1 refused, 2 usage, dependency or internal error."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator"),
                          ("markdown_it", "markdown-it-py")):
    deps.require(_module, _package)

from prdlint import model, publish  # noqa: E402


def _refuse(*reasons: str) -> int:
    for r in reasons:
        print(f"refused: {r}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_publish.py", description="Render a PRD as one self-contained HTML page.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("render")
    c.add_argument("prd_dir")
    c.add_argument("--out", required=True)
    c.add_argument("--summaries", metavar="JSON")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_publish: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_publish: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if prd.adoption_unmigrated:
        print(f"prd_publish: {prd.root.as_posix()}/prd.md: {model.UNMIGRATED}", file=sys.stderr)
        return 2
    out = Path(args.out).resolve()
    if out == prd.root or prd.root in out.parents:
        return _refuse("--out is inside the PRD folder")
    summaries = None
    if args.summaries:
        try:
            summaries = json.loads(Path(args.summaries).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"prd_publish: cannot read {args.summaries}: {e}", file=sys.stderr)
            return 2
    notes: list[tuple[str, int, str]] = []
    try:
        page = publish.render_page(prd, model.repo_root(prd.root), summaries, date.today(), notes)
    except publish.Refused as e:
        return _refuse(*e.reasons)
    except Exception as e:
        print(f"prd_publish: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for file, line, reason in notes:
        print(f"prd_publish: diagram at {file}:{line} shown as source: {reason}", file=sys.stderr)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
    except OSError as e:
        print(f"prd_publish: cannot write {out}: {e}", file=sys.stderr)
        return 2
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
