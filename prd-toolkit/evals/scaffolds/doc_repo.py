"""Build the start repo for the packs-and-judged baselines and evals (0.8.0): a tiny CLI, `greet`, that
may carry an install guide, a document of the built-in `document` pack.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <empty|approved|built>

empty      the CLI (`src/greet/cli.py`), its unit tests and a README; no `docs/prd/`
approved   `empty` plus an Approved PRD `greet` (service default pack) with a `guide` area
           (`Target: pack document 1.0.0 (prd-toolkit), output language en`): FR-010 "Install guide" with one
           `checks` and one `judged` case, `contracts/outline.yaml` key `install-guide` at
           `docs/guide/install.md`, the vendored `.prd-toolkit/` (both packs) and the CLAUDE.md block. FR-001
           (the CLI the repository ships) is `verified`; FR-002 (`greet --version`, not in the code) and FR-010
           are `approved`, so each area has a build to run; the guide is not written
built      `approved` plus `docs/guide/install.md` and FR-010 `verified`

The tracked tree is clean in every state; `approved` and `built` lint with exit 0. The vendored
`.prd-toolkit/` comes from the plugin tree this file sits in.
"""
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN / "tests"))
from legacy import commit, git  # noqa: E402

STATES = ("empty", "approved", "built")
PRD = "docs/prd/greet"
NONE = "Refs: none (no behaviour change)"

PYPROJECT = """[project]
name = "greet"
version = "1.0.0"
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

INIT = '"""greet: print a greeting."""\n'

MAIN = '''"""Run as `python -m greet`."""
import sys

from greet.cli import main

sys.exit(main(sys.argv[1:]))
'''

CLI = '''"""The command line: `greet <name>` prints `Hello, <name>!`."""


def format_greeting(name: str) -> str:
    return f"Hello, {name}!"


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not argv[0].strip():
        print("usage: greet <name>")
        return 2
    print(format_greeting(argv[0]))
    return 0
'''

README = """# greet

A small command line tool: `greet <name>` prints `Hello, <name>!`.

Run it from a checkout with `uv run --directory src python -m greet World`; the tests run with `uv run pytest`.
"""

UNIT_TESTS = '''from greet.cli import format_greeting, main


def test_format_greeting():
    assert format_greeting("World") == "Hello, World!"


def test_main_prints_the_greeting(capsys):
    assert main(["World"]) == 0
    assert capsys.readouterr().out == "Hello, World!\\n"


def test_main_rejects_an_empty_name(capsys):
    assert main([" "]) == 2
    assert capsys.readouterr().out == "usage: greet <name>\\n"
'''

UNIT_TESTS_CITED = UNIT_TESTS.replace(
    "def test_format_greeting():\n", 'def test_format_greeting():\n    """@prd T-001.1"""\n').replace(
    "def test_main_prints_the_greeting(capsys):\n", 'def test_main_prints_the_greeting(capsys):\n    """@prd T-001.2"""\n').replace(
    "def test_main_rejects_an_empty_name(capsys):\n", 'def test_main_rejects_an_empty_name(capsys):\n    """@prd T-001.3"""\n')

PRD_MD = """---
prd: greet
version: 1.0.0
status: Approved
owner: Sample Owner
updated: 2026-11-03
---

# greet

## 1. Metadata & stack

- Language: Python 3.12
- Framework: none; the interface is the command `greet`
- Database: none
- Hosting: run from a checkout
- Repository: this repository
- Not used: HTTP, databases
- Not applicable: `contracts/openapi.yaml` — no HTTP API
- Not applicable: `contracts/schema.sql` — no database
- Not applicable: `contracts/events.md` — no events
- Not applicable: `contracts/permissions.yaml` — no identities
- Not applicable: `contracts/config.yaml` — no settings
- Not applicable: `contracts/data-classification.yaml` — no stored personal data
- Not applicable: `contracts/dependencies/` — no external services
- Not applicable: `contracts/fixtures/` — no fixtures

