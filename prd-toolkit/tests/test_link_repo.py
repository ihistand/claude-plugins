"""The link_repo eval scaffold (prd-toolkit 0.7): greet-client and greet, unlinked, linked and mid-change-set.

Each build makes two real repositories (uv lock and sync, a staging deploy run of greet), so every state is
built once per module and shared by the tests that read it.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "evals/scaffolds/link_repo.py"
CLIENT_PRD = "docs/prd/greet-client"
GREET_PRD = "docs/prd/greet"
BRANCH = "cs-001-greet-json"
VALIDATOR = ("uv run --with pyyaml python3 -c \"import sys,yaml; sys.exit(0 if isinstance(yaml.safe_load("
             "open('contracts/cli.yaml')), dict) else 1)\"")
STATES = ["unlinked", "linked", "cs-running"]


def run(repo: Path, *cmd: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), cwd=repo, capture_output=True, text=True, env={**os.environ, **(env or {})})


def tool(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return run(repo, "uv", "run", "--script", script, *args)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def build(dst: Path, state: str, *extra: str) -> tuple[Path, Path]:
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(dst), state, *extra], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    upstream = Path(extra[extra.index("--upstream") + 1]) if "--upstream" in extra else dst / "upstream/greet"
    return dst, upstream


_BUILT: dict[str, tuple[Path, Path]] = {}


@pytest.fixture(scope="module")
def states(tmp_path_factory):
    def get(state: str) -> tuple[Path, Path]:
        if state not in _BUILT:
            _BUILT[state] = build(tmp_path_factory.mktemp(state.replace("-", "_")) / "greet-client", state)
        return _BUILT[state]
    yield get
    _BUILT.clear()


def check(repo: Path, prd: str) -> subprocess.CompletedProcess:
    return tool(repo, ".prd-toolkit/prd_links.py", "check", prd)


# ---------------------------------------------------------------- every state

@pytest.mark.parametrize("state", STATES)
def test_every_state_is_clean_lints_and_traces(states, state):
    client, greet = states(state)
    for repo, prd in ((client, CLIENT_PRD), (greet, GREET_PRD)):
        assert git(repo, "status", "--porcelain", "--untracked-files=no") == "", (repo, state)
        assert (repo / ".prd-toolkit/prd_links.py").is_file()
        lint = tool(repo, str(ROOT / "scripts/prd_lint.py"), prd)
        assert lint.returncode == 0, (prd, state, lint.stdout + lint.stderr)
        trace = tool(repo, str(ROOT / "scripts/prd_trace.py"), prd)
        assert trace.returncode == 0, (prd, state, trace.stdout + trace.stderr)
        claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        assert "<!-- prd-toolkit:start -->" in claude and git(repo, "ls-files", "CLAUDE.md").strip() == "CLAUDE.md"
        block = tool(repo, ".prd-toolkit/prd_block.py", prd, "--check")
        assert block.returncode == 0, (prd, state, block.stdout + block.stderr)
    # the upstream clone sits inside the client by default, and the client ignores it
    assert "upstream/greet/" in (client / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert git(client, "ls-files", "upstream") == ""


# ---------------------------------------------------------------- unlinked

def test_unlinked_has_no_links_and_greet_deployed_to_staging(states):
    client, greet = states("unlinked")
    for repo, prd in ((client, CLIENT_PRD), (greet, GREET_PRD)):
        assert not (repo / prd / "links.md").exists()
        assert not (repo / prd / "contracts/upstream").exists()
        r = check(repo, prd)
        assert (r.returncode, r.stdout) == (0, ""), r.stdout + r.stderr
        assert git(repo, "branch", "--show-current").strip() == "main"
    # greet: the cli custom type, validated from the PRD folder, its own §14 row, and a staging install
    prd_md = (greet / GREET_PRD / "prd.md").read_text(encoding="utf-8")
    assert f"| cli | `contracts/cli.yaml` | `{VALIDATOR}` |" in prd_md
    assert re.search(r"^\| 1\.0\.1 \| .*\bcli\b", prd_md, re.M)
    cli = (greet / GREET_PRD / "contracts/cli.yaml").read_text(encoding="utf-8")
    assert re.search(r"^greet:\n  arguments:", cli, re.M) and "\n  output:" in cli and "\n  exit codes:" in cli
    staging = greet / ".deploy/staging/bin/greet"
    assert run(greet, str(staging), "World").stdout == "Hi, World!\n"
    # the client: its GREET setting is greet's staging install, relative to the client root
    config = (client / CLIENT_PRD / "contracts/config.yaml").read_text(encoding="utf-8")
    assert ("environments: {local: upstream/greet/.deploy/staging/bin/greet, staging: upstream/greet/.deploy/staging/bin/greet, "
            "production: upstream/greet/.deploy/production/bin/greet}") in config
    feats = "".join(p.read_text(encoding="utf-8") for p in (client / CLIENT_PRD / "features").glob("*.md"))
    assert feats.count("Status: verified (since 1.0.0)") == 2 and "*** <greeting> ***" in feats
    # the client's deploy-gate system test passes against its own staging install, which runs greet's
    assert run(client, sys.executable, "scripts/deploy.py", "staging").returncode == 0
    assert run(client, str(client / ".deploy/staging/bin/welcome"), "World").stdout == "*** Hi, World! ***\n"
    r = run(client, "uv", "run", "pytest", "-q", "tests/system", env={"TEST_ENV": "staging"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = run(client, "uv", "run", "pytest", "-q", "tests/unit")
    assert r.returncode == 0 and "3 passed" in r.stdout, r.stdout + r.stderr
    assert run(client, str(client / ".deploy/staging/bin/welcome"), "").returncode == 1


# ---------------------------------------------------------------- linked

def test_linked_cites_cli_greet_and_holds_the_synced_snapshot(states):
    client, greet = states("linked")
    client_links = (client / CLIENT_PRD / "links.md").read_text(encoding="utf-8")
    greet_head = git(greet, "rev-parse", "main").strip()
    version = re.search(r"^version: (\S+)$", (greet / GREET_PRD / "prd.md").read_text(encoding="utf-8"), re.M).group(1)
    assert f"| greet | `upstream/greet` | {version} | {greet_head} |  |" in client_links
    assert "| greet-client | `../..` |" in (greet / GREET_PRD / "links.md").read_text(encoding="utf-8")
    cases = (client / CLIENT_PRD / "test-cases").glob("*.yaml")
    system = [t for p in cases for t in p.read_text(encoding="utf-8").split("\n\n") if "level: system" in t]
    assert len(system) == 1 and "target: cli:greet/greet" in system[0]
    snap = client / CLIENT_PRD / "contracts/upstream/greet"
    assert sorted(p.name for p in snap.iterdir()) == ["cli.yaml"]
    text = (snap / "cli.yaml").read_text(encoding="utf-8")
    assert text.splitlines()[0] == (f"# Snapshot of greet {version} at {greet_head}, written by prd_links.py sync. "
                                    "Do not edit. Type: cli.")
    assert re.findall(r"^(\w[\w ]*):", text, re.M) == ["greet"]
    for repo, prd in ((client, CLIENT_PRD), (greet, GREET_PRD)):
        r = check(repo, prd)
        assert r.returncode == 0, r.stdout + r.stderr
        assert r.stdout.strip() and all(line.endswith(": same") for line in r.stdout.splitlines()), r.stdout


def test_linked_with_a_sibling_upstream(tmp_path):
    client, greet = build(tmp_path / "greet-client", "linked", "--upstream", str(tmp_path / "greet"))
    assert "upstream" not in (client / ".gitignore").read_text(encoding="utf-8")
    assert "| greet | `../greet` |" in (client / CLIENT_PRD / "links.md").read_text(encoding="utf-8")
    assert "| greet-client | `../greet-client` |" in (greet / GREET_PRD / "links.md").read_text(encoding="utf-8")
    config = (client / CLIENT_PRD / "contracts/config.yaml").read_text(encoding="utf-8")
    assert "staging: ../greet/.deploy/staging/bin/greet, production: ../greet/.deploy/production/bin/greet}" in config
    for repo, prd in ((client, CLIENT_PRD), (greet, GREET_PRD)):
        assert git(repo, "status", "--porcelain", "--untracked-files=no") == ""
        assert check(repo, prd).returncode == 0
        assert tool(repo, str(ROOT / "scripts/prd_lint.py"), prd).returncode == 0


# ---------------------------------------------------------------- cs-running

def test_cs_running_record_and_branches(states, tmp_path):
    client, greet = states("cs-running")
    record = greet / GREET_PRD / "changes/CS-001.md"
    text = record.read_text(encoding="utf-8")
    assert text.startswith("# CS-001 greet --json\n")
    assert "\nStatus: running\n" in text
    assert re.search(r'^Approval: \d{4}-\d{2}-\d{2}, "approve CS-001"$', text, re.M)
    rows = {cells[1]: cells for cells in (
        [c.strip() for c in line.strip("|").split("|")] for line in text.splitlines() if re.match(r"\| \d+ \|", line))}
    assert rows["greet"][3] == rows["greet-client"][3] == BRANCH
    assert rows["greet"][8] == "verified" and rows["greet"][7] == "live in staging"
    assert rows["greet-client"][8] == "approved" and rows["greet-client"][6] == "greet live in staging"
    # the record passes change-sets: lint is clean, and the vendored writer reads it back
    lint = tool(greet, str(ROOT / "scripts/prd_lint.py"), GREET_PRD)
    assert lint.returncode == 0 and "change-sets" not in lint.stdout, lint.stdout
    copy = tmp_path / "changes/CS-001.md"  # a copy, so the shared state is never written
    copy.parent.mkdir()
    copy.write_text(text, encoding="utf-8")
    r = tool(greet, ".prd-toolkit/prd_links.py", "changeset", "log", str(copy), "probe")
    assert r.returncode == 0 and copy.read_text(encoding="utf-8").rstrip().endswith(" probe"), r.stdout + r.stderr
    assert record.read_text(encoding="utf-8") == text
    for repo in (client, greet):
        assert git(repo, "branch", "--show-current").strip() == BRANCH
        assert BRANCH in git(repo, "log", "-1", "--format=%D")
        assert "Change-set: greet/CS-001" in git(repo, "log", "main..HEAD", "--format=%B")
    # greet built and verified on its branch: greet --json prints the greeting and the name
    r = run(greet, sys.executable, "-m", "greet", "--json", "World", env={"PYTHONPATH": "src", "GREET_SETTINGS": ""})
    assert r.returncode == 0 and json.loads(r.stdout) == {"greeting": "Hello", "name": "World"}, r.stdout + r.stderr
    r = run(greet, "uv", "run", "pytest", "-q", "tests/unit")
    assert r.returncode == 0, r.stdout + r.stderr
    feats = (greet / GREET_PRD / "features/greet.md").read_text(encoding="utf-8")
    assert re.search(r"### FR-003 .*\nStatus: verified \(since 1\.1\.0\)", feats)
    # the client's PRD change is approved on its branch, not built
    client_feats = (client / CLIENT_PRD / "features/welcome.md").read_text(encoding="utf-8")
    assert "Status: approved (since 1.1.0)" in client_feats and "greet --json" in client_feats
    changed = git(client, "diff", "--name-only", "main..HEAD").split()
    assert changed and all(x.startswith(CLIENT_PRD + "/") or x == "CLAUDE.md" for x in changed), changed  # nothing built
    # check: the client reads greet at main (unchanged); greet's working tree changed cli:greet, which the client cites
    r = check(client, CLIENT_PRD)
    assert r.returncode == 0, r.stdout + r.stderr
    r = check(greet, GREET_PRD)
    assert r.returncode == 1 and "consumer greet-client cli:greet: changed" in r.stdout, r.stdout + r.stderr
    r = tool(greet, ".prd-toolkit/prd_links.py", "impact", GREET_PRD, "--base", "main")
    assert r.returncode == 1 and "consumer greet-client: cli:greet" in r.stdout, r.stdout + r.stderr


# ---------------------------------------------------------------- refusals

def test_refuses_a_non_empty_destination_and_an_unknown_state(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x/f").write_text("a")
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "x"), "linked"], capture_output=True, text=True)
    assert r.returncode != 0 and "is not empty" in r.stderr and "Traceback" not in r.stderr, r.stderr
    assert [p.name for p in (tmp_path / "x").iterdir()] == ["f"]
    (tmp_path / "up").mkdir()
    (tmp_path / "up/f").write_text("a")
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "c"), "linked", "--upstream", str(tmp_path / "up")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "is not empty" in r.stderr and "Traceback" not in r.stderr, r.stderr
    assert not (tmp_path / "c").exists()
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), str(tmp_path / "y"), "nope"], capture_output=True, text=True)
    assert r.returncode != 0 and "usage: link_repo.py" in r.stderr and "Traceback" not in r.stderr, r.stderr
    assert not (tmp_path / "y").exists()
