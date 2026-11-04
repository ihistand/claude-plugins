#!/usr/bin/env bash
# Start state: scaffolds/doc_repo.py state `approved` (D4's): the greet PRD Approved at 1.0.0 with a `guide`
# area (Target: pack document 1.0.0 (prd-toolkit), output language en), FR-010 approved with T-010.1
# [checks] and T-010.2 [judged] and no unit T-id; docs/guide/install.md is not written.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/doc_repo.py" "$PWD" approved
grep -q "^Target: pack document 1.0.0 (prd-toolkit), output language en$" docs/prd/greet/features/guide.md
test ! -e docs/guide/install.md
test -z "$(git status --porcelain)"
