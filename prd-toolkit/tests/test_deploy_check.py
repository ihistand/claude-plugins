"""prd_deploy.py check --diff: the close check accepts a correct close and rejects each wrong one."""
import json
import re
from pathlib import Path

import pytest
from deploy_fixture import deploy_repo
from legacy import commit, git
from test_deploy import OPS, PLUGINS_FILE, change, confirm, deploy_cli, prd_dir, resume, run_id_of, stopped_run

from prdlint import deploy, model

PRD = "docs/prd/orders"
ERRORS = f"{PRD}/errors.md"
ROW = "| {env} | 1.0.0 | {sha} | {date} | {run} |"
ENTRY = """
### E-002 Deploy failed
Detected: 2026-11-02, deploy {run} step {step}
Classification: unclassified
Touches: -
Diagnosis: see the deploy log {run}
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def head_sha(repo) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def full_run(repo) -> str:
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 0, r.stdout + r.stderr
    return run_id


def staging_run(repo) -> str:
    r = deploy_cli(repo, "run", "--until", "staging")
    assert r.returncode == 0, r.stdout + r.stderr
    return run_id_of(r)


def failed_run(repo) -> str:
    change(repo, OPS, "echo Hi > .deploy/staging/greeting", "echo Bad > .deploy/staging/greeting")
    r = deploy_cli(repo, "run")
    assert r.returncode == 4, r.stdout + r.stderr
    return run_id_of(r)


def run_date(run_id: str) -> str:
    """The run id's first eight digits as YYYY-MM-DD: the date a Deployed row carries."""
    return f"{run_id[:4]}-{run_id[4:6]}-{run_id[6:8]}"


def deployed(repo, run_id, *envs) -> str:
    sha = deploy.read_log(repo, run_id)[0]["head"][:7]
    rows = "\n".join(ROW.format(env=e, sha=sha, run=run_id, date=run_date(run_id)) for e in envs)
    return f"\n## Deployed\n\n| Environment | PRD version | Commit | Date | Run |\n|---|---|---|---|---|\n{rows}\n"


def add_deployed(repo, run_id, *envs) -> None:
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n" + deployed(repo, run_id, *envs), encoding="utf-8")


def go_live(repo, since="1.0.0", skip=()) -> None:
    for rel in ("prd.md", "nfr.md", "features/api.md", "features/import.md"):
        p = repo / PRD / rel
        text = p.read_text(encoding="utf-8")
        for bid in re.findall(r"^### ((?:UJ|FR|NFR)-\d+)", text, flags=re.M) + re.findall(r"^\| ((?:UJ|FR|NFR)-\d+) \|", text, flags=re.M):
            if bid in skip:
                continue
            text = re.sub(rf"(### {bid}\b.*?\nStatus: )verified \(since 1\.0\.0\)", rf"\1live (since {since})", text, flags=re.S, count=1)
            text = re.sub(rf"^(\| {bid} \|.*?\| )verified( \|)", r"\1live\2", text, flags=re.M, count=1)
        p.write_text(text, encoding="utf-8")


def close(repo, run_id, message="Close the deploy", *paths) -> None:
    commit(repo, message, *(paths or (PRD,)))


def check(repo, run_id):
    base = deploy.read_log(repo, run_id)[0]["head"]
    return deploy_cli(repo, "check", "--run", run_id, "--diff", f"{base}..HEAD")


def findings(r) -> list[str]:
    assert r.returncode == 1 and r.stderr == "", (r.returncode, r.stdout, r.stderr)
    return r.stdout.splitlines()


