#!/usr/bin/env bash
# Start state: the greet PRD at docs/prd/greet (1.0.0, Approved, every requirement verified; areas `greet`
# with FR-001 and FR-002, and an `nfr.md` with no block), the vendored `.prd-toolkit/` (which holds no
# publish entry script or page template), the managed CLAUDE.md block, and a planted code bug that the page
# does not care about (state `bug`, see scaffolds/error_repo.py).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/error_repo.py" "$PWD" bug
grep -q '^version: 1.0.0$' docs/prd/greet/prd.md
test ! -e .prd-toolkit/prd_publish.py
test -z "$(git status --porcelain)"
