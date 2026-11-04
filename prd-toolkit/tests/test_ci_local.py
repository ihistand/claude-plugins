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
    assert "bad" not in r.stdout
