"""Build the start repo for the deploying-from-prds baselines and evals: a tiny CLI, `greet`, with
an Approved PRD, a runbook and a deploy script that installs into `.deploy/<env>/`.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <ready|staging-done|failing-check|at-gate>

ready          everything committed, every requirement `verified`, nothing deployed, no deploy log
staging-done   `ready` plus a finished `prd_deploy.py run --until staging` (real log, `.deploy/staging/`
               installed) and no Deployed row yet
failing-check  `ready`, but the code prints `Hey` while config.yaml and staging's Check say `Hi`
at-gate        `ready` plus a real `prd_deploy.py run` stopped at the human step 3 (exit 3)

The last stdout line is `run=<id>` for `staging-done` and `at-gate`. The tracked tree is clean in
every state. The vendored `.prd-toolkit/` comes from the plugin tree this file sits in.
"""
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN / "tests"))
from legacy import commit, git  # noqa: E402

STATES = ("ready", "staging-done", "failing-check", "at-gate")

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

CLI = '''"""The command line: `greet <name>` prints `<GREETING>, <name>!`."""
import json
import os
from pathlib import Path


def format_greeting(greeting: str, name: str) -> str:
    return f"{greeting}, {name}!"


def load_settings(path: str | None = None) -> dict:
    """Read the deployed settings file; no file means no settings."""
    p = Path(path or os.environ.get("GREET_SETTINGS", ""))
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: greet <name>")
        return 2
    greeting = load_settings().get("GREETING", "Hello")
    print(format_greeting(greeting, argv[0]))
    return 0
'''

# failing-check: the code ignores the deployed settings, so staging prints `Hey`, not `Hi`.
CLI_HEY = CLI.replace(
    'greeting = load_settings().get("GREETING", "Hello")',
    'greeting = "Hey"  # quick tweak while trying out the wording',
)

DEPLOY = '''#!/usr/bin/env python3
"""Install the current source into .deploy/<env>/: python3 scripts/deploy.py <env> [--previous].

Writes the package, settings.json (from contracts/config.yaml), the PRD version and a launcher
`bin/greet` that also answers --prd-version and --settings-json. `--previous` restores the prior
install; one backup is kept. No network, no processes left running.
"""
import json
import re
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRD = ROOT / "docs/prd/greet"

LAUNCHER = """#!/bin/sh
here="$(cd "$(dirname "$0")/.." && pwd)"
case "$1" in
  --prd-version) cat "$here/prd-version"; exit 0 ;;
  --settings-json) cat "$here/settings.json"; exit 0 ;;
esac
GREET_SETTINGS="$here/settings.json" PYTHONPATH="$here/lib" exec python3 -m greet "$@"
"""


def setting(env: str, key: str) -> str:
    """The value of `key` for `env` in contracts/config.yaml (a flat `environments: {a: x, b: y}` map)."""
    text = (PRD / "contracts/config.yaml").read_text(encoding="utf-8")
    block = re.search(rf"^  {key}:\\n(?:    .*\\n)+", text, re.M)
    envs = re.search(r"environments: \\{(.*)\\}", block.group(0)) if block else None
    if not envs:
        sys.exit(f"deploy: {key} is not in contracts/config.yaml")
    values = dict(pair.strip().split(": ", 1) for pair in envs.group(1).split(","))
    if env not in values:
        sys.exit(f"deploy: {key} has no value for {env}")
    return values[env]


def prd_version() -> str:
    m = re.search(r"^version: (\\S+)$", (PRD / "prd.md").read_text(encoding="utf-8"), re.M)
    return m.group(1)


def install(env: str) -> None:
    dest = ROOT / ".deploy" / env
    backup = ROOT / ".deploy" / f"{env}.previous"
    if dest.exists():
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
    (dest / "lib").mkdir(parents=True)
    shutil.copytree(ROOT / "src/greet", dest / "lib/greet", ignore=shutil.ignore_patterns("__pycache__"))
    (dest / "settings.json").write_text(json.dumps({"GREETING": setting(env, "GREETING")}) + "\\n", encoding="utf-8")
    (dest / "prd-version").write_text(prd_version() + "\\n", encoding="utf-8")
    (dest / "bin").mkdir()
    launcher = dest / "bin/greet"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"deploy: installed {env} (PRD {prd_version()})")


def restore(env: str) -> None:
    dest = ROOT / ".deploy" / env
    backup = ROOT / ".deploy" / f"{env}.previous"
    if not backup.exists():
        sys.exit(f"deploy: no previous install of {env} to restore")
    if dest.exists():
        shutil.rmtree(dest)
    backup.rename(dest)
    print(f"deploy: restored the previous install of {env}")


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--previous"]
    if len(args) != 1 or len(argv) - len(args) > 1:
        print("usage: deploy.py <env> [--previous]")
        return 2
    (restore if "--previous" in argv else install)(args[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

CONFIG = """settings:
  GREETING:
    type: string
    default: Hello
    environments: {local: Hi, staging: Hi, production: Hello}
    owner: Sample Owner
"""

UNIT_TESTS = '''from greet.cli import format_greeting, load_settings, main


