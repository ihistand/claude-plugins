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
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", "Run: `sleep 30; mkdir -p .deploy/staging && echo Hi")
    started = time.monotonic()
    r = deploy_cli(repo, "run", "--timeout", "1")
    assert r.returncode == 4 and time.monotonic() - started < 15  # well under the 30 s sleep: the timeout ended it
    rec = records(repo, r)[-1]
    assert rec["result"] == "fail" and rec["stderr"].endswith("timed out after 1 s (--timeout)")


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
    assert not list((repo / ".git/prd-toolkit").glob("**/*.jsonl"))  # no run log; the repo lock file may exist


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
    header, steps = recs[0], [x for x in recs[1:] if x["kind"] == "step"]
    assert set(header) == {"kind", "run", "head", "prd", "runbook", "version", "until", "started"}
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
    out = [x for x in records(repo, r) if x["kind"] == "step"][0]["stdout"]
    assert 1000 < len(out) <= 4096


def test_log_records_survive_line_separator_characters(repo):
    """json.dumps(ensure_ascii=False) writes U+0085, U+2028 and U+2029 raw; str.splitlines() splits a record on them."""
    run_id = deploy.new_run_id(repo, None)
    tail = "a\x85b\u2028c\u2029d"
    deploy.append(repo, run_id, {"kind": "header", "run": run_id})
    deploy.append(repo, run_id, {"kind": "step", "step": 1, "stdout": tail})
    recs = deploy.read_log(repo, run_id)
    assert len(recs) == 2 and recs[1]["stdout"] == tail


def uncite(repo: Path, tid: str) -> None:
    change(repo, "tests/test_cases.py", f"@prd {tid}", "no citation")


def test_production_run_refused_when_a_deploy_gate_test_is_uncited(repo):
    uncite(repo, "T-004.1")
    r = deploy_cli(repo, "run")
    assert r.returncode == 1
    assert "refused: NFR-004: T-004.1 (deploy gate) has no citing test; it cannot go live" in r.stdout.splitlines(), r.stdout
    assert last(r) == "prd-deploy: refused step=0 run=none"
    assert not (repo / ".deploy").exists()


def test_staging_run_ignores_an_uncited_deploy_gate_test(repo):
    uncite(repo, "T-004.1")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (repo / ".deploy/staging/version").is_file()


def test_production_run_with_all_citations_still_runs(repo):
    assert deploy_cli(repo, "run").returncode == 3  # stops at the human approval, not at pre-flight


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


# ---- confirm, resume and rollback ----

def run_id_of(r) -> str:
    return r.stdout.splitlines()[0].removeprefix("run: ")


def stopped_run(repo) -> str:
    """A run stopped at human step 3; returns its id."""
    r = deploy_cli(repo, "run")
    assert r.returncode == 3, r.stdout + r.stderr
    return run_id_of(r)


def confirm(repo, run_id, step="3", reply="deploy production"):
    return deploy_cli(repo, "confirm", "--run", run_id, "--step", step, "--reply", reply)


def resume(repo, run_id):
    return deploy_cli(repo, "resume", "--run", run_id)


def rollback(repo, run_id, step):
    return deploy_cli(repo, "rollback", "--run", run_id, "--step", str(step))


def edit_header(repo, run_id, **fields):
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = {**json.loads(lines[0]), **fields}
    path.write_text("\n".join([json.dumps(header), *lines[1:]]) + "\n", encoding="utf-8")


def test_confirm_then_resume_to_done(repo):
    run_id = stopped_run(repo)
    reply = 'deploy "production" — now\n'
    c = confirm(repo, run_id, reply=reply)
    assert c.returncode == 0 and c.stdout == f"confirmed: step 3 run={run_id}\n", c.stdout + c.stderr
    assert not (repo / ".deploy/production").exists()
    r = resume(repo, run_id)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = r.stdout.splitlines()
    assert lines[0] == f"resume: {run_id}"
    assert lines[1:-1] == ["step 4 agent production: pass", "step 5 agent production: pass"]
    assert lines[-1] == f"prd-deploy: done step=5 run={run_id}"
    assert (repo / ".deploy/production/greeting").read_text() == "Hello\n"
    recs = deploy.read_log(repo, run_id)
    confirms = [x for x in recs if x["kind"] == "confirm"]
    assert len(confirms) == 1 and confirms[0]["reply"] == reply and confirms[0]["step"] == 3 and "at" in confirms[0]
    assert [x["step"] for x in recs if x["kind"] == "step"] == [1, 2, 3, 4, 5]  # earlier steps were not run again
    kinds = [x["kind"] for x in recs]
    assert kinds.index("confirm") > max(i for i, x in enumerate(recs) if x.get("step") == 3 and x["kind"] == "step")
    assert kinds.index("resume") > kinds.index("confirm") and recs[kinds.index("resume")]["step"] == 3
    assert [x["step"] for x in recs[kinds.index("resume") + 1:] if x["kind"] == "start"] == [4, 4, 5]  # step 4's Run and Check, then smoke


def test_resume_without_confirm(repo):
    run_id = stopped_run(repo)
    r = resume(repo, run_id)
    assert r.returncode == 1
    assert "refused: step 3 has no confirm record" in r.stdout.splitlines()
    assert r.stdout.splitlines()[-1] == f"prd-deploy: refused step=3 run={run_id}"
    assert not (repo / ".deploy/production").exists()


def test_confirm_wrong_step(repo):
    run_id = stopped_run(repo)
    r = confirm(repo, run_id, step="2")
    assert r.returncode == 2 and r.stdout == "" and "step 2 is not the human step this run stopped at" in r.stderr
    assert confirm(repo, run_id, step="9").returncode == 2
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "confirm"]


@pytest.mark.parametrize("reply", ["", "   ", "\n\t"])
def test_confirm_refuses_an_empty_reply(repo, reply):
    run_id = stopped_run(repo)
    r = confirm(repo, run_id, reply=reply)
    assert r.returncode == 2 and r.stdout == "" and r.stderr
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "confirm"]


def test_confirm_unknown_run(repo):
    for bad in ("20990101T000000Z-all", "a/b", ""):
        r = confirm(repo, bad)
        assert r.returncode == 2 and r.stdout == "", bad


def test_confirm_refuses_a_run_id_that_names_a_path(repo):
    """`../../x` from the deploys folder is `.git/x.jsonl`: a well-formed log that must not be touched."""
    stopped_run(repo)
    target = repo / ".git/x.jsonl"
    target.write_text(json.dumps({"kind": "header", "run": "x", "head": "0", "version": "1.0.0", "until": None, "started": "t"}) + "\n"
                      + json.dumps({"kind": "step", "step": 3, "result": "human"}) + "\n", encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    r = confirm(repo, "../../x")
    assert r.returncode == 2 and r.stdout == "" and target.read_text(encoding="utf-8") == before


def test_confirm_twice(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    r = confirm(repo, run_id, reply="again")
    assert r.returncode == 2 and r.stdout == ""
    assert [x["reply"] for x in deploy.read_log(repo, run_id) if x["kind"] == "confirm"] == ["deploy production"]


def test_confirm_a_failed_run(repo):
    change(repo, OPS, "prints `Hi`", "prints `Nope`")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4
    assert confirm(repo, run_id_of(r), step="1").returncode == 2


def test_resume_after_head_moved(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    change(repo, "tools/gate.sh", "exit 0", "exit 0\n# later")
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: HEAD moved since the run started" in r.stdout.splitlines()
    assert r.stdout.splitlines()[-1].startswith("prd-deploy: refused step=3 run=")
    assert not (repo / ".deploy/production").exists()


def test_resume_head_check_stands_alone(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    edit_header(repo, run_id, head="0" * 40)
    r = resume(repo, run_id)
    assert r.returncode == 1 and r.stdout.splitlines()[:-1] == ["refused: HEAD moved since the run started"]
    assert not (repo / ".deploy/production").exists()


def test_resume_after_version_changed(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    edit_header(repo, run_id, version="0.9.0")
    r = resume(repo, run_id)
    assert r.returncode == 1 and r.stdout.splitlines()[:-1] == ["refused: the PRD version changed since the run started"]
    assert not (repo / ".deploy/production").exists()


def test_resume_after_a_committed_version_bump(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    change(repo, "docs/prd/orders/prd.md", "version: 1.0.0", "version: 1.0.1")
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: the PRD version changed since the run started" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()


def test_resume_refuses_a_dirty_tree(repo):
    """Resume reads the runbook as it is now, so an uncommitted runbook edit must not run."""
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace("echo Hello > .deploy/production/greeting", "touch .deploy/evil"), encoding="utf-8")
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: the tracked tree has changes" in r.stdout.splitlines()
    assert not (repo / ".deploy/evil").exists() and not (repo / ".deploy/production").exists()


def test_resume_after_failure(repo):
    change(repo, OPS, "prints `Hi`", "prints `Nope`")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4
    r = resume(repo, run_id_of(r))
    assert r.returncode == 1 and "refused: step 1 failed; a failed run ends (start a new run)" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists() and not (repo / ".deploy/tests").exists()


def test_resume_a_done_run(repo):
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0
    r = resume(repo, run_id_of(r))
    assert r.returncode == 1 and "refused: the run is done" in r.stdout.splitlines()


def test_resume_a_second_time_after_it_finished(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0 and resume(repo, run_id).returncode == 0
    n = len(deploy.read_log(repo, run_id))
    r = resume(repo, run_id)
    assert r.returncode == 1 and len(deploy.read_log(repo, run_id)) == n


def test_resume_older_run(repo):
    first = stopped_run(repo)
    second = stopped_run(repo)
    assert first != second
    assert confirm(repo, first).returncode == 0
    r = resume(repo, first)
    assert r.returncode == 0 and r.stdout.splitlines()[-1] == f"prd-deploy: done step=5 run={first}"
    assert not [x for x in deploy.read_log(repo, second) if x["kind"] == "confirm"]
    assert resume(repo, second).returncode == 1


def test_resume_stops_again_at_a_later_failure(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    (repo / ".deploy/production").mkdir(parents=True)
    (repo / ".deploy/production").chmod(0o500)
    try:
        r = resume(repo, run_id)
    finally:
        (repo / ".deploy/production").chmod(0o700)
    assert r.returncode == 4 and r.stdout.splitlines()[-1] == f"prd-deploy: failed step=4 run={run_id}"
    assert "rollback: `mkdir -p .deploy/production && touch .deploy/production/rolled-back`" in r.stdout
    assert deploy.read_log(repo, run_id)[-1]["step"] == 4


def failed_run(repo, step=1) -> str:
    """Fail step 1 (its Check) or step 2 (a failing harness level)."""
    if step == 1:
        change(repo, OPS, "prints `Hi`", "prints `Nope`")
    else:
        change(repo, "tools/gate.sh", "exit 0", "exit 1")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4, r.stdout + r.stderr
    return run_id_of(r)


def test_rollback_runs_only_that_step(repo):
    run_id = failed_run(repo)
    r = rollback(repo, run_id, 1)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.splitlines() == ["rollback step 1 staging: pass", f"prd-deploy: rolled-back step=1 run={run_id}"]
    assert (repo / ".deploy/staging/rolled-back").exists()
    assert not (repo / ".deploy/production").exists() and not (repo / ".deploy/tests").exists()
    rec = deploy.read_log(repo, run_id)[-1]
    assert rec["kind"] == "rollback" and rec["step"] == 1 and rec["exit"] == 0
    assert rec["command"] == "mkdir -p .deploy/staging && touch .deploy/staging/rolled-back"
    assert {"stdout", "stderr", "started", "ended"} <= set(rec)
    r = rollback(repo, run_id, 1)  # once only
    assert r.returncode == 2 and r.stdout == "" and "already" in r.stderr
    assert len([x for x in deploy.read_log(repo, run_id) if x["kind"] == "rollback"]) == 1


def test_rollback_needs_failed_step(repo):
    run_id = failed_run(repo, step=2)  # step 1 passed, step 2 failed
    r = rollback(repo, run_id, 1)
    assert r.returncode == 2 and r.stdout == "" and "step 1" in r.stderr
    assert not (repo / ".deploy/staging/rolled-back").exists()
    r = rollback(repo, run_id, 2)  # step 2 is the failed step but has no Rollback
    assert r.returncode == 2 and r.stdout == "" and "Rollback" in r.stderr
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "rollback"]


def test_rollback_a_run_stopped_at_a_human_step(repo):
    run_id = stopped_run(repo)
    r = rollback(repo, run_id, 1)
    assert r.returncode == 2 and r.stdout == ""
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_rollback_after_head_moved(repo):
    run_id = failed_run(repo)
    change(repo, "tools/gate.sh", "exit 0", "exit 0\n# later")
    r = rollback(repo, run_id, 1)
    assert r.returncode == 1 and "refused: HEAD moved since the run started" in r.stdout.splitlines()
    assert r.stdout.splitlines()[-1] == f"prd-deploy: refused step=1 run={run_id}"
    assert not (repo / ".deploy/staging/rolled-back").exists()
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "rollback"]


def test_rollback_after_version_changed(repo):
    run_id = failed_run(repo)
    edit_header(repo, run_id, version="0.9.0")
    r = rollback(repo, run_id, 1)
    assert r.returncode == 1 and r.stdout.splitlines()[0] == "refused: the PRD version changed since the run started"
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_rollback_failure_exits_4_and_is_logged(repo):
    change(repo, OPS, "touch .deploy/staging/rolled-back`", "echo oops >&2; exit 7`")
    run_id = failed_run(repo)
    r = rollback(repo, run_id, 1)
    assert r.returncode == 4
    assert r.stdout.splitlines() == ["rollback step 1 staging: fail", f"prd-deploy: rollback-failed step=1 run={run_id}"]
    rec = deploy.read_log(repo, run_id)[-1]
    assert rec["kind"] == "rollback" and rec["exit"] == 7 and "oops" in rec["stderr"]
    assert rollback(repo, run_id, 1).returncode == 2


def test_rollback_uses_the_step_environment(repo, monkeypatch):
    monkeypatch.setenv("TEST_ENV", "inherited")
    change(repo, OPS, "touch .deploy/staging/rolled-back`", 'echo "$PRD_ENV|${TEST_ENV-unset}" > .deploy/rb.env`')
    run_id = failed_run(repo)
    assert rollback(repo, run_id, 1).returncode == 0
    assert (repo / ".deploy/rb.env").read_text().strip() == "staging|unset"


