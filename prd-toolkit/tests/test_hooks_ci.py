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
    assert job.script == ["git ls-files -z --format='./%(path)' -- ':(glob)**/*.sql' | xargs -0 -r python3 -m json.tool"]


def test_standards_job_passes_dash_paths_as_dot_slash(repo):
    """Minor 9: a path starting with `-` reaches the linter as `./-…`, never as an option."""
    (repo / "-x.sql").write_text("{}\n")
    (repo / "a b.sql").write_text("{}\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    job = next(j for j in jobs(repo / PRD) if j.name == "standards-1")
    cmd = job.script[0].replace("python3 -m json.tool", "printf '[%s]\\n'")
    out = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True, check=True).stdout
    assert "[./-x.sql]" in out and "[./a b.sql]" in out


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


def test_ci_mode_still_reports_enforced_row_with_no_command(prd, monkeypatch):
    """Minor 7: --ci skips only the on-PATH lookup; an enforced row with no command is a finding anywhere."""
    edit(prd, "prd.md", "| `**/*.sql` | `python3 -m json.tool` |", "| `**/*.sql` | none |")
    monkeypatch.setenv("PRD_LINT_CI", "1")
    assert any("enforced" in f.message and "none" in f.message for f in lint(prd) if f.rule == "registries")


def test_job_ids_are_sanitized_and_deduped(prd):
    """Minor 8: a Levels name may hold characters a CI job id may not; ids match ^[_A-Za-z][\\w-]*$ and stay unique."""
    import re
    rows = ("| a b | `true` | local | build |\n| a-b | `true` | local | build |\n| a.b | `true` | local | build |\n"
            "| 9x | `true` | local | build |\n")
    text = (prd / "testing.md").read_text()
    head = text.index("|---|---|---|---|\n") + len("|---|---|---|---|\n")
    (prd / "testing.md").write_text(text[:head] + rows + text[head:])
    names = [j.name for j in jobs(prd)]
    assert all(re.fullmatch(r"[_A-Za-z][A-Za-z0-9_-]*", n) for n in names), names
    assert len(set(names)) == len(names)
    assert names[names.index("test-a-b"):names.index("test-a-b") + 4] == ["test-a-b", "test-a-b-2", "test-a-b-3", "test-9x"]
    assert hooks.ci_jobs(model.load(prd), PRD) == jobs(prd)  # deterministic
    assert hooks.job_id("9 x") == "_9-x" and hooks.job_id("ok_1") == "ok_1"


def test_github_workflow_reads_only(prd):
    data = yaml.safe_load(hooks.render_github(jobs(prd)))
    assert data["permissions"] == {"contents": "read"}


# ---- 0.5: manual drift and deploy-test jobs ----

def all_jobs(prd):
    return hooks.ci_jobs(model.load(prd), PRD) + hooks.deploy_jobs(model.load(prd), PRD)


def test_deploy_jobs(prd):
    dj = hooks.deploy_jobs(model.load(prd), PRD)
    assert [j.name for j in dj] == ["drift-production", "test-deploy-staging", "test-deploy-production"]
    assert all(j.manual for j in dj) and not any(j.manual for j in jobs(prd))
    by = {j.name: j for j in dj}
    assert by["drift-production"].script == ["uv run --script .prd-toolkit/prd_drift.py docs/prd/orders --env production"]
    assert by["test-deploy-staging"].script == ["export PRD_ENV=staging TEST_ENV=staging; pytest tests/system",
                                                "export PRD_ENV=staging TEST_ENV=staging; pytest tests/e2e"]
    assert by["test-deploy-production"].script == ["export PRD_ENV=production TEST_ENV=production; pytest tests/smoke"]


def test_ci_never_deploys(prd):
    for j in all_jobs(prd):
        assert not any("prd_deploy.py" in s for s in j.script)
    for render in (hooks.render_gitlab, hooks.render_github):
        assert "prd_deploy.py" not in render(all_jobs(prd))


def test_gitlab_manual(prd):
    data = yaml.safe_load(hooks.render_gitlab(all_jobs(prd)))
    for name in ("drift-production", "test-deploy-staging", "test-deploy-production"):
        assert data[name]["rules"] == [{"when": "manual"}] and data[name]["allow_failure"] is True
        assert data[name]["image"] == hooks.GITLAB_IMAGE and "pip install uv" in " ".join(data[name]["before_script"])
    for name in ("prd-lint", "prd-trace", "test-unit"):
        assert "allow_failure" not in data[name] and "if" in data[name]["rules"][0]


