"""Build the hello-world proof repo: git init on `main`, TICKET.md and .gitignore, one commit.

Usage (from the proof workspace; never write into the plugin tree):
    python3 -B <this file> <dst>

<dst> must not exist or must be empty; nothing is written outside it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from legacy import commit, git  # noqa: E402

TICKET = (
    "# Ticket\n\n"
    "Add a `hello` command: `hello <name>` prints `Hello, <name>!`; an empty name is an error.\n"
)
GITIGNORE = ".venv/\n__pycache__/\n.pytest_cache/\n"


def main(dst: str) -> None:
    repo = Path(dst)
    if repo.exists() and (not repo.is_dir() or any(repo.iterdir())):
        sys.exit(f"refusing a non-empty destination: {repo}")
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-q", "--initial-branch=main")
    (repo / "TICKET.md").write_text(TICKET, encoding="utf-8")
    (repo / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    commit(repo, "Add the ticket", "TICKET.md", ".gitignore", date="2026-01-02T12:00:00+0000")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: hello_repo.py <dst>")
    main(sys.argv[1])