def test_good_production_close(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    close(repo, run_id)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "" and r.stderr == "", r.stdout + r.stderr


def test_good_staging_close(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    close(repo, run_id)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_status_move_after_staging(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    go_live(repo)
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert "FR-001: live after a run that did not finish production" in out


def test_wrong_since(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo, since="0.9.0")
    close(repo, run_id)
    assert "FR-001: since 0.9.0, the run deployed 1.0.0" in findings(check(repo, run_id))


def test_verified_left(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo, skip=("FR-002",))
    close(repo, run_id)
    assert "FR-002: still verified after a production finish" in findings(check(repo, run_id))


def test_index_cell_must_move_with_block(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    p = repo / PRD / "prd.md"
    p.write_text(re.sub(r"^(\| FR-003 \|.*?\| )live( \|)", r"\1verified\2", p.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(f.startswith("FR-003: ") and "index" in f for f in out), out


def test_row_for_unfinished_env(repo):
    run_id = stopped_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert out == ["Deployed production: the run did not finish production"]


def test_row_wrong_commit(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace(deploy.read_log(repo, run_id)[0]["head"][:7], "abc1234"), encoding="utf-8")
    close(repo, run_id)
    assert "Deployed staging: commit abc1234 is not the run's HEAD" in findings(check(repo, run_id))


@pytest.mark.parametrize("old,new,needle", [
    ("| 1.0.0 |", "| 1.0.1 |", "Deployed staging: version 1.0.1"),
    ("| {date} |", "| Nov 2 |", "Deployed staging: date Nov 2"),
    ("| " + "{run}" + " |", "| other-run |", "Deployed staging: run other-run"),
])
def test_row_other_cells(repo, old, new, needle):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    fill = lambda t: t.replace("{run}", run_id).replace("{date}", run_date(run_id))
    p.write_text(p.read_text(encoding="utf-8").replace(fill(old), fill(new)), encoding="utf-8")
    close(repo, run_id)
    assert any(f.startswith(needle) for f in findings(check(repo, run_id)))


def test_two_rows_for_an_environment(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging", "staging")
    close(repo, run_id)
    assert any("more than one row" in f for f in findings(check(repo, run_id)))


def test_other_edit(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / PRD / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nAn extra line.\n", encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{PRD}/features/api\.md:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_edit_outside_the_prd(repo):
    run_id = staging_run(repo)
    (repo / "tools/gate.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    close(repo, run_id, "Touch the harness", "tools")
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(r"tools/gate\.sh:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_edit_in_operations_outside_deployed(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace("Hi > .deploy/staging/greeting", "Hey > .deploy/staging/greeting"), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{OPS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_other_status_change(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    p = repo / PRD / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Status: live (since 1.0.0)", "Status: draft", 1), encoding="utf-8")
    close(repo, run_id)
    assert any(f.startswith("UJ-01: ") for f in findings(check(repo, run_id)))


def add_entry(repo, run_id, step=1, number="E-002", text=None) -> None:
    p = repo / ERRORS
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n" + (text or ENTRY.format(run=run_id, step=step)).replace("E-002", number), encoding="utf-8")


def test_failure_entry_accepted(repo):
    run_id = failed_run(repo)
    add_entry(repo, run_id)
    close(repo, run_id, "Record the failure", ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_a_failed_run_accepts_its_entry_with_another_of_its_entries(repo):
    run_id = failed_run(repo)
    add_entry(repo, run_id)
    add_entry(repo, run_id, number="E-003", text=ENTRY.format(run=run_id, step=3))
    close(repo, run_id, "Record the failure", ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_a_failed_run_needs_an_entry_naming_its_failed_step(repo):
    run_id = failed_run(repo)
    add_entry(repo, run_id, step=3)
    add_entry(repo, run_id, number="E-003", step=4)
    close(repo, run_id, "Record the failure", ERRORS)
    assert findings(check(repo, run_id)) == [f"errors.md: the run failed at step 1 but no open unclassified entry names run {run_id} and that step in Detected:"]


@pytest.mark.parametrize("old,new", [
    ("Classification: unclassified", "Classification: code bug"),
    ("step 1", "step 2"),
    ("deploy {run}", "deploy other"),
])
def test_failure_entry_wrong(repo, old, new):
    run_id = failed_run(repo)
    text = ENTRY.format(run=run_id, step=1).replace(old.replace("{run}", run_id), new, 1)
    add_entry(repo, run_id, text=text)
    close(repo, run_id, "Record the failure", ERRORS)
    out = findings(check(repo, run_id))
    assert any(f.startswith(f"{ERRORS}:") for f in out), out


def test_failure_entry_resolved(repo):
    run_id = failed_run(repo)
    add_entry(repo, run_id, text=ENTRY.format(run="X", step=1).replace("X", run_id) + "Resolution: fixed\n")
    close(repo, run_id, "Record the failure", ERRORS)
    assert any(f.startswith(f"{ERRORS}:") for f in findings(check(repo, run_id)))


def test_an_entry_on_a_run_that_did_not_fail_is_accepted(repo):
    run_id = staging_run(repo)
    add_entry(repo, run_id, text=ENTRY.format(run=run_id, step=1))
    add_deployed(repo, run_id, "staging")
    close(repo, run_id, "Record an entry", ERRORS, OPS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_an_entry_naming_another_run_is_not_accepted_at_the_close(repo):
    run_id = staging_run(repo)
    add_entry(repo, run_id, text=ENTRY.format(run="20200101T000000Z", step=1))
    add_deployed(repo, run_id, "staging")
    close(repo, run_id, "Record an entry", ERRORS, OPS)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{ERRORS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_range_must_start_at_run_head(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    close(repo, run_id)
    short = deploy.read_log(repo, run_id)[0]["head"][:7]
    r = deploy_cli(repo, "check", "--run", run_id, "--diff", "HEAD..HEAD")
    assert findings(r) == [f"the range must start at the run's HEAD {short}"]


def test_a_failed_step_is_not_finished(repo):
    """A run that failed finished no environment: a row for staging is rejected."""
    run_id = failed_run(repo)
    add_deployed(repo, run_id, "staging")
    close(repo, run_id)
    assert "Deployed staging: the run did not finish staging" in findings(check(repo, run_id))


def test_finished_envs_unit(repo):
    run_id = full_run(repo)
    log = deploy.read_log(repo, run_id)
    prd = model.load(repo / PRD)
    assert deploy.finished_envs(log, prd) == ["staging", "production"]
    stopped = [r for r in log if not (r.get("kind") == "step" and r.get("step") in (4, 5))]
    assert deploy.finished_envs(stopped, prd) == ["staging"]
    # a tests step is finished only when every level record passed
    broken = [dict(r, result="fail") if r.get("kind") == "step" and r.get("step") == 2 else r for r in log]
    assert deploy.finished_envs(broken, prd) == ["production"]


@pytest.mark.parametrize("args,code", [
    (["--diff", "nope..HEAD"], 2), (["--diff", "HEAD"], 2), (["--diff", "HEAD...HEAD"], 2),
])
def test_bad_range_is_a_usage_error(repo, args, code):
    run_id = staging_run(repo)
    r = deploy_cli(repo, "check", "--run", run_id, *args)
    assert r.returncode == code and r.stdout == "" and r.stderr


def test_unknown_run_is_a_usage_error(repo):
    r = deploy_cli(repo, "check", "--run", "20990101T000000Z-all", "--diff", "HEAD~0..HEAD")
    assert r.returncode == 2 and r.stdout == "" and "no log for run" in r.stderr


def test_unknown_run_creates_no_log(repo):
    staging_run(repo)
    before = sorted(p.name for p in deploy.log_dir(repo).iterdir())
    bad = "20990101T000000Z-all"
    for args in (("confirm", "--run", bad, "--step", "3", "--reply", "yes"), ("resume", "--run", bad)):
        r = deploy_cli(repo, *args)
        assert r.returncode == 2 and r.stdout == "" and f"no log for run {bad}" in r.stderr, r.stderr
    assert sorted(p.name for p in deploy.log_dir(repo).iterdir()) == before


# ---- fix round 1 ----

HUMAN_LAST = """5. Smoke on production (actor: human) (env: production)
   Do: look at production and reply "smoke ok"
   Check: the reply says "smoke ok"
"""


def test_human_last_step_counts_as_finished_once_confirmed_and_resumed(repo):
    change(repo, OPS, "5. Smoke on production (actor: agent) (env: production)\n   Run: tests smoke\n", HUMAN_LAST)
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 3, r.stdout + r.stderr
    assert confirm(repo, run_id, step="5", reply="smoke ok").returncode == 0
    r = resume(repo, run_id)
    assert r.returncode == 0, r.stdout + r.stderr
    log = deploy.read_log(repo, run_id)
    assert deploy.finished_envs(log, model.load(repo / PRD)) == ["staging", "production"]
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    close(repo, run_id)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_human_last_step_not_finished_before_it_is_confirmed(repo):
    change(repo, OPS, "5. Smoke on production (actor: agent) (env: production)\n   Run: tests smoke\n", HUMAN_LAST)
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    assert resume(repo, run_id).returncode == 3
    log = deploy.read_log(repo, run_id)
    assert deploy.finished_envs(log, model.load(repo / PRD)) == ["staging"]
    assert confirm(repo, run_id, step="5", reply="smoke ok").returncode == 0  # confirmed, not yet resumed
    log = deploy.read_log(repo, run_id)
    assert deploy.finished_envs(log, model.load(repo / PRD)) == ["staging"]


def test_index_since_must_match(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    p = repo / PRD / "prd.md"
    p.write_text(re.sub(r"^(\| FR-001 \|.*?\| live \| \S+ \| )1\.0\.0( \|)", r"\g<1>0.1.0\2", p.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(f.startswith("FR-001: ") and "index" in f and "0.1.0" in f for f in out), out


def test_index_row_without_a_block_may_not_change(repo):
    run_id = full_run(repo)
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    p = repo / PRD / "features/import.md"
    p.write_text(p.read_text(encoding="utf-8").replace("### FR-001 ", "### FR-001x ", 1), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(f.startswith("FR-001: ") and "no block" in f for f in out), out


def seed_deployed_section(repo, extra="") -> None:
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n\n## Deployed\n\n" + extra
                 + "| Environment | PRD version | Commit | Date | Run |\n|---|---|---|---|---|\n", encoding="utf-8")
    commit(repo, "Seed the Deployed section", OPS)


def test_deployed_prose_deleted(repo):
    seed_deployed_section(repo, "Rows are written by the deploy close.\n\n")
    run_id = staging_run(repo)
    p = repo / OPS
    text = p.read_text(encoding="utf-8").replace("Rows are written by the deploy close.\n\n", "")
    row = ROW.format(env="staging", sha=deploy.read_log(repo, run_id)[0]["head"][:7], run=run_id, date=run_date(run_id))
    p.write_text(text.rstrip("\n") + "\n" + row + "\n", encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{OPS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_deployed_header_renamed(repo):
    seed_deployed_section(repo)
    run_id = staging_run(repo)
    p = repo / OPS
    row = ROW.format(env="staging", sha=deploy.read_log(repo, run_id)[0]["head"][:7], run=run_id, date=run_date(run_id))
    p.write_text(p.read_text(encoding="utf-8").replace("PRD version", "Version").rstrip("\n") + "\n" + row + "\n", encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{OPS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_created_deployed_section_must_have_the_spec_header(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace("PRD version", "Version"), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{OPS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_created_deployed_section_may_not_carry_prose(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace("\n## Deployed\n", "\n## Deployed\n\nAll good.\n"), encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{OPS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_failed_run_needs_its_entry(repo):
    run_id = failed_run(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", "Close without an entry")
    out = findings(check(repo, run_id))
    assert out == ["errors.md: the run failed at step 1 but no open unclassified entry was added"]


def test_range_head_must_descend_from_base(repo):
    run_id = staging_run(repo)
    base = deploy.read_log(repo, run_id)[0]["head"]
    git(repo, "checkout", "-q", "--orphan", "other")
    git(repo, "commit", "-q", "--allow-empty", "-m", "Unrelated")
    r = deploy_cli(repo, "check", "--run", run_id, "--diff", f"{base}..other")
    assert findings(r) == ["the range's head does not descend from the run's HEAD"]


# --- the template placeholder in errors.md (R19) ---

PLACEHOLDER = "No entries yet. Add `### E-001 <title>` when the first error is diagnosed."


def empty_ledger(repo, extra="") -> None:
    (repo / ERRORS).write_text(f"# Error ledger\n\n{PLACEHOLDER}\n{extra}", encoding="utf-8")
    commit(repo, "Empty the ledger", ERRORS)


def test_first_entry_may_replace_the_placeholder(repo):
    empty_ledger(repo)
    run_id = failed_run(repo)
    (repo / ERRORS).write_text("# Error ledger\n" + ENTRY.format(run=run_id, step=1).replace("E-002", "E-001"), encoding="utf-8")
    close(repo, run_id, "Record the failure", ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_first_entry_may_keep_the_placeholder(repo):
    empty_ledger(repo)
    run_id = failed_run(repo)
    add_entry(repo, run_id, number="E-001")
    close(repo, run_id, "Record the failure", ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_placeholder_removed_without_an_entry(repo):
    empty_ledger(repo)
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    (repo / ERRORS).write_text("# Error ledger\n", encoding="utf-8")
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{ERRORS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_placeholder_removed_when_the_ledger_had_entries(repo):
    old = (repo / ERRORS).read_text(encoding="utf-8")
    (repo / ERRORS).write_text(old.rstrip("\n") + f"\n\n{PLACEHOLDER}\n", encoding="utf-8")
    commit(repo, "A stray placeholder", ERRORS)
    run_id = failed_run(repo)
    (repo / ERRORS).write_text(old.rstrip("\n") + "\n" + ENTRY.format(run=run_id, step=1), encoding="utf-8")
    close(repo, run_id, "Record the failure", ERRORS)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{ERRORS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


def test_other_lines_still_count_in_the_first_entry_close(repo):
    empty_ledger(repo)
    run_id = failed_run(repo)
    (repo / ERRORS).write_text("# Errors\n" + ENTRY.format(run=run_id, step=1).replace("E-002", "E-001"), encoding="utf-8")
    close(repo, run_id, "Record the failure", ERRORS)
    out = findings(check(repo, run_id))
    assert any(re.fullmatch(rf"{ERRORS}:\d+: only Deployed rows and Status: lines may change", f) for f in out), out


# ---- final review: every finished environment has its row (2), complete level records (7), the run's date (8) ----

def test_production_close_without_rows(repo):
    run_id = full_run(repo)
    go_live(repo)
    close(repo, run_id)
    out = findings(check(repo, run_id))
    assert "Deployed: staging finished in this run but has no row for it" in out
    assert "Deployed: production finished in this run but has no row for it" in out


def test_finished_env_whose_row_was_not_replaced(repo):
    """An earlier run's row left in place is not this run's row."""
    first = staging_run(repo)
    add_deployed(repo, first, "staging")
    close(repo, first)
    run_id = staging_run(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", "Close without rows")
    assert findings(check(repo, run_id)) == ["Deployed: staging finished in this run but has no row for it"]


def test_staging_close_needs_only_the_staging_row(repo):
    run_id = staging_run(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", "Close without rows")
    assert findings(check(repo, run_id)) == ["Deployed: staging finished in this run but has no row for it"]


def test_row_date_must_be_the_runs_date(repo):
    run_id = staging_run(repo)
    add_deployed(repo, run_id, "staging")
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace(f"| {run_date(run_id)} |", "| 1999-01-01 |"), encoding="utf-8")
    close(repo, run_id)
    assert f"Deployed staging: date 1999-01-01 is not the run's date {run_date(run_id)}" in findings(check(repo, run_id))


def test_a_tests_step_needs_every_planned_level(repo):
    """The reviewer's probe: a level record that never reached the log leaves the environment unfinished."""
    change(repo, OPS, "   Run: tests system\n", "   Run: tests system, e2e\n")
    prd = model.load(repo / PRD)
    log = [{"kind": "header"},
           {"kind": "step", "step": 1, "env": "staging", "result": "pass"},
           {"kind": "start", "step": 2, "env": "staging", "level": "system"},
           {"kind": "step", "step": 2, "env": "staging", "level": "system", "result": "pass"}]
    assert deploy.finished_envs(log, prd) == []  # e2e has no record at all
    log += [{"kind": "start", "step": 2, "env": "staging", "level": "e2e"}]
    assert deploy.finished_envs(log, prd) == []  # e2e started and did not finish
    log += [{"kind": "step", "step": 2, "env": "staging", "level": "e2e", "result": "pass"}]
    assert deploy.finished_envs(log, prd) == ["staging"]


def test_an_unfinished_start_leaves_its_environment_unfinished(repo):
    prd = model.load(repo / PRD)
    log = [{"kind": "header"},
           {"kind": "step", "step": 1, "env": "staging", "result": "pass"},
           {"kind": "start", "step": 2, "env": "staging", "level": "system"},
           {"kind": "start", "step": 2, "env": "staging", "level": "e2e"},
           {"kind": "step", "step": 2, "env": "staging", "level": "system", "result": "pass"}]
    assert deploy.finished_envs(log, prd) == []


def unwritten_failure(repo, monkeypatch, capsys) -> str:
    """A run whose step 1 record could not be written: it exits 4 with a start and no step record."""
    from prd_deploy import main

    real = deploy.append

    def flaky(repo_root, rid, record):
        if record.get("kind") == "step" and record.get("step") == 1:
            raise OSError("disk full")
        return real(repo_root, rid, record)

    monkeypatch.setattr(deploy, "append", flaky)
    assert main(["run", prd_dir(repo)]) == 4
    monkeypatch.setattr(deploy, "append", real)
    run_id = capsys.readouterr().out.splitlines()[0].removeprefix("run: ")
    assert not [r for r in deploy.read_log(repo, run_id) if r.get("kind") == "step"]
    return run_id


def test_an_unfinished_start_needs_an_errors_entry(repo, monkeypatch, capsys):
    run_id = unwritten_failure(repo, monkeypatch, capsys)
    git(repo, "commit", "-q", "--allow-empty", "-m", "Close without an entry")
    assert findings(check(repo, run_id)) == ["errors.md: the run failed at step 1 but no open unclassified entry was added"]


def test_an_unfinished_start_accepts_its_entry(repo, monkeypatch, capsys):
    run_id = unwritten_failure(repo, monkeypatch, capsys)
    add_entry(repo, run_id)
    close(repo, run_id, "Record the failure", ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


# ---- a by-hand record's close (spec section 17, fix 5) ----

def hand_record(repo, env, sha=None) -> str:
    return deploy.record(model.load(repo / PRD), repo, env, sha or head_sha(repo), "I promoted it in the service's console")


@pytest.mark.parametrize("env", ["staging", "production"])
def test_by_hand_close_accepted(repo, env):
    run_id = hand_record(repo, env)
    close(repo, run_id, "Record the deploy done by hand")
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "" and r.stderr == "", r.stdout + r.stderr


def test_by_hand_close_of_an_older_commit_accepted(repo):
    old = head_sha(repo)
    (repo / "tools/notes.txt").write_text("a later change\n", encoding="utf-8")
    commit(repo, "A later commit", "tools")
    run_id = hand_record(repo, "production", old)
    close(repo, run_id, "Record the deploy done by hand")
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "", r.stdout + r.stderr


def test_by_hand_close_moves_no_status(repo):
    run_id = hand_record(repo, "production")
    go_live(repo)
    close(repo, run_id, "Record the deploy done by hand")
    out = findings(check(repo, run_id))
    assert "FR-001: a by-hand record moves no status" in out
    assert not any("still verified" in f or "after a run that did not finish" in f for f in out), out


def test_by_hand_close_row_for_another_env(repo):
    run_id = hand_record(repo, "staging")
    add_deployed(repo, run_id, "production")
    close(repo, run_id, "Record the deploy done by hand")
    assert "Deployed production: the run did not finish production" in findings(check(repo, run_id))


def test_by_hand_close_wrong_commit(repo):
    old = head_sha(repo)
    (repo / "tools/notes.txt").write_text("a later change\n", encoding="utf-8")
    commit(repo, "A later commit", "tools")
    run_id = hand_record(repo, "production", old)
    new = head_sha(repo)[:7]  # the repo's HEAD, which the record did not deploy
    p = repo / OPS
    p.write_text(p.read_text(encoding="utf-8").replace(f"| {old[:7]} |", f"| {new} |"), encoding="utf-8")
    close(repo, run_id, "Record the deploy done by hand")
    assert findings(check(repo, run_id)) == [f"Deployed production: commit {new} is not the recorded commit {old[:7]}"]


def test_close_after_an_ahead_confirm(repo):
    from test_deploy import ahead_repo, confirm_pairs
    run_id = ahead_repo(repo)
    assert confirm_pairs(repo, run_id, (2, "a"), (3, "b"), (4, "c")).returncode == 0
    assert resume(repo, run_id).returncode == 0
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    close(repo, run_id)
    r = check(repo, run_id)
    assert r.returncode == 0, r.stdout + r.stderr


# ---- an error entry recorded while a run is stopped (0.8.5, spec 5.2) ----

ERROR_SCRIPT = Path(__file__).parent.parent / "scripts/prd_error.py"


def record_entry(repo, source: str, title: str = "Greeting is wrong") -> None:
    """Append an entry with `prd_error.py new` and leave it uncommitted."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-B", str(ERROR_SCRIPT), "new", prd_dir(repo), "--title", title, "--source", source],
                       capture_output=True, text=True, encoding="utf-8", cwd=repo)
    assert r.returncode == 0, r.stdout + r.stderr


def confirmed_stop(repo) -> str:
    run_id = stopped_run(repo)
    assert confirm(repo, run_id).returncode == 0
    return run_id


def refused_with(r, reason: str) -> None:
    assert r.returncode == 1 and f"refused: {reason}" in r.stdout.splitlines(), r.stdout + r.stderr


def test_an_entry_recorded_mid_run_passes_resume_and_the_close_carries_it(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    r = resume(repo, run_id)
    assert r.returncode == 0, r.stdout + r.stderr
    add_deployed(repo, run_id, "staging", "production")
    go_live(repo)
    close(repo, run_id)
    assert "Greeting is wrong" in git(repo, "show", "HEAD:" + ERRORS)
    r = check(repo, run_id)
    assert r.returncode == 0 and r.stdout == "" and r.stderr == "", r.stdout + r.stderr


def test_an_entry_naming_another_run_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, "deploy run 20200101T000000Z, step 2")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_an_entry_without_a_step_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_an_entry_plus_another_file_edit_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    (repo / "tools/gate.sh").write_text("exit 0\n# changed\n", encoding="utf-8")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_an_entry_plus_one_changed_word_in_an_older_entry_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    p = repo / ERRORS
    text = p.read_text(encoding="utf-8")
    first = re.search(r"^Diagnosis: (\S+)", text, re.M)
    assert first, text
    p.write_text(text[:first.start(1)] + "changed" + text[first.end(1):], encoding="utf-8")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_a_reordered_older_entry_is_refused_at_resume(repo):
    """The same lines in another order are a change: the old text must be kept as it was."""
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    p = repo / ERRORS
    lines = p.read_text(encoding="utf-8").split("\n")
    i = next(n for n, ln in enumerate(lines) if ln.startswith("Diagnosis:"))
    lines[i], lines[i + 1] = lines[i + 1], lines[i]
    p.write_text("\n".join(lines), encoding="utf-8")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_a_whitespace_change_in_an_older_entry_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    p = repo / ERRORS
    p.write_text(p.read_text(encoding="utf-8").replace("Classification: code bug", "Classification:  code bug", 1), encoding="utf-8")
    refused_with(resume(repo, run_id), "the tracked tree has changes")


def test_a_committed_entry_is_refused_at_resume(repo):
    run_id = confirmed_stop(repo)
    record_entry(repo, f"deploy run {run_id}, step 2")
    commit(repo, "Record the entry", ERRORS)
    refused_with(resume(repo, run_id), "HEAD moved since the run started")
