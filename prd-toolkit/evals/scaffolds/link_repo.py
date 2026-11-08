"""Build the start repos for the coordinating-prds (0.7) baselines, evals and proof: `greet-client`, which prints a
banner around the greeting of `greet`'s staging install, and `greet`, the repo of deploy_repo.py with a `cli` contract.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <unlinked|linked|cs-running> [--upstream <path>]

<dst> becomes the greet-client repository (so an eval session's cwd is a repository) and <path> (default
<dst>/upstream/greet, then listed in the client's .gitignore) the greet repository. Both must be empty or absent.
The client's contracts/config.yaml setting GREET holds the path of greet's staging install relative to the client
root, and every links.md Location is a relative path too.

unlinked    greet: deploy_repo.py's `ready`, plus a patch (1.0.1) adding the custom contract type `cli`
            (contracts/cli.yaml, key `greet`: arguments, output, exit codes; its validator runs from the PRD folder)
            and a real `prd_deploy.py run --until staging` (the log under .git, `.deploy/staging/` installed, no
            Deployed row, as deploy_repo's `staging-done`). greet-client: an Approved PRD for `welcome <name>`
            (FR-001 prints `*** <greeting> ***` around the output of greet's staging install; FR-002 an empty name
            is an error), code, unit tests, a deploy-gate system test and a runbook with a local staging install,
            every requirement `verified`. No links.md on either side.
linked      `unlinked`, then the client's system T-id cites `cli:greet/greet`, the vendored `prd_links.py add`
            writes links.md on both sides and `sync` the snapshot and lock, each side a patch (`format: links.md
            (prd-toolkit 0.7)`) committed; lint and `check` exit 0 in both.
cs-running  `linked`, then greet's `changeset new` writes greet/changes/CS-001.md "greet --json" (both repos as
            members), both repos branch `cs-001-greet-json`, both PRDs change (greet 1.1.0: FR-003 `greet --json`
            prints {"greeting": …, "name": …}; greet-client 1.1.0: FR-001 reads `greet --json`), `changeset approve`
            records the reply "approve CS-001", greet's change is built (code and a unit test citing T-003.1) and
            moved to `verified` with `changeset set`; Status `running`, the client's row `approved`. greet's
            `check` exits 1 there (its working tree changed `cli:greet`, which the client cites); the client's 0.

Every repo gets the managed CLAUDE.md block (the vendored `prd_block.py`, `Refs: none (no behaviour change)`), as
approval writes it, so a plain prompt routes to the skills in either repo. Every date the tools write is fixed by
`PRD_LINKS_TODAY`. The tracked trees are clean in every state; `cs-running` leaves both on its branch.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(PLUGIN / "tests"))
import deploy_repo  # noqa: E402
from legacy import commit, git  # noqa: E402

STATES = ("unlinked", "linked", "cs-running")
GREET = "docs/prd/greet"
CLIENT = "docs/prd/greet-client"
TODAY = "2026-11-02"
TITLE = "greet --json"
BRANCH = "cs-001-greet-json"
NONE = "Refs: none (no behaviour change)"
VALIDATOR = ("uv run --with pyyaml python3 -c \"import sys,yaml; sys.exit(0 if isinstance(yaml.safe_load("
             "open('contracts/cli.yaml')), dict) else 1)\"")

# ---------------------------------------------------------------- greet: the cli contract (1.0.1)

CLI_YAML = """# Format: the custom contract type cli (prd.md section 7): one top-level key per command.
greet:
  arguments:
    - name: name
      required: true
      description: the person to greet
  output: 'one line on stdout, `<GREETING>, <name>!`, GREETING from the settings file of the install'
  exit codes:
    0: the greeting was printed
    2: 'not exactly one argument; prints `usage: greet <name>`'
"""

# cs-running: the --json form of the same command
CLI_YAML_JSON = """# Format: the custom contract type cli (prd.md section 7): one top-level key per command.
greet:
  arguments:
    - name: --json
      required: false
      description: print the greeting and the name as one JSON object instead
    - name: name
      required: true
      description: the person to greet
  output: 'one line on stdout, `<GREETING>, <name>!`, GREETING from the settings file of the install; with --json, `{"greeting": "<GREETING>", "name": "<name>"}`'
  exit codes:
    0: the greeting was printed
    2: 'not exactly one name; prints `usage: greet [--json] <name>`'
