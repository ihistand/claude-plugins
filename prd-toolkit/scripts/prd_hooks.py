#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "sqlglot>=25", "openapi-spec-validator>=0.7"]
# ///
"""Vendor the toolkit into a repo and manage its git hooks: install | check | uninstall <prd-folder>. Exit 0 clean, 1 findings, 2 usage, dependency or internal error."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prdlint import deps  # noqa: E402

for _module, _package in (("yaml", "pyyaml"), ("sqlglot", "sqlglot"), ("openapi_spec_validator", "openapi-spec-validator")):
    deps.require(_module, _package)

from prdlint import hooks, model  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="prd_hooks.py", description="Vendor the PRD toolkit and install its git hooks.")
    parser.add_argument("action", choices=("install", "check", "uninstall"))
    parser.add_argument("prd_dir")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 2
    try:
        prd = model.load(Path(args.prd_dir))
    except model.NotAPrd as e:
        print(f"prd_hooks: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"prd_hooks: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    try:
        root = model.repo_root(prd.root).resolve()
        if args.action == "check" and not hooks.is_plugin():
            print("prd_hooks: run check from the plugin, not the vendored copy", file=sys.stderr)
            return 2
        if args.action == "install":
            try:
                prd_rel = prd.root.resolve().relative_to(root).as_posix()
            except ValueError:
                print(f"prd_hooks: {prd.root} is not inside the repository at {root}", file=sys.stderr)
                return 2
            out = hooks.install(root, prd_rel)
        elif args.action == "check":
            out = hooks.check(root, hooks.PLUGIN_ROOT)
        else:
            out = hooks.uninstall(root)
    except Exception as e:
        print(f"prd_hooks: internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for line in out:
        print(line)
    return 1 if args.action == "check" and out else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
