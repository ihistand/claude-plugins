"""prd_deploy.py plan and run."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from deploy_fixture import deploy_repo
from legacy import commit, git

from prdlint import deploy

SCRIPT = Path(__file__).parent.parent / "scripts/prd_deploy.py"
PLUGINS_FILE = Path(__file__).parent / "fixtures/installed_plugins.json"
OPS = "docs/prd/orders/operations.md"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def prd_dir(repo: Path) -> str:
    return str(repo / "docs/prd/orders")


def deploy_cli(repo: Path, *args: str):
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    return subprocess.run([sys.executable, "-B", str(SCRIPT), args[0], prd_dir(repo), *args[1:]],
                          capture_output=True, text=True, encoding="utf-8", env=env, cwd=repo)


def change(repo: Path, rel: str, old: str, new: str) -> None:
    """Edit a tracked file and commit it, so the tree stays clean for pre-flight."""
    p = repo / rel
    text = p.read_text(encoding="utf-8")
    assert text.count(old) == 1, (rel, old, text.count(old))
    p.write_text(text.replace(old, new), encoding="utf-8")
    commit(repo, f"Edit {rel}", rel)


def last(r) -> str:
    return r.stdout.splitlines()[-1]


def records(repo: Path, r) -> list[dict]:
    run_id = r.stdout.splitlines()[0].removeprefix("run: ")
    return deploy.read_log(repo, run_id)


def test_plan_lists_steps(repo):
    r = deploy_cli(repo, "plan")
    lines = r.stdout.splitlines()
    assert r.returncode == 0 and len(lines) == 5
    assert lines[0].startswith("1 agent staging: Deploy to staging — mkdir -p .deploy/staging")
    assert lines[1] == "2 agent staging: System tests on staging — tests system"
    assert lines[2] == "3 human production: Approve production"
    assert lines[4] == "5 agent production: Smoke on production — tests smoke"
    assert not (repo / ".deploy").exists()


def test_plan_until_staging(repo):
    r = deploy_cli(repo, "plan", "--until", "staging")
    assert r.returncode == 0 and [x.split()[0] for x in r.stdout.splitlines()] == ["1", "2"]


def test_plan_until_unknown_env(repo):
    r = deploy_cli(repo, "plan", "--until", "nowhere")
    assert r.returncode == 2 and r.stdout == ""
    assert "nowhere" in r.stderr and "staging" in r.stderr and "production" in r.stderr
    assert "local" not in r.stderr


def test_usage_errors_print_nothing_on_stdout(repo, tmp_path):
    for argv in ([SCRIPT], [SCRIPT, "bogus"], [SCRIPT, "plan"], [SCRIPT, "run", str(tmp_path)], [SCRIPT, "run", prd_dir(repo), "--timeout", "0"]):
        r = subprocess.run([sys.executable, "-B", *map(str, argv)], capture_output=True, text=True, cwd=repo)
        assert r.returncode == 2 and r.stdout == "", argv


def test_run_to_human(repo):
    r = deploy_cli(repo, "run")
    assert r.returncode == 3, r.stdout + r.stderr
    lines = r.stdout.splitlines()
    assert lines[0].startswith("run: ") and lines[0].endswith("-all")
    assert "step 1 agent staging: pass" in lines and "step 2 agent staging: pass" in lines
    assert "step 3 human production: human" in lines
    assert lines[-1].startswith("prd-deploy: human step=3 run=") and lines[-1].endswith("-all")
    assert (repo / ".deploy/staging/greeting").read_text() == "Hi\n"
    assert not (repo / ".deploy/production").exists()
    recs = records(repo, r)
    assert recs[-1]["step"] == 3 and recs[-1]["result"] == "human" and recs[-1]["command"] is None


def test_run_until_staging_done(repo):
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0 and last(r).startswith("prd-deploy: done step=2 run=")
    assert r.stdout.splitlines()[0].endswith("-staging")


def test_failed_check_prints_rollback(repo):
    change(repo, OPS, "prints `Hi`", "prints `Nope`")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4
    assert "step 1 agent staging: fail" in r.stdout
    assert "rollback: `mkdir -p .deploy/staging && touch .deploy/staging/rolled-back`" in r.stdout
    assert last(r).startswith("prd-deploy: failed step=1 run=")
    assert not (repo / ".deploy/staging/rolled-back").exists()
    assert records(repo, r)[-1]["result"] == "fail"


def test_failed_run_without_rollback_prints_none(repo):
    change(repo, "tools/gate.sh", "exit 0", "exit 1")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4 and "step 2 agent staging: fail" in r.stdout and "rollback:" not in r.stdout


@pytest.mark.parametrize("printed,ok", [("Hello, World!\\r\\n", True), ("Hello, World!!\\n", False), ("Say Hello, World! now\\n", False)])
def test_prints_exact_line(repo, printed, ok):
    change(repo, OPS, "Check: `cat .deploy/staging/greeting` prints `Hi`", f"Check: `printf '{printed}'` prints `Hello, World!`")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == (0 if ok else 4), r.stdout


def test_stdin_closed(repo):
    """The runner's own stdin is an open pipe, so a command that inherited it would block."""
    change(repo, OPS, "Check: `cat .deploy/staging/greeting` prints `Hi`", "Check: `read x`")
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    out_file = repo.parent / "stdin-test.out"
    with open(out_file, "w", encoding="utf-8") as sink:
        proc = subprocess.Popen([sys.executable, "-B", str(SCRIPT), "run", prd_dir(repo), "--timeout", "30"], stdin=subprocess.PIPE,
                                stdout=sink, stderr=subprocess.STDOUT, text=True, env=env, cwd=repo)  # the pipe stays open: no communicate()
        started = time.monotonic()
        try:
            code = proc.wait(timeout=20)
        finally:
            proc.kill()
            proc.stdin.close()
    assert code == 4 and time.monotonic() - started < 15, out_file.read_text(encoding="utf-8")


