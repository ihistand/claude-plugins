"""Build an eval start repo: tests/legacy.py's make_legacy_repo plus an export module, and
optionally the notes PRD at docs/prd/notes in one of its adoption states.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <bare|confirmed|export-confirmed>

bare       the legacy service with an export module and a pyproject, no PRD
confirmed  a Draft PRD whose `notes` area is `confirmed` (FR-001 confirmed, FR-002 corrected)
export-confirmed  first the PRD Approved at 1.0.0 with `notes` adopted (T-002.1 known-failing
           E-001, characterization tests in tests/), then the `export` area extracted and
           confirmed (FR-003 live since 1.1.0, no bug), the PRD In review, ready for step 4
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from legacy import commit, git, make_legacy_repo  # noqa: E402

EXPORT = '''"""Export the stored notes."""
from notes.app import _NOTES


def export_notes() -> str:
    """Return every note as one `<id>\\t<text>` line, in id order."""
    return "".join(f"{i}\\t{t}\\n" for i, t in sorted(_NOTES.items()))
'''

PYPROJECT = """[project]
name = "notes"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest"]

[tool.pytest.ini_options]
pythonpath = ["src"]

# A fixed resolution date keeps uv.lock, and so every later commit SHA, the same on every build.
[tool.uv]
exclude-newer = "2026-10-01T00:00:00Z"
"""


def prd_files(sha_app: str) -> dict[str, str]:
    """The notes PRD, a Draft whose `notes` area is `confirmed`: FR-001 confirmed, FR-002 corrected."""
    fr1_status = "live (since 1.0.0)"
    fr2_status = "approved"
    fr2_ac = (
        "- AC-002.1 When `notes.app.search_notes(term)` is called, it shall return, in insertion order, the\n"
        "  text of every stored note that contains `term`, ignoring case."
    )
    s1 = f"Source: src/notes/app.py:6 @{sha_app}"
    s2 = f"Source: src/notes/app.py:13 @{sha_app}"
    changelog_extra = (
        f"| 0.1.0 | 2026-10-29 | notes area extracted from @{sha_app}; E-001 recorded | FR-001, FR-002, T-001.1, T-002.1 |\n"
        "| 0.1.0 | 2026-10-29 | notes area confirmed: FR-001 confirmed, FR-002 corrected (ignore case) | FR-001, FR-002, AC-002.1 |\n"
    )
    return {
        "prd.md": f"""---
prd: notes
version: 0.1.0
status: Draft
owner: Sample Owner
updated: 2026-10-29
---

# notes

## 1. Metadata & stack

- Language: Python 3.12
- Framework: none; the interface is the Python module `notes.app`
- Database: none; notes live in memory
- Hosting: imported as a library by the caller
- Repository: this repository
- Not used: HTTP, databases
- Not applicable: `contracts/openapi.yaml` — no HTTP API
- Not applicable: `contracts/schema.sql` — no database
- Not applicable: `contracts/events.md` — no events
- Not applicable: `contracts/permissions.yaml` — no identities
- Not applicable: `contracts/config.yaml` — no settings
- Not applicable: `contracts/data-classification.yaml` — no stored personal data
- Not applicable: `contracts/dependencies/` — no external services
- Not applicable: `contracts/fixtures/` — preconditions are calls to `add_note`

## 2. Summary & goals

An in-memory notes store for one process: add a note, search notes by a term, export them.

Goals:

- Every stored note is found by a search for any word in it.

Personas: a developer who imports `notes.app`.

Out of scope: persistence, users, HTTP.

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| note | One stored text, with an integer id from 1 | memo |

## 4. Architecture

One module, `notes.app`, holds a dict `_NOTES` from id to text; `notes.export` reads it.

## 5. Standards registry

| Object (glob) | Linter command | Rules live in | Applies to | Decision |
|---|---|---|---|---|
| `src/**/*.py` | `uv run python -m py_compile` | none; no linter is configured in the repo | code | declined |

## 6. Skills registry

| Object or activity | Skill | Decision |
|---|---|---|
| plans | superpowers:writing-plans | recommended |

## 7. Contract types

| Type | Files (glob) | Validator |
|---|---|---|
| errors | `contracts/errors.yaml` | built-in |

## 8. Adoption map

| Area | State | Boundary |
|---|---|---|
| notes | confirmed | `src/notes/app.py`, `tests/test_notes.py` |
| export | not started | `src/notes/export.py` |

## 9. Versioning

- Breaking for the API: a changed signature or return value of a public function in `notes`
- Breaking for the schema: Not applicable: no database
- Breaking for events: Not applicable: no events
- Compatibility window: none; callers pin the version
- Migration rule: callers upgrade when they pin a new version

## 10. Design & UI

Not applicable: no user interface.

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|
| FR-001 | Add a note | live | features/notes.md | 1.0.0 |
| FR-002 | Search notes | {fr2_status} | features/notes.md |  |

## 12. Assumptions index

| ID | Assumption | Status |
|---|---|---|

## 13. Open questions