def test_rollback_stdin_is_closed(repo):
    """Open-pipe approach of test_stdin_closed: an inherited stdin would block `read`."""
    change(repo, OPS, "touch .deploy/staging/rolled-back`", "read x`")
    run_id = failed_run(repo)
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    out_file = repo.parent / "rb-stdin.out"
    with open(out_file, "w", encoding="utf-8") as sink:
        proc = subprocess.Popen([sys.executable, "-B", str(SCRIPT), "rollback", prd_dir(repo), "--run", run_id, "--step", "1", "--timeout", "30"],
                                stdin=subprocess.PIPE, stdout=sink, stderr=subprocess.STDOUT, text=True, env=env, cwd=repo)
        started = time.monotonic()
        try:
            code = proc.wait(timeout=20)
        finally:
            proc.kill()
            proc.stdin.close()
    assert code == 4 and time.monotonic() - started < 15, out_file.read_text(encoding="utf-8")


def test_rollback_times_out(repo):
    change(repo, OPS, "touch .deploy/staging/rolled-back`", "sleep 30`")
    run_id = failed_run(repo)
    started = time.monotonic()
    r = deploy_cli(repo, "rollback", "--run", run_id, "--step", "1", "--timeout", "1")
    assert r.returncode == 4 and time.monotonic() - started < 15  # well under the 30 s sleep: the timeout ended it
    assert deploy.read_log(repo, run_id)[-1]["stderr"].endswith("timed out after 1 s (--timeout)")


