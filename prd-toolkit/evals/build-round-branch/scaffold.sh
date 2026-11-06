#!/usr/bin/env bash
# Start state: build_repo.py's repo (FR-003 "Count notes" approved, count_notes not implemented), moved onto a side
# branch: `feature/count-notes` holds FR-003's approval commit, and `base` is put back one commit, so the approval
# is on the side branch only (a checkout of `base` would build without it).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/build_repo.py" "$PWD"
git switch -q -c feature/count-notes
git branch -f base HEAD~1
test "$(git branch --show-current)" = feature/count-notes
grep -q "^### FR-003 Count notes$" docs/prd/notes/features/notes.md
test -z "$(git branch --list 'prd-round/*')"
test -z "$(git status --porcelain)"
