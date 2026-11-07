"""prd_deploy.py recover: a step killed between its start and its result becomes an ordinary failed step."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from deploy_fixture import deploy_repo

from prdlint import deploy

SCRIPT = Path(__file__).parent.parent / "scripts/prd_deploy.py"
PLUGINS_FILE = Path(__file__).parent / "fixtures/installed_plugins.json"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def cli(repo: Path, *args: str):
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    return subprocess.run([sys.executable, "-B", str(SCRIPT), args[0], str(repo / "docs/prd/orders"), *args[1:]],
                          capture_output=True, text=True, encoding="utf-8", env=env, cwd=repo)


def killed_run(repo: Path, step: int = 1, **extra) -> str:
    """A real run, cut back to its header and one `start` record with no result: the process died there."""
    r = cli(repo, "run")
    assert r.returncode == 3, r.stdout + r.stderr
    run_id = r.stdout.splitlines()[0].removeprefix("run: ")
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    header = path.read_text(encoding="utf-8").splitlines()[0]
    start = {"kind": "start", "step": step, "env": "staging", "command": "x", "at": "2026-11-01T10:00:00+00:00", **extra}
    path.write_text(header + "\n" + json.dumps(start) + "\n", encoding="utf-8")
    return run_id


def recover(repo, run_id, step="1", reply="checked staging: nothing was deployed"):
    return cli(repo, "recover", "--run", run_id, "--step", step, "--reply", reply)


def test_recover_then_rollback(repo):
    run_id = killed_run(repo)
    r = recover(repo, run_id)
    assert r.returncode == 4, r.stdout + r.stderr
    assert r.stdout.splitlines()[-1] == f"prd-deploy: failed step=1 run={run_id}"
    recs = deploy.read_log(repo, run_id)
    rec, step = recs[-2], recs[-1]
    assert rec["kind"] == "recover" and rec["step"] == 1 and rec["reply"] == "checked staging: nothing was deployed" and rec["at"]
    assert step["kind"] == "step" and step["step"] == 1 and step["env"] == "staging" and step["result"] == "fail"
    assert step["reason"] == "recovered: no result after start" and step["started"] == "2026-11-01T10:00:00+00:00" and step["ended"]
    assert "level" not in step
    r = cli(repo, "rollback", "--run", run_id, "--step", "1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (repo / ".deploy/staging/rolled-back").exists()


def test_the_start_level_is_kept(repo):
    run_id = killed_run(repo, step=2, level="system")
    assert recover(repo, run_id, "2").returncode == 4
    step = deploy.read_log(repo, run_id)[-1]
    assert step["level"] == "system" and step["result"] == "fail"
    assert deploy.unfinished_starts(deploy.read_log(repo, run_id)[1:]) == []


def test_resume_still_refuses(repo):
    run_id = killed_run(repo)
    r = cli(repo, "resume", "--run", run_id)
    assert r.returncode == 1 and "step 1 started and did not finish" in r.stdout


def test_a_recovered_run_cannot_resume(repo):
    run_id = killed_run(repo)
    assert recover(repo, run_id).returncode == 4
    r = cli(repo, "resume", "--run", run_id)
    assert r.returncode == 1 and "step 1 failed; a failed run ends" in r.stdout


def test_a_step_with_no_unfinished_start(repo):
    run_id = killed_run(repo)
    r = recover(repo, run_id, "2")
    assert r.returncode == 1
    assert f"refused: step 2 has no unfinished start in run {run_id}" in r.stdout.splitlines()
    assert r.stdout.splitlines()[-1] == f"prd-deploy: refused step=2 run={run_id}"
    assert [x["kind"] for x in deploy.read_log(repo, run_id)] == ["header", "start"]


def test_a_step_that_already_has_a_result(repo):
    run_id = killed_run(repo)
    assert recover(repo, run_id).returncode == 4
    r = recover(repo, run_id)
    assert r.returncode == 1
    assert f"refused: step 1 already has a result in run {run_id}" in r.stdout.splitlines()
    assert len([x for x in deploy.read_log(repo, run_id) if x["kind"] == "recover"]) == 1


def test_an_empty_reply_is_a_usage_error(repo):
    run_id = killed_run(repo)
    for reply in ("", "   "):
        r = recover(repo, run_id, reply=reply)
        assert r.returncode == 2 and r.stdout == "" and "reply" in r.stderr
    assert [x["kind"] for x in deploy.read_log(repo, run_id)] == ["header", "start"]


def test_no_log_is_a_usage_error(repo):
    r = recover(repo, "20260101T000000-none")
    assert r.returncode == 2 and r.stdout == "" and "no log for run" in r.stderr


def test_another_prds_run(repo):
    run_id = killed_run(repo)
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(json.dumps({**json.loads(lines[0]), "prd": "docs/prd/other"}) + "\n" + "\n".join(lines[1:]) + "\n", encoding="utf-8")
    r = recover(repo, run_id)
    assert r.returncode == 1
    assert f"refused: run {run_id} is for docs/prd/other, not docs/prd/orders" in r.stdout.splitlines()
    assert [x["kind"] for x in deploy.read_log(repo, run_id)] == ["header", "start"]


def test_a_held_repo_lock(repo):
    run_id = killed_run(repo)
    with deploy.repo_lock(repo):
        r = recover(repo, run_id)
    assert r.returncode == 1 and "refused: another prd_deploy command is running in this repository" in r.stdout
    assert [x["kind"] for x in deploy.read_log(repo, run_id)] == ["header", "start"]


def test_a_held_run_lock(repo):
    run_id = killed_run(repo)
    with deploy.run_lock(repo, run_id):
        r = recover(repo, run_id)
    assert r.returncode == 1 and "another prd_deploy command is working on this run" in r.stdout


def test_recover_never_done(repo):
    run_id = killed_run(repo)
    recover(repo, run_id)
    assert not [x for x in deploy.read_log(repo, run_id) if x.get("result") == "pass"]


def test_finished_envs_after_recover(repo):
    from prdlint import model
    run_id = killed_run(repo)
    prd = model.load(repo / "docs/prd/orders")
    assert "staging" not in deploy.finished_envs(deploy.read_log(repo, run_id)[1:], prd)
    recover(repo, run_id)
    assert "staging" not in deploy.finished_envs(deploy.read_log(repo, run_id)[1:], prd)


def test_corrupt_run_log_is_an_internal_error(repo):
    run_id = killed_run(repo)
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    header = path.read_text(encoding="utf-8").splitlines()[0]
    path.write_text(header + "\n{not json\n", encoding="utf-8")
    r = cli(repo, "confirm", "--run", run_id, "--step", "1", "--reply", "checked")
    assert r.returncode == 2 and r.stderr.startswith(f"prd_deploy: internal error: CorruptLog: cannot read the log of run {run_id}"), r.stderr
    path.write_text("", encoding="utf-8")
    r = cli(repo, "confirm", "--run", run_id, "--step", "1", "--reply", "checked")
    assert r.returncode == 2 and r.stderr.startswith(f"prd_deploy: internal error: CorruptLog: the log of run {run_id} has no header"), r.stderr
    r = cli(repo, "confirm", "--run", "nosuch", "--step", "1", "--reply", "checked")
    assert r.returncode == 2 and r.stderr.strip() == "prd_deploy: no log for run nosuch"
