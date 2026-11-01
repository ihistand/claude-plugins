"""prd_status.py: the read-only status report."""
import json
import subprocess
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, FIXTURE, edit
from prd_status import main
from prdlint import model, status
from prdlint.status import StatusItem

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
OPEN_ERROR = "\n### E-002 Duplicate check ignores case\nDetected: 2026-10-30, review\nClassification: code bug\nTouches: FR-001\nResolution: open\n"


def git(root: Path, *args: str) -> None:
    subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def prd_repo(tmp_path, monkeypatch):
    """The orders fixture in a git repo, with one test file citing T-001.1."""
    import shutil

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders")
    (tmp_path / "tests/unit").mkdir(parents=True)
    (tmp_path / "tests/unit/test_import.py").write_text('def test_a():\n    """@prd T-001.1"""\n')
    return tmp_path


@pytest.fixture
def cli(capsys):
    def run(path, *args):
        code = main([str(path), *args])
        out, err = capsys.readouterr()
        return code, out, err
    return run


@pytest.fixture
def items(prd_repo):
    return status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)


@pytest.fixture
def items_with_error(prd_repo):
    path = prd_repo / "docs/prd/orders/errors.md"
    path.write_text(path.read_text() + OPEN_ERROR)
    return status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)


def test_parts_in_order(prd_repo, cli):
    code, out, _ = cli(prd_repo / "docs/prd/orders")
    assert code == 0
    assert [h[3:] for h in out.splitlines() if h.startswith("## ")] == list(status.PARTS)


def test_counts_by_area(items):
    reqs = [i.text for i in items if i.part == "Requirements"]
    assert reqs == ["api: live 3", "import: live 1", "nfr: live 1"]


def test_matrix_row(items):
    row = next(i for i in items if i.part == "Matrix" and i.id == "FR-001")
    assert "T-001.1 integration build cited" in row.text and "missing" in row.text
    assert "T-001.4 acceptance deploy missing" in row.text and "; " in row.text


def test_no_adoption_map(items):
    assert StatusItem("Adoption map", None, "Not applicable: new project") in items


def test_header(items):
    head = next(i for i in items if i.part == "Header")
    assert "version 1.0.0" in head.text and "status Approved" in head.text


def test_not_built_and_not_verified(prd_repo):
    edit(prd_repo / "docs/prd/orders", "features/import.md", "Status: live (since 1.0.0)", "Status: approved")
    edit(prd_repo / "docs/prd/orders", "features/api.md", "### FR-002 Get an order\nStatus: live (since 1.0.0)", "### FR-002 Get an order\nStatus: built")
    out = status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)
    assert [i.id for i in out if i.part == "Not built"] == ["FR-001"]
    assert [i.id for i in out if i.part == "Not verified"] == ["FR-002"]


def test_open_errors_list_touches(items_with_error):
    assert any(i.part == "Open errors" and i.id == "E-002" and "Duplicate check ignores case" in i.text
               and "Touches: FR-001" in i.text for i in items_with_error)
    assert not any(i.id == "E-001" for i in items_with_error if i.part == "Open errors")


def test_json_matches_text_and_is_deterministic(prd_repo, cli):
    prd_dir = prd_repo / "docs/prd/orders"
    a, b = cli(prd_dir, "--json"), cli(prd_dir, "--json")
    expected = [(i.part, i.id) for i in status.build_status(model.load(prd_dir), prd_repo)]
    assert a[1] == b[1] and a[1].endswith("\n")
    assert [(x["part"], x["id"]) for x in json.loads(a[1])] == expected


def test_usage_error_prints_nothing(tmp_path, cli):
    code, out, err = cli(tmp_path / "missing")
    assert code == 2 and out == "" and err


def test_adoption_rows(prd_repo):
    prd_dir = prd_repo / "docs/prd/orders"
    (prd_dir / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n"
                                         "| api | adopted | `src/api/**` |\n| import | not started | |\n")
    edit(prd_dir, "prd.md", "Not applicable: new project.", "See adoption.md.")
    out = status.build_status(model.load(prd_dir), prd_repo)
    assert [(i.id, i.text) for i in out if i.part == "Adoption map"] == [
        ("api", "api | adopted | src/api/**"), ("import", "import | not started | -")]


def test_unmigrated_prd_exits_2_with_nothing_on_stdout(prd_repo, cli):
    prd_dir = prd_repo / "docs/prd/orders"
    edit(prd_dir, "prd.md", "Not applicable: new project.",
         "| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |")
    code, out, err = cli(prd_dir)
    assert code == 2 and out == "" and f"prd_status: {prd_dir.as_posix()}/prd.md: {model.UNMIGRATED}" in err


# --- Deployed part ---

STAGING_ROW = "| staging | 1.0.0 | 3f2c1a9 | 2026-11-02 | 20261102T090000Z-staging |\n"
PROD_RUN = "20261102T103000Z-production"


def deployed(items):
    return [i.text for i in items if i.part == "Deployed"]


def build(prd_repo):
    return status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)


def write_log(repo, run_id, *recs, header=True, prd="docs/prd/orders"):
    from prdlint import deploy
    if header:
        h = {"kind": "header", "run": run_id, "head": "x", "version": "1.0.0", "until": None, "started": "t"}
        deploy.append(repo, run_id, h if prd is None else {**h, "prd": prd})
    for r in recs:
        deploy.append(repo, run_id, r)


