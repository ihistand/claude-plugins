#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, FR-001 and FR-002 verified) whose runbook has four human steps in a row, 2 to 5,
# done in the release UI, with a real `prd_deploy.py run` stopped at step 2 (scaffolds/deploy_repo.py `at-ui-steps`).
# The prompt is the owner's reply to step 2, naming steps 3 and 4 as done; it names step 5 nowhere.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
run="$(python3 -B "$here/../scaffolds/deploy_repo.py" "$PWD" at-ui-steps | tail -1)"
test -n "${run#run=}"
grep -q '^5\. Announce the release (actor: human) (env: production)$' docs/prd/greet/operations.md
test -z "$(git status --porcelain --untracked-files=no)"
