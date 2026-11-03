#!/usr/bin/env bash
# Start state: the hello ticket (TICKET.md and .gitignore, one commit on main) and no PRD folder. The ticket
# says nothing about packaging, so the PRD must either name a build backend and an install command or mark the gap.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/hello_repo.py" "$PWD"
test -f TICKET.md
test ! -e docs
test -z "$(git status --porcelain)"