None.

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 0.1.0 | 2026-10-29 | Draft started (adoption bootstrap) | none |
{changelog_extra}""",
        "features/notes.md": f"""# Notes

### FR-001 Add a note
Status: {fr1_status}
{s1}
Acceptance (EARS):
- AC-001.1 When a note is added to an empty store, `notes.app.add_note(text)` shall return the id `1`.
Errors: -
Tests: T-001.1 [integration]  (test-cases/notes.yaml)

### FR-002 Search notes
Status: {fr2_status}
{s2}
Acceptance (EARS):
{fr2_ac}
Errors: -
Tests: T-002.1 [integration]  (test-cases/notes.yaml)
Traces: E-001
""".replace("\n\n\n", "\n\n").replace(f"Status: {fr1_status}\n\nAcceptance", f"Status: {fr1_status}\nAcceptance").replace(f"Status: {fr2_status}\n\nAcceptance", f"Status: {fr2_status}\nAcceptance"),
        "test-cases/notes.yaml": f"""T-001.1:
  ac: AC-001.1
  level: integration
  refs: ["testing.md#Harness"]
  target: code:notes.app.add_note
  environment: local
  identity: none
  preconditions: []
  input:
    text: "buy milk"
  expect:
    output: 1
    effects: []
    errors: []
    leaks: none

T-002.1:
  ac: AC-002.1
  level: integration
  refs: ["testing.md#Harness"]
  target: code:notes.app.search_notes
  environment: local
  identity: none
  preconditions: []
  input:
    notes_added_first: ["Buy Milk", "call bob"]
    term: "milk"
  expect:
    output: ["Buy Milk"]
    effects: []
    errors: []
    leaks: none
""",
        "testing.md": """# Testing

## Levels

| Level | Harness command | Environment |
|---|---|---|
| integration | `uv run pytest tests` | local |

## Harness

- **Lifecycle.** Not applicable: the store is in memory; the harness imports the module.
- **Environment switch.** Not applicable: one environment, `local`.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** `uv` on PATH; `tests/` sits at the repository root.
- **Clean state.** Every test starts from an empty store: an autouse fixture in `tests/conftest.py` clears `notes.app._NOTES` before each test.
- **Persistent environments.** Not applicable: no persistent environment.
- **Layout.** `tests/test_<area>.py`; each test's docstring cites its T-id, e.g. `@prd T-001.1`. `pyproject.toml` puts `src/` on the import path. Test roots: `tests/`.
- **HTTP requests.** Not applicable: no HTTP API.
- **Fixtures.** Not applicable: no fixture files; an input's `notes_added_first` list is added with `notes.app.add_note`, in order, before the call under test.
- **Browser identity.** Not applicable: no UI.
- **Assertions.** Outputs compare with `==`; an expected error asserts its exception type only.
- **Waits.** Not applicable: calls are synchronous.
- **Effects.** Not applicable: no side effects outside the store.
- **Leaks.** Not applicable: no logs.
- **Acceptance.** Not applicable: no acceptance cases.

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | Developer machine | Developer | none | none | none |

## Leak checks

| Sink | Read from | Scanned for |
|---|---|---|
| application logs | Not applicable: the module writes no logs | none |

## Fixtures

| Fixture | Creates | Load | Teardown |
|---|---|---|---|

## Sign-offs

| T-id | Owner | Date | Result |
|---|---|---|---|
""",
        "nfr.md": """# Non-functional requirements

None: the notes area has no measured bound.

## Observability

Not applicable: the module writes no logs and exports no metrics.
""",
        "operations.md": """# Operations

## Environments

| Environment | URL |
|---|---|
| local | none |

## Runbook

1. (actor: human) Release by tagging the repository; callers pin the tag.

## Secrets

- None.
""",
        "errors.md": f"""# Error ledger

### E-001 search_notes matches case-sensitively
Detected: 2026-10-29, adoption extract of the notes area (src/notes/app.py:15 @{sha_app})
Classification: code bug
Diagnosis: `search_notes` compares with `term in t`, so "milk" does not find "Buy Milk"; the README says it returns "the notes that contain `term`", and the code's own comment calls it an apparent bug
Resolution: open
Recurrence of: -
""",
        "contracts/errors.yaml": "# Format: references/prd-format.md, \"Contract YAML shapes\".\n{}\n",
    }


CONFTEST = '''"""Shared harness for the notes PRD (docs/prd/notes/testing.md, Harness)."""

import pytest

import notes.app


@pytest.fixture(autouse=True)
def _empty_store():
    """Clean state: every test starts from an empty store."""
    notes.app._NOTES.clear()
    yield
'''

TESTS = '''from notes.app import add_note, search_notes


def test_add_note_returns_an_id():
    """@prd T-001.1"""
    assert add_note("buy milk") == 1


def test_search_ignores_case_in_insertion_order():
    """@prd T-002.1"""
    for text in ["Buy Milk", "call bob"]:
        add_note(text)
    assert search_notes("milk") == ["Buy Milk"]
'''


def _sub(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


def adopted_files(sha_app: str) -> dict[str, str]:
    """The confirmed PRD after its suite (T-001.1 pass, T-002.1 known-failing E-001) and approval."""
    files = prd_files(sha_app)
    prd = files["prd.md"]
    prd = _sub(prd, "version: 0.1.0", "version: 1.0.0")
    prd = _sub(prd, "status: Draft", "status: Approved")
    prd = _sub(prd, "| notes | confirmed |", "| notes | adopted |")
    prd = prd.rstrip("\n") + (
        "\n| 1.0.0 | 2026-10-29 | Approved; notes area adopted; suite T-001.1 pass, T-002.1 known-failing"
        " E-001; dry run passed | FR-001, FR-002, T-001.1, T-002.1 |\n"
    )
    files["prd.md"] = prd
    cases = files["test-cases/notes.yaml"]
    files["test-cases/notes.yaml"] = _sub(
        cases, "  target: code:notes.app.search_notes\n", "  target: code:notes.app.search_notes\n  known-failing: E-001\n"
    )
    return files


EXPORT_FEATURE = """# Export

