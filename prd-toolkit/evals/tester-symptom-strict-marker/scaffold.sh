#!/usr/bin/env bash
# Start state: the notes PRD (area `confirmed`); T-002.1's case carries `known-failing: E-001` (open) and a `symptom:`.
# The code is case-sensitive, so the symptom shows: search_notes("milk") returns [] while the store holds "Buy Milk".
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" confirmed
python3 -B - <<'PY'
from pathlib import Path

c = Path("docs/prd/notes/test-cases/notes.yaml")
s = c.read_text(encoding="utf-8")
old = "  target: code:notes.app.search_notes\n"
assert s.count(old) == 1
c.write_text(s.replace(old, '  known-failing: E-001\n  symptom: "search_notes(\\"milk\\") returns an empty list while the store holds \\"Buy Milk\\""\n' + old), encoding="utf-8")
PY
git add docs
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "PRD: T-002.1 is known-failing E-001 with its symptom"
test -z "$(git status --porcelain)"
