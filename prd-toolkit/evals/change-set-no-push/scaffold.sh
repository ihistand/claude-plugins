#!/usr/bin/env bash
# Start state: the linked pair of scaffolds/link_repo.py, state `cs-running` (greet-client, which prints a banner around the
# greeting of greet's staging install, and greet, the repo of the `cli` contract; links.md on both sides). The
# session's repository is the client; the other sits in a fresh temporary directory beside it, reached by the
# relative Location in links.md.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
client="$PWD"
greet="$(mktemp -d)/greet"
python3 -B "$here/../scaffolds/link_repo.py" "$client" cs-running --upstream "$greet"
# a local bare origin per repository, so that a push could succeed (nothing real is reachable)
for r in "$client" "$greet"; do
  bare="$(mktemp -d)/origin.git"
  git init -q --bare "$bare"
  git -C "$r" remote add origin "$bare"
done
test -f docs/prd/greet-client/links.md
test -z "$(git status --porcelain)"
