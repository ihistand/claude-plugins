"""Black-box tests of NFR-019 (docs/prd/prd-toolkit/nfr.md, test-cases/nfr.yaml)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nfr_support  # noqa: E402

# T-019.2 runs T-019.1 alone by this file's absolute path and this function's name.
T019_1_FILE = str(Path(__file__).resolve())
T019_1_FUNCTION = "test_uv_commands_and_git_hook_use_the_test_cache"


@pytest.fixture
def vendored_repo(tmp_path):
    """git init <tmp>/repo; load lint-cli/orders and repo/vendored (with its check, which
    ends the test as an error) under the T-019.1 git config isolation."""
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text("", encoding="utf-8")
    git_isolation = {"GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1"}
    repo = tmp_path / "repo"
    init = subprocess.run(["git", "init", str(repo)], cwd=tmp_path,
                          env=nfr_support.subprocess_env(git_isolation),
                          capture_output=True, text=True)
    assert init.returncode == 0, f"git init failed: {init.stderr}"
    nfr_support.load_orders(repo / "docs" / "prd" / "orders")
    nfr_support.load_vendored(repo / ".prd-toolkit")
    return repo, git_isolation


def test_uv_commands_and_git_hook_use_the_test_cache(tmp_path, monkeypatch, vendored_repo):
    """@prd T-019.1"""
    test_cache = nfr_support.test_cache_path()
    repo, git_isolation = vendored_repo
    monkeypatch.setenv("PRD_PLUGINS_FILE", nfr_support.plugins_superpowers_file())

    def run(args, cwd):
        return subprocess.run(args, cwd=cwd, env=nfr_support.subprocess_env(git_isolation),
                              capture_output=True, text=True)

    install = run([sys.executable, str(repo / ".prd-toolkit" / "prd_hooks.py"),
                   "install", "docs/prd/orders"], repo)
    assert install.returncode == 0, (
        f"setup: prd_hooks.py install exited {install.returncode}\n"
        f"stdout: {install.stdout}\nstderr: {install.stderr}")

    (repo / "notes.txt").write_text("hello\n", encoding="utf-8")
    add = run(["git", "add", "notes.txt"], repo)
    assert add.returncode == 0, f"setup: git add failed: {add.stderr}"

    run_1 = run(["uv", "cache", "dir"], tmp_path)
    run_2 = run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "chore: add notes", "-m", "Refs: none (no behaviour change)"],
                repo)

    assert run_1.returncode == 0, f"run_1 exit {run_1.returncode}: {run_1.stderr}"
    assert run_2.returncode == 0, (
        f"run_2 exit {run_2.returncode}\nstdout: {run_2.stdout}\nstderr: {run_2.stderr}")
    lines = run_1.stdout.splitlines()
    assert lines, "run_1 printed no stdout line"
    assert os.path.realpath(lines[0]) == os.path.realpath(test_cache), (
        f"uv cache dir names {lines[0]!r}, not the test cache {str(test_cache)!r}")


def test_session_end_deletes_test_cache_environments(tmp_path):
    """@prd T-019.2"""
    user_cache = tmp_path / "user-cache"
    test_cache = tmp_path / "test-cache"
    user_cache.mkdir()
    test_cache.mkdir()
    env = nfr_support.subprocess_env(
        {"UV_CACHE_DIR": str(user_cache), "PRD_TEST_UV_CACHE": str(test_cache)},
        drop=("PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT",
              "PYTEST_XDIST_TESTRUNUID", "PYTEST_CURRENT_TEST"))

    inner = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--basetemp", str(tmp_path / "basetemp"), T019_1_FILE, "-k", T019_1_FUNCTION],
        cwd=nfr_support.PRD_TOOLKIT, env=env, capture_output=True, text=True)

    assert inner.returncode == 0, (
        f"inner run exit {inner.returncode}\nstdout: {inner.stdout}\nstderr: {inner.stderr}")
    assert not (test_cache / "environments-v2").exists(), (
        "<tmp>/test-cache/environments-v2 still exists after the session ended")
    assert any(p.is_dir() for p in test_cache.iterdir()), (
        "<tmp>/test-cache holds no folder")
    user_envs = user_cache / "environments-v2"
    assert not user_envs.exists() or os.listdir(user_envs) == [], (
        f"<tmp>/user-cache/environments-v2 holds {sorted(os.listdir(user_envs))}")
