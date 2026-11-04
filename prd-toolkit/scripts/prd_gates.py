#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""The pending human decisions of a PRD (`list`). Exit 0 done, 2 usage, dependency or internal error."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import gates, interface, model  # noqa: E402


def _flags(parser: argparse.ArgumentParser, leaf: bool) -> None:
    """--json and --interface on the top parser and each leaf; a leaf that does not see them leaves the top value alone."""
    interface.add_flags(parser)
    if leaf:
        for a in parser._actions:
            if a.dest in ("json", "interface"):
                a.default = argparse.SUPPRESS


def _build() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prd_gates.py", description="The pending human decisions of a PRD.")
    _flags(parser, leaf=False)
    sub = parser.add_subparsers(dest="cmd")
    lst = sub.add_parser("list", help="print every pending gate")
    lst.add_argument("prd_dir")
    lst.add_argument("--worktrees", action="store_true", help="also list the approval gates of every worktree of the repository")
    _flags(lst, leaf=True)
    return parser


def _cmd_list(prd: model.Prd, args) -> tuple[str, dict]:
    found = gates.list_gates(prd, model.repo_root(prd.root), args.worktrees)
    return "".join(f"{g.id} {g.title}\n" for g in found), {"prd": prd.frontmatter.get("prd", prd.root.name), "gates": [g.to_dict() for g in found]}


COMMANDS = {"list": ("gates", _cmd_list)}


def main(argv: list[str]) -> int:
    return interface.run(_main, "gates", argv)


def _main(argv: list[str]) -> int:
    parser = _build()
    try:
        argv, asked = interface.split_argv(argv)
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    if args.interface:
        print(interface.INTERFACE)
        return 0
    bad = interface.check_version(asked)
    if bad:
        print(f"prd_gates: {bad}", file=sys.stderr)
        return 2
    entry = COMMANDS.get(args.cmd)
    if entry is None:
        parser.print_usage(sys.stderr)
        return 2
    _, handler = entry
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_gates: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_gates: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    try:
        text, payload = handler(prd, args)
    except Exception as e:
        print(f"prd_gates: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(interface.dump("gates", payload) if args.json else text)
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
