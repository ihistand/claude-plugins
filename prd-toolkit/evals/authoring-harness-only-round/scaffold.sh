#!/usr/bin/env bash
# Start state: the legacy notes service with the notes PRD `In review` (version 0.1.0), eight non-unit cases
# (T-001.1 to T-001.4, T-002.1 to T-002.4) and a testing.md Harness whose Layout and Fixtures slots say too little:
# the file a test lives in, how a test cites its T-id, and how an input's `notes_added_first` is applied are not stated.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" confirmed
python3 -B - <<'PY'
from pathlib import Path


def sub(path, old, new):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    assert s.count(old) == 1, (path, old)
    p.write_text(s.replace(old, new), encoding="utf-8")


d = "docs/prd/notes/"
sub(d + "prd.md", "status: Draft", "status: In review")
sub(d + "testing.md",
    "`tests/test_<area>.py`; each test's docstring cites its T-id, e.g. `@prd T-001.1`. `pyproject.toml` puts `src/` on the import path. Test roots: `tests/`.",
    "`pyproject.toml` puts `src/` on the import path. Test roots: `tests/`.")
sub(d + "testing.md",
    "Not applicable: no fixture files; an input's `notes_added_first` list is added with `notes.app.add_note`, in order, before the call under test.",
    "Not applicable: no fixture files.")
sub(d + "testing.md", "an autouse fixture in `tests/conftest.py` clears `notes.app._NOTES` before each test.",
    "an autouse fixture in `tests/conftest.py` calls `notes.app._NOTES.clear()` before each test; `_NOTES` is a dict from id to text, and ids count from 1 again after it is cleared.")
sub(d + "errors.md", "Resolution: open", "Resolution: fixed in 0.1.0; search_notes ignores case")
sub(d + "features/notes.md", "Traces: E-001\n", "")
sub(d + "features/notes.md",
    "shall return the id `1`.\nErrors: -\nTests: T-001.1 [integration]  (test-cases/notes.yaml)\n",
    "shall return the id `1`.\n"
    "- AC-001.2 When a second note is added, `notes.app.add_note(text)` shall return the id `2`.\n"
    "- AC-001.3 When a third note is added, `notes.app.add_note(text)` shall return the id `3`.\n"
    "- AC-001.4 When a note is added, `notes.app.add_note(text)` shall return an integer.\n"
    "Errors: -\nTests: T-001.1 [integration], T-001.2 [integration], T-001.3 [integration], T-001.4 [integration]  (test-cases/notes.yaml)\n")
sub(d + "features/notes.md",
    "Tests: T-002.1 [integration]  (test-cases/notes.yaml)\n",
    "- AC-002.2 When `term` is in capitals, `notes.app.search_notes(term)` shall still find a note written in lower case.\n"
    "- AC-002.3 When `term` is the empty string, `notes.app.search_notes(term)` shall return every stored note's text.\n"
    "- AC-002.4 When two stored notes contain `term`, `notes.app.search_notes(term)` shall return them in insertion order.\n"
    "Tests: T-002.1 [integration], T-002.2 [integration], T-002.3 [integration], T-002.4 [integration]  (test-cases/notes.yaml)\n")


def case(tid, ac, target, first, term_or_text, output):
    inp = f'    notes_added_first: {first}\n' if first else ""
    key = "term" if "search" in target else "text"
    return (f"\n{tid}:\n  ac: {ac}\n  level: integration\n  refs: [\"testing.md#Harness\"]\n  target: code:{target}\n"
            f"  environment: local\n  identity: none\n  preconditions: []\n  input:\n{inp}    {key}: \"{term_or_text}\"\n"
            f"  expect:\n    output: {output}\n    effects: []\n    errors: []\n    leaks: none\n")


add, search = "notes.app.add_note", "notes.app.search_notes"
extra = (case("T-001.2", "AC-001.2", add, '["buy milk"]', "call bob", 2)
         + case("T-001.3", "AC-001.3", add, '["buy milk", "call bob"]', "pay rent", 3)
         + case("T-001.4", "AC-001.4", add, "", "buy milk", 1)
         + case("T-002.2", "AC-002.2", search, '["buy milk"]', "MILK", '["buy milk"]')
         + case("T-002.3", "AC-002.3", search, '["buy milk", "call bob"]', "", '["buy milk", "call bob"]')
         + case("T-002.4", "AC-002.4", search, '["milk one", "milk two"]', "milk", '["milk one", "milk two"]'))
p = Path(d + "test-cases/notes.yaml")
p.write_text(p.read_text(encoding="utf-8") + extra, encoding="utf-8")
PY
git add -A
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "PRD: notes In review with eight cases"
test -z "$(git status --porcelain)"
