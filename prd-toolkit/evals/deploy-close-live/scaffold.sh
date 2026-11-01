#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, FR-001 and FR-002 verified) with its runbook, in the state `at-gate`
# (see scaffolds/deploy_repo.py).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/deploy_repo.py" "$PWD" at-gate
test -f docs/prd/greet/operations.md
test -z "$(git status --porcelain)"
