"""A repository with two worktrees, both holding docs/prd/orders, and one pending gate of every kind.

- the main worktree (branch `main`, at `tmp/repo`): `error-class:E-003`, the approval gate of a recorded and
  reviewed change, a deploy run stopped at its human step 3, `signoff:T-001.4` (its Sign-offs row removed),
  and `adoption:import` (area `import` extracted, its answers file opened with `prd_confirm.py open`);
- the second worktree (branch `feature-x`, at `tmp/wt`): its own `error-class:E-003`, `signoff:T-001.4` and
  `adoption:import`, from the same commit, with no approval gate.

E-003's evidence line holds `<script>alert(1)</script>`. The deploy log lives in the git common dir, so both
worktrees list the deploy-step gate.
"""
import json
import subprocess
import sys
from pathlib import Path

from conftest import edit
from deploy_fixture import deploy_repo
from prdlint import change, deploy, model
from test_change_record import new_ac_with_test

PRD = "docs/prd/orders"
AREA = "import"
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = "<script>alert(1)</script>"
DRY = "dry run T-002.3, 0 open questions, 1 dismissed by quote"
ADOPTION = "# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n| import | extracted | `src/import/**` |\n"
E002 = '\n### E-002 Fixture entry keeping the ledger without a gap\nDetected: 2026-11-04, test fixture\nClassification: code bug\nResolution: not a defect: fixture filler\n'
E003 = f"""
### E-003 Importer reads the wrong key
Detected: 2026-11-04, test failure in T-001.3
Classification: code bug
Touches: FR-001
Evidence: T-001.3 fails: {SCRIPT}
Diagnosis: wrong key
Resolution: open
"""


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def summaries_file(tmp: Path) -> Path:
    f = tmp / "summaries.json"
    f.write_text(json.dumps({"E-003": "E-003: the importer reads the wrong key."}), encoding="utf-8")
    return f


def open_area(root: Path, summaries: Path) -> None:
    run = subprocess.run([sys.executable, str(SCRIPTS / "prd_confirm.py"), "open", str(root / PRD), "--area", AREA, "--summaries", str(summaries)],
                         capture_output=True, text=True, encoding="utf-8")
    assert run.returncode == 0, run.stderr


def human_stop(repo: Path) -> str:
    prd = model.load(repo / PRD)
    run_id = deploy.new_run_id(repo, None)
    deploy.start_run(prd, repo, run_id, None)
    deploy.append(repo, run_id, {"kind": "step", "step": 3, "env": "production", "actor": "human", "command": None, "exit": None,
                                 "stdout": "", "stderr": "", "started": "t", "ended": "t", "result": "human"})
    return run_id


def verdict(repo: Path) -> None:
    v = {"interface": 1, "kind": "review", "head": "x", "digest": change.digest(repo / PRD), "restate": "Repeat lookups return the same order.",
         "touches": ["AC-002.3"], "impact": {"exit": 0, "lines": ["no consumer"]}, "bump": {"level": "minor", "decided": []},
         "dry_run": {"tids": ["T-002.3"], "open": 0, "dismissed": 1, "record": DRY}, "ready": True, "blockers": []}
    (repo / PRD / ".prd-review.json").write_text(json.dumps(v), encoding="utf-8")


def make_inbox_repo(tmp_path: Path) -> dict:
    """{"repo", "second", "run_id"}: the main worktree, the second worktree and the stopped deploy run."""
    tmp_path = Path(tmp_path)
    repo = deploy_repo(tmp_path)
    for key, value in (("user.name", "Test Author"), ("user.email", "test@example.com"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    prd = repo / PRD
    (prd / "adoption.md").write_text(ADOPTION, encoding="utf-8")
    edit(prd, "prd.md", "Not applicable: new project.", "See adoption.md.")
    (prd / "errors.md").write_text((prd / "errors.md").read_text(encoding="utf-8") + E002 + E003, encoding="utf-8")
    testing = prd / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |\n", ""), encoding="utf-8")
    git(repo, "add", PRD)
    git(repo, "commit", "-q", "-m", "docs(prd): adopt import, E-003")
    second = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "-b", "feature-x", str(second))
    summaries = summaries_file(tmp_path)
    open_area(repo, summaries)
    open_area(second, summaries)
    run_id = human_stop(repo)
    # the approval gate, in the main worktree only: a recorded, reviewed change
    new_ac_with_test(prd)
    edit(prd, "prd.md", "\nstatus: Approved\n", "\nstatus: In review\n")
    (repo / "tests/test_repeat.py").write_text('def test_repeat():\n    """@prd T-002.3"""\n', encoding="utf-8")
    git(repo, "add", "tests/test_repeat.py")
    git(repo, "commit", "-q", "-m", "test: T-002.3")
    change.record(repo, prd, "HEAD", "minor", "Repeat lookups", "2026-11-04")
    verdict(repo)
    return {"repo": repo, "second": second, "run_id": run_id}
