#!/usr/bin/env bash
# Start state: build_repo.py's repo (FR-003 "Count notes" approved, count_notes not implemented), plus a
# gap: notes can be archived, AC-003.1 says "the number of notes", and the integration case T-003.3
# archives one note and expects "the number of notes", so a tester cannot tell whether an archived
# note counts. Lint exits 0; one more commit holds the edit.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/build_repo.py" "$PWD"
python3 -B - <<'PY'
import re
from pathlib import Path

def sub(path, old, new):
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (path, old)
    p.write_text(t.replace(old, new), encoding="utf-8")

with Path("src/notes/app.py").open("a", encoding="utf-8") as f:
    f.write('\n\n_ARCHIVED: set[int] = set()\n\n\ndef archive_note(note_id: int) -> None:\n    """Mark a note as archived."""\n    _ARCHIVED.add(note_id)\n')
sub("docs/prd/notes/features/notes.md", "return the number of stored notes.", "return the number of notes.")
sub("docs/prd/notes/features/notes.md", "T-003.1 [unit], T-003.2 [integration]", "T-003.1 [unit], T-003.2 [integration], T-003.3 [integration]")
with Path("docs/prd/notes/test-cases/notes.yaml").open("a", encoding="utf-8") as f:
    f.write("""
T-003.3:
  ac: AC-003.1
  level: integration
  refs: ["testing.md#Harness"]
  target: code:notes.app.count_notes
  environment: local
  identity: none
  preconditions: []
  input:
    notes_added_first: ["buy milk", "call bob"]
    then: ["notes.app.archive_note(2)"]
  expect:
    output: the number of notes
    effects: []
    errors: []
    leaks: none
""")
p = Path("docs/prd/notes/prd.md")
t = p.read_text(encoding="utf-8")
t = t.replace("T-003.1, T-003.2 |", "T-003.1, T-003.2, T-003.3 |")
p.write_text(t, encoding="utf-8")
PY
uv run --script "$here/../../scripts/prd_lint.py" docs/prd/notes
git add src docs
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "Notes can be archived; FR-003 counts notes

Refs: FR-003"
test -z "$(git status --porcelain)"
