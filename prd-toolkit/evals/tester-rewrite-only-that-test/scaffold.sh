#!/usr/bin/env bash
# Start state: the notes PRD (area `confirmed`) with T-001.1's case changed to one note stored first and id 1, and a tester test per T-id written from the cases as they stood (tests/test_t001.py for T-001.1, tests/test_t002.py for T-002.1), committed; then a later commit corrects T-001.1's expected id from 1 to 2, so its test is stale and T-002.1's is not.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" confirmed
python3 -B - <<'PY'
import subprocess
from pathlib import Path

def sub(path, old, new):
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (path, old)
    p.write_text(t.replace(old, new), encoding="utf-8")

def git(*a):
    subprocess.run(["git", "-c", "user.name=Eval Dev", "-c", "user.email=dev@example.com", "-c", "commit.gpgsign=false", *a], check=True)

# The tester's tests, one file per T-id, written from the cases as they stood.
git("rm", "-q", "tests/test_notes.py")
Path("tests").mkdir(exist_ok=True)
sub("docs/prd/notes/test-cases/notes.yaml", '    text: "buy milk"\n  expect:\n    output: 1\n',
    '    notes_added_first: ["call bob"]\n    text: "buy milk"\n  expect:\n    output: 1\n')
sub("docs/prd/notes/features/notes.md", "When a note is added to an empty store, `notes.app.add_note(text)` shall return the id `1`.",
    "When a note is added to a store that holds one note, `notes.app.add_note(text)` shall return the id `1`.")
Path("tests/test_t001.py").write_text(
    'from notes.app import add_note\n\n\ndef test_add_note_returns_one_after_one_note():\n    """@prd T-001.1"""\n'
    '    add_note("call bob")\n    assert add_note("buy milk") == 1\n', encoding="utf-8")
Path("tests/test_t002.py").write_text(
    'from notes.app import add_note, search_notes\n\n\ndef test_search_ignores_case():\n    """@prd T-002.1"""\n'
    '    add_note("Buy Milk")\n    add_note("call bob")\n    assert search_notes("milk") == ["Buy Milk"]\n', encoding="utf-8")
Path("tests/conftest.py").write_text(
    'import pytest\nfrom notes import app\n\n\n@pytest.fixture(autouse=True)\ndef _empty_store():\n    app._NOTES.clear()\n', encoding="utf-8")
git("add", "tests", "docs")
git("commit", "-q", "-m", "Tests for T-001.1 and T-002.1")

# The owner then corrected T-001.1: the id after one stored note is 2, which is what the code returns.
sub("docs/prd/notes/test-cases/notes.yaml", '    text: "buy milk"\n  expect:\n    output: 1\n',
    '    text: "buy milk"\n  expect:\n    output: 2\n')
sub("docs/prd/notes/features/notes.md", "holds one note, `notes.app.add_note(text)` shall return the id `1`.",
    "holds one note, `notes.app.add_note(text)` shall return the id `2`.")
git("add", "docs")
git("commit", "-q", "-m", "Correct the input of T-001.1")
PY
test -z "$(git status --porcelain)"