"""

# ---------------------------------------------------------------- greet-client

PYPROJECT = """[project]
name = "greet-client"
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

INIT = '"""welcome: print a banner around the greeting of greet."""\n'

MAIN = '''"""Run as `python -m welcome`."""
import sys

from welcome.cli import main

sys.exit(main(sys.argv[1:]))
'''

CLI = '''"""The command line: `welcome <name>` prints `*** <greeting> ***`, the greeting printed by greet's install."""
import json
import os
import subprocess
import sys
from pathlib import Path


def banner(greeting: str) -> str:
    return f"*** {greeting} ***"


def load_settings(path: str | None = None) -> dict:
    """Read the deployed settings file; no file means no settings."""
    p = Path(path or os.environ.get("WELCOME_SETTINGS", ""))
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: welcome <name>")
        return 2
    if not argv[0].strip():
        print("welcome: the name is empty", file=sys.stderr)
        return 1
    greet = load_settings().get("GREET", "greet")
    out = subprocess.run([greet, argv[0]], capture_output=True, text=True, check=True).stdout
    print(banner(out.strip()))
    return 0
'''

DEPLOY = '''#!/usr/bin/env python3
"""Install the current source into .deploy/<env>/: python3 scripts/deploy.py <env> [--previous].

Writes the package, settings.json (GREET from contracts/config.yaml, resolved against the repository root) and a
launcher `bin/welcome`. `--previous` restores the prior install; one backup is kept. No network, no processes left
running.
"""
import json
import re
import shutil
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRD = ROOT / "docs/prd/greet-client"

LAUNCHER = """#!/bin/sh
here="$(cd "$(dirname "$0")/.." && pwd)"
WELCOME_SETTINGS="$here/settings.json" PYTHONPATH="$here/lib" exec python3 -m welcome "$@"
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


def install(env: str) -> None:
    dest = ROOT / ".deploy" / env
    backup = ROOT / ".deploy" / f"{env}.previous"
    if dest.exists():
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
    (dest / "lib").mkdir(parents=True)
    shutil.copytree(ROOT / "src/welcome", dest / "lib/welcome", ignore=shutil.ignore_patterns("__pycache__"))
    greet = (ROOT / setting(env, "GREET")).resolve()
    (dest / "settings.json").write_text(json.dumps({"GREET": str(greet)}) + "\\n", encoding="utf-8")
    (dest / "bin").mkdir()
    launcher = dest / "bin/welcome"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"deploy: installed {env}")


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

UNIT_TESTS = '''import subprocess

from welcome.cli import banner, main


def test_banner():
    """@prd T-001.1"""
    assert banner("Hi, World!") == "*** Hi, World! ***"


def test_prints_the_banner_around_the_greet_output(tmp_path, monkeypatch, capsys):
    """@prd T-001.1"""
    settings = tmp_path / "settings.json"
    settings.write_text('{"GREET": "greet"}', encoding="utf-8")
    monkeypatch.setenv("WELCOME_SETTINGS", str(settings))
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "Hi, World!\\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert main(["World"]) == 0
    assert calls == [["greet", "World"]]
    assert capsys.readouterr().out == "*** Hi, World! ***\\n"


def test_an_empty_name_is_an_error(monkeypatch, capsys):
    """@prd T-002.1"""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("greet was called")))
    assert main([""]) == 1
    out = capsys.readouterr()
    assert out.out == "" and out.err == "welcome: the name is empty\\n"
'''

SYSTEM_TESTS = '''"""System tests: call the launcher deployed to $TEST_ENV, which runs greet's install named by GREET."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = os.environ["TEST_ENV"]


def greet_install() -> Path:
    """GREET for $TEST_ENV in contracts/config.yaml, relative to the repository root."""
    text = (ROOT / "docs/prd/greet-client/contracts/config.yaml").read_text(encoding="utf-8")
    envs = re.search(r"^  GREET:\\n(?:    .*\\n)*?    environments: \\{(.*)\\}", text, re.M).group(1)
    return ROOT / dict(p.strip().split(": ", 1) for p in envs.split(","))[ENV]


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def test_deployed_banner_wraps_the_staging_greeting():
    """@prd T-001.2"""
    greeting = run([str(greet_install()), "World"])
    assert greeting
    assert run([str(ROOT / ".deploy" / ENV / "bin/welcome"), "World"]) == f"*** {greeting} ***"
'''

CONFIG = """settings:
  GREET:
    type: string
    default: {path}
    environments: {{local: {path}, staging: {path}, production: {production}}}
    owner: Sample Owner