def test_rollback_usage_errors_print_nothing_on_stdout(repo):
    run_id = failed_run(repo)
    for argv in (["rollback", "--run", run_id], ["rollback", "--step", "1"], ["rollback", "--run", "nope", "--step", "1"],
                 ["rollback", "--run", run_id, "--step", "x"], ["resume"], ["confirm", "--run", run_id, "--step", "1"]):
        r = deploy_cli(repo, *argv)
        assert r.returncode == 2 and r.stdout == "", argv


# ---- a confirm is used once; a started command is never run again ----

def hand_append(repo, run_id, *records_):
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for rec in records_:
            f.write(json.dumps(rec) + "\n")


def test_resume_refuses_a_used_confirm(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    hand_append(repo, run_id, {"kind": "resume", "step": 3, "at": "t"})
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: step 3's confirm was already used" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()


def test_resume_refuses_an_unfinished_start(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    hand_append(repo, run_id, {"kind": "start", "step": 4, "command": "x", "at": "t"})
    r = resume(repo, run_id)
    assert r.returncode == 1
    assert "refused: step 4 started and did not finish; check the environment, then start a new run" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()


def test_a_finished_start_does_not_block_resume(repo):
    """The unfinished-start check must be able to pass: starts that have a step record after them are finished."""
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0 and resume(repo, run_id).returncode == 0
    assert any(x["kind"] == "start" for x in deploy.read_log(repo, run_id))


def test_a_killed_resume_cannot_be_resumed_again(repo, monkeypatch, capsys):
    """The completion record of step 4 cannot be written: the log ends with confirm, resume and a start."""
    from prd_deploy import main

    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    real = deploy.append

    def flaky(repo_root, rid, record):
        if record.get("kind") == "step" and record.get("step") == 4:
            raise OSError("disk full")
        return real(repo_root, rid, record)

    monkeypatch.setattr(deploy, "append", flaky)
    assert main(["resume", prd_dir(repo), "--run", run_id]) == 4
    monkeypatch.setattr(deploy, "append", real)
    capsys.readouterr()
    shutil_rm = repo / ".deploy/production"
    import shutil
    shutil.rmtree(shutil_rm)
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: step 3's confirm was already used" in r.stdout.splitlines()
    assert "refused: step 4 started and did not finish; check the environment, then start a new run" in r.stdout.splitlines()
    assert not shutil_rm.exists()


def test_rollback_refuses_a_started_rollback(repo):
    run_id = failed_run(repo)
    hand_append(repo, run_id, {"kind": "start", "step": 1, "rollback": True, "command": "x", "at": "t"})
    r = rollback(repo, run_id, 1)
    assert r.returncode == 2 and r.stdout == "" and "step 1's rollback was already started" in r.stderr
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_rollback_writes_its_start_first(repo):
    run_id = failed_run(repo)
    assert rollback(repo, run_id, 1).returncode == 0
    recs = deploy.read_log(repo, run_id)
    assert [x["kind"] for x in recs[-2:]] == ["start", "rollback"] and recs[-2]["rollback"] is True and recs[-2]["step"] == 1


def test_start_record_failure_runs_no_command(repo, monkeypatch, capsys):
    from prd_deploy import main

    real = deploy.append

    def flaky(repo_root, rid, record):
        if record.get("kind") == "start":
            raise OSError("disk full")
        return real(repo_root, rid, record)

    monkeypatch.setattr(deploy, "append", flaky)
    assert main(["run", prd_dir(repo)]) == 4
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1].startswith("prd-deploy: failed step=1 run=")
    assert not (repo / ".deploy").exists()


def test_start_record_failure_runs_no_rollback(repo, monkeypatch, capsys):
    from prd_deploy import main

    run_id = failed_run(repo)
    real = deploy.append

    def flaky(repo_root, rid, record):
        if record.get("kind") == "start":
            raise OSError("disk full")
        return real(repo_root, rid, record)

    monkeypatch.setattr(deploy, "append", flaky)
    assert main(["rollback", prd_dir(repo), "--run", run_id, "--step", "1"]) == 2
    assert capsys.readouterr().out == "" and not (repo / ".deploy/staging/rolled-back").exists()


def test_resume_record_failure_runs_no_command(repo, monkeypatch, capsys):
    from prd_deploy import main

    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    real = deploy.append

    def flaky(repo_root, rid, record):
        if record.get("kind") == "resume":
            raise OSError("disk full")
        return real(repo_root, rid, record)

    monkeypatch.setattr(deploy, "append", flaky)
    assert main(["resume", prd_dir(repo), "--run", run_id]) == 2
    assert capsys.readouterr().out == "" and not (repo / ".deploy/production").exists()


# ---- round 2: two human steps, matched completions, a lock around the check-and-record window ----

TWO_HUMAN_TAIL = """5. Approve smoke (actor: human) (env: production)
   Do: reply "run smoke"
   Check: the reply says "run smoke"
6. Mark done (actor: agent) (env: production)
   Run: `mkdir -p .deploy && touch .deploy/step6`
   Check: `ls .deploy/step6` prints `.deploy/step6`
"""


def two_human_steps(repo):
    p = repo / OPS
    text = p.read_text(encoding="utf-8")
    head, tail = text.split("5. Smoke on production")
    rest = tail.split("## Drift", 1)[1]
    p.write_text(head + TWO_HUMAN_TAIL + "\n## Drift" + rest, encoding="utf-8")
    commit(repo, "Two human steps", OPS)


def test_second_human_step_can_be_resumed(repo):
    two_human_steps(repo)
    from conftest import lint
    assert [(f.rule, f.message) for f in lint(repo / "docs/prd/orders")] == []
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 3 and r.stdout.splitlines()[-1] == f"prd-deploy: human step=5 run={run_id}", r.stdout + r.stderr
    assert not (repo / ".deploy/step6").exists()
    r = resume(repo, run_id)  # step 5 has no confirm yet
    assert r.returncode == 1 and "refused: step 5 has no confirm record" in r.stdout.splitlines()
    assert confirm(repo, run_id, step="5", reply="run smoke").returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 0 and r.stdout.splitlines()[-1] == f"prd-deploy: done step=6 run={run_id}", r.stdout + r.stderr
    assert (repo / ".deploy/step6").exists()
    assert resume(repo, run_id).returncode == 1


def test_a_start_is_finished_only_by_its_own_step_and_level(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    rec = {"kind": "step", "env": "production", "actor": "agent", "command": "x", "exit": 0, "stdout": "", "stderr": "", "started": "t", "ended": "t", "result": "pass"}
    hand_append(repo, run_id, {"kind": "start", "step": 4, "command": "x", "at": "t"}, {**rec, "step": 5})
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: step 4 started and did not finish; check the environment, then start a new run" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()


def test_a_level_start_is_not_finished_by_another_level(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    rec = {"kind": "step", "step": 2, "level": "system", "env": "staging", "actor": "agent", "command": "x", "exit": 0, "stdout": "", "stderr": "", "started": "t", "ended": "t", "result": "pass"}
    hand_append(repo, run_id, {"kind": "start", "step": 2, "level": "e2e", "command": "x", "at": "t"}, rec)
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: step 2 started and did not finish; check the environment, then start a new run" in r.stdout.splitlines()


@pytest.fixture
def locked(repo):
    """Hold the exclusive lock of a run's log, as a concurrent prd_deploy would while it checks and records."""
    import fcntl

    handles = []

    def hold(run_id):
        f = open(deploy.log_dir(repo) / f"{run_id}.jsonl", "a", encoding="utf-8")
        fcntl.flock(f, fcntl.LOCK_EX)
        handles.append(f)

    yield hold
    for f in handles:
        f.close()


def test_resume_refuses_while_the_run_is_locked(repo, locked):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    locked(run_id)
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: another prd_deploy command is working on this run" in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "resume"]


def test_confirm_refuses_while_the_run_is_locked(repo, locked):
    run_id = stopped_run(repo)
    locked(run_id)
    r = confirm(repo, run_id)
    assert r.returncode == 2 and r.stdout == "" and "another prd_deploy command" in r.stderr
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "confirm"]


def test_rollback_refuses_while_the_run_is_locked(repo, locked):
    run_id = failed_run(repo)
    locked(run_id)
    r = rollback(repo, run_id, 1)
    assert r.returncode == 1 and "refused: another prd_deploy command is working on this run" in r.stdout.splitlines()
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_the_lock_is_released_before_a_command_runs(repo):
    probe = ("python3 -c \"import fcntl,glob; [fcntl.flock(open(p, 'a'), fcntl.LOCK_EX | fcntl.LOCK_NB) for p in glob.glob('.git/prd-toolkit/deploys/*.jsonl')]\""
             " && touch .deploy/lock-free")
    change(repo, OPS, "Run: `mkdir -p .deploy/production && echo Hello", f"Run: `{probe}; mkdir -p .deploy/production && echo Hello")
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    assert resume(repo, run_id).returncode == 0
    assert (repo / ".deploy/lock-free").exists()


# ---- final review: the log names its PRD and runbook (finding 1) ----

OTHER = "docs/prd/other"


def other_prd(repo, tracked: bool) -> None:
    """A second PRD whose production deploy leaves a marker; tracked ones are committed before any run."""
    import shutil
    shutil.copytree(repo / "docs/prd/orders", repo / OTHER)
    p = repo / OTHER / "operations.md"
    p.write_text(p.read_text(encoding="utf-8").replace("echo Hello > .deploy/production/greeting",
                                                       "echo OTHER > .deploy/other-marker; echo Hello > .deploy/production/greeting"), encoding="utf-8")
    if tracked:
        commit(repo, "A second PRD", OTHER)


def other_cli(repo, *args):
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    return subprocess.run([sys.executable, "-B", str(SCRIPT), args[0], str(repo / OTHER), *args[1:]],
                          capture_output=True, text=True, encoding="utf-8", env=env, cwd=repo)


def test_header_names_the_prd_and_the_runbook_hash(repo):
    import hashlib
    r = deploy_cli(repo, "run", "--until", "staging")
    header = records(repo, r)[0]
    assert header["prd"] == "docs/prd/orders"
    prd = repo / "docs/prd/orders"
    assert header["runbook"] == deploy.runbook_hash(prd) and len(header["runbook"]) == 64
    assert header["runbook"] != hashlib.sha256(b"").hexdigest()


@pytest.mark.parametrize("tracked", [True, False])
def test_resume_refuses_another_prds_run(repo, tracked):
    if tracked:
        other_prd(repo, True)
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    if not tracked:
        other_prd(repo, False)
    r = other_cli(repo, "resume", "--run", run_id)
    assert r.returncode == 1, r.stdout + r.stderr
    assert f"refused: run {run_id} is for docs/prd/orders, not {OTHER}" in r.stdout.splitlines()
    assert not (repo / ".deploy/other-marker").exists() and not (repo / ".deploy/production").exists()
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "resume"]
    assert resume(repo, run_id).returncode == 0  # the confirm was not used up


@pytest.mark.parametrize("tracked", [True, False])
def test_confirm_refuses_another_prds_run(repo, tracked):
    if tracked:
        other_prd(repo, True)
    run_id = stopped_run(repo)
    if not tracked:
        other_prd(repo, False)
    r = other_cli(repo, "confirm", "--run", run_id, "--step", "3", "--reply", "deploy production")
    assert r.returncode == 2 and r.stdout == "" and f"run {run_id} is for docs/prd/orders, not {OTHER}" in r.stderr
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "confirm"]


