#!/usr/bin/env bash
# Start state: the legacy notes service (3 legacy commits, then export, project file and PRD commits)
# with docs/prd/notes a Draft whose notes area is `confirmed`; pytest synced into .venv.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" confirmed
test -f docs/prd/notes/prd.md
test "$(git rev-list --count HEAD)" -eq 6
