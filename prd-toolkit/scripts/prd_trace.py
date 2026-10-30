#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Trace a PRD folder against its repo's tests and commits. Exit 0 clean, 1 findings, 2 usage, dependency or internal error."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import model, trace  # noqa: E402


def _display_root(root: Path) -> str:
    root = root.resolve()
    try:
        return root.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return root.as_posix()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_trace.py", description="Trace a PRD folder against tests and commits.")
    parser.add_argument("prd_dir", nargs="?")
    parser.add_argument("--range", metavar="BASE..HEAD", help="also check commit-refs on this git revision range")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    if not args.prd_dir:
        parser.print_usage(sys.stderr)
        return 2

    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_trace: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_trace: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    try:
        findings = trace.run_trace(prd, model.repo_root(prd.root), args.range)
    except trace.BadRange as e:
        print(f"prd_trace: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_trace: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    prefix = _display_root(prd.root)
    for f in findings:
        print(f"{os.path.normpath(os.path.join(prefix, f.file))}:{f.line}: {f.rule}: {f.message}" if prefix != "." else str(f))
    return 1 if findings else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
