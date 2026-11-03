"""A minimal approved document PRD (pack `document`) for the built-in pack tests (0.8.0)."""
from pathlib import Path

PRD = """---
prd: guide
version: 1.0.0
status: Approved
owner: Sample Owner
updated: 2026-11-03
{language}---

# Install guide

## 1. Metadata & stack

- Format: Markdown, written for people
- Repository: `github.com/example/guide`
- Pack: document 1.0.0 (prd-toolkit)
- Not used: wikis, PDF output
- Not applicable: `contracts/openapi.yaml` — the guide has no API
- Not applicable: `contracts/schema.sql` — the guide has no database
- Not applicable: `contracts/events.md` — the guide has no events
- Not applicable: `contracts/permissions.yaml` — the guide has no access control
- Not applicable: `contracts/config.yaml` — the guide has no configuration
- Not applicable: `contracts/data-classification.yaml` — the guide holds no classified data
- Not applicable: `contracts/dependencies/` — the guide has no external service
- Not applicable: `contracts/fixtures/` — the guide has no fixtures

## 2. Summary & goals

The guide shows a first-time reader how to install the tool and run it once.

Goals:

- A first-time reader installs the tool in under 10 minutes.

Personas: a first-time user.

Out of scope: advanced configuration.

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| token | The secret string the reader pastes into the tool | key |

## 4. Architecture

Not applicable: the guide is a single Markdown file.

## 5. Standards registry

| Object (glob) | Linter command | Rules live in | Applies to | Decision |
|---|---|---|---|---|
| `docs/**/*.md` | `npx markdownlint-cli2 "docs/**/*.md"` | `.markdownlint.yaml` | the guide | enforced |

## 6. Skills registry

| Object or activity | Skill | Decision |
|---|---|---|
| plans | superpowers:writing-plans | required |

## 7. Contract types

| Type | Files (glob) | Validator |
|---|---|---|
| outline | `contracts/outline.yaml` | pack |

## 8. Adoption map

Not applicable: new project.

## 9. Versioning

- Breaking for the guide: removing a section a reader follows.
- Compatibility window: one minor version.
- Migration rule: none; the guide is replaced in place.

## 10. Design & UI

Not applicable: the guide has no user interface.

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|
| FR-001 | Install section | live | features/install.md | 1.0.0 |

## 12. Assumptions index

None.

## 13. Open questions

None.

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 1.0.0 | 2026-11-03 | Initial release | FR-001 |
"""

FEATURE = """# Install

### FR-001 Install section
Status: live (since 1.0.0)
Flow: 1. Reader opens the guide → 2. follows Install → 3. runs the tool once.
Acceptance (EARS):
- AC-001.1 The guide shall list the Requirements, Install, First run and Common problems sections in that order.
- AC-001.2 The guide shall explain each step of Install in one sentence.
Errors: -
Tests: T-001.1 [checks], T-001.2 [judged]  (test-cases/install.yaml)
Traces: -
"""

CASES = """T-001.1:
  ac: AC-001.1
  level: checks
  target: doc:install-guide
  environment: local
  identity: none
  preconditions: []
  input: {path: docs/guide/install.md}
  expect:
    output: {sections: "Requirements, Install, First run, Common problems, in that order"}
    effects: []
    errors: []
    leaks: none

T-001.2:
  ac: AC-001.2
  level: judged
  target: doc:install-guide
  environment: local
  identity: none
  preconditions: []
  input: {reader: has never used a terminal}
  expect:
    rubric:
      - Each step in Install names one action the reader performs
      - No step relies on a tool that Requirements does not list
    threshold: 0.67
    effects: []
    errors: []
    leaks: none
"""

TESTING = """# Testing

## Levels

| Level | Harness command | Environment | Gate |
|---|---|---|---|
| checks | `uv run pytest tests/checks` | local | build |
| judged | `uv run pytest tests/judged` | local | build |

## Harness

- **Lifecycle.** Not applicable: the guide has no running service.
- **Environment switch.** Not applicable: only the local environment exists.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** `uv` and `claude` on PATH.
- **Clean state.** Not applicable: tests only read the guide.
- **Persistent environments.** Not applicable: no persistent environment.
- **Layout.** `tests/<level>/test_<area>.py`; each test's docstring cites its T-id, e.g. `@prd T-001.2`. Test roots: `tests/`.
- **HTTP requests.** Not applicable: no HTTP interface.
- **Fixtures.** Not applicable: no fixtures.
- **Browser identity.** Not applicable: no UI.
- **Assertions.** A judged test asserts `prd_judge.py`'s exit code and nothing else.
- **Waits.** Not applicable: nothing is asynchronous.
- **Effects.** Not applicable: tests have no side effects.
- **Leaks.** Not applicable: the guide holds no classified data.
- **Acceptance.** Not applicable: no acceptance level.

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | Writer's machine | Writer | none | none | the test output |

## Leak checks

None.

## Fixtures

None.

## Sign-offs

None.
"""

OUTLINE = """install-guide:
  path: docs/guide/install.md
  audience: first-time users on Windows or macOS
  purpose: install the CLI and run it once
  sections: [Requirements, Install, First run, Common problems]
  terms: [CLI, token]
  length: {min-words: 300, max-words: 1200}
"""

OPERATIONS = """# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| local | none | yes |

## Runbook

None.

## Deployed

None.

## Drift

None.

## Secrets

None.
"""


def document_prd(tmp: Path, language: str = "en") -> Path:
    """Write the approved PRD `guide` (pack document, area install) at tmp/docs/prd/guide and return its folder."""
    root = Path(tmp) / "docs/prd/guide"
    (root / "features").mkdir(parents=True)
    (root / "test-cases").mkdir()
    (root / "contracts").mkdir()
    (root / "prd.md").write_text(PRD.format(language="" if language == "en" else f"language: {language}\n"), encoding="utf-8")
    (root / "features/install.md").write_text(FEATURE, encoding="utf-8")
    (root / "test-cases/install.yaml").write_text(CASES, encoding="utf-8")
    (root / "testing.md").write_text(TESTING, encoding="utf-8")
    (root / "contracts/outline.yaml").write_text(OUTLINE, encoding="utf-8")
    (root / "contracts/errors.yaml").write_text("{}\n", encoding="utf-8")
    (root / "errors.md").write_text("# Error ledger\n", encoding="utf-8")
    (root / "nfr.md").write_text("# Non-functional requirements\n", encoding="utf-8")
    (root / "operations.md").write_text(OPERATIONS, encoding="utf-8")
    return root