def test_timeout(repo):
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", "Run: `sleep 5; mkdir -p .deploy/staging && echo Hi")
    started = time.monotonic()
    r = deploy_cli(repo, "run", "--timeout", "1")
    assert r.returncode == 4 and time.monotonic() - started < 4.5
    rec = records(repo, r)[-1]
    assert rec["result"] == "fail" and rec["stderr"].endswith("timed out after 1 s")


def test_tests_step_env(repo):
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0
    assert (repo / ".deploy/tests/system.env").read_text().strip() == "staging"


def test_tests_step_one_record_per_level_and_stops_at_first_failure(repo):
    change(repo, OPS, "   Run: tests system\n", "   Run: tests system, e2e\n")
    change(repo, "tools/gate.sh", "exit 0", '[ "$1" = e2e ] && exit 1\nexit 0')
    r = deploy_cli(repo, "run")
    assert r.returncode == 4 and last(r).startswith("prd-deploy: failed step=2 run=")
    recs = [x for x in records(repo, r) if x["kind"] == "step" and x["step"] == 2]
    assert [(x["level"], x["result"], x["exit"]) for x in recs] == [("system", "pass", 0), ("e2e", "fail", 1)]
    assert recs[0]["command"] == "bash tools/gate.sh system"
    change(repo, "tools/gate.sh", '[ "$1" = e2e ] && exit 1', '[ "$1" = system ] && exit 1')
    r = deploy_cli(repo, "run")
    recs = [x for x in records(repo, r) if x["kind"] == "step" and x["step"] == 2]
    assert [x["level"] for x in recs] == ["system"] and recs[0]["result"] == "fail"


def test_refuses_dirty_tree(repo):
    (repo / "tools/gate.sh").write_text("exit 0\n# changed\n", encoding="utf-8")
    r = deploy_cli(repo, "run")
    assert r.returncode == 1 and "refused: the tracked tree has changes" in r.stdout.splitlines()
    assert last(r) == "prd-deploy: refused step=0 run=none"
    assert not (repo / ".git/prd-toolkit").exists()


def test_untracked_files_do_not_dirty_the_tree(repo):
    (repo / "scratch.txt").write_text("x", encoding="utf-8")
    assert deploy_cli(repo, "run", "--until", "staging").returncode == 0


def test_refuses_built_block(repo):
    change(repo, "docs/prd/orders/features/import.md", "Status: verified (since 1.0.0)", "Status: built (since 1.0.0)")
    r = deploy_cli(repo, "run")
    assert r.returncode == 1
    assert "refused: FR-001 is built; its tests have not passed (run /prd-build)" in r.stdout.splitlines()
    assert not (repo / ".deploy").exists()


def test_refuses_lint(repo):
    change(repo, OPS, "   Check: `cat .deploy/production/greeting` prints `Hello`\n", "")
    r = deploy_cli(repo, "run")
    assert r.returncode == 1 and "refused: prd_lint has findings" in r.stdout.splitlines()


def test_refuses_trace(repo):
    git(repo, "rm", "-q", "tests/test_cases.py")
    commit(repo, "Drop tests")
    r = deploy_cli(repo, "run")
    assert r.returncode == 1 and "refused: prd_trace has findings" in r.stdout.splitlines()
    assert last(r) == "prd-deploy: refused step=0 run=none"


def test_log_shape(repo):
    r = deploy_cli(repo, "run")
    recs = records(repo, r)
    header, steps = recs[0], recs[1:]
    assert set(header) == {"kind", "run", "head", "version", "until", "started"}
    assert header["kind"] == "header" and header["run"] == r.stdout.splitlines()[0].removeprefix("run: ")
    assert header["head"] == git(repo, "rev-parse", "HEAD").strip() and header["version"] == "1.0.0" and header["until"] is None
    assert [s["step"] for s in steps] == [1, 2, 3]
    for s in steps:
        assert s["kind"] == "step" and {"env", "actor", "command", "exit", "stdout", "stderr", "started", "ended", "result"} <= set(s)
        assert len(s["stdout"].encode()) <= 4096 and len(s["stderr"].encode()) <= 4096
    assert steps[0]["env"] == "staging" and steps[0]["actor"] == "agent" and steps[0]["exit"] == 0 and steps[0]["result"] == "pass"
    assert steps[0]["check"]["stdout"] == "Hi\n"
    assert steps[2]["actor"] == "human" and steps[2]["result"] == "human"
    log = deploy.log_dir(repo) / f"{header['run']}.jsonl"
    assert log.is_file() and all(json.loads(line) for line in log.read_text(encoding="utf-8").splitlines())


def test_big_binary_output(repo):
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", "Run: `head -c 2000000 /dev/urandom; mkdir -p .deploy/staging && echo Hi")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    out = records(repo, r)[1]["stdout"]
    assert 1000 < len(out) <= 4096


