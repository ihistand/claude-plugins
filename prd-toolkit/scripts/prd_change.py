#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""The change bookkeeping of a PRD: next IDs, the digest and the version bump. Exit 0 done, 1 refused, 2 usage, dependency or internal error."""
import argparse
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import change, interface, model  # noqa: E402


def _flags(parser: argparse.ArgumentParser, leaf: bool) -> None:
    """--json and --interface on the top parser and each leaf; a leaf that does not see them leaves the top value alone."""
    interface.add_flags(parser)
    if leaf:
        for a in parser._actions:
            if a.dest in ("json", "interface"):
                a.default = argparse.SUPPRESS


def _build() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prd_change.py", description="The change bookkeeping of a PRD.")
    _flags(parser, leaf=False)
    sub = parser.add_subparsers(dest="cmd")
    ids = sub.add_parser("ids", help="work with requirement IDs")
    ids_sub = ids.add_subparsers(dest="ids_cmd")
    nxt = ids_sub.add_parser("next", help="print the next free ID of a kind")
    nxt.add_argument("prd_dir")
    nxt.add_argument("kind", help="FR, NFR, UJ, AC-<nnn> or T-<nnn>")
    _flags(nxt, leaf=True)
    dig = sub.add_parser("digest", help="print the SHA-256 digest of the PRD folder")
    dig.add_argument("prd_dir")
    _flags(dig, leaf=True)
    bmp = sub.add_parser("bump", help="propose patch, minor or major from the diff against a ref")
    bmp.add_argument("prd_dir")
    bmp.add_argument("--base", required=True, help="the git ref the PRD folder is compared with")
    _flags(bmp, leaf=True)
    return parser


def _cmd_ids_next(prd: model.Prd, args) -> tuple[str, dict]:
    value = change.next_id(prd, args.kind)
    return value + "\n", {"next": value}


def _cmd_digest(prd: model.Prd, args) -> tuple[str, dict]:
    value = change.digest(prd.root)
    return value + "\n", {"digest": value}


def _cmd_bump(prd: model.Prd, args) -> tuple[str, dict]:
    result = change.bump(change.repo_root(prd.root), prd.root, args.base)
    lines = [f"{i.level} {i.id} {i.file}:{i.line} {i.reason}\n" for i in result.items]
    payload = {"level": result.level, "items": [dataclasses.asdict(i) for i in result.items]}
    return "".join(lines) + f"level {result.level}\n", payload


# (command, subcommand) -> (document kind, handler); the next tasks add record and approve here
COMMANDS = {
    ("ids", "next"): ("change.ids", _cmd_ids_next),
    ("digest", None): ("change.digest", _cmd_digest),
    ("bump", None): ("change.bump", _cmd_bump),
}


def main(argv: list[str]) -> int:
    return interface.run(_main, "change", argv)


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
        print(f"prd_change: {bad}", file=sys.stderr)
        return 2
    entry = COMMANDS.get((args.cmd, getattr(args, "ids_cmd", None)))
    if entry is None:
        parser.print_usage(sys.stderr)
        return 2
    kind, handler = entry
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_change: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_change: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    try:
        text, payload = handler(prd, args)
    except change.ChangeError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except change.UsageError as e:
        print(e, file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_change: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(interface.dump(kind, payload) if args.json else text)
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
