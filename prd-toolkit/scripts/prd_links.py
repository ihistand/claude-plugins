#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Links between PRDs in different repositories: add, sync. Exit 0 done, 1 refused (`refused: <why>` on stderr), 2 usage or tool error."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import links, model  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prd_links.py", description="Link PRDs across repositories.")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    p = sub.add_parser("add", help="add an Upstreams row here and the Consumers row in the upstream")
    p.add_argument("prd_dir", metavar="PRD")
    p.add_argument("location", help="a path to the other repository's root, or <git URL>#<PRD folder>")
    p.add_argument("--needs", default="", help="verified, or live in <env> (empty: the default)")
    p = sub.add_parser("sync", help="copy the cited upstream items into the snapshot and write the lock")
    p.add_argument("prd_dir", metavar="PRD")
    p.add_argument("upstream")
    p.add_argument("--ref", help="the upstream ref to copy from (default: its default branch)")
    return parser


def main(argv: list[str]) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    if not args.command:
        parser.print_usage(sys.stderr)
        print("prd_links: give a command", file=sys.stderr)
        return 2
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_links: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_links: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if prd.adoption_unmigrated:
        print(f"prd_links: {prd.root.as_posix()}/prd.md: {model.UNMIGRATED}", file=sys.stderr)
        return 2
    try:
        if args.command == "add":
            report = links.add(prd, args.location, args.needs)
        else:
            report = links.sync(prd, args.upstream, args.ref)
    except links.BadArgument as e:
        print(f"prd_links: {e}", file=sys.stderr)
        return 2
    except (links.Refused, links.Unreachable) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"prd_links: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for line in report:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
