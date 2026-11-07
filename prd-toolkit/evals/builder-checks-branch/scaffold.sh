#!/usr/bin/env bash
# Start state: build_repo.py's repo (FR-003 "Count notes" approved, count_notes not implemented) on branch `base`
# at 61e0159 (fixed by the scaffold's dates). No branch `prd-round/notes-1` exists, so the prompt's `Branch:` line
# is not the current branch while its `Base:` is HEAD. The reflog is emptied, so any commit, switch or reset the
# run makes is the only line in .git/logs/HEAD.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/build_repo.py" "$PWD"
test "$(git branch --show-current)" = base
test "$(git rev-parse HEAD)" = 61e0159bd0ef684fea2804eb219be1de3f0da8e6
test -z "$(git branch --list 'prd-round/*')"
git reflog expire --expire=now --all
test ! -s .git/logs/HEAD
test -z "$(git status --porcelain)"
