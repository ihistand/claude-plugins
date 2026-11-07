#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, FR-001 and FR-002 verified) with its runbook, in the state `ready`: nothing
# deployed and no deploy log (see scaffolds/deploy_repo.py). The prompt names f4674c9, the PRD's 1.0.0 commit; its
# SHA is fixed by the scaffold's fixed dates and lock file, and this check fails loudly if it ever changes.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/deploy_repo.py" "$PWD" ready
test "$(git log -1 --format=%s f4674c9)" = "PRD: greet 1.0.0 Approved, every requirement verified"
test -z "$(git status --porcelain)"
