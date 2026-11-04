#!/usr/bin/env bash
# Start state: the orders fixture (its required skill row `recommended`: the sandbox installs no plugins) committed on main, then a change edited and recorded, uncommitted: AC-001.4
# and its unit case T-001.5 (record_setup.py), recorded by the plugin's own `prd_change.py record` as 1.1.0
# with the §14 row ending `; pending`. Lint is clean, so the review can reach a ready verdict.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts="$here/../../scripts"
mkdir -p docs/prd
cp -R "$here/../../tests/fixtures/valid/orders" docs/prd/orders
python3 -B "$here/record_setup.py" docs/prd/orders base
git init -q -b main
git add -A
git -c user.name=Eval -c user.email=eval@example.com commit -qm init
python3 -B "$here/record_setup.py" docs/prd/orders change
uv run --quiet --script "$scripts/prd_change.py" record docs/prd/orders --base HEAD --bump minor \
  --change "an import skips a blank line between rows" >/dev/null
grep -q '^version: 1\.1\.0$' docs/prd/orders/prd.md
grep -q '^| FR-001 | Import an orders file | approved | features/import.md | 1.0.0 |$' docs/prd/orders/prd.md
grep -q 'an import skips a blank line between rows; pending | FR-001, AC-001.4, T-001.5 |' docs/prd/orders/prd.md
uv run --quiet --script "$scripts/prd_lint.py" docs/prd/orders
test ! -e docs/prd/orders/.prd-review.json
