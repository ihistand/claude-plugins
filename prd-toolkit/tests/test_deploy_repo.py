"""The deploy_repo eval scaffold: four start states of a greet repo with a runbook and a deploy script."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "evals/scaffolds/deploy_repo.py"
PRD = "docs/prd/greet"


def build(tmp_path: Path, state: str) -> tuple[Path, str]:
    dst = tmp_path / state
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(dst), state], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return dst, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


def tool(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "--script", script, *args], cwd=repo, capture_output=True, text=True)


def records(repo: Path, run_id: str) -> list[dict]:
    common = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip())
    log = common / "prd-toolkit/deploys" / f"{run_id}.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture(params=["ready", "staging-done", "failing-check", "at-gate"])
def built(request, tmp_path):
    repo, last = build(tmp_path, request.param)
    return request.param, repo, last


def test_every_state_is_clean_lints_traces_and_plans(built):
    state, repo, _ = built
    assert subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo, capture_output=True, text=True).stdout == ""
    assert (repo / ".prd-toolkit/prd_deploy.py").is_file()
    assert tool(repo, str(ROOT / "scripts/prd_lint.py"), PRD).returncode == 0
    assert tool(repo, str(ROOT / "scripts/prd_trace.py"), PRD).returncode == 0
    plan = tool(repo, ".prd-toolkit/prd_deploy.py", "plan", PRD)
    assert plan.returncode == 0, plan.stdout + plan.stderr
    assert "3 human production" in plan.stdout


def test_ready_has_nothing_deployed_and_no_log(tmp_path):
    repo, last = build(tmp_path, "ready")
    assert last == ""
    assert not (repo / ".deploy").exists()
    assert "## Deployed" not in (repo / PRD / "operations.md").read_text(encoding="utf-8")
    assert not (repo / ".git/prd-toolkit").exists()


def test_staging_done_has_a_passed_staging_run_and_no_deployed_row(tmp_path):
    repo, last = build(tmp_path, "staging-done")
    assert last.startswith("run=")
    recs = records(repo, last.removeprefix("run="))
    steps = [r for r in recs if r["kind"] == "step"]
    assert [r["step"] for r in steps] == [1, 2]
    assert all(r["result"] == "pass" for r in steps)
    assert (repo / ".deploy/staging/bin/greet").is_file()
    assert subprocess.run([str(repo / ".deploy/staging/bin/greet"), "World"], capture_output=True, text=True).stdout == "Hi, World!\n"
    assert "## Deployed" not in (repo / PRD / "operations.md").read_text(encoding="utf-8")


def test_at_gate_stops_at_the_human_step(tmp_path):
    repo, last = build(tmp_path, "at-gate")
    recs = records(repo, last.removeprefix("run="))
    assert recs[-1]["kind"] == "step" and recs[-1]["step"] == 3
    assert recs[-1]["result"] == "human"
    assert not (repo / ".deploy/production").exists()


def test_failing_check_fails_staging(tmp_path):
    repo, last = build(tmp_path, "failing-check")
    assert last == ""
    r = tool(repo, ".prd-toolkit/prd_deploy.py", "run", PRD, "--until", "staging")
    assert r.returncode == 4, r.stdout + r.stderr
    last_step = [x for x in records(repo, r.stdout.strip().splitlines()[-1].rsplit("run=", 1)[1]) if x["kind"] == "step"][-1]
    assert last_step["result"] == "fail" and "Hey, World!" in last_step["check"]["stdout"]
    assert subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo, capture_output=True, text=True).stdout == ""


def test_refuses_a_non_empty_destination(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x/f").write_text("a")
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "x"), "ready"], capture_output=True, text=True)
    assert r.returncode != 0
