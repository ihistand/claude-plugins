"""A git repo with a lint-clean, trace-clean PRD and a shell-only runbook, for the deploy tests.

Layout of the runbook (spec section 3): 1 staging deploy, 2 `tests system` on staging, 3 human approval
on production, 4 production deploy, 5 `tests smoke` on production. Everything the steps do happens
in marker files under `.deploy/`, which is git-ignored.
"""
import re
import shutil
from pathlib import Path

from legacy import commit, git

FIXTURE = Path(__file__).parent / "fixtures/valid/orders"

CONFIG = """settings:
  IMPORT_BATCH_SIZE:
    type: integer
    default: 500
    environments: {local: 10, ci: 10, staging: 500, production: 500}
    owner: Sample Owner
  GREETING:
    type: string
    default: Hello
    environments: {local: Hi, ci: Hi, staging: Hi, production: Hello}
    owner: Sample Owner
"""

OPERATIONS = """# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| local | http://localhost:8080 | no |
| ci | none; runs inside the pipeline | no |
| staging | file:.deploy/staging | no |
| production | file:.deploy/production | yes |

## Runbook

1. Deploy to staging (actor: agent) (env: staging)
   Run: `mkdir -p .deploy/staging && echo Hi > .deploy/staging/greeting && echo 1.0.0 > .deploy/staging/version`
   Check: `cat .deploy/staging/greeting` prints `Hi`
   Rollback: `mkdir -p .deploy/staging && touch .deploy/staging/rolled-back`
2. System tests on staging (actor: agent) (env: staging)
   Run: tests system
3. Approve production (actor: human) (env: production)
   Do: read the staging results and reply "deploy production"
   Check: the reply says "deploy production"
4. Deploy to production (actor: agent) (env: production)
   Run: `mkdir -p .deploy/production && echo Hello > .deploy/production/greeting && echo 1.0.0 > .deploy/production/version && echo '{"GREETING": "Hello"}' > .deploy/production/settings.json`
   Check: `cat .deploy/production/greeting` prints `Hello`
   Rollback: `mkdir -p .deploy/production && touch .deploy/production/rolled-back`
5. Smoke on production (actor: agent) (env: production)
   Run: tests smoke

## Drift

| Environment | Check | Introspection command |
|---|---|---|
| production | version | `cat .deploy/production/version` |
| production | config | `cat .deploy/production/settings.json` |

## Secrets

None.
"""

GATE = """#!/usr/bin/env bash
# A stand-in harness command: records the environment it ran in and passes.
mkdir -p .deploy/tests
echo "$TEST_ENV" > ".deploy/tests/$1.env"
exit 0
"""


def deploy_repo(tmp_path: Path) -> Path:
    """Build the repo under `tmp_path/repo` and return its root; the PRD is `docs/prd/orders`."""
    repo = Path(tmp_path) / "repo"
    prd = repo / "docs/prd/orders"
    shutil.copytree(FIXTURE, prd)
    (prd / "operations.md").write_text(OPERATIONS, encoding="utf-8")
    (prd / "contracts/config.yaml").write_text(CONFIG, encoding="utf-8")
    for rel in ("prd.md", "nfr.md", "features/api.md", "features/import.md"):
        p = prd / rel
        text = p.read_text(encoding="utf-8").replace("Status: live (since 1.0.0)", "Status: verified (since 1.0.0)")
        text = re.sub(r"^(\| (?:UJ|FR|NFR)-\d+ \|.*?\| )live( \|)", r"\1verified\2", text, flags=re.M)
        p.write_text(text, encoding="utf-8")
    testing = (prd / "testing.md").read_text(encoding="utf-8")
    for level in ("system", "e2e", "smoke"):
        testing = re.sub(rf"^(\| {level} \| )`[^`]*`", rf"\1`bash tools/gate.sh {level}`", testing, flags=re.M)
    (prd / "testing.md").write_text(testing, encoding="utf-8")
    (repo / "tools").mkdir()
    (repo / "tools/gate.sh").write_text(GATE, encoding="utf-8")
    (repo / ".gitignore").write_text(".deploy/\n", encoding="utf-8")
    tids = sorted(set(re.findall(r"^(T-\d{3}\.\d+):", "".join(p.read_text(encoding="utf-8") for p in (prd / "test-cases").glob("*.yaml")), flags=re.M)))
    (repo / "tests").mkdir()
    (repo / "tests/test_cases.py").write_text("".join(f'def test_{t[2:].replace(".", "_")}():\n    """@prd {t}"""\n\n\n' for t in tids), encoding="utf-8")
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "Fixture", ".gitignore", "docs", "tests", "tools")
    return repo


AHEAD_TAIL = """2. Approve staging (actor: human) (env: staging)
   Do: reply "staging ok"
   Check: the reply says "staging ok"
3. Approve notes (actor: human) (env: staging)
   Do: reply "notes ok"
   Check: the reply says "notes ok"
4. Approve production (actor: human) (env: production)
   Do: reply "deploy production"
   Check: the reply says "deploy production"
5. Mark done (actor: agent) (env: production)
   Run: `mkdir -p .deploy && touch .deploy/step5`
   Check: `ls .deploy/step5` prints `.deploy/step5`

"""


def three_human_steps(repo: Path) -> None:
    """Runbook of agent step 1, human steps 2, 3 (staging) and 4 (production), agent step 5."""
    p = repo / "docs/prd/orders/operations.md"
    text = p.read_text(encoding="utf-8")
    head = text.split("2. System tests on staging")[0]
    rest = text.split("## Drift", 1)[1]
    p.write_text(head + AHEAD_TAIL + "## Drift" + rest, encoding="utf-8")
    commit(repo, "Three human steps", "docs/prd/orders/operations.md")
