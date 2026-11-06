#!/usr/bin/env bash
# Start state: the legacy notes service with a Draft docs/prd/notes whose notes area is extracted: FR-001 and FR-002
# `as-built` with their Source lines, E-001 open; pytest in .venv. Step 3 is what is left. No stand-in owner: the
# session is headless, so it serves no inbox and waits on no gate.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" extracted
grep -q '^| notes | extracted |' docs/prd/notes/adoption.md
test -z "$(git status --porcelain)"
