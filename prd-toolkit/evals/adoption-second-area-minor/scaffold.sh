#!/usr/bin/env bash
# Start state: the legacy notes service with docs/prd/notes adopted at 1.0.0 for its notes area
# (characterization tests in tests/), and its export area extracted and confirmed (FR-003 live
# since 1.1.0, no bug, the PRD In review); pytest in .venv. The export suite is what is left.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" export-confirmed
grep -q '^version: 1\.0\.0$' docs/prd/notes/prd.md
grep -q '^| export | confirmed |' docs/prd/notes/prd.md
test "$(git rev-list --count HEAD)" -eq 7
