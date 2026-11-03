"""A small git repository with an adoption area `notes` waiting for its owner's confirmation."""
import subprocess
from pathlib import Path

from legacy import commit, git

APP = "\n".join(
    ["import re", "", "_NOTES: dict[int, str] = {}", ""]
    + [f"# line {n}" for n in range(5, 12)]
    + ["def add_note(text):", "    note_id = len(_NOTES) + 1", "    _NOTES[note_id] = text", "    return note_id", "",
       "def search(term):", "    return [t for t in _NOTES.values() if term in t]", ""]
    + [f"# tail {n}" for n in range(22, 40)]
) + "\n"

ADOPTION = "# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n| notes | extracted | `src/notes/**` |\n"

PRD = """---
project: notes
version: 0.1.0
status: draft
---
# Notes

## 12. Assumptions

None.

## 13. Open questions

- Q-01 Should FR-001 keep empty notes?
- Q-02 Is the retention period settled for FR-099?
  It was never decided.

## 14. Changelog

None.
"""

FEATURES = """# Notes

### FR-001 Add a note
Status: as-built
Source: src/notes/app.py:13 @{sha}
Acceptance (EARS):
- AC-001.1 When a note is added, the service shall store it and return its id.
- AC-001.2 The id shall grow by one for each note.
Errors: -
Traces: `NOTES_LIMIT` caps the store

### FR-002 Search notes
Status: as-built
Source: src/notes/app.py:17 @{sha}
  src/notes/app.py:13 @{sha}
Acceptance (EARS):
- AC-002.1 When a term is searched, the service shall return the notes containing it.
Errors: -

### FR-003 Delete a note
Status: approved
Acceptance (EARS):
- AC-003.1 When a note is deleted, the service shall forget it.
Errors: -
"""

ERRORS = """# Error ledger

### E-001 Search is case-sensitive
Detected: 2026-10-30, wrong result at src/notes/app.py:17
Touches: FR-002
Classification: unclassified
Diagnosis: the comparison does not fold case
Resolution: open

### E-002 Empty id
Detected: 2026-10-30, test failure
Touches: FR-001
Classification: code bug
Diagnosis: fixed
Resolution: the id starts at 1
"""

CONFIG = """settings:
  NOTES_LIMIT:
    type: integer
    default: 100
    owner: "[NEEDS CLARIFICATION: who owns the limit]"
  OTHER:
    owner: "[NEEDS CLARIFICATION: not named by the area]"
"""


def make_confirm_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = Path(tmp_path) / "repo"
    (repo / "src/notes").mkdir(parents=True)
    (repo / "src/notes/app.py").write_text(APP, encoding="utf-8")
    git(repo, "init", "-q")
    commit(repo, "Add the notes service", "src")
    sha = git(repo, "rev-parse", "--short", "HEAD").strip()
    prd = repo / "docs/prd/notes"
    (prd / "features").mkdir(parents=True)
    (prd / "contracts").mkdir()
    (prd / "prd.md").write_text(PRD, encoding="utf-8")
    (prd / "adoption.md").write_text(ADOPTION, encoding="utf-8")
    (prd / "features/notes.md").write_text(FEATURES.format(sha=sha), encoding="utf-8")
    (prd / "errors.md").write_text(ERRORS, encoding="utf-8")
    (prd / "contracts/config.yaml").write_text(CONFIG, encoding="utf-8")
    commit(repo, "Add the PRD", "docs")
    return repo, prd
