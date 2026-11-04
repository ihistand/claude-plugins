#!/usr/bin/env bash
# Start state: the valid orders fixture (1.0.0, FR-001..FR-003 and NFR-004) at docs/prd/orders in a fresh git repo.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p docs/prd
cp -R "$here/../../tests/fixtures/valid/orders" docs/prd/orders
test -f docs/prd/orders/prd.md
# The eval sandbox installs no plugins, so the fixture's required skill row would fail lint: make it recommended.
python3 -B "$here/../review-edits-nothing/record_setup.py" docs/prd/orders base
git init -q -b main
git add -A
git -c user.name=Eval -c user.email=eval@example.com commit -qm init