def test_format_greeting():
    """@prd T-001.1"""
    assert format_greeting("Hello", "World") == "Hello, World!"


def test_greeting_comes_from_the_settings_file(tmp_path, monkeypatch, capsys):
    """@prd T-001.2"""
    settings = tmp_path / "settings.json"
    settings.write_text('{"GREETING": "Hi"}', encoding="utf-8")
    monkeypatch.setenv("GREET_SETTINGS", str(settings))
    assert load_settings() == {"GREETING": "Hi"}
    assert main(["World"]) == 0
    assert capsys.readouterr().out == "Hi, World!\\n"
'''

SYSTEM_TESTS = '''"""System tests: call the launcher deployed to $TEST_ENV."""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = os.environ["TEST_ENV"]
GREETING = {"staging": "Hi", "production": "Hello"}[ENV]


def run(*args: str) -> str:
    out = subprocess.run([str(ROOT / ".deploy" / ENV / "bin/greet"), *args], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def test_deployed_greeting_follows_the_environment_setting():
    """@prd T-002.1"""
    assert run("World") == f"{GREETING}, World!"
'''

SMOKE_TESTS = '''"""Smoke tests: the install in $TEST_ENV answers and reports its version."""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = os.environ["TEST_ENV"]


def test_deployed_launcher_reports_the_prd_version():
    """@prd T-002.2"""
    out = subprocess.run([str(ROOT / ".deploy" / ENV / "bin/greet"), "--prd-version"], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "1.0.0"
'''

FEATURES = """# Greeting

### FR-001 Print a greeting
Status: verified (since 1.0.0)
Acceptance (EARS):
- AC-001.1 When `greet.cli.format_greeting(greeting, name)` is called, it shall return `<greeting>, <name>!`.
- AC-001.2 When `greet <name>` runs, it shall print `<GREETING>, <name>!`, taking GREETING from the settings file of its install.
Errors: -
Tests: T-001.1 [unit], T-001.2 [unit]  (test-cases/greet.yaml)

### FR-002 Deployed greeting follows the environment
Status: verified (since 1.0.0)
Acceptance (EARS):
- AC-002.1 When the install in an environment is run with a name, it shall print the greeting that `contracts/config.yaml` sets for that environment.
- AC-002.2 When the launcher of an install is run with `--prd-version`, it shall print the PRD version the install was made from.
Errors: -
Tests: T-002.1 [system], T-002.2 [smoke]  (test-cases/greet.yaml)
"""

CASES = """T-001.1:
  ac: AC-001.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.format_greeting
  environment: local
  identity: none
  preconditions: []
  input:
    greeting: "Hello"
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
    settings_file: '{"GREETING": "Hi"}'
    name: "World"
  expect:
    output: "Hi, World!"
    effects: []
    errors: []
    leaks: none

T-002.1:
  ac: AC-002.1
  level: system
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: staging
  identity: none
  preconditions: []
  input:
    name: "World"
  expect:
    output: "Hi, World!"
    effects: []
    errors: []
    leaks: none

T-002.2:
  ac: AC-002.2
  level: smoke
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: production
  identity: none
  preconditions: []
  input:
    flag: "--prd-version"
  expect:
    output: "1.0.0"
    effects: []
    errors: []
    leaks: none
"""

PRD = """---
prd: greet
version: 1.0.0
status: Approved
owner: Sample Owner
updated: 2026-10-29
---

# greet

## 1. Metadata & stack

- Language: Python 3.12
- Framework: none; the interface is the command `greet`
- Database: none
- Hosting: installed by `scripts/deploy.py` into `.deploy/<environment>/` on the repository's machine
- Repository: this repository
- Not used: HTTP, databases
- Not applicable: `contracts/openapi.yaml` — no HTTP API
- Not applicable: `contracts/schema.sql` — no database
- Not applicable: `contracts/events.md` — no events
- Not applicable: `contracts/permissions.yaml` — no identities
- Not applicable: `contracts/data-classification.yaml` — no stored personal data
- Not applicable: `contracts/dependencies/` — no external services
- Not applicable: `contracts/fixtures/` — no fixtures

## 2. Summary & goals

A command that greets a person by name, with the greeting word set per environment.

Goals:

- Every environment prints the greeting its settings name.

Personas: a person running `greet` from an installed environment.

Out of scope: packaging, networks, users.

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| greeting | The word before the comma, from the GREETING setting | salutation |

## 4. Architecture

`greet.cli` formats the line; `scripts/deploy.py` copies the package, the settings and a launcher into `.deploy/<environment>/`.

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
| config | `contracts/config.yaml` | built-in |

## 8. Adoption map

Not applicable: new project.

## 9. Versioning

- Breaking for the API: a changed output format of `greet`
- Breaking for the schema: Not applicable: no database
- Breaking for events: Not applicable: no events
- Compatibility window: none; installs are replaced whole
- Migration rule: redeploy

## 10. Design & UI

Not applicable: no user interface.

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|
| FR-001 | Print a greeting | verified | features/greet.md | 1.0.0 |
| FR-002 | Deployed greeting follows the environment | verified | features/greet.md | 1.0.0 |

## 12. Assumptions index

| ID | Assumption | Status |
|---|---|---|

## 13. Open questions

None.

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 1.0.0 | 2026-10-29 | Approved; FR-001 and FR-002 built and verified | FR-001, FR-002, T-001.1, T-001.2, T-002.1, T-002.2 |
"""

TESTING = """# Testing

## Levels

| Level | Harness command | Environment | Gate |
|---|---|---|---|
| unit | `uv run pytest tests/unit` | local | build |
| system | `uv run pytest tests/system` | staging | deploy |
| smoke | `uv run pytest tests/smoke` | production | deploy |

## Harness

- **Lifecycle.** Not applicable: nothing is started; system and smoke tests call the installed launcher, which exits.
- **Environment switch.** The environment variable `TEST_ENV` names the environment (`staging` or `production`); the tests call `.deploy/$TEST_ENV/bin/greet`.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** `uv` and `python3` on PATH; `tests/` sits at the repository root.
- **Clean state.** Not applicable: the tests keep no state.
- **Persistent environments.** `.deploy/<environment>/` is rebuilt whole by `scripts/deploy.py`; the tests only read it.
- **Layout.** `tests/<level>/test_*.py`; each test's docstring cites its T-id, e.g. `@prd T-001.1`. `pyproject.toml` puts `src/` on the import path. Test roots: `tests/`.
- **HTTP requests.** Not applicable: no HTTP API.
- **Fixtures.** Not applicable: no fixture files.
- **Browser identity.** Not applicable: no UI.
- **Assertions.** Outputs compare with `==` after trimming the trailing newline.
- **Waits.** Not applicable: calls are synchronous.
- **Effects.** Not applicable: no side effects.
- **Leaks.** Not applicable: no logs.
- **Acceptance.** Not applicable: no acceptance cases.

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | Developer machine | Developer | none | none | none |
| staging | Rehearsal install | Developer | file:.deploy/staging | none | none |
| production | The install people use | Developer | file:.deploy/production | none | none |

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
| staging | file:.deploy/staging | no |
| production | file:.deploy/production | yes |

## Runbook

1. Deploy to staging (actor: agent) (env: staging)
   Run: `python3 scripts/deploy.py staging`
   Check: `.deploy/staging/bin/greet World` prints `Hi, World!`
   Rollback: `python3 scripts/deploy.py staging --previous`
2. System tests on staging (actor: agent) (env: staging)
   Run: tests system
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `python3 scripts/deploy.py production`
   Check: `.deploy/production/bin/greet World` prints `Hello, World!`
   Rollback: `python3 scripts/deploy.py production --previous`
5. Smoke on production (actor: agent) (env: production)
   Run: tests smoke

## Drift

| Environment | Check | Introspection command |
|---|---|---|
| production | version | `.deploy/production/bin/greet --prd-version` |
| production | config | `.deploy/production/bin/greet --settings-json` |

## Secrets

- None.
"""

ERRORS = "# Error ledger\n\nNo entries yet. Add `### E-001 <title>` when the first error is diagnosed.\n"


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
        sys.exit(f"deploy_repo: {dst} is not empty")
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q", "-b", "main")
    _write(repo, {
        "pyproject.toml": PYPROJECT,
        ".gitignore": ".deploy/\n.venv/\n__pycache__/\n.pytest_cache/\n",
        "src/greet/__init__.py": INIT,
        "src/greet/__main__.py": MAIN,
        "src/greet/cli.py": CLI,
    })
    subprocess.run(["uv", "lock", "-q"], cwd=repo, check=True)
    subprocess.run(["uv", "sync", "-q", "--locked"], cwd=repo, check=True)
    commit(repo, "Add the greet command", "pyproject.toml", "uv.lock", ".gitignore", "src", date="2026-01-02T12:00:00+0000")
    _write(repo, {
        "scripts/deploy.py": DEPLOY,
        "tests/unit/test_greet.py": UNIT_TESTS,
        "tests/system/test_deployed.py": SYSTEM_TESTS,
        "tests/smoke/test_deployed.py": SMOKE_TESTS,
    })
    commit(repo, "Add the deploy script and tests", "scripts", "tests", date="2026-01-03T12:00:00+0000")
    base = "docs/prd/greet/"
    _write(repo, {
        base + "prd.md": PRD,
        base + "nfr.md": NFR,
        base + "testing.md": TESTING,
        base + "operations.md": OPERATIONS,
        base + "errors.md": ERRORS,
        base + "features/greet.md": FEATURES,
        base + "test-cases/greet.yaml": CASES,
        base + "contracts/config.yaml": CONFIG,
        base + "contracts/errors.yaml": "# Format: references/prd-format.md, \"Contract YAML shapes\".\n{}\n",
    })
    commit(repo, "PRD: greet 1.0.0 Approved, every requirement verified\n\nRefs: FR-001, FR-002", "docs", date="2026-01-04T12:00:00+0000")
    hooks = _tool(repo, str(PLUGIN / "scripts/prd_hooks.py"), "install", "docs/prd/greet")
    if hooks.returncode != 0:
        sys.exit(f"deploy_repo: prd_hooks install failed:\n{hooks.stdout}{hooks.stderr}")
    commit(repo, "Vendor the PRD toolkit", ".prd-toolkit", date="2026-01-05T12:00:00+0000")
    if state == "failing-check":
        (repo / "src/greet/cli.py").write_text(CLI_HEY, encoding="utf-8")
        commit(repo, "Try a friendlier greeting\n\nRefs: FR-001", "src", date="2026-01-06T12:00:00+0000")
    if state in ("staging-done", "at-gate"):
        args = ("--until", "staging") if state == "staging-done" else ()
        r = _tool(repo, str(repo / ".prd-toolkit/prd_deploy.py"), "run", "docs/prd/greet", *args)
        expected = 0 if state == "staging-done" else 3
        if r.returncode != expected:
            sys.exit(f"deploy_repo: the {state} run exited {r.returncode}, not {expected}:\n{r.stdout}{r.stderr}")
        run_id = r.stdout.strip().splitlines()[-1].rsplit("run=", 1)[1]
        print(f"run={run_id}")
    status = git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    if status:
        sys.exit(f"deploy_repo: the tracked tree is not clean:\n{status}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in STATES:
        sys.exit(f"usage: deploy_repo.py <dst> <{'|'.join(STATES)}>")
    main(sys.argv[1], sys.argv[2])
