#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Lint a PRD folder. Exit 0 clean, 1 violations, 2 usage, dependency or internal error."""
import argparse
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import model, registry  # noqa: E402


def _display_root(root: Path) -> str:
    root = root.resolve()
    try:
        return root.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return root.as_posix()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_lint.py", description="Lint a PRD folder.")
    parser.add_argument("prd_dir", nargs="?")
    parser.add_argument("--list-rules", action="store_true")
    parser.add_argument("--sample-tids", type=int, metavar="N")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2

    if args.list_rules:
        from prdlint import rules  # noqa: F401

        for name in sorted(registry.RULES):
            print(name)
        return 0
    if not args.prd_dir:
        parser.print_usage(sys.stderr)
        return 2

    if args.sample_tids is not None and args.sample_tids < 0:
        print("prd_lint: --sample-tids N must be >= 0", file=sys.stderr)
        return 2

    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_lint: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_lint: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if args.sample_tids is not None:
        tids = [t.id for t in prd.test_cases]
        for tid in random.sample(tids, min(args.sample_tids, len(tids))):
            print(tid)
        return 0

    try:
        findings = registry.run(prd)
    except registry.RuleCrash as e:
        print(f"prd_lint: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_lint: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    prefix = _display_root(prd.root)
    for f in findings:
        print(f"{os.path.join(prefix, f.file)}:{f.line}: {f.rule}: {f.message}" if prefix != "." else str(f))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
