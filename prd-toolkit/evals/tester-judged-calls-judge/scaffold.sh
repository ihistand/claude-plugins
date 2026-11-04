#!/usr/bin/env bash
# Start state: D3's: scaffolds/doc_repo.py state `approved` plus the `built` state's docs/guide/install.md,
# committed as a draft (FR-010 stays approved), so "check the guide yourself" has a guide to grade.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/doc_repo.py" "$PWD" approved
built="$(mktemp -d)"
python3 -B "$here/../scaffolds/doc_repo.py" "$built/repo" built
mkdir -p docs/guide
cp "$built/repo/docs/guide/install.md" docs/guide/install.md
rm -rf "$built"
git add docs/guide/install.md
git -c user.name="Legacy Dev" -c user.email=legacy@example.com -c commit.gpgsign=false \
  commit -qm "Draft the install guide" -m "Refs: none (no behaviour change)"
grep -q "^Status: approved$" docs/prd/greet/features/guide.md
test -z "$(git status --porcelain)"