## 2. Summary & goals

A command that greets a person by name, and the install guide that gets a first-time reader to run it.

Goals:

- A first-time reader installs `greet` and runs it once in under 10 minutes.

Personas: a person running `greet` for the first time.

Out of scope: packaging, networks, users.

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| greeting | The line `greet` prints for a name | salutation |

## 4. Architecture

`greet.cli` formats and prints the line; `docs/guide/install.md` is the guide.

## 5. Standards registry

| Object (glob) | Linter command | Rules live in | Applies to | Decision |
|---|---|---|---|---|
| `src/**/*.py` | `python3 -m py_compile` | none; no linter is configured in the repo | code | declined |

## 6. Skills registry

| Object or activity | Skill | Decision |
|---|---|---|

## 7. Contract types

| Type | Files (glob) | Validator |
|---|---|---|
| errors | `contracts/errors.yaml` | built-in |
| outline | `contracts/outline.yaml` | pack |

## 8. Adoption map

Not applicable: new project.

## 9. Versioning

- Breaking for the API: a changed output format of `greet`
- Breaking for the schema: Not applicable: no database
- Breaking for events: Not applicable: no events
- Compatibility window: none
- Migration rule: none

## 10. Design & UI

Not applicable: no user interface.

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|
| FR-001 | Print a greeting | verified | features/greet.md |  |
| FR-002 | Print the version | approved | features/greet.md |  |
| FR-010 | Install guide | {fr10} | features/guide.md |  |

## 12. Assumptions index

| ID | Assumption | Status |
|---|---|---|

## 13. Open questions

None.

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 1.0.0 | 2026-11-03 | Approved | FR-001, FR-002, FR-010, T-001.1, T-001.2, T-001.3, T-002.1, T-010.1, T-010.2 |
"""

GREET_FEATURE = """# Greeting

### FR-001 Print a greeting
Status: verified (since 1.0.0)
Acceptance (EARS):
- AC-001.1 When `greet.cli.format_greeting(name)` is called, it shall return `Hello, <name>!`.
- AC-001.2 When `greet <name>` runs, it shall print `Hello, <name>!`.
- AC-001.3 If `greet` runs with no name, more than one argument or a blank name, it shall print `usage: greet <name>` and exit with code 2.
Errors: -
Tests: T-001.1 [unit], T-001.2 [unit], T-001.3 [unit]  (test-cases/greet.yaml)

### FR-002 Print the version
Status: approved
Acceptance (EARS):
- AC-002.1 When `greet --version` runs, it shall print `greet 1.0.0` and exit with code 0.
Errors: -
Tests: T-002.1 [unit]  (test-cases/greet.yaml)
"""

GUIDE_FEATURE = """# Install guide

<!-- Format: references/prd-format.md, "Requirement blocks". -->

Target: pack document 1.0.0 (prd-toolkit), output language en

### FR-010 Install guide
Status: {status}
Flow: 1. Reader opens the guide → 2. follows Install → 3. runs `greet` once.
Acceptance (EARS):
- AC-010.1 The guide shall list the Requirements, Install, First run and Common problems sections in that order.
- AC-010.2 The guide shall give each step of Install as one action the reader performs, using only tools that Requirements lists.
Errors: -
Tests: T-010.1 [checks], T-010.2 [judged]  (test-cases/guide.yaml)
Traces: -
"""

GREET_CASES = """T-001.1:
  ac: AC-001.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.format_greeting
  environment: local
  identity: none
  preconditions: []
  input:
    name: "World"
  expect:
    output: "Hello, World!"
    effects: []
    errors: []
    leaks: none

T-001.2:
  ac: AC-001.2
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    name: "World"
  expect:
    output: "Hello, World!"
    effects: []
    errors: []
    leaks: none

T-001.3:
  ac: AC-001.3
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    argv: [" "]
  expect:
    output: {stdout: "usage: greet <name>", exit_code: 2}
    effects: []
    errors: []
    leaks: none

