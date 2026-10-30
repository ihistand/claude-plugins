"""Build the synthetic legacy repo: a small service with real git history."""
import os
import shutil
import subprocess
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures/legacy"

_IDENT = {"NAME": "Legacy Dev", "EMAIL": "legacy@example.com"}


def git(repo: Path, *args: str, date: str = "2026-01-01T12:00:00+0000") -> str:
    """Run git in `repo` with a fixed identity and date, never touching global config."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    for who in ("AUTHOR", "COMMITTER"):
        env[f"GIT_{who}_NAME"], env[f"GIT_{who}_EMAIL"], env[f"GIT_{who}_DATE"] = _IDENT["NAME"], _IDENT["EMAIL"], date
    cmd = ["git", "-c", "user.name=Legacy Dev", "-c", "user.email=legacy@example.com", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(cmd, cwd=repo, env=env, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def commit(repo: Path, message: str, *paths: str, date: str = "2026-01-04T12:00:00+0000") -> None:
    git(repo, "add", *paths)
    git(repo, "commit", "-q", "-m", message, date=date)


def make_legacy_repo(dst: Path) -> Path:
    """Copy fixtures/legacy to `dst`, `git init`, and make 3 commits; the third carries `Refs: FR-001`.

    1. add_note + README (no Refs)   2. tests/test_notes.py (cites T-001.1)   3. app.py fix (Refs: FR-001)
    """
    dst = Path(dst)
    shutil.copytree(FIXTURE, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"), dirs_exist_ok=True)
    src = dst / "src/notes/app.py"
    final = src.read_text(encoding="utf-8")
    src.write_text(final.replace("[t for t in _NOTES.values() if term in t]  # apparent bug: case-sensitive", "[]"), encoding="utf-8")
    # commit 1 is the service as first written; the bug and the search arrive in commit 3
    tests = (dst / "tests/test_notes.py").read_bytes()
    (dst / "tests/test_notes.py").unlink()
    git(dst, "init", "-q")
    commit(dst, "Add the notes service", "src", "README.md", date="2026-01-02T12:00:00+0000")
    (dst / "tests/test_notes.py").write_bytes(tests)
    commit(dst, "Add tests", "tests", date="2026-01-03T12:00:00+0000")
    src.write_text(final, encoding="utf-8")
    commit(dst, "Search notes by term\n\nRefs: FR-001", "src", date="2026-01-04T12:00:00+0000")
    return dst
