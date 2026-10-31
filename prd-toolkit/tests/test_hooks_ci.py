"""Generated merge-gate CI: prdlint.hooks.ci_jobs/render_* and `prd_hooks.py ci`."""
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from conftest import edit, lint

from prdlint import hooks, model

PLUGIN_ROOT = Path(__file__).parent.parent
PRD = "docs/prd/orders"
ORIGINAL = "stages: [test]\n"


def jobs(prd):
    return hooks.ci_jobs(model.load(prd), PRD)


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".gitlab-ci.yml").write_text(ORIGINAL)
    return root


def run(repo, *args):
    return subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_hooks.py"), *args], cwd=repo, capture_output=True, text=True)


def test_jobs_from_the_prd(prd):
    names = [j.name for j in jobs(prd)]
    assert names == ["prd-lint", "prd-trace", "standards-1", "test-unit", "test-integration", "test-component"]


def test_model_keeps_harness_commands(prd):
    assert model.load(prd).testing.commands["unit"] == "pytest tests/unit"


def test_lint_job_runs_ci_mode(prd):
    lint_job = jobs(prd)[0]
    assert "uv run --script .prd-toolkit/prd_lint.py --ci docs/prd/orders" in lint_job.script


def test_standards_job_uses_git_glob_pathspec(prd):
    job = next(j for j in jobs(prd) if j.name == "standards-1")
    assert job.script == ["git ls-files -z -- ':(glob)**/*.sql' | xargs -0 -r python3 -m json.tool"]


def test_test_job_runs_the_harness_command(prd):
    job = next(j for j in jobs(prd) if j.name == "test-unit")
    assert job.script == ["pytest tests/unit"]


def test_only_enforced_rows_get_jobs(prd):
    edit(prd, "prd.md", "| code, schema.sql | enforced |", "| code, schema.sql | declined |")
    assert not [j for j in jobs(prd) if j.name.startswith("standards-")]


def test_gitlab_trace_range_and_shape(prd):
    data = yaml.safe_load(hooks.render_gitlab(jobs(prd)))
    assert list(data)[:2] == ["prd-lint", "prd-trace"] and "standards-1" in data
    script = " ".join(data["prd-trace"]["script"])
    assert "--range $CI_MERGE_REQUEST_DIFF_BASE_SHA..HEAD" in script
    assert data["prd-trace"]["variables"]["GIT_DEPTH"] == "0"
    assert "pip install uv" in " ".join(data["prd-lint"]["before_script"])


def test_github_trace_range_and_shape(prd):
    data = yaml.safe_load(hooks.render_github(jobs(prd)))
    assert list(data["jobs"]) == [j.name for j in jobs(prd)]
    steps = data["jobs"]["prd-trace"]["steps"]
    assert steps[0]["uses"] == "actions/checkout@v4" and steps[0]["with"]["fetch-depth"] == 0
    assert any("astral-sh/setup-uv@" in s.get("uses", "") for s in steps)
    assert "${{ github.event.pull_request.base.sha }}..HEAD" in steps[-1]["run"]
    assert data["name"] and "pull_request" in data[True if True in data else "on"]


@pytest.mark.parametrize("kind", ["gitlab", "github"])
def test_rendered_file_parses_and_is_deterministic(prd, kind):
    render = getattr(hooks, f"render_{kind}")
    text = render(jobs(prd))
    assert yaml.safe_load(text) and text == render(jobs(prd))


def test_quoting_survives_yaml(prd):
    edit(prd, "testing.md", "`pytest tests/unit`", "`echo 'a: b' # {x} $HOME`")
    for render in (hooks.render_gitlab, hooks.render_github):
        text = render(jobs(prd))
        assert "echo 'a: b' # {x} $HOME" in str(yaml.safe_load(text))


def test_ci_writes_include_not_main_file(repo):
    r = run(repo, "ci", "--gitlab", PRD)
    assert r.returncode == 0, r.stderr
    assert (repo / ".gitlab/prd-toolkit.yml").is_file() and (repo / ".gitlab-ci.yml").read_text() == ORIGINAL
    assert "include: '.gitlab/prd-toolkit.yml'" in r.stdout


def test_ci_github_writes_workflow(repo):
    r = run(repo, "ci", "--github", PRD)
    assert r.returncode == 0, r.stderr
    assert yaml.safe_load((repo / ".github/workflows/prd-toolkit.yml").read_text())["jobs"]
    assert "include:" not in r.stdout


def test_ci_refuses_existing_include_without_force(repo):
    run(repo, "ci", "--gitlab", PRD)
    (repo / ".gitlab/prd-toolkit.yml").write_text("mine\n")
    r = run(repo, "ci", "--gitlab", PRD)
    assert r.returncode == 1 and "mine" in r.stdout and "---" in r.stdout
    assert (repo / ".gitlab/prd-toolkit.yml").read_text() == "mine\n"
    r = run(repo, "ci", "--gitlab", "--force", PRD)
    assert r.returncode == 0 and "mine" not in (repo / ".gitlab/prd-toolkit.yml").read_text()


def test_ci_identical_file_is_not_a_refusal(repo):
    run(repo, "ci", "--gitlab", PRD)
    assert run(repo, "ci", "--gitlab", PRD).returncode == 0


def test_ci_usage_errors(repo):
    for args in (["ci", PRD], ["ci", "--gitlab", "--github", PRD], ["install", "--gitlab", PRD]):
        r = run(repo, *args)
        assert r.returncode == 2 and r.stdout == ""


def test_ci_mode_skips_machine_checks(prd, monkeypatch):
    edit(prd, "prd.md", "| `**/*.sql` | `python3 -m json.tool` |", "| `**/*.sql` | `no-such-linter-xyz` |")
    edit(prd, "prd.md", "| plans | superpowers:writing-plans | required |", "| plans | nonexistent:skill | required |")
    msgs = lambda: [f.message for f in lint(prd) if f.rule == "registries"]  # noqa: E731
    assert any("is not on PATH" in m for m in msgs()) and any("is not installed" in m for m in msgs())
    monkeypatch.setenv("PRD_LINT_CI", "1")
    assert msgs() == []


def test_ci_mode_keeps_decision_checks(prd, monkeypatch):
    monkeypatch.setenv("PRD_LINT_CI", "1")
    edit(prd, "prd.md", "| code, schema.sql | enforced |", "| code, schema.sql | maybe |")
    assert any("Decision" in f.message for f in lint(prd) if f.rule == "registries")


def test_lint_cli_ci_flag(prd):
    edit(prd, "prd.md", "| `**/*.sql` | `python3 -m json.tool` |", "| `**/*.sql` | `no-such-linter-xyz` |")
    cmd = [sys.executable, str(PLUGIN_ROOT / "scripts/prd_lint.py")]
    assert "is not on PATH" in subprocess.run([*cmd, str(prd)], capture_output=True, text=True).stdout
    assert subprocess.run([*cmd, "--ci", str(prd)], capture_output=True, text=True).stdout == ""
