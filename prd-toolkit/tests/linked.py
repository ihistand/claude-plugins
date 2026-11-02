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
    """Write reports' links.md with an `orders` Upstreams row (`../orders`) and one test case per cited target (see add_cases); uncommitted."""
    prd = reports / "docs/prd/reports"
    (prd / "links.md").write_text(
        "# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n"
        "| orders | `../orders` | | | |\n\n## Consumers\n\n| Consumer | Location |\n|---|---|\n", encoding="utf-8")
    add_cases(prd, cited)


def add_cases(prd: Path, cited: list[str]) -> None:
    """One passing integration case per cited target, T-002.3 onward, in api.yaml and AC-002's Tests line."""
    cases = prd / "test-cases/api.yaml"
    ids = [f"T-002.{i}" for i in range(3, 3 + len(cited))]
    cases.write_text(cases.read_text(encoding="utf-8") + "".join(
        f"\n{t}:\n  ac: AC-002.1\n  level: integration\n  target: {c}\n  environment: ci\n  identity: test-rep\n"
        "  preconditions: []\n  input:\n    id: 1\n  expect:\n    output:\n      status: 200\n      body: {id: 1}\n"
        "    effects: []\n    errors: []\n    leaks: none\n" for t, c in zip(ids, cited)), encoding="utf-8")
    api = prd / "features/api.md"
    old = "Tests: T-002.1 [integration], T-002.2 [integration]  (test-cases/api.yaml)"
    api.write_text(api.read_text(encoding="utf-8").replace(old, old.replace("  (", "".join(f", {t} [integration]" for t in ids) + "  (")), encoding="utf-8")


def bare_origin(repo: Path) -> Path:
    """Give `repo` an `origin`: a bare clone beside it (`<name>.git`), fetched, with `origin/HEAD` -> `origin/main`. Returns the bare path."""
    bare = repo.parent / f"{repo.name}.git"
    git(repo.parent, "clone", "-q", "--bare", str(repo), str(bare))
    git(repo, "remote", "add", "origin", str(bare))
    git(repo, "fetch", "-q", "origin")
    git(repo, "remote", "set-head", "origin", "main")
    return bare
