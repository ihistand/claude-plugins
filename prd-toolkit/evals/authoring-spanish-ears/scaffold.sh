#!/usr/bin/env bash
# Start state: the greet CLI (src/greet/cli.py, its unit tests, a README), one commit, no docs/prd/
# (scaffolds/doc_repo.py state `empty`), the start of the D1 and D2 baselines in baselines/packs-and-judged.md.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/doc_repo.py" "$PWD" empty
test -f src/greet/cli.py
test ! -e docs/prd
test -z "$(git status --porcelain)"
