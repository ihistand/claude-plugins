"""prd_deploy.py record: a deploy the owner did by hand gets a run log and its environment's Deployed row."""
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import pytest
from deploy_fixture import deploy_repo
from legacy import commit, git
from test_deploy import OPS, PLUGINS_FILE, change, deploy_cli, prd_dir

from prdlint import deploy, model

PRD = "docs/prd/orders"
NOW = datetime(2026, 11, 3, 9, 30, 0, tzinfo=timezone.utc)
HEADER = "| Environment | PRD version | Commit | Date | Run |"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def head_sha(repo) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


def load(repo):
    return model.load(repo / PRD)


def record(repo, env, commit_, reply="I promoted it in the console"):
    return deploy.record(load(repo), repo, env, commit_, reply)


def deployed_lines(repo) -> list[str]:
    return [line for line in (repo / OPS).read_text(encoding="utf-8").split("\n") if line.startswith("| ") and re.match(r"\| \S+ \| \d", line)]


def status(repo) -> str:
    return git(repo, "status", "--porcelain", "--untracked-files=no")


def test_record_writes_the_log_and_the_row(repo, monkeypatch):
    monkeypatch.setattr(deploy, "_now", lambda: NOW)
    sha = head_sha(repo)
    runbook = deploy.runbook_hash(repo / PRD)  # as it was before the row was written
    run_id = record(repo, "production", sha, "Promoted v1 in the console")
    assert run_id == "20261103T093000Z-production"
    log = deploy.read_log(repo, run_id)
    assert len(log) == 2
    header, hand = log
    assert header == {"kind": "header", "by": "hand", "run": run_id, "head": sha, "commit": sha, "prd": PRD,
                      "runbook": runbook, "version": "1.0.0", "until": "production",
                      "started": NOW.isoformat()}
    assert hand == {"kind": "hand", "env": "production", "commit": sha, "reply": "Promoted v1 in the console", "at": NOW.isoformat()}
    text = (repo / OPS).read_text(encoding="utf-8")
    assert text.rstrip("\n").endswith(f"## Deployed\n\n{HEADER}\n|---|---|---|---|---|\n| production | 1.0.0 | {sha[:7]} | 2026-11-03 | {run_id} |")
    assert [(r.env, r.version, r.commit, r.date, r.run) for r in load(repo).operations.deployed] == [("production", "1.0.0", sha[:7], "2026-11-03", run_id)]
    assert status(repo).split() == ["M", OPS]  # left uncommitted: the skill commits it as the close


def test_a_later_record_replaces_the_row(repo):
    first = record(repo, "staging", head_sha(repo))
    commit(repo, "Close the first record", PRD)
    (repo / "tools/notes.txt").write_text("a later change\n", encoding="utf-8")
    commit(repo, "A later commit to deploy", "tools")
    second = record(repo, "staging", head_sha(repo))
    rows = load(repo).operations.deployed
    assert [(r.env, r.commit, r.run) for r in rows] == [("staging", head_sha(repo)[:7], second)]
    assert first != second


def test_other_rows_are_untouched_and_ids_never_clash(repo, monkeypatch):
    """Review Focus 12."""
    monkeypatch.setattr(deploy, "_now", lambda: NOW)
    sha = head_sha(repo)
    a = record(repo, "staging", sha)
    b = record(repo, "production", sha)
    before = [line for line in deployed_lines(repo) if line.startswith("| production ")]
    c = record(repo, "staging", sha)
    assert (a, c) == ("20261103T093000Z-staging", "20261103T093000Z-staging-2")
    assert [line for line in deployed_lines(repo) if line.startswith("| production ")] == before
    rows = {r.env: r.run for r in load(repo).operations.deployed}
    assert rows == {"staging": c, "production": b}
    assert len(deployed_lines(repo)) == 2


def test_the_version_is_the_one_at_the_deployed_commit(repo):
    old = head_sha(repo)
    change(repo, f"{PRD}/prd.md", "version: 1.0.0", "version: 1.1.0")
    run_id = record(repo, "production", old)
    assert deploy.read_log(repo, run_id)[0]["version"] == "1.0.0"
    assert deploy.read_log(repo, run_id)[0]["head"] == head_sha(repo)
    assert [(r.version, r.commit) for r in load(repo).operations.deployed] == [("1.0.0", old[:7])]


def nothing_written(repo, before_logs):
    assert status(repo) == ""
    assert sorted(p.name for p in deploy.log_dir(repo).glob("*.jsonl")) == before_logs


def logs(repo):
    d = deploy.log_dir(repo)
    return sorted(p.name for p in d.glob("*.jsonl")) if d.exists() else []


@pytest.mark.parametrize("env", ["nowhere", "qa"])
def test_unknown_environment_refused(repo, env):
    p = repo / OPS  # qa is in operations.md's Environments only
    p.write_text(p.read_text(encoding="utf-8").replace("| staging | file:", "| qa | file:.deploy/qa | no |\n| staging | file:"), encoding="utf-8")
    commit(repo, "Add qa to operations.md only", OPS)
    before = logs(repo)
    with pytest.raises(deploy.Refused) as e:
        record(repo, env, head_sha(repo))
    assert e.value.reasons == [f"environment {env} is not in both Environments tables"]
    nothing_written(repo, before)


def test_unknown_commit_refused(repo):
    before = logs(repo)
    with pytest.raises(deploy.Refused) as e:
        record(repo, "staging", "0" * 40)
    assert e.value.reasons == [f"commit {'0' * 40} is not in the repository"]
    nothing_written(repo, before)


