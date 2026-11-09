"""Stale CI: hooks.stale_ci, `prd_hooks.py check [--ci]`, the /prd-status CI part and the changing-prds close."""
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from prdlint import hooks, model, status

PLUGIN_ROOT = Path(__file__).parent.parent
PRD = "docs/prd/orders"
GITLAB = ".gitlab/prd-toolkit.yml"
GITHUB = ".github/workflows/prd-toolkit.yml"
SKILL = PLUGIN_ROOT / "skills/changing-prds/SKILL.md"


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_block.py"), PRD], cwd=root, check=True)  # these tests are about the CI files; the blocks start current
    return root


def run(repo, *args, script="scripts/prd_hooks.py"):
    return subprocess.run([sys.executable, str(PLUGIN_ROOT / script), *args], cwd=repo, capture_output=True, text=True)


def stale(repo):
    return [x for x in hooks.stale_ci(repo, model.load(repo / PRD), PRD) if "; run prd_block.py" not in x]


def vendored(repo, *args):
    return subprocess.run([sys.executable, str(repo / ".prd-toolkit/prd_hooks.py"), *args], cwd=repo, capture_output=True, text=True)


def test_prd_lint_job_runs_the_stale_check_second(prd):
    job = hooks.ci_jobs(model.load(prd), PRD)[0]
    assert job.script == ["uv run --script .prd-toolkit/prd_lint.py --ci docs/prd/orders",
                          "uv run --script .prd-toolkit/prd_hooks.py check --ci docs/prd/orders"]


def test_fresh_files_are_not_stale(repo):
    run(repo, "ci", "--gitlab", PRD)
    run(repo, "ci", "--github", PRD)
    assert stale(repo) == []


def test_no_ci_files_is_not_stale(repo):
    assert stale(repo) == []


def test_new_build_level_makes_the_file_stale(repo):
    run(repo, "ci", "--gitlab", PRD)
    edit(repo / PRD, "testing.md", "| system | `pytest tests/system` | staging | deploy |", "| system | `pytest tests/system` | staging | build |")
    assert stale(repo) == [f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force"]


def test_one_line_per_forge(repo):
    run(repo, "ci", "--gitlab", PRD)
    run(repo, "ci", "--github", PRD)
    edit(repo / PRD, "testing.md", "| system | `pytest tests/system` | staging | deploy |", "| system | `pytest tests/system` | staging | build |")
    assert stale(repo) == [f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force",
                           f"stale: {GITHUB}: re-run prd_hooks.py ci --github --force"]


def test_hand_edited_file_is_stale(repo):
    run(repo, "ci", "--github", PRD)
    (repo / GITHUB).write_text("mine\n")
    assert len(stale(repo)) == 1


def test_check_from_plugin_reports_stale_ci(repo):
    hooks.install(repo, PRD)
    run(repo, "ci", "--gitlab", PRD)
    edit(repo / PRD, "testing.md", "| system | `pytest tests/system` | staging | deploy |", "| system | `pytest tests/system` | staging | build |")
    r = run(repo, "check", PRD)
    assert r.returncode == 1 and f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force" in r.stdout


def test_check_ci_from_vendored_copy(repo):
    hooks.install(repo, PRD)
    run(repo, "ci", "--gitlab", PRD)
    r = vendored(repo, "check", "--ci", PRD)
    assert r.returncode == 0 and r.stdout == "", r.stderr
    edit(repo / PRD, "testing.md", "| system | `pytest tests/system` | staging | deploy |", "| system | `pytest tests/system` | staging | build |")
    r = vendored(repo, "check", "--ci", PRD)
    assert r.returncode == 1 and r.stdout == f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force\n"


def test_check_ci_never_reports_vendored_drift(repo):
    hooks.install(repo, PRD)
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    r = run(repo, "check", "--ci", PRD)
    assert r.returncode == 0 and r.stdout == ""
    assert run(repo, "check", PRD).returncode == 1  # plain check still sees the drift


def test_check_without_ci_from_vendored_copy_still_refused(repo):
    hooks.install(repo, PRD)
    assert vendored(repo, "check", PRD).returncode == 2


def test_ci_flag_belongs_to_check(repo):
    r = run(repo, "install", "--ci", PRD)
    assert r.returncode == 2 and r.stdout == ""


def ci_items(repo):
    return [i for i in status.build_status(model.load(repo / PRD), repo) if i.part == "CI"]


def test_status_shows_none_when_fresh(repo):
    run(repo, "ci", "--gitlab", PRD)
    assert [i.text for i in ci_items(repo)] == ["None."]


def test_status_shows_each_stale_line(repo):
    run(repo, "ci", "--gitlab", PRD)
    edit(repo / PRD, "testing.md", "| system | `pytest tests/system` | staging | deploy |", "| system | `pytest tests/system` | staging | build |")
    assert [i.text for i in ci_items(repo)] == [f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force"]


def test_ci_part_sits_before_deployed():
    assert status.PARTS.index("CI") == status.PARTS.index("Deployed") - 1


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def test_changing_prds_close_reruns_ci():
    text = flat(SKILL)
    assert "touched `testing.md` or `operations.md`" in text
    assert re.search(r"`uv run --script \.prd-toolkit/prd_hooks\.py ci --<forge> --force docs/prd/<slug>`", text)
    assert "check --ci" in text


def test_changing_prds_entry_change_cites_it_in_refs():
    assert "`Refs: FR-002, E-003`" in flat(SKILL)


# ---- 0.7: the links line ----

LINKS_LINE = "uv run --script .prd-toolkit/prd_links.py check --ci docs/prd/orders"


def add_links(prd):
    (prd / "links.md").write_text(
        "# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n\n"
        "## Consumers\n\n| Consumer | Location |\n|---|---|\n", encoding="utf-8")


def test_stale_ci_after_links_md_is_added(repo):
    run(repo, "ci", "--gitlab", PRD)
    assert stale(repo) == []
    add_links(repo / PRD)
    assert stale(repo) == [f"stale: {GITLAB}: re-run prd_hooks.py ci --gitlab --force"]
    assert run(repo, "ci", "--gitlab", "--force", PRD).returncode == 0
    assert stale(repo) == []
    assert LINKS_LINE in (repo / GITLAB).read_text()
