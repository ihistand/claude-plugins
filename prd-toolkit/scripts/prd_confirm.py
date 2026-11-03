#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Confirm an adopted area in the browser: serve the form, or print what is still open. Exit 0 Done, 2 usage or tool error, 3 stopped without Done."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import confirm, model  # noqa: E402


def _fail(message: str) -> int:
    print(f"prd_confirm: {message}", file=sys.stderr)
    return 2


def _status(prd, area: str) -> int:
    items = confirm.build_items(prd, area)
    answers = confirm.load_answers(confirm.answers_path(model.repo_root(prd.root), area))
    open_ids = confirm.open_ids(items, answers)
    print(f"{len(items) - len(open_ids)}/{len(items)}")
    for iid in open_ids:
        print(f"open {iid}")
    return 0


def _serve(prd, args) -> int:
    items = confirm.build_items(prd, args.area)
    summaries = confirm.load_summaries(Path(args.summaries), items, args.area) if args.summaries else {}
    try:
        page = confirm.page_path().read_text(encoding="utf-8")
    except OSError as e:
        return _fail(f"cannot read the form page: {e}")
    try:
        server, token = confirm.make_server(prd, args.area, items, summaries, page, port=args.port or 0, idle_minutes=args.idle_minutes)
    except OSError as e:
        return _fail(f"port {args.port} is in use" if args.port else f"cannot start the server: {e}")
    try:
        confirm.ensure_excluded(model.repo_root(prd.root))
        print(f"url=http://127.0.0.1:{server.server_address[1]}/?token={token}", flush=True)
        if not args.no_open:
            try:
                import webbrowser
                webbrowser.open(f"http://127.0.0.1:{server.server_address[1]}/?token={token}")
            except Exception:
                pass
        return confirm.run(server)
    finally:
        server.server_close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_confirm.py", description="Confirm an adopted area in the browser.")
    sub = parser.add_subparsers(dest="command")
    sv = sub.add_parser("serve", help="serve the form until Done")
    st = sub.add_parser("status", help="print answered/total and the open items")
    for p in (sv, st):
        p.add_argument("prd_dir")
        p.add_argument("--area", required=True)
    sv.add_argument("--summaries", metavar="FILE", help="JSON mapping item ID to a one or two sentence summary")
    sv.add_argument("--port", type=int, help="bind this port (default: a free one)")
    sv.add_argument("--no-open", action="store_true", help="do not open the browser")
    sv.add_argument("--idle-minutes", type=float, default=120, help="stop after this long without a request (default 120)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    if not args.command:
        parser.print_usage(sys.stderr)
        return 2
    try:
        prd = model.load(Path(args.prd_dir))
        return _serve(prd, args) if args.command == "serve" else _status(prd, args.area)
    except (model.NotAPrd, confirm.Refused) as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"internal error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