def test_empty_reply_refused(repo):
    before = logs(repo)
    with pytest.raises(deploy.Refused) as e:
        record(repo, "staging", head_sha(repo), " \n\t")
    assert e.value.reasons == ["the reply is empty"]
    nothing_written(repo, before)


def test_tag_and_short_sha_resolve(repo):
    """Review Focus 13."""
    sha = head_sha(repo)
    git(repo, "tag", "-a", "v1.0.0", "-m", "Release", sha)
    run_id = record(repo, "staging", "v1.0.0")
    assert deploy.read_log(repo, run_id)[0]["commit"] == sha
    run_id = record(repo, "production", sha[:8])
    assert deploy.read_log(repo, run_id)[0]["commit"] == sha


def ambiguous_prefix(repo) -> str:
    """Write commits until two share a four-character prefix; return it."""
    stream = "".join(f"commit refs/heads/many\ncommitter A <a@example.com> {1700000000 + i} +0000\ndata {len(str(i))}\n{i}\n\n"
                     for i in range(3000))  # about 68 shared prefixes expected; none is a ~e^-68 chance
    subprocess.run(["git", "fast-import", "--quiet"], cwd=repo, input=stream, text=True, check=True, capture_output=True)
    shas = git(repo, "rev-list", "refs/heads/many").split()
    by = defaultdict(list)
    for s in shas:
        by[s[:4]].append(s)
    return next(k for k, v in by.items() if len(v) > 1)


def test_ambiguous_short_sha_refused(repo):
    """Review Focus 13."""
    prefix = ambiguous_prefix(repo)
    before = logs(repo)
    with pytest.raises(deploy.Refused) as e:
        record(repo, "staging", prefix)
    assert e.value.reasons == [f"commit {prefix} is not in the repository"]
    nothing_written(repo, before)


def test_reply_reaches_the_log_verbatim(repo):
    """Review Focus 11."""
    reply = 'She said "ship it" — déployé à 9h\nsecond line \'quoted\' ✓'
    run_id = record(repo, "staging", head_sha(repo), reply)
    assert deploy.read_log(repo, run_id)[1]["reply"] == reply


def test_cli_exit_codes(repo):
    sha = head_sha(repo)
    r = deploy_cli(repo, "record", "--env", "staging", "--commit", sha, "--reply", "promoted by hand")
    assert r.returncode == 0 and r.stderr == "", r.stdout + r.stderr
    assert re.fullmatch(r"run=\d{8}T\d{6}Z-staging\n", r.stdout), r.stdout
    assert deploy.read_log(repo, r.stdout.strip().removeprefix("run="))[1]["reply"] == "promoted by hand"
    r = deploy_cli(repo, "record", "--env", "nowhere", "--commit", sha, "--reply", "x")
    assert (r.returncode, r.stdout, r.stderr) == (1, "", "prd_deploy: environment nowhere is not in both Environments tables\n")
    r = deploy_cli(repo, "record", "--env", "staging", "--commit", "nosuchref", "--reply", "x")
    assert (r.returncode, r.stdout, r.stderr) == (1, "", "prd_deploy: commit nosuchref is not in the repository\n")
    for argv in (("record",), ("record", "--env", "staging", "--commit", sha), ("record", "--env", "staging", "--reply", "x")):
        r = deploy_cli(repo, *argv)
        assert r.returncode == 2 and r.stdout == "", argv


def test_write_deployed_row_creates_the_section_once(repo):
    prd = load(repo)
    deploy.write_deployed_row(prd, "staging", "1.0.0", "abc1234", "2026-11-03", "20261103T093000Z-staging")
    deploy.write_deployed_row(load(repo), "production", "1.0.0", "abc1234", "2026-11-03", "20261103T093000Z-production")
    text = (repo / OPS).read_text(encoding="utf-8")
    assert text.count("## Deployed") == 1 and text.count(HEADER) == 1
    assert text.endswith(f"{HEADER}\n|---|---|---|---|---|\n| staging | 1.0.0 | abc1234 | 2026-11-03 | 20261103T093000Z-staging |\n"
                         "| production | 1.0.0 | abc1234 | 2026-11-03 | 20261103T093000Z-production |\n")


def test_commit_without_the_prd_refused(repo):
    """A commit that holds no prd.md has no version to record; the refusal echoes the caller's input."""
    empty = git(repo, "commit-tree", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "-m", "An empty tree").strip()
    before = logs(repo)
    with pytest.raises(deploy.Refused) as e:
        record(repo, "staging", empty)
    assert e.value.reasons == [f"commit {empty} has no {PRD}/prd.md version"]
    nothing_written(repo, before)


def test_a_held_repo_lock_refuses(repo):
    """record takes the repository lock as recover does: non-waiting, so a held lock refuses with nothing written."""
    before = logs(repo)
    with deploy.repo_lock(repo):
        with pytest.raises(deploy.Refused) as e:
            record(repo, "staging", head_sha(repo))
        r = deploy_cli(repo, "record", "--env", "staging", "--commit", head_sha(repo), "--reply", "x")
    assert e.value.reasons == ["another prd_deploy command is running in this repository"]
    assert (r.returncode, r.stdout, r.stderr) == (1, "", "prd_deploy: another prd_deploy command is running in this repository\n")
    nothing_written(repo, before)
