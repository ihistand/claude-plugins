#!/usr/bin/env bash
# Start state: the linked pair of scaffolds/link_repo.py, state `linked` (greet-client, which prints a banner around the
# greeting of greet's staging install, and greet, the repo of the `cli` contract; links.md on both sides). The
# session's repository is the client; the other sits in a fresh temporary directory beside it, reached by the
# relative Location in links.md.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
client="$PWD"
greet="$(mktemp -d)/greet"
python3 -B "$here/../scaffolds/link_repo.py" "$client" linked --upstream "$greet"
test -f docs/prd/greet-client/links.md
test -z "$(git status --porcelain)"
