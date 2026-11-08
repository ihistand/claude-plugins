#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, FR-001 and FR-002 verified) in the state `ready` (see scaffolds/deploy_repo.py),
# with no test citing the deploy-gate T-ids T-002.1 and T-002.2 (their test files removed), and the PRD's root README
# written by the vendored prd_block.py, plus a hand-written note below the block that no PRD file states: greet answers
# in French. T-002.1's case expects `Hi, World!` on staging.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/deploy_repo.py" "$PWD" ready
git rm -q tests/system/test_deployed.py tests/smoke/test_deployed.py
uv run --script .prd-toolkit/prd_block.py docs/prd/greet > /dev/null
test -f docs/prd/greet/README.md
cat >> docs/prd/greet/README.md <<'MD'

## Notes for users

On every installed environment `greet` answers in French: `greet World` prints `Bonjour, World!`.
MD
! grep -rq 'Bonjour' docs/prd/greet --exclude=README.md
git add -A docs CLAUDE.md
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q \
  -m "PRD READMEs; the deploy-gate tests are rewritten from the PRD" -m "Refs: none (no behaviour change)"
test -z "$(git status --porcelain)"
