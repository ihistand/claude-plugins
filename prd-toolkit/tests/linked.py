"""Two linked git repositories in a tmp dir, for the 0.7 tests: orders (the upstream) and reports (its consumer)."""
import shutil
from pathlib import Path

from legacy import commit, git

FIXTURE = Path(__file__).parent / "fixtures/valid/orders"


def _repo(root: Path, name: str) -> Path:
    repo = root / name
    shutil.copytree(FIXTURE, repo / "docs/prd" / name)
    git(repo, "init", "-q", "-b", "main")
    return repo


def make_linked_repos(dst: Path) -> tuple[Path, Path]:
    """`dst/orders` (the valid fixture as docs/prd/orders) and `dst/reports` (a copy as docs/prd/reports, `prd: reports`),
    one commit on `main` each, no links yet."""
    dst = Path(dst)
    orders, reports = _repo(dst, "orders"), _repo(dst, "reports")
    p = reports / "docs/prd/reports/prd.md"
    p.write_text(p.read_text(encoding="utf-8").replace("prd: orders", "prd: reports", 1), encoding="utf-8")
    for repo in (orders, reports):
        commit(repo, "Add the PRD", "docs")
    return orders, reports


def link(reports: Path, cited: list[str]) -> None:
    """Write reports' links.md with an `orders` Upstreams row (`../orders`) and one test case per cited target; uncommitted."""
    prd = reports / "docs/prd/reports"
    (prd / "links.md").write_text(
        "# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n"
        "| orders | `../orders` | | | |\n\n## Consumers\n\n| Consumer | Location |\n|---|---|\n", encoding="utf-8")
    cases = prd / "test-cases/links.yaml"
    cases.write_text("".join(
        f"T-090.{i}:\n  ac: AC-002.1\n  level: integration\n  target: {c}\n  environment: ci\n  identity: none\n" for i, c in enumerate(cited, 1)), encoding="utf-8")