def test_run_id_collision(repo, monkeypatch, capsys):
    from prd_deploy import main

    monkeypatch.setattr(deploy, "_now", lambda: datetime(2026, 11, 2, 10, 15, 0, tzinfo=timezone.utc))
    ids = []
    for _ in range(3):
        assert main(["run", prd_dir(repo), "--until", "staging"]) == 0
        ids.append(capsys.readouterr().out.splitlines()[0].removeprefix("run: "))
    assert ids == ["20261102T101500Z-staging", "20261102T101500Z-staging-2", "20261102T101500Z-staging-3"]


def test_log_shared_across_worktrees(repo, tmp_path):
    other = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "side", str(other))
    assert deploy.log_dir(other).resolve() == deploy.log_dir(repo).resolve()
    assert deploy.log_dir(repo).is_absolute()


def test_plan_steps_unit(repo):
    from prdlint import model

    prd = model.load(Path(prd_dir(repo)))
    assert [s.number for s in deploy.plan_steps(prd, "production")] == [1, 2, 3, 4, 5]
    assert deploy.EXIT == {"done": 0, "refused": 1, "usage": 2, "human": 3, "failed": 4}
    with pytest.raises(ValueError, match="staging, production"):
        deploy.plan_steps(prd, "local")


def test_tests_step_without_levels_fails(repo):
    change(repo, OPS, "   Run: tests system\n", "   Run: tests ,\n")
    assert deploy_cli(repo, "run").returncode == 1  # lint refuses it first
    from prdlint import model
    prd = model.load(Path(prd_dir(repo)))
    assert prd.operations.steps[1].tests == []
    run_id = "20261102T101500Z-test"
    deploy.start_run(prd, repo, run_id, None)
    state, n = deploy.run_steps(prd, repo, run_id, prd.operations.steps[1:2], 2, 5)
    assert (state, n) == ("failed", 2)
    rec = deploy.read_log(repo, run_id)[-1]
    assert rec["step"] == 2 and rec["result"] == "fail" and rec["stderr"] == "tests step names no levels"


def test_lint_flags_a_tests_step_without_levels(repo):
    from conftest import lint
    change(repo, OPS, "   Run: tests system\n", "   Run: tests ,\n")
    assert ("runbook-steps", "step 2: a tests step names no levels") in {(f.rule, f.message) for f in lint(repo / "docs/prd/orders")}


def test_unexpected_error_mid_run_exits_4_with_final_line(repo, monkeypatch, capsys):
    from prd_deploy import main

    real = subprocess.Popen

    def boom(cmd, *a, **k):
        if "tools/gate.sh" in cmd[-1]:
            raise OSError("no fork")
        return real(cmd, *a, **k)

    monkeypatch.setattr(deploy.subprocess, "Popen", boom)
    assert main(["run", prd_dir(repo)]) == 4
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1].startswith("prd-deploy: failed step=2 run=")
    rec = deploy.read_log(repo, lines[0].removeprefix("run: "))[-1]
    assert rec["step"] == 2 and rec["result"] == "fail" and "no fork" in rec["stderr"]


def test_error_before_the_header_exits_2_silently(repo, monkeypatch, capsys):
    from prd_deploy import main

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(deploy, "start_run", boom)
    assert main(["run", prd_dir(repo)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "disk full" in captured.err


def test_run_id_is_reserved_by_creating_the_log(repo, monkeypatch):
    monkeypatch.setattr(deploy, "_now", lambda: datetime(2026, 11, 2, 10, 15, 0, tzinfo=timezone.utc))
    a, b = deploy.new_run_id(repo, "staging"), deploy.new_run_id(repo, "staging")
    assert (a, b) == ("20261102T101500Z-staging", "20261102T101500Z-staging-2")
    assert (deploy.log_dir(repo) / f"{a}.jsonl").is_file()


def test_environment_variables(repo, monkeypatch):
    monkeypatch.setenv("TEST_ENV", "inherited")
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", "Run: `mkdir -p .deploy/staging && echo \"$PRD_ENV|${TEST_ENV-unset}\" > .deploy/agent.env && echo Hi")
    change(repo, "tools/gate.sh", 'echo "$TEST_ENV"', 'echo "$TEST_ENV|$PRD_ENV"')
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (repo / ".deploy/agent.env").read_text().strip() == "staging|unset"
    assert (repo / ".deploy/tests/system.env").read_text().strip() == "staging|staging"
