"""scripts/ci-local.sh runs the PR workflow's jobs locally in a clean HOME (prd-toolkit 0.8.1, Task 11)."""
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci-local.sh"
REPO = SCRIPT.parent.parent

WORKFLOW = """\
name: stub
jobs:
  good:
    steps:
      - uses: actions/checkout@v4
      - run: "echo base=${{ github.event.pull_request.base.sha }}"
      - run: "echo home=$HOME"
  bad:
    steps:
      - run: "echo before"
      - run: "false"
      - run: "echo never-reached"
"""


def run(tmp_path, *args, jobs=None):
    wf = tmp_path / "wf.yml"
    wf.write_text(WORKFLOW, encoding="utf-8")
    env = dict(os.environ, CI_LOCAL_WORKFLOW=str(wf))
    env.pop("CI_LOCAL_JOBS", None)
    if jobs:
        env["CI_LOCAL_JOBS"] = jobs
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=tmp_path)


def head():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def test_per_job_lines_and_exit_code(tmp_path):
    r = run(tmp_path, "HEAD")
    out = r.stdout + r.stderr
    assert r.returncode == 1, out
    assert "ci-local: good pass" in r.stdout
    assert "ci-local: bad fail" in r.stdout
    assert "never-reached" not in out


def test_base_sha_is_substituted_with_merge_base(tmp_path):
    r = run(tmp_path, "HEAD")
    assert f"base={head()}" in r.stdout + r.stderr


def test_home_is_not_the_real_one(tmp_path):
    r = run(tmp_path, "HEAD")
    homes = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("home=")]
    assert len(homes) == 1
    assert homes[0] != f"home={os.environ['HOME']}"


def test_job_subset_and_all_pass_exits_zero(tmp_path):
    r = run(tmp_path, "HEAD", jobs="good")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ci-local: good pass" in r.stdout
    assert "ci-local: bad" not in r.stdout  # a bare "bad" can be part of the base SHA the good job echoes


def run_wf(tmp_path, text, *args, script=SCRIPT):
    wf = tmp_path / "wf2.yml"
    wf.write_text(text, encoding="utf-8")
    env = dict(os.environ, CI_LOCAL_WORKFLOW=str(wf))
    env.pop("CI_LOCAL_JOBS", None)
    return subprocess.run([str(script), *args], capture_output=True, text=True, env=env, cwd=tmp_path)


def test_a_step_reading_stdin_does_not_eat_the_job_list(tmp_path):
    r = run_wf(tmp_path, "jobs:\n  first:\n    steps:\n      - run: cat >/dev/null\n  second:\n    steps:\n      - run: 'true'\n", "HEAD")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ci-local: first pass" in r.stdout
    assert "ci-local: second pass" in r.stdout


def test_leftover_expression_is_unsupported(tmp_path):
    r = run_wf(tmp_path, "jobs:\n  a:\n    steps:\n      - run: echo ${{ secrets.X }}\n", "HEAD")
    assert r.returncode == 2
    assert "ci-local: unsupported" in r.stderr


def test_unhonoured_key_is_unsupported(tmp_path):
    for where in ("    needs: b\n    steps:\n      - run: 'true'\n", "    steps:\n      - run: 'true'\n        working-directory: x\n"):
        r = run_wf(tmp_path, "jobs:\n  a:\n" + where, "HEAD")
        assert r.returncode == 2, r.stdout + r.stderr
        assert "ci-local: unsupported" in r.stderr


def test_substitution_is_the_merge_base_not_the_base(tmp_path):
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    script = repo / "scripts" / "ci-local.sh"
    script.write_bytes(SCRIPT.read_bytes())
    script.chmod(0o755)

    def g(*a):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()

    g("init", "-q", "-b", "main")
    g("add", "scripts")
    g("commit", "-q", "-m", "a")
    fork = g("rev-parse", "HEAD")
    g("checkout", "-q", "-b", "feature")
    (repo / "f").write_text("b")
    g("add", "f")
    g("commit", "-q", "-m", "b")
    g("checkout", "-q", "main")
    (repo / "m").write_text("c")
    g("add", "m")
    g("commit", "-q", "-m", "c")
    main_head = g("rev-parse", "main")
    g("checkout", "-q", "feature")
    assert fork != main_head
    r = run_wf(tmp_path, "jobs:\n  a:\n    steps:\n      - run: echo got=${{ github.event.pull_request.base.sha }}\n", "main", script=script)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"got={fork}" in r.stdout
    assert main_head not in r.stdout


def test_each_job_gets_its_own_fresh_home(tmp_path):
    wf = ("jobs:\n  writer:\n    steps:\n      - run: 'touch \"$HOME/left-by-writer\" && ls -A \"$HOME\"'\n"
          "  reader:\n    steps:\n      - run: 'test -z \"$(ls -A \"$HOME\")\" && echo reader-home-empty'\n")
    r = run_wf(tmp_path, wf, "HEAD")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ci-local: writer pass" in r.stdout and "ci-local: reader pass" in r.stdout
    assert "reader-home-empty" in r.stdout