@pytest.mark.parametrize("tracked", [True, False])
def test_rollback_refuses_another_prds_run(repo, tracked):
    if tracked:
        other_prd(repo, True)
    run_id = failed_run(repo)
    if not tracked:
        other_prd(repo, False)
    r = other_cli(repo, "rollback", "--run", run_id, "--step", "1")
    assert r.returncode == 1 and f"refused: run {run_id} is for docs/prd/orders, not {OTHER}" in r.stdout.splitlines(), r.stdout + r.stderr
    assert not (repo / ".deploy/staging/rolled-back").exists()
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] in ("rollback", "start") and x.get("rollback")]


@pytest.mark.parametrize("tracked", [True, False])
def test_check_refuses_another_prds_run(repo, tracked):
    if tracked:
        other_prd(repo, True)
    r = deploy_cli(repo, "run", "--until", "staging")
    run_id = run_id_of(r)
    if not tracked:
        other_prd(repo, False)
    base = deploy.read_log(repo, run_id)[0]["head"]
    git(repo, "commit", "-q", "--allow-empty", "-m", "Close")
    r = other_cli(repo, "check", "--run", run_id, "--diff", f"{base}..HEAD")
    assert r.returncode == 1 and r.stdout.splitlines() == [f"refused: run {run_id} is for docs/prd/orders, not {OTHER}"], r.stdout + r.stderr


