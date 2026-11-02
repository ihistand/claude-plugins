#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Links between PRDs in different repositories: add, sync, check, impact.

Exit 0 done or clean, 1 refused (`refused: <why>` on stderr) or drift, 2 usage or tool error, 3 (check and impact)
nothing drifted but a side was unreachable; `check --ci` exits 0 there, after printing the unreachable line.
"""
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
    p = sub.add_parser("check", help="compare every snapshot with the other side, and the rows on both sides")
    p.add_argument("prd_dir", metavar="PRD")
    p.add_argument("--ref", help="the ref to read each upstream at (default: its default branch); consumers are read at theirs")
    p.add_argument("--ci", action="store_true", help="exit 0 where an unreachable side alone would exit 3")
    p = sub.add_parser("impact", help="the contract items this working tree changes, and the consumers that cite them")
    p.add_argument("prd_dir", metavar="PRD")
    p.add_argument("--base", default="HEAD", help="the ref to compare the working tree with (default: HEAD)")
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
    code = 0
    try:
        if args.command == "add":
            report = links.add(prd, args.location, args.needs)
        elif args.command == "sync":
            report = links.sync(prd, args.upstream, args.ref)
        elif args.command == "check":
            lines = links.check(prd, args.ref)
            report, code = [str(x) for x in lines], links.check_exit(lines)
            if args.ci and code == 3:
                code = 0
        else:
            changed, cited, unreachable = links.impact(prd, args.base)
            report = ([f"changed: {x}" for x in changed] + [f"consumer {c}: {x}" for c in sorted(cited) for x in cited[c]]
                      + [f"consumer {c}: unreachable" for c in unreachable])
            code = 1 if cited else 3 if unreachable else 0
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
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