def test_github_dispatch(prd):
    data = yaml.safe_load(hooks.render_github(all_jobs(prd)))
    on = data[True if True in data else "on"]
    assert "workflow_dispatch" in on and "pull_request" in on
    for name, job in data["jobs"].items():
        want = "github.event_name == 'workflow_dispatch'" if name in ("drift-production", "test-deploy-staging", "test-deploy-production") else "github.event_name == 'pull_request'"
        assert job["if"] == want, name


def test_github_unchanged_without_manual(prd):
    """No manual jobs: the render is exactly the 0.4 render."""
    j = jobs(prd)
    expected = ("# Generated by prd_hooks.py ci --github; regenerate rather than edit.\nname: prd-toolkit\non:\n  pull_request:\n\n"
                "permissions:\n  contents: read\n\njobs:\n")
    text = hooks.render_github(j)
    assert text.startswith(expected) and "workflow_dispatch" not in text and "if:" not in text and "secrets" not in text
    assert "allow_failure" not in hooks.render_gitlab(j) and "secrets" not in hooks.render_gitlab(j)


def test_no_manual_jobs_without_drift_or_tests_steps(prd):
    loaded = model.load(prd)
    loaded.operations.drift.clear()
    loaded.operations.steps = [s for s in loaded.operations.steps if s.tests is None]
    assert hooks.deploy_jobs(loaded, PRD) == []


def test_secrets_comment(prd):
    line = "# Manual jobs may need these secrets (operations.md Secrets): GEOCODER_API_KEY, ORDERS_TEST_ADMIN_TOKEN, ORDERS_TEST_REP_TOKEN"
    secrets = model.load(prd).operations.secrets
    for render in (hooks.render_gitlab, hooks.render_github):
        lines = render(all_jobs(prd), secrets).split("\n")
        assert lines[1] == line, render.__name__
        assert line not in render(jobs(prd), secrets)


def test_secrets_comment_omitted_when_none(prd):
    for render in (hooks.render_gitlab, hooks.render_github):
        assert "Manual jobs may need" not in render(all_jobs(prd), [])


def test_deploy_job_ids_stay_unique_with_merge_gate(prd):
    names = [j.name for j in all_jobs(prd)]
    assert len(set(names)) == len(names)
    edit(prd, "testing.md", "| unit |", "| deploy-staging |")  # the merge-gate job test-deploy-staging
    names = [j.name for j in all_jobs(prd)]
    assert len(set(names)) == len(names) and "test-deploy-staging" in names and "test-deploy-staging-2" in names


def test_ci_cli_writes_manual_jobs(repo):
    r = run(repo, "ci", "--gitlab", PRD)
    assert r.returncode == 0, r.stderr
    data = yaml.safe_load((repo / ".gitlab/prd-toolkit.yml").read_text())
    assert data["drift-production"]["allow_failure"] is True and "prd-lint" in data
    r = run(repo, "ci", "--github", PRD)
    assert r.returncode == 0, r.stderr
    text = (repo / ".github/workflows/prd-toolkit.yml").read_text()
    assert "workflow_dispatch" in text and "Manual jobs may need these secrets" in text and "prd_deploy.py" not in text


def test_test_deploy_skips_levels_without_a_command(prd):
    loaded = model.load(prd)
    del loaded.testing.commands["e2e"]
    by = {j.name: j for j in hooks.deploy_jobs(loaded, PRD)}
    assert by["test-deploy-staging"].script == ["export PRD_ENV=staging TEST_ENV=staging; pytest tests/system"]


def test_test_deploy_exports_the_environment_for_a_compound_command(prd, tmp_path):
    """`A=x cd tools && bash gate.sh` would set A for `cd` only; the job must export it for the whole line."""
    import subprocess
    loaded = model.load(prd)
    loaded.testing.commands["smoke"] = 'cd "$TOOLS" && bash gate.sh smoke'
    script = {j.name: j for j in hooks.deploy_jobs(loaded, PRD)}["test-deploy-production"].script
    assert script == ['export PRD_ENV=production TEST_ENV=production; cd "$TOOLS" && bash gate.sh smoke']
    (tmp_path / "gate.sh").write_text('echo "$PRD_ENV|$TEST_ENV"\n', encoding="utf-8")
    out = subprocess.run(["bash", "-c", script[0]], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "TOOLS": str(tmp_path)})
    assert out.stdout.strip() == "production|production", out.stderr
