#!/usr/bin/env bash
# Start state: the notes PRD Approved at 1.1.0 on branch `base` with FR-003 "Count notes" approved
# (T-003.1 unit, T-003.2 integration) and count_notes not implemented; pytest synced into .venv.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/build_repo.py" "$PWD"
grep -q "^status: Approved$" docs/prd/notes/prd.md
grep -q "^### FR-003 Count notes$" docs/prd/notes/features/notes.md
test "$(git branch --show-current)" = base
test -z "$(git status --porcelain)"
