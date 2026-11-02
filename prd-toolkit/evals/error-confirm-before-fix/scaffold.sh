#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, every requirement verified) with a planted code bug committed: the CLI reads
# the settings key `greeting` instead of `GREETING`, so the unit test citing T-001.2 fails (state `bug`, see
# scaffolds/error_repo.py).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/error_repo.py" "$PWD" bug
test -f docs/prd/greet/errors.md
grep -q 'get("greeting", "Hello")' src/greet/cli.py
test -z "$(git status --porcelain)"