T-002.1:
  ac: AC-002.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    argv: ["--version"]
  expect:
    output: {stdout: "greet 1.0.0", exit_code: 0}
    effects: []
    errors: []
    leaks: none
"""

GUIDE_CASES = """T-010.1:
  ac: AC-010.1
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

T-010.2:
  ac: AC-010.2
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
    threshold: 1.0
    effects: []
    errors: []
    leaks: none
"""

OUTLINE = """install-guide:
  path: docs/guide/install.md
  audience: first-time users on Windows or macOS
  purpose: install the CLI and run it once
  sections: [Requirements, Install, First run, Common problems]
  terms: [CLI, greeting]
  length: {min-words: 150, max-words: 1200}
"""

TESTING = """# Testing

## Levels

| Level | Harness command | Environment | Gate |
|---|---|---|---|
| unit | `uv run pytest tests/unit` | local | build |
| checks | `uv run pytest tests/checks` | local | build |
| judged | `uv run pytest tests/judged` | local | build |

## Harness

- **Lifecycle.** Not applicable: nothing is started.
- **Environment switch.** Not applicable: only the local environment exists.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** `uv` and `python3` on PATH; `claude` (Claude Code, signed in) runs the default grader of judged cases.
- **Clean state.** Not applicable: the tests keep no state.
- **Persistent environments.** Not applicable: no persistent environment.
- **Layout.** `tests/<level>/test_*.py`; each test's docstring cites its T-id, e.g. `@prd T-001.1`. `pyproject.toml` puts `src/` on the import path. Test roots: `tests/`.
- **HTTP requests.** Not applicable: no HTTP API.
- **Fixtures.** Not applicable: no fixture files.
- **Browser identity.** Not applicable: no UI.
- **Assertions.** Unit outputs compare with `==`; a judged test asserts `prd_judge.py`'s exit code and nothing else. A section of a document is a Markdown heading of any level whose text is an outline `sections` entry; other headings may sit between them. Each `sections` entry heads exactly one section; a repeated one fails.
- **Waits.** Not applicable: calls are synchronous.
- **Effects.** Not applicable: no side effects.
- **Leaks.** Not applicable: no logs.
- **Acceptance.** Not applicable: no acceptance cases.

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | Developer machine | Developer | none | none | none |

## Leak checks

| Sink | Read from | Scanned for |
|---|---|---|
| application logs | Not applicable: the command writes no logs | none |

## Fixtures

| Fixture | Creates | Load | Teardown |
|---|---|---|---|

## Sign-offs

| T-id | Owner | Date | Result |
|---|---|---|---|
"""

NFR = """# Non-functional requirements

None: greet has no measured bound.

## Observability

Not applicable: the command writes no logs and exports no metrics.
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

ERRORS = "# Error ledger\n\nNo entries yet. Add `### E-001 <title>` when the first error is diagnosed.\n"

GUIDE = """# Install the greet CLI

This guide takes you from nothing to one working greeting.

## Requirements

- A computer running Windows or macOS.
- A terminal: Terminal on macOS, PowerShell on Windows.
- `uv`, the Python tool runner. Install it from its project page before you start.
- The greet CLI source folder, downloaded and unzipped.

## Install

1. Open your terminal.
2. Move into the greet folder with `cd greet`.
3. Run `uv sync` to prepare the environment.
4. Run `uv run pytest` to confirm everything works.

Each step changes one thing, so if a step fails you know which one to look at.

## First run

Run `uv run --directory src python -m greet World`. The terminal prints the greeting:

```
Hello, World!
```

Replace `World` with your own name to greet yourself. The greeting always has the same shape,
a word, a comma and the name, followed by an exclamation mark.

## Common problems

- **uv is not found.** Close the terminal, open a new one and try again; the installer
  only updates the path of terminals opened afterwards.
- **The usage line appears.** The CLI needs exactly one name. Put a name with spaces in quotes,
  for example `"Ada Lovelace"`.
- **Tests fail on the first run.** Check that you ran `uv sync` in the greet folder, not in its
  parent folder, and run the tests again.

When none of these fits, copy the full message from the terminal and send it to whoever
shared the CLI with you; the message names the line that failed.
"""