def step(n, env, result):
    return {"kind": "step", "step": n, "env": env, "actor": "agent", "result": result}


def levels(n, env, *names, result="pass"):
    """A tests step's records, one per level."""
    return [{**step(n, env, result), "level": lv} for lv in names]


def add_staging_row(prd_repo):
    path = prd_repo / "docs/prd/orders/operations.md"
    text = path.read_text()
    marker = "| production | 1.0.0 | 3f2c1a9"
    path.write_text(text.replace(marker, STAGING_ROW + marker))


def test_deployed_before_matrix():
    assert status.PARTS[-2:] == ("Deployed", "Matrix")


def test_deployed_lines_in_environment_order(prd_repo):
    add_staging_row(prd_repo)
    assert deployed(build(prd_repo)) == ["staging: 1.0.0 at 3f2c1a9, 2026-11-02", "production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_deployed_none_without_rows(prd_repo):
    path = prd_repo / "docs/prd/orders/operations.md"
    path.write_text("".join(l for l in path.read_text().splitlines(True) if not l.startswith("| production | 1.0.0")))
    assert deployed(build(prd_repo)) == ["None."]


def test_unfinished_human_run_after_row(prd_repo):
    run = "20261103T000000Z-production"
    write_log(prd_repo, run, step(1, "staging", "pass"), step(2, "staging", "pass"), step(3, "production", "human"))
    assert deployed(build(prd_repo)) == [
        "production: 1.0.0 at 3f2c1a9, 2026-11-02", f"production: run {run} stopped (human) at step 3"]


def test_unfinished_env_without_row(prd_repo):
    run = "20261103T000000Z-staging"
    write_log(prd_repo, run, step(1, "staging", "pass"), step(2, "staging", "fail"))
    got = deployed(build(prd_repo))
    assert got == [f"staging: run {run} stopped (failed) at step 2", "production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_unfinished_start_record(prd_repo):
    run = "20261103T000000Z-staging"
    write_log(prd_repo, run, step(1, "staging", "pass"), {"kind": "start", "step": 2, "env": "staging", "at": "t"})
    assert deployed(build(prd_repo))[0] == f"staging: run {run} stopped (unfinished) at step 2"


def test_row_follows_its_environment_when_both(prd_repo):
    add_staging_row(prd_repo)
    run = "20261103T000000Z-staging"
    write_log(prd_repo, run, step(1, "staging", "pass"), step(2, "staging", "fail"))
    assert deployed(build(prd_repo))[:2] == ["staging: 1.0.0 at 3f2c1a9, 2026-11-02", f"staging: run {run} stopped (failed) at step 2"]


def test_finished_or_older_run_adds_nothing(prd_repo):
    write_log(prd_repo, "20261103T000000Z-staging", step(1, "staging", "pass"), step(2, "staging", "pass"))
    write_log(prd_repo, "20261101T000000Z-production", step(3, "production", "human"))  # older than the row's run
    assert deployed(build(prd_repo)) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_newest_run_wins(prd_repo):
    write_log(prd_repo, "20261103T000000Z-staging", step(1, "staging", "fail"))
    write_log(prd_repo, "20261104T000000Z-staging", step(1, "staging", "pass"), step(2, "staging", "pass"))
    assert deployed(build(prd_repo)) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_headerless_and_unreadable_logs_skipped(prd_repo):
    from prdlint import deploy
    write_log(prd_repo, "20261103T000000Z-staging", step(1, "staging", "fail"), header=False)
    (deploy.log_dir(prd_repo) / "20261104T000000Z-staging.jsonl").write_text("{not json\n")
    assert deployed(build(prd_repo)) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_no_git_repo_skips_logs(prd_repo, tmp_path_factory):
    import shutil
    bare = tmp_path_factory.mktemp("nogit")
    shutil.copytree(prd_repo / "docs/prd/orders", bare / "orders")
    got = status.build_status(model.load(bare / "orders"), bare)
    assert deployed(got) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


# --- final review: only this PRD's runs (finding 1) ---

def test_another_prds_stopped_run_is_not_shown(prd_repo):
    run = "20261103T000000Z-staging"
    write_log(prd_repo, run, step(1, "staging", "pass"), step(2, "staging", "fail"), prd="docs/prd/other")
    assert deployed(build(prd_repo)) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_a_log_without_a_prd_is_not_shown(prd_repo):
    run = "20261103T000000Z-staging"
    write_log(prd_repo, run, step(1, "staging", "pass"), step(2, "staging", "fail"), prd=None)
    assert deployed(build(prd_repo)) == ["production: 1.0.0 at 3f2c1a9, 2026-11-02"]


def test_another_prds_newer_run_does_not_hide_this_prds(prd_repo):
    mine, other = "20261103T000000Z-staging", "20261104T000000Z-staging"
    write_log(prd_repo, mine, step(1, "staging", "fail"))
    write_log(prd_repo, other, step(1, "staging", "pass"), *levels(2, "staging", "system", "e2e"), prd="docs/prd/other")
    assert deployed(build(prd_repo))[0] == f"staging: run {mine} stopped (failed) at step 1"
