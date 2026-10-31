"""prd_context.py --for implement: code excerpts around cited Source lines, staleness, Levels."""
import subprocess
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, edit
from context_fixture import context_prd, pack, parts

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


def git(root: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit(root: Path, msg: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/importer.py").write_text("".join(f"line {n}\n" for n in range(1, 61)))
    (tmp_path / "src/legacy.bin").write_bytes(b"ok\xff\xfe\n" * 30)
    commit(tmp_path, "code")
    sha = git(tmp_path, "rev-parse", "--short", "HEAD")
    prd = context_prd(tmp_path)
    edit(prd, "features/import.md", "Tests: T-001.1",
         f"Source: src/importer.py:30 @{sha}\n  src/legacy.bin:3 @{sha}\nTests: T-001.1")
    commit(tmp_path, "prd")
    return tmp_path, prd, sha


def test_excerpt_window_and_exit_0(repo):
    root, prd, sha = repo
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--context", "5")
    code_part = parts(out)["Code"]
    assert code == 0 and "line 25" in code_part and "line 35" in code_part and "line 24" not in code_part and "line 36" not in code_part
    assert "STALE" not in out and "## Levels" in out and "pytest tests/integration" in out


def test_every_ref_of_a_multi_line_source(repo):
    _, prd, _ = repo
    out = pack(prd, "--area", "import", "--for", "implement")[1]
    assert "src/importer.py:30" in out and "src/legacy.bin:3" in out and "�" in out


def test_changed_file_is_stale_exit_1(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("changed\n" * 10)
    commit(root, "change")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and f"STALE: changed since {sha}" in out
    assert "   10  changed" in out and "   11  changed" not in out  # window clamped to the 10-line file


def test_unknown_sha_and_missing_file_are_stale(repo):
    root, prd, sha = repo
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", "src/importer.py:30 @0000000")
    edit(prd, "features/import.md", f"src/legacy.bin:3 @{sha}", f"src/gone.py:3 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: unknown commit 0000000" in out and "STALE: file missing" in out


def test_line_past_end_is_stale(repo):
    root, prd, sha = repo
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", f"src/importer.py:99 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: line 99 is past the end (60 lines)" in out


def test_runs_from_another_directory(repo, monkeypatch):
    root, prd, _ = repo
    monkeypatch.chdir(prd / "features")
    code, out, _ = pack(Path(".."), "--area", "import", "--for", "implement")
    assert code == 0 and "line 30" in out


def test_implement_outside_git_exits_2(ctx):
    code, out, err = pack(ctx, "--area", "import", "--for", "implement")
    assert code == 2 and out == "" and "git" in err


def test_decide_ignores_staleness(repo):
    root, prd, _ = repo
    (root / "src/importer.py").write_text("x\n")
    assert pack(prd, "--area", "import")[0] == 0


def test_req_pack_holds_the_whole_block_and_each_code_excerpt(repo):
    _, prd, _ = repo
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--req", "FR-001")
    assert code == 0 and "FR-001" in out and "Source: src/importer.py:30" in out
    assert "src/legacy.bin:3" in out and "line 30" in parts(out)["Code"]


def test_uncommitted_edit_is_stale_exit_1(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("edited\n" * 60)
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: uncommitted changes; the cited line may have moved" in out


def test_committed_change_wins_over_uncommitted(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("changed\n" * 60)
    commit(root, "change")
    (root / "src/importer.py").write_text("edited\n" * 60)
    out = pack(prd, "--area", "import", "--for", "implement")[1]
    assert f"STALE: changed since {sha}" in out and "uncommitted changes" not in out


def test_malformed_source_is_a_stale_code_item(repo):
    _, prd, sha = repo
    edit(prd, "features/import.md", f"Source: src/importer.py:30 @{sha}\n  src/legacy.bin:3 @{sha}", "Source: `src/importer.py:30`")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: Source not in <path>:<line> @<sha> form" in parts(out)["Code"]
    assert "None." not in parts(out)["Code"]
