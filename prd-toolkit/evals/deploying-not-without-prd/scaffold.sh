#!/usr/bin/env bash
# Start state: a tiny argparse CLI with one commit, a deploy script and no docs/prd/ folder.
set -euo pipefail
mkdir -p src/greet scripts
cat > src/greet/cli.py <<'PY'
"""A tiny greeting CLI."""
import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="greet")
    parser.add_argument("name")
    args = parser.parse_args(argv)
    print(f"Hello, {args.name}!")
    return 0
PY
printf '"""Install the CLI into .deploy/<env>."""\nimport sys\nprint("deployed to", sys.argv[1])\n' > scripts/deploy.py
printf '[project]\nname = "greet"\nversion = "0.3.1"\n' > pyproject.toml
git init -q
git -c user.name=Dev -c user.email=dev@example.com add .
git -c user.name=Dev -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "Add the greet CLI"
test ! -e docs/prd