### FR-003 Export notes
Status: live (since 1.1.0)
Source: src/notes/export.py:5 @{sha}
Acceptance (EARS):
- AC-003.1 When `notes.export.export_notes()` is called, it shall return one line per stored note,
  in ascending id order, each line the note's id, a tab, the note's text and a newline; on an
  empty store that is no lines, the empty string.
Errors: -
Tests: T-003.1 [integration]  (test-cases/export.yaml)
"""

EXPORT_CASES = """T-003.1:
  ac: AC-003.1
  level: integration
  refs: ["testing.md#Harness"]
  target: code:notes.export.export_notes
  environment: local
  identity: none
  preconditions: []
  input:
    notes_added_first: ["buy milk", "call bob"]
  expect:
    output: "1\\tbuy milk\\n2\\tcall bob\\n"
    effects: []
    errors: []
    leaks: none
"""


def export_confirmed_files(sha_app: str, sha_export: str) -> dict[str, str]:
    """The adopted PRD with its second area, export, extracted and confirmed (no bug; In review)."""
    files = adopted_files(sha_app)
    prd = files["prd.md"]
    prd = _sub(prd, "status: Approved", "status: In review")
    prd = _sub(prd, "| export | not started |", "| export | confirmed |")
    prd = _sub(prd, "| FR-002 | Search notes | approved | features/notes.md |  |\n",
               "| FR-002 | Search notes | approved | features/notes.md |  |\n"
               "| FR-003 | Export notes | live | features/export.md | 1.1.0 |\n")
    files["prd.md"] = prd
    files["testing.md"] = _sub(
        files["testing.md"],
        "clears `notes.app._NOTES` before each test.",
        "clears `notes.app._NOTES` before each test, so ids start again at 1 (AC-001.1) in every test.",
    )
    files["features/export.md"] = EXPORT_FEATURE.format(sha=sha_export)
    files["test-cases/export.yaml"] = EXPORT_CASES
    return files


def main(dst: str, state: str) -> None:
    repo = make_legacy_repo(Path(dst))
    (repo / "src/notes/export.py").write_text(EXPORT, encoding="utf-8")
    commit(repo, "Export notes as TSV", "src", date="2026-01-05T12:00:00+0000")
    (repo / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (repo / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    subprocess.run(["uv", "lock", "-q"], cwd=repo, check=True)
    subprocess.run(["uv", "sync", "-q", "--locked"], cwd=repo, check=True)
    commit(repo, "Add the project file", "pyproject.toml", "uv.lock", ".gitignore", date="2026-01-06T12:00:00+0000")
    if state == "bare":
        return
    sha_app = git(repo, "log", "-1", "--format=%h", "--", "src/notes/app.py").strip()
    if state == "confirmed":
        _write_prd(repo, prd_files(sha_app))
        commit(repo, "PRD: notes area confirmed", "docs", date="2026-01-07T12:00:00+0000")
        return
    _write_prd(repo, adopted_files(sha_app))
    (repo / "tests/conftest.py").write_text(CONFTEST, encoding="utf-8")
    (repo / "tests/test_notes.py").write_text(TESTS, encoding="utf-8")
    commit(repo, "PRD: notes area adopted (1.0.0)\n\nRefs: FR-001, FR-002", "docs", "tests", date="2026-01-07T12:00:00+0000")
    sha_export = git(repo, "log", "-1", "--format=%h", "--", "src/notes/export.py").strip()
    _write_prd(repo, export_confirmed_files(sha_app, sha_export))
    commit(repo, "PRD: export area extracted and confirmed", "docs", date="2026-01-08T12:00:00+0000")


def _write_prd(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = repo / "docs/prd/notes" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("bare", "confirmed", "export-confirmed"):
        sys.exit("usage: notes_repo.py <dst> <bare|confirmed|export-confirmed>")
    main(sys.argv[1], sys.argv[2])
