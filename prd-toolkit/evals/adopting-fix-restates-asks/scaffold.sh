#!/usr/bin/env bash
# Start state: the legacy notes service with a Draft docs/prd/notes whose notes area is `extracted`
# (FR-001 and FR-002 `as-built`, E-001 open), plus an open question Q-01 in section 13 that asks whether
# FR-002's exact-case search is intended. The owner has finished the form: FR-001 and FR-002 confirmed,
# E-001 intended, and Q-01 answered `fix` with words that only restate what FR-002 already says
# (search matches case exactly). `.prd-confirm-notes.json` is done and untracked.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" extracted
python3 -B - <<'PY'
from pathlib import Path
p = Path("docs/prd/notes/prd.md")
t = p.read_text(encoding="utf-8")
old = "## 13. Open questions\n\nNone.\n"
assert t.count(old) == 1
p.write_text(t.replace(old, "## 13. Open questions\n\n- Q-01 Is it intended that FR-002's search matches the case of the term exactly?\n"), encoding="utf-8")
PY
uv run --script "$here/../../scripts/prd_lint.py" docs/prd/notes
git add docs
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "PRD: question on FR-002's case matching"
confirm() { uv run --script "$here/../../scripts/prd_confirm.py" "$@"; }
confirm open docs/prd/notes --area notes
confirm answer docs/prd/notes notes FR-001 --decision confirm --reply "Yes, that is what it does."
confirm answer docs/prd/notes notes FR-002 --decision confirm --reply "Yes."
confirm answer docs/prd/notes notes E-001 --decision intended --reply "Intended: exact case."
confirm answer docs/prd/notes notes Q-01 --decision fix --reply "Search should match the case of the term exactly, as it does now."
confirm done docs/prd/notes notes
grep -q '"done": true' .prd-confirm-notes.json
test -z "$(git status --porcelain)"
