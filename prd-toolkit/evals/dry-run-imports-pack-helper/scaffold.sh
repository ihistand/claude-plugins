#!/usr/bin/env bash
# Start state: the legacy notes service with a Draft docs/prd/notes whose notes area is `confirmed`, plus a
# vendored pack `ledger` (a made-up name) under .prd-toolkit/packs/ that ships a helper, `stored_notes`. The pack's
# `harness` states the helper's module, parameter and result and that it is never copied; testing.md's Assertions slot
# only says T-001.1's effect is checked with `stored_notes`.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/notes_repo.py" "$PWD" confirmed
python3 -B - <<'PY'
from pathlib import Path

t = Path("docs/prd/notes/testing.md")
s = t.read_text(encoding="utf-8")
old = "- **Assertions.** Outputs compare with `==`; an expected error asserts its exception type only.\n"
assert s.count(old) == 1
t.write_text(s.replace(old, old.rstrip("\n") + " An expected effect on the store is checked with `stored_notes`.\n"), encoding="utf-8")

c = Path("docs/prd/notes/test-cases/notes.yaml")
s = c.read_text(encoding="utf-8")
old = '    output: 1\n    effects: []\n'
assert s.count(old) == 1
c.write_text(s.replace(old, '    output: 1\n    effects: ["the store holds the note `buy milk`"]\n'), encoding="utf-8")

pack = Path(".prd-toolkit/packs/ledger")
pack.mkdir(parents=True)
(pack / "pack.yaml").write_text(
    "pack: ledger\nversion: 1.0.0\ntoolkit: \">=0.8.0,<0.9\"\ndescription: A made-up pack that ships a helper.\n"
    "harness:\n"
    "  Assertions: \"`stored_notes(match=None)` is in `.prd-toolkit/packs/ledger/helpers.py`; a test puts that directory on `sys.path` and runs `from helpers import stored_notes`; the pack's helper is imported from there, never copied. It returns the list of stored note texts in id order, only those containing `match` when it is given.\"\n"
    "builder-tests: unit\n", encoding="utf-8")
(pack / "helpers.py").write_text(
    '"""Test helpers the ledger pack ships."""\n\n\ndef stored_notes(match=None):\n    from notes import app\n\n'
    "    return [n for n in app._NOTES.values() if match is None or match in n]\n", encoding="utf-8")
PY
git add docs .prd-toolkit
git -c user.name="Eval Dev" -c user.email=dev@example.com -c commit.gpgsign=false commit -q -m "PRD: T-001.1 checks the store; vendor the ledger pack"
test -z "$(git status --porcelain)"