"""

FEATURES = """# Welcome

### FR-001 Print a banner around the greeting
Status: verified (since 1.0.0)
Acceptance (EARS):
- AC-001.1 When `welcome <name>` runs, it shall run the install of greet that GREET names with `<name>` and print `*** <greeting> ***`, `<greeting>` being the line greet printed.
- AC-001.2 When the install of welcome in staging is run with a name, it shall print `*** <greeting> ***` around the output of the staging install of greet for that name.
Errors: -
Tests: T-001.1 [unit], T-001.2 [system]  (test-cases/welcome.yaml)

### FR-002 An empty name is an error
Status: verified (since 1.0.0)
Acceptance (EARS):
- AC-002.1 If `welcome` is run with an empty name, then it shall print `welcome: the name is empty` on stderr, exit 1 and not run greet.
Errors: -
Tests: T-002.1 [unit]  (test-cases/welcome.yaml)
"""

CASES = """T-001.1:
  ac: AC-001.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:welcome.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    greet_prints: "Hi, World!"
    name: "World"
  expect:
    output: "*** Hi, World! ***"
    effects: []
    errors: []
    leaks: none

T-001.2:
  ac: AC-001.2
  level: system
  refs: ["testing.md#Harness"]
  target: code:welcome.cli.main
  environment: staging
  identity: none
  preconditions: []
  input:
    name: "World"
  expect:
    output: "*** <the staging install of greet's output for World> ***"
    effects: []
    errors: []
    leaks: none

T-002.1:
  ac: AC-002.1
  level: unit
  refs: ["testing.md#Harness"]
  target: code:welcome.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    name: ""
  expect:
    output: "exit 1; stderr `welcome: the name is empty`; greet not run"
    effects: []
    errors: []
    leaks: none
"""

PRD = """---
prd: greet-client
version: 1.0.0
status: Approved
owner: Sample Owner
updated: 2026-10-30
---

# greet-client

## 1. Metadata & stack

- Language: Python 3.12
- Framework: none; the interface is the command `welcome`
- Database: none
- Hosting: installed by `scripts/deploy.py` into `.deploy/<environment>/` on the repository's machine
- Repository: this repository
- Not used: HTTP, databases
- Not applicable: `contracts/openapi.yaml` — no HTTP API
- Not applicable: `contracts/schema.sql` — no database
- Not applicable: `contracts/events.md` — no events
- Not applicable: `contracts/permissions.yaml` — no identities
- Not applicable: `contracts/data-classification.yaml` — no stored personal data
- Not applicable: `contracts/dependencies/` — greet is reached through its install, named by the GREET setting
- Not applicable: `contracts/fixtures/` — no fixtures

## 2. Summary & goals

A command that prints a banner around the greeting of the `greet` command.

Goals:

- `welcome <name>` shows greet's greeting for the name, framed.

Personas: a person running `welcome` from an installed environment.

Out of scope: packaging, networks, users, greet itself.

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| greeting | The line the install of greet prints for a name | salutation |
| banner | The greeting between `*** ` and ` ***` | frame |

## 4. Architecture

`welcome.cli` runs the install of greet that the GREET setting names and prints its output as a banner; `scripts/deploy.py` copies the package, the settings and a launcher into `.deploy/<environment>/`.

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

- Breaking for the API: a changed output format of `welcome`
- Breaking for the schema: Not applicable: no database
- Breaking for events: Not applicable: no events
- Compatibility window: none; installs are replaced whole
- Migration rule: redeploy

## 10. Design & UI

Not applicable: no user interface.

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|
| FR-001 | Print a banner around the greeting | verified | features/welcome.md | 1.0.0 |
| FR-002 | An empty name is an error | verified | features/welcome.md | 1.0.0 |

## 12. Assumptions index

| ID | Assumption | Status |
|---|---|---|

## 13. Open questions

