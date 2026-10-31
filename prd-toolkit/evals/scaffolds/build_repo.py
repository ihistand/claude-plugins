"""Build the start repo for the building-from-prds baselines and evals.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst>

Runs notes_repo's `export-confirmed` state, switches to branch `base` at HEAD~1 (the PRD Approved at
1.0.0, `notes` adopted, T-002.1 known-failing on E-001), then commits an approved FR-003 "Count
notes" with a unit T-id (T-003.1) and an integration T-id (T-003.2). `count_notes` is not implemented.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import notes_repo  # noqa: E402
from legacy import commit, git  # noqa: E402

FEATURE = """
### FR-003 Count notes
Status: approved
Acceptance (EARS):
- AC-003.1 When `notes.app.count_notes()` is called on a store holding notes, it shall return the number of stored notes.
- AC-003.2 When `notes.app.count_notes()` is called on an empty store, it shall return `0`.
Errors: -
Tests: T-003.1 [unit], T-003.2 [integration]  (test-cases/notes.yaml)
"""

CASES = """
T-003.1:
  ac: AC-003.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:notes.app.count_notes
  environment: local
  identity: none
  preconditions: []
  input:
    notes_added_first: ["buy milk", "call bob"]
  expect:
    output: 2
    effects: []
    errors: []
    leaks: none

T-003.2:
  ac: AC-003.2
  level: integration
  refs: ["testing.md#Harness"]
  target: code:notes.app.count_notes
  environment: local
  identity: none
  preconditions: []
  input:
    notes_added_first: []
  expect:
    output: 0
    effects: []
    errors: []
    leaks: none
"""


def _sub(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


def main(dst: str) -> None:
    notes_repo.main(dst, "export-confirmed")
    repo = Path(dst)
    git(repo, "switch", "-q", "-c", "base", "HEAD~1")
    prd = repo / "docs/prd/notes"
    with (prd / "features/notes.md").open("a", encoding="utf-8") as f:
        f.write(FEATURE)
    with (prd / "test-cases/notes.yaml").open("a", encoding="utf-8") as f:
        f.write(CASES)
    testing = prd / "testing.md"
    t = testing.read_text(encoding="utf-8")
    testing.write_text(_sub(t, "| integration | `uv run pytest tests` | local | build |\n",
                            "| unit | `uv run pytest tests` | local | build |\n"
                            "| integration | `uv run pytest tests` | local | build |\n"), encoding="utf-8")
    p = prd / "prd.md"
    text = p.read_text(encoding="utf-8")
    text = _sub(text, "version: 1.0.0", "version: 1.1.0")
    text = _sub(text, "| FR-002 | Search notes | approved | features/notes.md |  |\n",
                "| FR-002 | Search notes | approved | features/notes.md |  |\n"
                "| FR-003 | Count notes | approved | features/notes.md |  |\n")
    text = text.rstrip("\n") + "\n| 1.1.0 | 2026-10-30 | FR-003 Count notes added and approved | FR-003, AC-003.1, AC-003.2, T-003.1, T-003.2 |\n"
    p.write_text(text, encoding="utf-8")
    commit(repo, "PRD: FR-003 Count notes approved (1.1.0)\n\nRefs: FR-003", "docs", date="2026-10-30T12:00:00+0000")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_repo.py <dst>")
    main(sys.argv[1])
