#!/usr/bin/env bash
# Start state: the greet PRD at docs/prd/greet (1.0.0, Approved, every requirement verified), the vendored
# `.prd-toolkit/` (no publish entry script), as publishing-trigger's (scaffolds/error_repo.py `bug`). The prompt asks
# for the page as a file inside another Artifact; an eval session has no Artifact tool, so what is graded is the
# render and what the reply says about where the page goes.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/error_repo.py" "$PWD" bug
grep -q '^version: 1.0.0$' docs/prd/greet/prd.md
test ! -e .prd-toolkit/prd_publish.py
test -z "$(git status --porcelain)"
