#!/usr/bin/env bash
# Start state: the valid orders fixture at docs/prd/orders in a fresh git repo.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p docs/prd
cp -R "$here/../../tests/fixtures/valid/orders" docs/prd/orders
test -f docs/prd/orders/prd.md
git init -q
git add -A
git -c user.name=Eval -c user.email=eval@example.com commit -qm init