def strip_header(repo, run_id, *keys):
    path = deploy.log_dir(repo) / f"{run_id}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    header = {k: v for k, v in json.loads(lines[0]).items() if k not in keys}
    path.write_text("\n".join([json.dumps(header), *lines[1:]]) + "\n", encoding="utf-8")


def test_a_header_without_a_prd_is_refused(repo):
    """A log written before the header named its PRD cannot be resumed, rolled back or checked."""
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    strip_header(repo, run_id, "prd", "runbook")
    r = resume(repo, run_id)
    assert r.returncode == 1 and f"refused: run {run_id}'s log names no PRD folder; start a new run" in r.stdout.splitlines(), r.stdout
    assert not (repo / ".deploy/production").exists()
    failed = failed_run(repo)
    strip_header(repo, failed, "prd", "runbook")
    r = rollback(repo, failed, 1)
    assert r.returncode == 1 and f"refused: run {failed}'s log names no PRD folder; start a new run" in r.stdout.splitlines()
    assert not (repo / ".deploy/staging/rolled-back").exists()
    base = deploy.read_log(repo, failed)[0]["head"]
    r = deploy_cli(repo, "check", "--run", failed, "--diff", f"{base}..HEAD")
    assert r.returncode == 1 and r.stdout.splitlines() == [f"refused: run {failed}'s log names no PRD folder; start a new run"]