None.

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 1.0.0 | 2026-10-30 | Approved; FR-001 and FR-002 built and verified | FR-001, FR-002, T-001.1, T-001.2, T-002.1 |
"""

TESTING = """# Testing

## Levels

| Level | Harness command | Environment | Gate |
|---|---|---|---|
| unit | `uv run pytest tests/unit` | local | build |
| system | `uv run pytest tests/system` | staging | deploy |

## Harness

- **Lifecycle.** Not applicable: nothing is started; system tests call the installed launcher, which exits.
- **Environment switch.** The environment variable `TEST_ENV` names the environment (`staging`) and must be set: a run without it fails before any test. The tests call `.deploy/$TEST_ENV/bin/welcome`, and the install of greet that GREET names for it in `contracts/config.yaml`, a path relative to the repository root.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** `uv` and `python3` on PATH; `tests/` sits at the repository root; greet's staging install at the path GREET names.
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

None: greet-client has no measured bound.

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
   Check: `.deploy/staging/bin/welcome World` prints `*** Hi, World! ***`
   Rollback: `python3 scripts/deploy.py staging --previous`
2. System tests on staging (actor: agent) (env: staging)
   Run: tests system
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `python3 scripts/deploy.py production`
   Check: `.deploy/production/bin/welcome World` prints `*** Hello, World! ***`
   Rollback: `python3 scripts/deploy.py production --previous`

## Drift

| Environment | Check | Introspection command |
|---|---|---|

## Secrets

- None.
"""

ERRORS = "# Error ledger\n\nNo entries yet. Add `### E-001 <title>` when the first error is diagnosed.\n"

# ---------------------------------------------------------------- cs-running: greet --json

GREET_JSON_FR = """
### FR-003 Print the greeting as JSON
Status: approved (since 1.1.0)
Acceptance (EARS):
- AC-003.1 When `greet --json <name>` runs, it shall print `{"greeting": "<GREETING>", "name": "<name>"}` on one line, taking GREETING from the settings file of its install.
Errors: -
Tests: T-003.1 [unit]  (test-cases/greet.yaml)
"""

GREET_JSON_CASE = """
T-003.1:
  ac: AC-003.1
  level: unit
  refs: ["testing.md#Harness"]
  target: cli:greet
  environment: local
  identity: none
  preconditions: []
  input:
    settings_file: '{"GREETING": "Hi"}'
    argv: ["--json", "World"]
  expect:
    output: '{"greeting": "Hi", "name": "World"}'
    effects: []
    errors: []
    leaks: none
