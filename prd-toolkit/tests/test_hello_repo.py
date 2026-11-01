"""The hello_repo eval scaffold: one commit, TICKET.md and .gitignore, on main."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "evals/scaffolds/hello_repo.py"
TICKET = "Add a `hello` command: `hello <name>` prints `Hello, <name>!`; an empty name is an error."


def _git(dst, *args):
    return subprocess.run(["git", *args], cwd=dst, capture_output=True, text=True, check=True).stdout.strip()


def test_hello_repo_is_one_commit_with_ticket_and_gitignore_on_main(tmp_path):
    dst = tmp_path / "hello"
    subprocess.run([sys.executable, "-B", str(SCRIPT), str(dst)], check=True, capture_output=True, text=True)
    assert _git(dst, "branch", "--show-current") == "main"
    assert _git(dst, "rev-list", "--count", "HEAD") == "1"
    assert sorted(_git(dst, "ls-files").split("\n")) == [".gitignore", "TICKET.md"]
    assert TICKET in (dst / "TICKET.md").read_text(encoding="utf-8")
    assert _git(dst, "status", "--porcelain") == ""


def test_hello_repo_refuses_a_non_empty_destination(tmp_path):
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "refusing a non-empty destination" in r.stderr
    assert not (tmp_path / "TICKET.md").exists()