def test_resume_refuses_a_changed_runbook(repo):
    """A runbook edit git does not see (assume-unchanged) leaves HEAD and the tree as they were."""
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    git(repo, "update-index", "--assume-unchanged", OPS)
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace("echo Hello > .deploy/production/greeting", "touch .deploy/evil; echo Hello > .deploy/production/greeting"), encoding="utf-8")
    assert git(repo, "status", "--porcelain", "--untracked-files=no").strip() == ""
    r = resume(repo, run_id)
    assert r.returncode == 1 and "refused: the runbook changed since the run started" in r.stdout.splitlines(), r.stdout + r.stderr
    assert not (repo / ".deploy/evil").exists()


def test_resume_refuses_a_changed_testing_md(repo):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    edit_header(repo, run_id, runbook="0" * 64)
    r = resume(repo, run_id)
    assert r.returncode == 1 and r.stdout.splitlines()[:-1] == ["refused: the runbook changed since the run started"]


def test_rollback_refuses_a_changed_runbook(repo):
    run_id = failed_run(repo)
    edit_header(repo, run_id, runbook="0" * 64)
    r = rollback(repo, run_id, 1)
    assert r.returncode == 1 and "refused: the runbook changed since the run started" in r.stdout.splitlines()
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_runbook_hash_covers_operations_and_testing(repo):
    prd = repo / "docs/prd/orders"
    before = deploy.runbook_hash(prd)
    (prd / "testing.md").write_text((prd / "testing.md").read_text(encoding="utf-8") + "\n", encoding="utf-8")
    after_testing = deploy.runbook_hash(prd)
    (prd / "operations.md").write_text((prd / "operations.md").read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert len({before, after_testing, deploy.runbook_hash(prd)}) == 3


# ---- final review: one prd_deploy command at a time per repository (finding 5) ----

REPO_BUSY = "refused: another prd_deploy command is running in this repository"


@pytest.fixture
def repo_locked(repo):
    import fcntl
    path = deploy.log_dir(repo) / ".active"
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a", encoding="utf-8")
    yield lambda: fcntl.flock(f, fcntl.LOCK_EX)
    f.close()


def test_run_refuses_while_the_repo_is_locked(repo, repo_locked):
    repo_locked()
    r = deploy_cli(repo, "run")
    assert r.returncode == 1 and REPO_BUSY in r.stdout.splitlines(), r.stdout + r.stderr
    assert last(r) == "prd-deploy: refused step=0 run=none"
    assert not (repo / ".deploy").exists() and not list(deploy.log_dir(repo).glob("*.jsonl"))


def test_resume_refuses_while_the_repo_is_locked(repo, repo_locked):
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    repo_locked()
    r = resume(repo, run_id)
    assert r.returncode == 1 and REPO_BUSY in r.stdout.splitlines()
    assert not (repo / ".deploy/production").exists()
    assert not [x for x in deploy.read_log(repo, run_id) if x["kind"] == "resume"]


def test_rollback_refuses_while_the_repo_is_locked(repo, repo_locked):
    run_id = failed_run(repo)
    repo_locked()
    r = rollback(repo, run_id, 1)
    assert r.returncode == 1 and REPO_BUSY in r.stdout.splitlines()
    assert not (repo / ".deploy/staging/rolled-back").exists()


def test_plan_confirm_and_check_take_no_repo_lock(repo, repo_locked):
    run_id = stopped_run(repo)
    repo_locked()
    assert deploy_cli(repo, "plan").returncode == 0
    assert confirm(repo, run_id).returncode == 0
    base = deploy.read_log(repo, run_id)[0]["head"]
    assert deploy_cli(repo, "check", "--run", run_id, "--diff", f"{base}..HEAD").returncode in (0, 1)


def test_a_stopped_run_holds_no_repo_lock(repo):
    stopped_run(repo)
    assert deploy_cli(repo, "run").returncode == 3  # a second run may start while the first waits for its reply


def test_the_repo_lock_is_held_while_a_command_runs(repo):
    probe = ("python3 -c \"import fcntl; fcntl.flock(open('.git/prd-toolkit/deploys/.active', 'a'), fcntl.LOCK_EX | fcntl.LOCK_NB)\""
             " || touch .deploy/repo-locked")
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", f"Run: `mkdir -p .deploy && {probe}; mkdir -p .deploy/staging && echo Hi")
    assert deploy_cli(repo, "run", "--until", "staging").returncode == 0
    assert (repo / ".deploy/repo-locked").exists()


# ---- final review: --until never takes a production step with it (finding 11) ----

def staging_after_production(repo):
    p = repo / OPS
    text = p.read_text(encoding="utf-8")
    p.write_text(text.replace("\n## Drift", "6. Tidy staging (actor: agent) (env: staging)\n   Run: `true`\n   Check: `true`\n\n## Drift", 1), encoding="utf-8")
    commit(repo, "Staging after production", OPS)


def test_until_refuses_a_cut_that_includes_production(repo):
    staging_after_production(repo)
    r = deploy_cli(repo, "plan", "--until", "staging")
    assert r.returncode == 2 and r.stdout == "" and "--until staging would include production step 3" in r.stderr, r.stderr
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 2 and r.stdout == "" and not (repo / ".deploy").exists()
    assert deploy_cli(repo, "plan", "--until", "production").returncode == 0


def test_plan_steps_until_production_env_unit(repo):
    from prdlint import model
    staging_after_production(repo)
    prd = model.load(Path(prd_dir(repo)))
    with pytest.raises(ValueError, match=r"^--until staging would include production step 3$"):
        deploy.plan_steps(prd, "staging")
    assert [s.number for s in deploy.plan_steps(prd, "production")] == [1, 2, 3, 4, 5]


# ---- 0.8.5: one confirm covers consecutive human steps ----

def ahead_repo(repo, *run_args):
    from deploy_fixture import three_human_steps
    three_human_steps(repo)
    r = deploy_cli(repo, "run", *run_args)
    assert r.returncode == 3 and r.stdout.splitlines()[-1].startswith("prd-deploy: human step=2"), r.stdout + r.stderr
    return run_id_of(r)


def confirm_pairs(repo, run_id, *pairs):
    args = [a for n, text in pairs for a in ("--step", str(n), "--reply", text)]
    return deploy_cli(repo, "confirm", "--run", run_id, *args)


def log_of(repo, run_id):
    return deploy.read_log(repo, run_id)


def test_one_confirm_covers_the_stopped_step_and_the_human_steps_after_it(repo):
    run_id = ahead_repo(repo)
    r = confirm_pairs(repo, run_id, (2, "staging ok"), (3, "notes ok"), (4, "deploy production"))
    assert r.returncode == 0, r.stdout + r.stderr
    confirms = [x for x in log_of(repo, run_id) if x.get("kind") == "confirm"]
    assert [(c["step"], c["reply"], c.get("ahead")) for c in confirms] == [(2, "staging ok", None), (3, "notes ok", True), (4, "deploy production", True)]
    r = resume(repo, run_id)
    assert r.returncode == 0 and r.stdout.splitlines()[-1] == f"prd-deploy: done step=5 run={run_id}", r.stdout + r.stderr
    humans = {x["step"]: x for x in log_of(repo, run_id) if x.get("kind") == "step" and x.get("actor") == "human"}
    assert humans[2].get("confirmed_ahead") is None
    assert all(humans[n]["result"] == "human" and humans[n]["confirmed_ahead"] is True for n in (3, 4))
    assert (repo / ".deploy/step5").exists()
    assert resume(repo, run_id).returncode == 1


@pytest.mark.parametrize("pairs", [
    [(2, "a"), (4, "c")],                  # a gap
    [(2, "a"), (3, "b"), (5, "e")],        # an agent step
    [(3, "b")],                            # not the stopped step
    [(2, "a"), (3, " ")],                  # an empty reply
    [(2, "a"), (3, "b"), (3, "b")],        # a repeat
])
def test_a_bad_pair_refuses_the_whole_confirm(repo, pairs):
    run_id = ahead_repo(repo)
    before = log_of(repo, run_id)
    r = confirm_pairs(repo, run_id, *pairs)
    assert r.returncode == 2 and r.stdout == "" and r.stderr.strip(), (r.stdout, r.stderr)
    assert log_of(repo, run_id) == before


def test_a_step_past_until_is_refused(repo):
    run_id = ahead_repo(repo, "--until", "staging")
    before = log_of(repo, run_id)
    r = confirm_pairs(repo, run_id, (2, "a"), (3, "b"), (4, "c"))
    assert r.returncode == 2 and "step 4" in r.stderr
    assert log_of(repo, run_id) == before


def test_unequal_step_and_reply_counts_are_refused(repo):
    run_id = ahead_repo(repo)
    before = log_of(repo, run_id)
    r = deploy_cli(repo, "confirm", "--run", run_id, "--step", "2", "--step", "3", "--reply", "a")
    assert r.returncode == 2 and r.stdout == ""
    assert log_of(repo, run_id) == before


def test_a_0_8_4_log_reads_as_before(repo):
    run_id = ahead_repo(repo)
    assert confirm_pairs(repo, run_id, (2, "staging ok")).returncode == 0
    assert not any("ahead" in x or "confirmed_ahead" in x for x in log_of(repo, run_id))
    r = resume(repo, run_id)
    assert r.returncode == 3 and r.stdout.splitlines()[-1] == f"prd-deploy: human step=3 run={run_id}", r.stdout + r.stderr


# ---- 0.8.5: a level's own Timeout, the close-branch note and matches Checks ----

TESTING = "docs/prd/orders/testing.md"
LEVELS = "| Level | Harness command | Environment | Gate |\n|---|---|---|---|\n"


def level_timeouts(repo, **cells) -> None:
    """Give testing.md's Levels table a Timeout column; `cells` maps a level to its cell, others stay blank."""
    p = repo / TESTING
    text = p.read_text(encoding="utf-8")
    assert text.count(LEVELS) == 1
    head, rest = text.split(LEVELS)
    rows, tail = rest.split("\n\n", 1)
    rows = "\n".join(f"{row} {cells.get(row.split('|')[1].strip(), '')} |" for row in rows.split("\n"))
    p.write_text(head + "| Level | Harness command | Environment | Gate | Timeout |\n|---|---|---|---|---|\n" + rows + "\n\n" + tail, encoding="utf-8")
    commit(repo, "Level timeouts", TESTING)


def slow_system(repo, seconds: int) -> None:
    """Step 2 runs `tests e2e, system`; the system level sleeps `seconds` first, e2e passes at once."""
    change(repo, OPS, "   Run: tests system\n", "   Run: tests e2e, system\n")
    change(repo, "tools/gate.sh", "exit 0", f'[ "$1" = system ] && sleep {seconds}\nexit 0')


def test_a_levels_timeout_applies_to_that_level_only(repo):
    level_timeouts(repo, system="2")
    slow_system(repo, 3)
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 4, r.stdout + r.stderr
    recs = [x for x in records(repo, r) if x["kind"] == "step" and x["step"] == 2]
    assert [(x["level"], x["result"]) for x in recs] == [("e2e", "pass"), ("system", "fail")]
    assert recs[1]["stderr"].endswith("timed out after 2 s (the system level's Timeout)"), recs[1]["stderr"]
    r = deploy_cli(repo, "run", "--until", "staging", "--timeout", "30")
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_given_timeout_overrides_every_level_even_at_600(repo, monkeypatch, capsys):
    """Review Focus 3: --timeout 600 on a level whose Timeout is 1200 runs it with 600, named (--timeout)."""
    from prd_deploy import main
    level_timeouts(repo, system="1200")
    seen = []
    real = deploy._execute

    def spy(cmd, root, env, timeout, why=None):
        seen.append((cmd, timeout, why))
        return real(cmd, root, env, timeout, why)

    monkeypatch.setattr(deploy, "_execute", spy)
    assert main(["run", prd_dir(repo), "--until", "staging", "--timeout", "600"]) == 0
    assert ("bash tools/gate.sh system", 600, "--timeout") in seen
    seen.clear()
    assert main(["run", prd_dir(repo), "--until", "staging"]) == 0
    assert ("bash tools/gate.sh system", 1200, "the system level's Timeout") in seen
    assert all(why == "the default" and t == 600 for c, t, why in seen if c != "bash tools/gate.sh system")


def test_level_timeout_unit(repo):
    from prdlint import model
    level_timeouts(repo, system="1200")
    prd = model.load(Path(prd_dir(repo)))
    assert deploy.level_timeout(prd, "system", None) == (1200, "the system level's Timeout")
    assert deploy.level_timeout(prd, "system", 600) == (600, "--timeout")
    assert deploy.level_timeout(prd, "e2e", None) == (600, "the default")


def test_timeout_is_not_given_by_default():
    from prd_deploy import _parser
    for argv in (["run", "x"], ["resume", "x", "--run", "r"], ["rollback", "x", "--run", "r", "--step", "1"]):
        assert _parser().parse_args(argv).timeout is None, argv


def test_a_run_command_times_out_at_the_default(repo, monkeypatch, capsys):
    from prd_deploy import main
    level_timeouts(repo, system="30")
    change(repo, OPS, "Run: `mkdir -p .deploy/staging && echo Hi", "Run: `sleep 3; mkdir -p .deploy/staging && echo Hi")
    monkeypatch.setattr(deploy, "DEFAULT_TIMEOUT", 1)
    assert main(["run", prd_dir(repo), "--until", "staging"]) == 4
    run_id = capsys.readouterr().out.splitlines()[0].removeprefix("run: ")
    rec = deploy.read_log(repo, run_id)[-1]
    assert rec["step"] == 1 and rec["stderr"].endswith("timed out after 1 s (the default)"), rec["stderr"]


BRANCHES = "| Environment | URL | Production | Branch |\n|---|---|---|---|\n"


def env_branches(repo, **branches) -> None:
    """Give operations.md's Environments table a Branch column."""
    p = repo / OPS
    text = p.read_text(encoding="utf-8")
    old = "| Environment | URL | Production |\n|---|---|---|\n"
    head, rest = text.split(old)
    rows, tail = rest.split("\n\n", 1)
    rows = "\n".join(f"{row} {branches.get(row.split('|')[1].strip(), '')} |" for row in rows.split("\n"))
    p.write_text(head + BRANCHES + rows + "\n\n" + tail, encoding="utf-8")
    commit(repo, "Environment branches", OPS)


NOTE = "prd_deploy: the close is on {current}, not release; push the close commit to release too"


@pytest.mark.parametrize("failing", [False, True])
def test_a_close_on_another_branch_prints_a_note(repo, failing):
    env_branches(repo, staging="release")
    if failing:
        change(repo, OPS, "prints `Hi`", "prints `Nope`")
    git(repo, "checkout", "-q", "-b", "work")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == (4 if failing else 0), r.stdout + r.stderr
    assert r.stderr == NOTE.format(current="work") + "\n", r.stderr
    assert "prd_deploy:" not in r.stdout


def test_no_note_on_the_environments_branch(repo):
    env_branches(repo, staging="release")
    git(repo, "checkout", "-q", "-b", "release")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0 and r.stderr == "", r.stdout + r.stderr


def test_a_detached_head_is_named(repo):
    env_branches(repo, staging="release")
    git(repo, "checkout", "-q", "--detach")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0 and r.stderr == NOTE.format(current="a detached HEAD") + "\n", r.stderr


def test_the_note_comes_at_a_resumes_finish(repo):
    env_branches(repo, production="release")
    git(repo, "checkout", "-q", "-b", "work")
    r = deploy_cli(repo, "run")
    assert r.returncode == 3 and r.stderr == "", r.stderr  # stopped at a human step: not finished
    run_id = run_id_of(r)
    assert confirm(repo, run_id).returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 0 and r.stderr == NOTE.format(current="work") + "\n", r.stderr


def test_branch_note_unit(repo):
    from prdlint import model
    env_branches(repo, staging="release")
    prd = model.load(Path(prd_dir(repo)))
    assert deploy.branch_note(prd, repo, ["production"]) == []
    assert deploy.branch_note(prd, repo, ["staging"]) == [NOTE.format(current="main")]


def note_for(current: str, branch: str) -> str:
    return f"prd_deploy: the close is on {current}, not {branch}; push the close commit to {branch} too"


def test_branch_note_names_each_other_branch_once_in_reached_order(repo):
    from prdlint import model
    env_branches(repo, staging="release", local="hotfix", production="release")
    prd = model.load(Path(prd_dir(repo)))
    git(repo, "checkout", "-q", "-b", "work")
    assert deploy.branch_note(prd, repo, ["staging", "local", "production"]) == [note_for("work", "release"), note_for("work", "hotfix")]


def test_a_run_reaching_two_other_branches_prints_two_lines(repo):
    env_branches(repo, staging="release", production="main")
    git(repo, "checkout", "-q", "-b", "work")
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 0 and r.stderr == note_for("work", "release") + "\n" + note_for("work", "main") + "\n", r.stderr


MATCHES = "Check: `cat .deploy/staging/greeting` prints `Hi`"


@pytest.mark.parametrize("printed,ok", [("deployed 3a27030", True), ("  deployed 3a27030  ", True), ("deployed", False), ("deployed 3a27030 now", False)])
def test_a_matches_check(repo, printed, ok):
    pattern = "^deployed [0-9a-f]{7,40}$"
    change(repo, OPS, MATCHES, f"Check: `echo '{printed}'` matches `{pattern}`")
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == (0 if ok else 4), r.stdout + r.stderr
    rec = next(x for x in records(repo, r) if x["kind"] == "step" and x["step"] == 1)
    if not ok:
        assert rec["check"]["stderr"].endswith(f"no stdout line matches '{pattern}'"), rec["check"]["stderr"]


def test_matches_ok_unit():
    assert deploy._matches_ok(b"x\ndeployed 3a27030\r\n", r"deployed [0-9a-f]{7,40}")
    assert not deploy._matches_ok(b"deployed 3a27030 now\n", r"deployed [0-9a-f]{7,40}")
    assert not deploy._matches_ok(b"", r".*")