"""

GREET_JSON_TEST = '''

def test_json_prints_the_greeting_and_the_name(tmp_path, monkeypatch, capsys):
    """@prd T-003.1"""
    import json

    settings = tmp_path / "settings.json"
    settings.write_text('{"GREETING": "Hi"}', encoding="utf-8")
    monkeypatch.setenv("GREET_SETTINGS", str(settings))
    assert main(["--json", "World"]) == 0
    assert json.loads(capsys.readouterr().out) == {"greeting": "Hi", "name": "World"}
'''

GREET_JSON_MAIN = '''def main(argv: list[str]) -> int:
    as_json = argv[:1] == ["--json"]
    names = argv[1:] if as_json else argv
    if len(names) != 1:
        print("usage: greet [--json] <name>")
        return 2
    greeting = load_settings().get("GREETING", "Hello")
    if as_json:
        print(json.dumps({"greeting": greeting, "name": names[0]}))
    else:
        print(format_greeting(greeting, names[0]))
    return 0
'''

CLIENT_JSON_AC = ("- AC-001.1 When `welcome <name>` runs, it shall run the install of greet that GREET names as "
                  "`greet --json <name>` and print `*** <greeting>, <name>! ***` from the `greeting` and `name` of its "
                  "JSON output.")


# ---------------------------------------------------------------- helpers

def _write(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"link_repo: {path.name}: expected one {old!r}; update the scaffold")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _tool(repo: Path, script: str, *args: str, expect: int = 0) -> str:
    env = {**os.environ, "PRD_LINKS_TODAY": TODAY}
    r = subprocess.run(["uv", "run", "--script", script, *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", env=env)
    if r.returncode != expect:
        sys.exit(f"link_repo: {Path(script).name} {' '.join(args)} exited {r.returncode}, not {expect}:\n{r.stdout}{r.stderr}")
    return r.stdout


def _links(repo: Path, *args: str, expect: int = 0) -> str:
    return _tool(repo, str(repo / ".prd-toolkit/prd_links.py"), *args, expect=expect)


def _bump(repo: Path, prd: str, old: str, new: str, row: str, date: str = TODAY) -> None:
    """Move the PRD from `old` to `new` (`updated: <date>`) and add its §14 row (`| new | date | row |`)."""
    p = repo / prd / "prd.md"
    _edit(p, f"\nversion: {old}\n", f"\nversion: {new}\n")
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"^updated: .*$", f"updated: {date}", text, count=1, flags=re.M)
    p.write_text(text.rstrip("\n") + f"\n| {new} | {date} | {row} |\n", encoding="utf-8")


def _claude_md(repo: Path, prd: str, date: str) -> None:
    _tool(repo, str(repo / ".prd-toolkit/prd_block.py"), prd)
    if git(repo, "status", "--porcelain", "--", "CLAUDE.md", "docs").strip():
        commit(repo, f"Update the CLAUDE.md block\n\n{NONE}", "CLAUDE.md", "docs", date=date)


def _relpath(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path, start)).as_posix()


def _empty(path: Path) -> bool:
    return not path.exists() or (path.is_dir() and not any(path.iterdir()))


# ---------------------------------------------------------------- the states

def _greet(greet: Path) -> None:
    """deploy_repo's `ready`, the cli patch (1.0.1), the CLAUDE.md block, and a staging run."""
    deploy_repo.main(str(greet), "ready")
    p = greet / GREET / "prd.md"
    _edit(p, "| config | `contracts/config.yaml` | built-in |\n",
          f"| config | `contracts/config.yaml` | built-in |\n| cli | `contracts/cli.yaml` | `{VALIDATOR}` |\n")
    _write(greet, {f"{GREET}/contracts/cli.yaml": CLI_YAML})
    _bump(greet, GREET, "1.0.0", "1.0.1", "Contract type cli: the greet command's arguments, output and exit codes | -", date="2026-10-30")
    commit(greet, f"PRD: greet 1.0.1, contract type cli\n\n{NONE}", GREET, date="2026-01-06T12:00:00+0000")
    _claude_md(greet, GREET, "2026-01-06T18:00:00+0000")
    out = _tool(greet, str(greet / ".prd-toolkit/prd_deploy.py"), "run", GREET, "--until", "staging")
    if "run=" not in out:
        sys.exit(f"link_repo: the staging run printed no run id:\n{out}")


def _client(client: Path, greet: Path) -> None:
    git(client, "init", "-q", "-b", "main")
    ignore = ".deploy/\n.venv/\n__pycache__/\n.pytest_cache/\n"
    if greet.is_relative_to(client):
        ignore += _relpath(greet, client) + "/\n"
    _write(client, {
        "pyproject.toml": PYPROJECT,
        ".gitignore": ignore,
        "src/welcome/__init__.py": INIT,
        "src/welcome/__main__.py": MAIN,
        "src/welcome/cli.py": CLI,
    })
    subprocess.run(["uv", "lock", "-q"], cwd=client, check=True)
    subprocess.run(["uv", "sync", "-q", "--locked"], cwd=client, check=True)
    commit(client, "Add the welcome command", "pyproject.toml", "uv.lock", ".gitignore", "src", date="2026-01-07T12:00:00+0000")
    _write(client, {
        "scripts/deploy.py": DEPLOY,
        "tests/unit/test_welcome.py": UNIT_TESTS,
        "tests/system/test_deployed.py": SYSTEM_TESTS,
    })
    commit(client, "Add the deploy script and tests", "scripts", "tests", date="2026-01-08T12:00:00+0000")
    install = _relpath(greet / ".deploy/staging/bin/greet", client)
    production = _relpath(greet / ".deploy/production/bin/greet", client)
    _write(client, {
        CLIENT + "/prd.md": PRD,
        CLIENT + "/nfr.md": NFR,
        CLIENT + "/testing.md": TESTING,
        CLIENT + "/operations.md": OPERATIONS,
        CLIENT + "/errors.md": ERRORS,
        CLIENT + "/features/welcome.md": FEATURES,
        CLIENT + "/test-cases/welcome.yaml": CASES,
        CLIENT + "/contracts/config.yaml": CONFIG.format(path=install, production=production),
        CLIENT + "/contracts/errors.yaml": "# Format: references/prd-format.md, \"Contract YAML shapes\".\n{}\n",
    })
    commit(client, "PRD: greet-client 1.0.0 Approved, every requirement verified\n\nRefs: FR-001, FR-002", "docs",
           date="2026-01-09T12:00:00+0000")
    _tool(client, str(PLUGIN / "scripts/prd_hooks.py"), "install", CLIENT)
    commit(client, "Ignore the judge record\n\nRefs: none (no behaviour change)", ".gitignore", date="2026-01-10T11:00:00+0000")
    commit(client, "Vendor the PRD toolkit", ".prd-toolkit", date="2026-01-10T12:00:00+0000")
    _claude_md(client, CLIENT, "2026-01-10T18:00:00+0000")