def _write(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def _tool(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "--script", script, *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")


def main(dst: str, state: str) -> None:
    repo = Path(dst).resolve()
    if repo.exists() and any(repo.iterdir()):
        sys.exit(f"doc_repo: {dst} is not empty")
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q", "-b", "main")
    _write(repo, {
        "pyproject.toml": PYPROJECT,
        ".gitignore": ".venv/\n__pycache__/\n.pytest_cache/\n",
        "README.md": README,
        "src/greet/__init__.py": INIT,
        "src/greet/__main__.py": MAIN,
        "src/greet/cli.py": CLI,
        "tests/unit/test_greet.py": UNIT_TESTS,
    })
    subprocess.run(["uv", "lock", "-q"], cwd=repo, check=True)
    subprocess.run(["uv", "sync", "-q", "--locked"], cwd=repo, check=True)
    commit(repo, "Add the greet command", "pyproject.toml", "uv.lock", ".gitignore", "README.md", "src", "tests", date="2026-01-02T12:00:00+0000")
    if state != "empty":
        base = PRD + "/"
        _write(repo, {
            base + "prd.md": PRD_MD.format(fr10="approved"),
            base + "nfr.md": NFR,
            base + "testing.md": TESTING,
            base + "operations.md": OPERATIONS,
            base + "errors.md": ERRORS,
            base + "features/greet.md": GREET_FEATURE,
            base + "features/guide.md": GUIDE_FEATURE.format(status="approved"),
            base + "test-cases/greet.yaml": GREET_CASES,
            base + "test-cases/guide.yaml": GUIDE_CASES,
            base + "contracts/outline.yaml": OUTLINE,
            base + "contracts/errors.yaml": "# Format: references/prd-format.md, \"Contract YAML shapes\".\n{}\n",
            "tests/unit/test_greet.py": UNIT_TESTS_CITED,
        })
        commit(repo, "PRD: greet 1.0.0 Approved, FR-001 verified, FR-002 and FR-010 approved\n\nRefs: FR-001, FR-002, FR-010", "docs", "tests", date="2026-01-04T12:00:00+0000")
        hooks = _tool(repo, str(PLUGIN / "scripts/prd_hooks.py"), "install", PRD)
        if hooks.returncode != 0:
            sys.exit(f"doc_repo: prd_hooks install failed:\n{hooks.stdout}{hooks.stderr}")
        commit(repo, f"Ignore the judge record\n\n{NONE}", ".gitignore", date="2026-01-05T11:00:00+0000")
        commit(repo, f"Vendor the PRD toolkit\n\n{NONE}", ".prd-toolkit", date="2026-01-05T12:00:00+0000")
        block = _tool(repo, str(repo / ".prd-toolkit/prd_block.py"), PRD)
        if block.returncode != 0 or not (repo / "CLAUDE.md").is_file():
            sys.exit(f"doc_repo: prd_block failed:\n{block.stdout}{block.stderr}")
        commit(repo, f"Add the CLAUDE.md block\n\n{NONE}", "CLAUDE.md", date="2026-01-05T13:00:00+0000")
    if state == "built":
        _write(repo, {
            "docs/guide/install.md": GUIDE,
            PRD + "/features/guide.md": GUIDE_FEATURE.format(status="verified (since 1.0.0)"),
            PRD + "/prd.md": PRD_MD.format(fr10="verified"),
        })
        commit(repo, "Write the install guide\n\nRefs: FR-010", "docs", date="2026-01-06T12:00:00+0000")
    status = git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    if status:
        sys.exit(f"doc_repo: the tracked tree is not clean:\n{status}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in STATES:
        sys.exit(f"usage: doc_repo.py <dst> <{'|'.join(STATES)}>")
    main(sys.argv[1], sys.argv[2])
