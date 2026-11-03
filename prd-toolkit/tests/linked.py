"""Two linked git repositories in a tmp dir, for the 0.7 tests: orders (the upstream) and reports (its consumer)."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from legacy import commit, git

FIXTURE = Path(__file__).parent / "fixtures/valid/orders"
SCRIPT = Path(__file__).parent.parent / "scripts/prd_links.py"


class Run(NamedTuple):
    code: int
    out: str
    err: str


def run_links(*args, env: dict | None = None, timeout: float | None = None) -> Run:
    """prd_links.py in a subprocess, with this process's environment (or `env`)."""
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, encoding="utf-8",
                       env=env if env is not None else os.environ.copy(), timeout=timeout)
    return Run(r.returncode, r.stdout, r.stderr)


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


def _links_md(upstreams: list[tuple[str, str]], consumers: list[str]) -> str:
    up = "".join(f"| {name} | `../{name}` | | | {needs} |\n" for name, needs in upstreams)
    down = "".join(f"| {name} | `../{name}` |\n" for name in consumers)
    return ("# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n" + up
            + "\n## Consumers\n\n| Consumer | Location |\n|---|---|\n" + down)


def make_three_repos(dst: Path, needs: dict[tuple[str, str], str] | None = None) -> tuple[Path, Path, Path]:
    """`dst/transform`, `dst/reports`, `dst/dashboards`: the valid fixture as docs/prd/<name> (`prd: <name>`), linked
    transform → reports, transform → dashboards and reports → dashboards, with links.md on every side and one commit on
    `main` each. `needs` maps (downstream, upstream) to a Needs cell (default empty: `live in staging`, the environment of
    the fixture's first deploy-gate level). The fixture's operations.md lists local, ci, staging, production in that order."""
    needs = needs or {}
    dst = Path(dst)
    graph = {"transform": [], "reports": ["transform"], "dashboards": ["transform", "reports"]}
    repos = {}
    for name, ups in graph.items():
        repo = _repo(dst, name)
        prd = repo / "docs/prd" / name
        p = prd / "prd.md"
        p.write_text(p.read_text(encoding="utf-8").replace("prd: orders", f"prd: {name}", 1), encoding="utf-8")
        consumers = [d for d, us in graph.items() if name in us]
        (prd / "links.md").write_text(_links_md([(u, needs.get((name, u), "")) for u in ups], consumers), encoding="utf-8")
        commit(repo, "Add the PRD", "docs")
        repos[name] = repo
    return repos["transform"], repos["reports"], repos["dashboards"]
