#!/usr/bin/env bash
# Start state: as tester-symptom-strict-marker (T-002.1 known-failing E-001 with a symptom: an empty list), but the code
# fails the case another way: search_notes ignores case and returns the note lower-cased, ["buy milk"], not an empty list.
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

a = Path("src/notes/app.py")
s = a.read_text(encoding="utf-8")
old = "[t for t in _NOTES.values() if term in t]"
assert s.count(old) == 1
a.write_text(s.replace(old, "[t.lower() for t in _NOTES.values() if term.lower() in t.lower()]"), encoding="utf-8")
PY
git add docs src
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "PRD: T-002.1 known-failing E-001 with its symptom; search now lower-cases"
test -z "$(git status --porcelain)"
