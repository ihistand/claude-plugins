"""prd_hooks.py install | check | uninstall, in a temp git repo with the orders fixture."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from prdlint import hooks

PLUGIN_ROOT = Path(__file__).parent.parent
PLUGIN_VERSION = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text())["version"]
PRD = "docs/prd/orders"


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)
    return r.stdout.strip()


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "T")
    (root / "src").mkdir()
    (root / "src/app.py").write_text("x = 1\n")
    return root


def test_install_vendors_and_writes_shims(repo):
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/VERSION").read_text().strip() == PLUGIN_VERSION
    assert all((repo / ".prd-toolkit" / f).is_file() for f in hooks.VENDORED)
    assert (repo / ".prd-toolkit/prdlint/model.py").is_file()
    assert not list((repo / ".prd-toolkit").rglob("__pycache__"))
    shim = (repo / ".git/hooks/commit-msg").read_text()
    assert hooks.MARKER in shim and PRD in shim and os.access(repo / ".git/hooks/commit-msg", os.X_OK)
    assert os.access(repo / ".prd-toolkit/prd_hooks.py", os.X_OK)


def test_install_is_idempotent_and_refreshes(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/prdlint/stale.py").write_text("x\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    hooks.install(repo, PRD)
    assert not (repo / ".prd-toolkit/prdlint/stale.py").exists()
    assert hooks.check(repo, PLUGIN_ROOT) == []


def test_existing_hook_is_never_overwritten(repo):
    (repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\necho mine\n")
    lines = hooks.install(repo, PRD)
    assert (repo / ".git/hooks/pre-commit").read_text() == "#!/bin/sh\necho mine\n"
    assert any("add this line to .git/hooks/pre-commit" in x for x in lines)


def test_never_sets_hooks_path(repo):
    hooks.install(repo, PRD)
    assert git(repo, "config", "--get", "core.hooksPath", check=False) == ""


def test_check_flags_stale_version_and_changed_file(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    problems = hooks.check(repo, PLUGIN_ROOT)
    assert any("VERSION 0.0.1" in x for x in problems) and any("prd_lint.py differs" in x for x in problems)


def test_uninstall_removes_only_marked_hooks(repo):
    hooks.install(repo, PRD)
    (repo / ".git/hooks/post-commit").write_text("#!/bin/sh\necho mine\n")
    hooks.uninstall(repo)
    assert not (repo / ".git/hooks/commit-msg").exists() and (repo / ".git/hooks/post-commit").exists()
    assert (repo / ".prd-toolkit/VERSION").exists()


def commit_in(cwd, message):
    git(cwd, "add", "app.py")
    return subprocess.run(["git", "commit", "-q", "-m", message], cwd=cwd, capture_output=True, text=True)


def test_end_to_end_commit_refused_from_subdirectory(repo):
    hooks.install(repo, PRD)
    r = commit_in(repo / "src", "Add x")
    assert r.returncode != 0 and "Refs" in r.stderr
    assert commit_in(repo / "src", "Add x\n\nRefs: none (no behaviour change)").returncode == 0


def test_shim_blocks_without_uv(repo):
    assert not Path("/usr/bin/uv").exists() and not Path("/bin/uv").exists()
    hooks.install(repo, PRD)
    msg = repo / "msg"
    msg.write_text("x\n")
    r = subprocess.run([str(repo / ".git/hooks/commit-msg"), str(msg)], cwd=repo, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert r.returncode != 0 and "prd-toolkit: uv is not on PATH; install uv to run this hook" in r.stderr


def run_vendored(repo, *args):
    return subprocess.run([sys.executable, str(repo / ".prd-toolkit/prd_hooks.py"), *args], cwd=repo, capture_output=True, text=True)


def test_vendored_install_writes_shims_only(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    for h in ("commit-msg", "pre-commit"):
        (repo / ".git/hooks" / h).unlink()
    r = run_vendored(repo, "install", PRD)
    assert r.returncode == 0, r.stderr
    assert (repo / ".git/hooks/commit-msg").is_file() and (repo / ".git/hooks/pre-commit").is_file()
    assert (repo / ".prd-toolkit/VERSION").read_text() == "0.0.1\n"
    assert (repo / ".prd-toolkit/prd_lint.py").read_text() == "# changed\n"


def test_vendored_check_exits_2(repo):
    hooks.install(repo, PRD)
    r = run_vendored(repo, "check", PRD)
    assert r.returncode == 2 and "run check from the plugin, not the vendored copy" in r.stderr and r.stdout == ""


GUARD = 'command -v uv >/dev/null 2>&1 || { echo "prd-toolkit: uv is not on PATH; install uv to run this hook" >&2; exit 1; }'


SKIP = "prd-toolkit: no .prd-toolkit/ (or no PRD folder) on this branch; hook skipped"
TOP = 'prd_top="$(git rev-parse --show-toplevel)" || exit 1; '


def appended(lines):
    line = next(x for x in lines if "add this line" in x)
    return line[line.index(TOP):]


def test_printed_line_is_appendable_sh(repo):
    (repo / ".git/hooks/commit-msg").write_text("#!/bin/sh\necho mine\n")
    lines = hooks.install(repo, PRD)
    line = next(x for x in lines if "add this line" in x)
    assert "exec" not in line and "before any `exit 0`" in line and "sh hook" in line
    hook = '"$prd_top/.prd-toolkit/prd_git_hook.py"'
    assert line.endswith(
        f'{TOP}if [ -f {hook} ] && [ -d "$prd_top/{PRD}" ]; then {GUARD}; '
        f'uv run --script {hook} commit-msg "$prd_top/{PRD}" "$@" || exit $?; else echo "{SKIP}" >&2; fi')


def test_appended_line_runs_and_propagates_failure(repo):
    log = repo / "log"
    (repo / ".git/hooks/commit-msg").write_text(f"#!/bin/sh\necho mine >> {log}\n")
    lines = hooks.install(repo, PRD)
    line = appended(lines)
    hook = repo / ".git/hooks/commit-msg"
    hook.write_text(f"#!/bin/sh\necho mine >> {log}\n{line}\necho after >> {log}\n")
    hook.chmod(0o755)
    (repo / "m").write_text("Add x\n\nRefs: none (no behaviour change)\n")
    r = subprocess.run([str(hook), str(repo / "m")], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0 and log.read_text().split() == ["mine", "after"]
    (repo / "m").write_text("Add x\n")
    git(repo, "add", "src/app.py")
    r = subprocess.run([str(hook), str(repo / "m")], cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and log.read_text().split() == ["mine", "after", "mine"]


def test_prd_path_with_space_and_dollar(repo):
    odd = "docs/prd/my $prd"
    (repo / odd).parent.mkdir(parents=True, exist_ok=True)
    (repo / "docs/prd/orders").rename(repo / odd)
    hooks.install(repo, odd)
    git(repo, "add", "src/app.py")
    r = subprocess.run(["git", "commit", "-q", "-m", "Add x"], cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and "Refs" in r.stderr


def test_hookspath_set_writes_no_shim(repo, tmp_path_factory):
    other = tmp_path_factory.mktemp("elsewhere")
    git(repo, "config", "core.hooksPath", str(other))
    lines = hooks.install(repo, PRD)
    assert list(other.iterdir()) == [] and not (repo / ".git/hooks/commit-msg").exists()
    assert sum("add this line" in x for x in lines) == 2 and any(str(other) in x for x in lines)
    other.joinpath("commit-msg").write_text(f"#!/bin/sh\n{hooks.MARKER}\n")
    assert hooks.uninstall(repo) and other.joinpath("commit-msg").exists()
    assert any("core.hooksPath" in x for x in hooks.uninstall(repo))


def test_marker_must_be_second_line(repo):
    mine = f"#!/bin/sh\necho x\n# note: {hooks.MARKER} is mentioned here\n{hooks.MARKER}\n"
    (repo / ".git/hooks/commit-msg").write_text(mine)
    lines = hooks.install(repo, PRD)
    assert (repo / ".git/hooks/commit-msg").read_text() == mine and any("add this line" in x for x in lines)
    hooks.uninstall(repo)
    assert (repo / ".git/hooks/commit-msg").read_text() == mine


def test_shim_has_lf_newlines(repo):
    hooks.install(repo, PRD)
    assert b"\r" not in (repo / ".git/hooks/commit-msg").read_bytes()


def test_vendored_install_when_repo_root_has_plugin_json(repo):
    hooks.install(repo, PRD)
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin/plugin.json").write_text('{"version": "9"}')
    for h in ("commit-msg", "pre-commit"):
        (repo / ".git/hooks" / h).unlink()
    r = run_vendored(repo, "install", PRD)
    assert r.returncode == 0, r.stderr
    assert (repo / ".git/hooks/commit-msg").is_file()


def test_hook_run_leaves_no_pycache(repo):
    hooks.install(repo, PRD)
    git(repo, "add", "src/app.py")
    subprocess.run(["git", "commit", "-q", "-m", "Add x"], cwd=repo, capture_output=True, text=True)
    assert not list((repo / ".prd-toolkit").rglob("__pycache__"))


def test_commit_on_branch_without_vendored_copy_is_skipped(repo):
    """R36: hooks are per clone, the copy is per branch: a branch with no .prd-toolkit/ commits, with a message."""
    hooks.install(repo, PRD)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--no-verify", "-m", "Start")
    git(repo, "switch", "-q", "-c", "no-toolkit")
    git(repo, "rm", "-r", "-q", ".prd-toolkit")
    (repo / "src/app.py").write_text("x = 2\n")
    git(repo, "add", "src/app.py")
    r = subprocess.run(["git", "commit", "-q", "-m", "Change x"], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stderr.count(SKIP) == 2  # pre-commit and commit-msg


def test_commit_without_prd_folder_is_skipped(repo):
    hooks.install(repo, PRD)
    git(repo, "rm", "-r", "-q", "--cached", "docs", check=False)
    import shutil
    shutil.rmtree(repo / "docs")
    git(repo, "add", "src/app.py")
    r = subprocess.run(["git", "commit", "-q", "-m", "Change x"], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0 and SKIP in r.stderr


def test_appended_line_skips_without_copy_and_blocks_without_uv(repo):
    log = repo / "log"
    (repo / ".git/hooks/commit-msg").write_text("#!/bin/sh\necho mine\n")
    line = appended(hooks.install(repo, PRD))
    hook = repo / ".git/hooks/commit-msg"
    hook.write_text(f"#!/bin/sh\n{line}\necho after >> {log}\n")
    hook.chmod(0o755)
    (repo / "m").write_text("Add x\n")
    r = subprocess.run([str(hook), str(repo / "m")], cwd=repo, env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True)
    assert r.returncode != 0 and "prd-toolkit: uv is not on PATH" in r.stderr and not log.exists()
    (repo / ".prd-toolkit").rename(repo / "elsewhere")
    r = subprocess.run([str(hook), str(repo / "m")], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0 and SKIP in r.stderr and log.read_text().split() == ["after"]


def test_install_writes_gitignore_for_pycache(repo):
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/.gitignore").read_text() == "__pycache__/\n"
    assert hooks.check(repo, PLUGIN_ROOT) == []


def test_vendored_has_deploy_scripts(repo):
    assert "prd_deploy.py" in hooks.VENDORED and "prd_drift.py" in hooks.VENDORED
    hooks.install(repo, PRD)
    for f in ("prd_deploy.py", "prd_drift.py", "prdlint/deploy.py", "prdlint/drift.py"):
        assert (repo / ".prd-toolkit" / f).is_file(), f
    assert hooks.check(repo, PLUGIN_ROOT) == []


def test_check_reports_stale_deploy_script(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/prd_deploy.py").write_text("# stale\n")
    assert any("prd_deploy.py differs" in x for x in hooks.check(repo, PLUGIN_ROOT))


# --- the vendored copy must run from .prd-toolkit/ alone (task 11 fix round 2) ---

def test_vendors_the_block_template(repo):
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/templates/claude-block.md").read_bytes() == (PLUGIN_ROOT / "templates/claude-block.md").read_bytes()


def test_check_reports_a_stale_vendored_block_template(repo):
    hooks.install(repo, PRD)
    assert hooks.check(repo, PLUGIN_ROOT) == []
    (repo / ".prd-toolkit/templates/claude-block.md").write_text("old\n")
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/templates/claude-block.md differs from the plugin copy"]
    (repo / ".prd-toolkit/templates/claude-block.md").unlink()
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/templates/claude-block.md is missing"]


def test_every_vendored_script_runs_from_the_vendored_copy(repo):
    """No traceback, missing file or import error from any VENDORED script run in .prd-toolkit/ (exit codes for findings are fine)."""
    hooks.install(repo, PRD)
    git(repo, "add", "-A"); git(repo, "commit", "-q", "--no-verify", "-m", "init")
    (repo / "msg.txt").write_text("feat: x\n\nRefs: none (no behaviour change)\n")
    calls = {
        "prd_lint.py": [PRD], "prd_trace.py": [PRD], "prd_status.py": [PRD], "prd_context.py": [PRD],
        "prd_block.py": [PRD, "--claude-md", "CLAUDE.md"], "prd_build_check.py": [PRD, "--diff", "HEAD..HEAD"],
        "prd_deploy.py": ["plan", PRD], "prd_drift.py": [PRD], "prd_hooks.py": ["check", PRD],
        "prd_git_hook.py": ["commit-msg", PRD, "msg.txt"], "prd_error.py": ["list", PRD], "prd_links.py": ["check", PRD],
        "prd_confirm.py": ["status", PRD, "--area", "none"],
        "prd_judge.py": [PRD, "T-999.9", "msg.txt"], "prd_change.py": ["digest", PRD],
        "prd_gates.py": ["list", PRD],
    }
    assert set(calls) == set(hooks.VENDORED), set(hooks.VENDORED) ^ set(calls)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    for name, args in calls.items():
        r = subprocess.run([sys.executable, f".prd-toolkit/{name}", *args], cwd=repo, capture_output=True, text=True, env=env)
        err = r.stdout + r.stderr
        for bad in ("Traceback", "No such file", "ModuleNotFoundError", "ImportError", "FileNotFoundError"):
            assert bad not in err, (name, err[-600:])
    assert "prd-toolkit:start" in (repo / "CLAUDE.md").read_text()


def test_vendors_prd_links_and_check_reports_it_missing(repo):
    assert "prd_links.py" in hooks.VENDORED
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/prd_links.py").is_file() and (repo / ".prd-toolkit/prdlint/links.py").is_file()
    assert hooks.check(repo, PLUGIN_ROOT) == []
    (repo / ".prd-toolkit/prd_links.py").unlink()
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/prd_links.py is missing"]


def test_vendored_prd_links_checks_a_linked_prd(repo):
    hooks.install(repo, PRD)
    (repo / PRD / "links.md").write_text(
        "# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n\n"
        "## Consumers\n\n| Consumer | Location |\n|---|---|\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, ".prd-toolkit/prd_links.py", "check", "--ci", PRD], cwd=repo, capture_output=True, text=True, env=env)
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


def test_vendors_the_confirm_script_and_page(repo):
    assert "prd_confirm.py" in hooks.VENDORED
    files = hooks._source_files(hooks.SCRIPTS, hooks.PLUGIN_ROOT / "templates/hooks")
    assert "prd_confirm.py" in files and "confirm/form.html" in files
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/confirm/form.html").read_bytes() == (PLUGIN_ROOT / "templates/confirm/form.html").read_bytes()
    assert (repo / ".prd-toolkit/prd_confirm.py").is_file()
    assert hooks.check(repo, PLUGIN_ROOT) == []


def test_check_reports_a_stale_vendored_confirm_page(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/confirm/form.html").write_text("old\n")
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/confirm/form.html differs from the plugin copy"]
    (repo / ".prd-toolkit/confirm/form.html").unlink()
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/confirm/form.html is missing"]
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/confirm/extra.html").write_text("x\n")
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/confirm/extra.html is not in the plugin"]
    hooks.install(repo, PRD)
    assert not (repo / ".prd-toolkit/confirm/extra.html").exists()


def test_vendors_prd_gates(repo):
    assert "prd_gates.py" in hooks.VENDORED
    hooks.install(repo, PRD)
    assert (repo / ".prd-toolkit/prd_gates.py").is_file() and (repo / ".prd-toolkit/prdlint/gates.py").is_file()
    assert hooks.check(repo, PLUGIN_ROOT) == []
    (repo / ".prd-toolkit/prd_gates.py").unlink()
    assert hooks.check(repo, PLUGIN_ROOT) == [".prd-toolkit/prd_gates.py is missing"]