def _link(client: Path, greet: Path) -> None:
    """The client cites cli:greet/greet on its system T-id; add, then greet's patch, then sync and the client's patch."""
    _edit(client / CLIENT / "test-cases/welcome.yaml", "  level: system\n  refs: [\"testing.md#Harness\"]\n  target: code:welcome.cli.main\n",
          "  level: system\n  refs: [\"testing.md#Harness\"]\n  target: cli:greet/greet\n")
    _links(client, "add", CLIENT, _relpath(greet, client))
    _bump(greet, GREET, "1.0.1", "1.0.2", "format: links.md (prd-toolkit 0.7); consumer greet-client | -")
    commit(greet, f"PRD: greet 1.0.2, consumer greet-client\n\n{NONE}", GREET, date="2026-01-11T12:00:00+0000")
    _claude_md(greet, GREET, "2026-01-11T18:00:00+0000")
    out = _links(client, "sync", CLIENT, "greet")
    if "wrote contracts/upstream/greet/cli.yaml" not in out.splitlines():
        sys.exit(f"link_repo: sync did not snapshot cli:greet/greet:\n{out}")
    _bump(client, CLIENT, "1.0.0", "1.0.1", "format: links.md (prd-toolkit 0.7); T-001.2 cites cli:greet/greet | T-001.2")
    commit(client, f"PRD: greet-client 1.0.1, cites cli:greet/greet\n\n{NONE}", CLIENT, date="2026-01-12T12:00:00+0000")
    _claude_md(client, CLIENT, "2026-01-12T18:00:00+0000")


