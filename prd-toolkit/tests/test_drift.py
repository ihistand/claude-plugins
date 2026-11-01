"""prd_drift.py: what an environment runs against what the PRD says."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from deploy_fixture import deploy_repo

SCRIPT = Path(__file__).parent.parent / "scripts/prd_drift.py"
OPS = "docs/prd/orders/operations.md"
CONFIG = "docs/prd/orders/contracts/config.yaml"
DEPLOYED = """
## Deployed

| Environment | PRD version | Commit | Date | Run |
|---|---|---|---|---|
| production | 1.0.0 | abc1234 | 2026-11-01 | r1 |
"""


@pytest.fixture
def repo(tmp_path):
    r = deploy_repo(tmp_path)
    ops = r / OPS
    ops.write_text(ops.read_text(encoding="utf-8").replace("## Secrets", DEPLOYED.lstrip("\n") + "\n## Secrets"), encoding="utf-8")
    put(r, "version", "1.0.0\n")
    put(r, "settings.json", json.dumps({"IMPORT_BATCH_SIZE": 500, "GREETING": "Hello"}))
    return r


def put(repo: Path, name: str, text: str, env: str = "production") -> None:
    (repo / ".deploy" / env).mkdir(parents=True, exist_ok=True)
    (repo / ".deploy" / env / name).write_text(text, encoding="utf-8")


def drift(repo: Path, *args: str):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), str(repo / "docs/prd/orders"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=dict(os.environ), cwd=repo)


def line_of(repo: Path, needle: str) -> int:
    return next(i for i, t in enumerate((repo / OPS).read_text(encoding="utf-8").splitlines(), 1) if needle in t)


def test_clean(repo):
    r = drift(repo)
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


def test_version_drift(repo):
    put(repo, "version", "0.9.0\n")
    r = drift(repo)
    n = line_of(repo, "| production | version |")
    assert r.returncode == 1 and r.stderr == ""
    assert r.stdout == f"operations.md:{n}: drift-version: production runs 0.9.0; Deployed says 1.0.0\n"


def test_no_deployed_row(repo):
    ops = repo / OPS
    ops.write_text(ops.read_text(encoding="utf-8").replace("| production | 1.0.0 | abc1234 | 2026-11-01 | r1 |\n", ""), encoding="utf-8")
    r = drift(repo)
    n = line_of(repo, "| production | version |")
    assert r.returncode == 1
    assert r.stdout == f"operations.md:{n}: drift-version: production has no Deployed row\n"


def test_config_differs(repo):
    put(repo, "settings.json", json.dumps({"IMPORT_BATCH_SIZE": 500, "GREETING": "Hi"}))
    r = drift(repo)
    n = line_of(repo, "| production | config |")
    assert r.returncode == 1
    assert r.stdout == f'operations.md:{n}: drift-config: production GREETING is "Hi"; config.yaml says "Hello"\n'


def test_config_value_types(repo):
    put(repo, "settings.json", json.dumps({"IMPORT_BATCH_SIZE": "500", "GREETING": "Hello"}))
    r = drift(repo)
    assert r.returncode == 1
    assert 'IMPORT_BATCH_SIZE is "500"; config.yaml says 500' in r.stdout


def test_config_missing_extra(repo):
    put(repo, "settings.json", json.dumps({"GREETING": "Hello", "SURPRISE": 1}))
    r = drift(repo)
    n = line_of(repo, "| production | config |")
    assert r.returncode == 1
    assert r.stdout.splitlines() == [
        f"operations.md:{n}: drift-config: production is missing IMPORT_BATCH_SIZE; config.yaml says 500",
        f"operations.md:{n}: drift-config: production has SURPRISE, which config.yaml does not define",
    ]


def test_config_default(repo):
    cfg = repo / CONFIG
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("staging: 500, production: 500", "staging: 500"), encoding="utf-8")
    put(repo, "settings.json", json.dumps({"IMPORT_BATCH_SIZE": 7, "GREETING": "Hello"}))
    r = drift(repo)
    assert r.returncode == 1
    assert "IMPORT_BATCH_SIZE is 7; config.yaml says 500" in r.stdout


def test_setting_without_value_not_compared(repo):
    cfg = repo / CONFIG
    cfg.write_text("settings:\n  ODD:\n    type: string\n    environments: {staging: x}\n    owner: o\n", encoding="utf-8")
    put(repo, "settings.json", "{}")
    r = drift(repo)
    assert (r.returncode, r.stdout) == (0, "")


def test_command_fails(repo):
    (repo / ".deploy/production/version").unlink()
    r = drift(repo)
    assert r.returncode == 2 and r.stdout == ""
    assert "drift production version: the command exited 1" in r.stderr


def test_error_keeps_findings_off_stdout(repo):
    put(repo, "version", "0.9.0\n")
    (repo / ".deploy/production/settings.json").unlink()
    r = drift(repo)
    assert r.returncode == 2 and r.stdout == ""
    assert "drift-version: production runs 0.9.0" in r.stderr and "drift production config: the command exited 1" in r.stderr


def test_unparseable_json(repo):
    put(repo, "settings.json", "[1, 2]")
    r = drift(repo)
    n = line_of(repo, "| production | config |")
    assert r.returncode == 2 and r.stdout == ""
    assert f"operations.md:{n}: drift production config: the output is not a JSON object" in r.stderr
    put(repo, "settings.json", "not json")
    assert "the output is not a JSON object" in drift(repo).stderr


def test_no_command(repo):
    ops = repo / OPS
    ops.write_text(ops.read_text(encoding="utf-8").replace("`cat .deploy/production/version`", "by hand"), encoding="utf-8")
    r = drift(repo)
    assert r.returncode == 2 and "drift production version: has no command" in r.stderr


def test_env_filter(repo):
    ops = repo / OPS
    ops.write_text(ops.read_text(encoding="utf-8").replace("| production | config |", "| staging | version | `cat .deploy/staging/version` |\n| production | config |", 1), encoding="utf-8")
    put(repo, "version", "9.9.9\n", env="staging")
    assert drift(repo, "--env", "production").returncode == 0
    r = drift(repo, "--env", "staging")
    assert r.returncode == 1 and "staging has no Deployed row" in r.stdout and "production" not in r.stdout


def test_env_without_rows(repo):
    r = drift(repo, "--env", "ci")
    assert r.returncode == 2 and r.stdout == "" and "production" in r.stderr


def test_command_gets_prd_env(repo):
    ops = repo / OPS
    ops.write_text(ops.read_text(encoding="utf-8").replace("`cat .deploy/production/version`", "`echo $PRD_ENV-x`"), encoding="utf-8")
    r = drift(repo)
    assert r.returncode == 1 and "production runs production-x" in r.stdout
