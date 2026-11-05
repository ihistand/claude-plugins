#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""The pending human decisions of a PRD (`list`), one reply for one of them (`answer`) and a wait for its answer (`wait`). Exit 0 done, 1 refused, 3 wait timed out, 2 usage, dependency or internal error."""
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
    ans = sub.add_parser("answer", help="pass one reply for one gate to the script that owns the decision",
                         description="Re-lists the gate first; a gate that is gone or whose question changed is refused (exit 1). "
                                     "Free text goes to the owner as --opt=VALUE, so a reply may start with a dash.")
    ans.add_argument("prd_dir")
    ans.add_argument("gate", help="a gate id from `list`")
    ans.add_argument("--reply", required=True, help="the owner's words, verbatim (write --reply=TEXT when it starts with a dash)")
    ans.add_argument("--choice", help="one of the gate's choices (default: approve, confirm, confirm; a decision or done for adoption)")
    ans.add_argument("--class", dest="cls", help="error-class: the corrected class, with --choice correct")
    ans.add_argument("--result", help="signoff: the result, required; --choice, when given, must equal it")
    ans.add_argument("--item", help="adoption: the item the decision answers")
    ans.add_argument("--correction", help="adoption: the corrected text")
    ans.add_argument("--question", help="the question the client showed; a gate whose question differs is refused. Omitting it skips that check (only a gone gate is refused): clients should pass the question they showed")
    _flags(ans, leaf=True)
    wt = sub.add_parser("wait", help="block until the owner answers one gate, then print the outcome",
                        description="Start it before giving the owner the URL. Exit 0 answered, 1 the gate is not pending (choice null), 3 timed out.")
    wt.add_argument("prd_dir")
    wt.add_argument("gate")
    wt.add_argument("--worktree", help="the worktree whose gate it is (default: the PRD's own)")
    wt.add_argument("--timeout", type=float, help="seconds to wait (default: until answered)")
    _flags(wt, leaf=True)
    return parser


def _cmd_answer(prd: model.Prd, args) -> tuple[str, dict]:
    done = gates.answer(prd, model.repo_root(prd.root), args.gate, args.reply, args.choice, args.cls, args.result, args.item, args.correction, args.question)
    return "", done


def _cmd_list(prd: model.Prd, args) -> tuple[str, dict]:
    found = gates.list_gates(prd, model.repo_root(prd.root), args.worktrees)
    return "".join(f"{g.id} {g.title}\n" for g in found), {"prd": prd.frontmatter.get("prd", prd.root.name), "gates": [g.to_dict() for g in found]}


def _cmd_wait(prd: model.Prd, args) -> tuple[str, dict]:
    code, outcome = gates.wait_gate(prd.root, args.gate, Path(args.worktree) if args.worktree else None, args.timeout)
    return str(code), outcome


COMMANDS = {"list": ("gates", _cmd_list), "answer": ("gates.answer", _cmd_answer), "wait": ("gates.outcome", _cmd_wait)}


def main(argv: list[str]) -> int:
    """The error document's kind comes from the subcommand an argv pre-pass finds; `gates` when none parses."""
    return interface.run(_main, interface.subcommand_kind(argv, {cmd: kind for cmd, (kind, _h) in COMMANDS.items()}, "gates"), argv)


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
    kind, handler = entry
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
    except gates.Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"prd_gates: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if args.cmd == "wait":
        code = int(text)
        if code == 3:
            print(f"prd_gates: timed out waiting for {args.gate}", file=sys.stderr)
        else:
            sys.stdout.write(interface.dump(kind, payload))
        return code
    if args.cmd == "answer":
        owner = payload["result"]
        if args.json:
            sys.stdout.write(interface.dump(kind, payload))
        else:
            sys.stdout.write("".join(f"{ln}\n" for ln in owner["stdout"]))
            sys.stderr.write("".join(f"{ln}\n" for ln in owner.get("stderr", [])))
        return owner["exit"]
    sys.stdout.write(interface.dump(kind, payload) if args.json else text)
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