def _cs_running(client: Path, greet: Path) -> None:
    trailer = "Change-set: greet/CS-001"
    record = f"{GREET}/changes/CS-001.md"
    out = _links(greet, "changeset", "new", GREET, "--title", TITLE, "--member", _relpath(client, greet))
    if not out.strip().endswith("changes/CS-001.md"):
        sys.exit(f"link_repo: changeset new wrote {out.strip()!r}, not CS-001")
    for repo in (greet, client):
        git(repo, "switch", "-q", "-c", BRANCH)
    # both PRD changes, shown together and approved by one reply
    g = greet / GREET
    _edit(g / "features/greet.md", "Tests: T-002.1 [system], T-002.2 [smoke]  (test-cases/greet.yaml)\n",
          "Tests: T-002.1 [system], T-002.2 [smoke]  (test-cases/greet.yaml)\n" + GREET_JSON_FR)
    (g / "test-cases/greet.yaml").write_text((g / "test-cases/greet.yaml").read_text(encoding="utf-8") + GREET_JSON_CASE, encoding="utf-8")
    _write(greet, {f"{GREET}/contracts/cli.yaml": CLI_YAML_JSON})
    _edit(g / "prd.md", "| FR-002 | Deployed greeting follows the environment | verified | features/greet.md | 1.0.0 |\n",
          "| FR-002 | Deployed greeting follows the environment | verified | features/greet.md | 1.0.0 |\n"
          "| FR-003 | Print the greeting as JSON | approved | features/greet.md | 1.1.0 |\n")
    _bump(greet, GREET, "1.0.2", "1.1.0", "FR-003: `greet --json` prints the greeting and the name as JSON (CS-001) | FR-003, T-003.1")
    c = client / CLIENT
    _edit(c / "features/welcome.md", FEATURES.split("\n")[5], CLIENT_JSON_AC)
    _edit(c / "features/welcome.md", "Status: verified (since 1.0.0)\nAcceptance (EARS):\n- AC-001.1",
          "Status: approved (since 1.1.0)\nAcceptance (EARS):\n- AC-001.1")
    _edit(c / "prd.md", "| FR-001 | Print a banner around the greeting | verified | features/welcome.md | 1.0.0 |",
          "| FR-001 | Print a banner around the greeting | approved | features/welcome.md | 1.1.0 |")
    _bump(client, CLIENT, "1.0.1", "1.1.0", "FR-001: read greet's output as `greet --json` (CS-001) | FR-001, T-001.1")
    _links(greet, "changeset", "approve", record, "--reply", "approve CS-001")
    _links(greet, "changeset", "set", record, "greet", "version=1.1.0", "ids=FR-003")
    _links(greet, "changeset", "set", record, "greet-client", "version=1.1.0", "ids=FR-001")
    commit(greet, f"PRD: greet 1.1.0 Approved, greet --json\n\nRefs: FR-003\n{trailer}", GREET, date="2026-01-13T12:00:00+0000")
    commit(client, f"PRD: greet-client 1.1.0 Approved, read greet --json\n\nRefs: FR-001\n{trailer}", CLIENT,
           date="2026-01-13T12:05:00+0000")
    # greet's build: the unit test first, then the code; then built and verified
    unit = greet / "tests/unit/test_greet.py"
    unit.write_text(unit.read_text(encoding="utf-8") + GREET_JSON_TEST, encoding="utf-8")
    src = greet / "src/greet/cli.py"
    text = src.read_text(encoding="utf-8")
    start = text.index("def main(argv: list[str]) -> int:")
    src.write_text(text[:start] + GREET_JSON_MAIN, encoding="utf-8")
    commit(greet, f"greet --json prints the greeting and the name\n\nRefs: FR-003\n{trailer}", "src", "tests",
           date="2026-01-14T12:00:00+0000")
    r = subprocess.run(["uv", "run", "pytest", "-q", "tests/unit"], cwd=greet, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"link_repo: greet's unit tests fail on {BRANCH}:\n{r.stdout}{r.stderr}")
    _links(greet, "changeset", "set", record, "greet", "state=built")
    for old, new in (("approved", "built"), ("built", "verified")):
        _edit(g / "features/greet.md", f"Status: {old} (since 1.1.0)", f"Status: {new} (since 1.1.0)")
        _edit(g / "prd.md", f"| FR-003 | Print the greeting as JSON | {old} |", f"| FR-003 | Print the greeting as JSON | {new} |")
    _links(greet, "changeset", "set", record, "greet", "state=verified")
    commit(greet, f"FR-003 built and verified\n\nRefs: FR-003\n{trailer}", GREET, date="2026-01-14T18:00:00+0000")
    for repo, prd, date in ((greet, GREET, "2026-01-14T19:00:00+0000"), (client, CLIENT, "2026-01-14T19:05:00+0000")):
        _claude_md(repo, prd, date)


def main(dst: str, state: str, upstream: str | None) -> None:
    client = Path(dst).resolve()
    greet = Path(upstream).resolve() if upstream else client / "upstream/greet"
    for p in (client, greet):
        if not _empty(p):
            sys.exit(f"link_repo: {p} is not empty")
    if greet == client:
        sys.exit("link_repo: --upstream must not be the destination")
    client.mkdir(parents=True, exist_ok=True)
    _greet(greet)
    _client(client, greet)
    if state in ("linked", "cs-running"):
        _link(client, greet)
    if state == "cs-running":
        _cs_running(client, greet)
    for repo in (client, greet):
        status = git(repo, "status", "--porcelain", "--untracked-files=no").strip()
        if status:
            sys.exit(f"link_repo: the tracked tree of {repo} is not clean:\n{status}")


if __name__ == "__main__":
    args = sys.argv[1:]
    up = None
    if len(args) == 4 and args[2] == "--upstream":
        up, args = args[3], args[:2]
    if len(args) != 2 or args[1] not in STATES:
        sys.exit(f"usage: link_repo.py <dst> <{'|'.join(STATES)}> [--upstream <path>]")
    main(args[0], args[1], up)
