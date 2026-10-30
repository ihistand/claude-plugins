#!/usr/bin/env bash
# Start state: tests/legacy.py's legacy notes service with its 3 commits, and no PRD.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B -c 'import sys; sys.path.insert(0, sys.argv[1]); from legacy import make_legacy_repo; make_legacy_repo(sys.argv[2])' \
  "$here/../../tests" "$PWD"
test -f src/notes/app.py
test "$(git rev-list --count HEAD)" -eq 3
