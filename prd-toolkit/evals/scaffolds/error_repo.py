"""Build the start repo for the handling-errors and publishing-prds baselines and evals: the `greet`
repo of deploy_repo.py (Approved PRD at docs/prd/greet, every requirement `verified`, a vendored
`.prd-toolkit/`), put into a state that has an error.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <bug|failed-deploy|killed-step>

Every state first writes the managed CLAUDE.md block with the vendored `prd_block.py` and commits it
(`Refs: none (no behaviour change)`), as approval does: the block is what routes a plain prompt to the
skills. The state's own commits come after it.

bug            `ready`, then one ordinary code commit ("Match settings keys case-insensitively",
               `Refs: FR-001`) that makes `greet <name>` read the key `greeting`, so a settings file
               holding `GREETING` is ignored and the command prints `Hello`. That breaks AC-001.2
               (GREETING from the settings file of its install) and, once the build is deployed,
               AC-002.1 too (both go through the changed line). At start only one test fails: the
               unit test citing T-001.2 (tests/unit/test_greet.py); T-001.1 passes, and T-002.1
               (a system test on a deployed install) fails once the build is deployed. Every requirement
               keeps its status: the bug is undetected, and the PRD, lint and trace are untouched.
failed-deploy  `failing-check` plus a real failed `prd_deploy.py run --until staging` and its close,
               committed: an open `unclassified` E-001 in errors.md (written by the vendored
               `prd_error.py new`, source "deploy run <id>, failed step <n>", n read from the log), so
               `prd_deploy.py check` passes on the close. Last stdout line `run=<id>`.
killed-step    `ready` plus a real run whose log is cut back to its header and one unfinished `start`
               record on step 1, as a killed process leaves it (the way test_deploy_recover.py builds
               it). Last stdout line `run=<id>`.

The tracked tree is clean in every state. The vendored `.prd-toolkit/` comes from the plugin tree
this file sits in.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(PLUGIN / "tests"))
import deploy_repo  # noqa: E402
from legacy import commit, git  # noqa: E402

STATES = ("bug", "failed-deploy", "killed-step")
PRD = "docs/prd/greet"


def _tool(repo: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return deploy_repo._tool(repo, script, *args)


def _run(repo: Path, *args: str, expect: int) -> str:
    """Run the vendored prd_deploy.py; return the run id from its last stdout line."""
    r = _tool(repo, str(repo / ".prd-toolkit/prd_deploy.py"), "run", PRD, *args)
    if r.returncode != expect:
        sys.exit(f"error_repo: the run exited {r.returncode}, not {expect}:\n{r.stdout}{r.stderr}")
    return r.stdout.strip().splitlines()[-1].rsplit("run=", 1)[1]


def _log(repo: Path, run_id: str) -> Path:
    common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    return Path(common) / "prd-toolkit/deploys" / f"{run_id}.jsonl"


def _claude_md(repo: Path, date: str) -> None:
    r = _tool(repo, str(repo / ".prd-toolkit/prd_block.py"), PRD)
    if r.returncode != 0 or not (repo / "CLAUDE.md").is_file():
        sys.exit(f"error_repo: prd_block failed:\n{r.stdout}{r.stderr}")
    commit(repo, "Add the CLAUDE.md block\n\nRefs: none (no behaviour change)", "CLAUDE.md", date=date)


def _bug(repo: Path) -> None:
    cli = repo / "src/greet/cli.py"
    text = cli.read_text(encoding="utf-8")
    broken = text.replace('load_settings().get("GREETING", "Hello")', 'load_settings().get("greeting", "Hello")')
    if broken == text:
        sys.exit("error_repo: the greet source changed; update the planted bug")
    cli.write_text(broken, encoding="utf-8")
    commit(repo, "Match settings keys case-insensitively\n\nRefs: FR-001", "src", date="2026-01-06T12:00:00+0000")


def _failed_deploy(repo: Path) -> str:
    run_id = _run(repo, "--until", "staging", expect=4)
    records = [json.loads(line) for line in _log(repo, run_id).read_text(encoding="utf-8").splitlines()]
    base = records[0]["head"]
    failed = [r["step"] for r in records if r["kind"] == "step" and r["result"] == "fail"]
    if len(failed) != 1:
        sys.exit(f"error_repo: expected one failed step in the log, found {failed}")
    r = _tool(repo, str(repo / ".prd-toolkit/prd_error.py"), "new", PRD, "--title", "Staging deploy failed",
              "--source", f"deploy run {run_id}, failed step {failed[0]}")
    if r.returncode != 0:
        sys.exit(f"error_repo: prd_error new failed:\n{r.stdout}{r.stderr}")
    commit(repo, "Record the failed staging deploy as E-001", "docs", date="2026-01-07T12:00:00+0000")
    c = _tool(repo, str(repo / ".prd-toolkit/prd_deploy.py"), "check", PRD, "--run", run_id, "--diff", f"{base}..HEAD")
    if c.returncode != 0:
        sys.exit(f"error_repo: the close does not pass prd_deploy check:\n{c.stdout}{c.stderr}")
    return run_id


def _killed_step(repo: Path) -> str:
    run_id = _run(repo, expect=3)
    path = _log(repo, run_id)
    header = path.read_text(encoding="utf-8").splitlines()[0]
    start = {"kind": "start", "step": 1, "env": "staging", "command": "python3 scripts/deploy.py staging", "at": "2026-01-06T10:00:00+00:00"}
    path.write_text(header + "\n" + json.dumps(start) + "\n", encoding="utf-8")
    shutil.rmtree(repo / ".deploy", ignore_errors=True)
    return run_id


def main(dst: str, state: str) -> None:
    repo = Path(dst).resolve()
    deploy_repo.main(dst, "failing-check" if state == "failed-deploy" else "ready")
    _claude_md(repo, "2026-01-06T18:00:00+0000" if state == "failed-deploy" else "2026-01-05T18:00:00+0000")
    run_id = ""
    if state == "bug":
        _bug(repo)
    elif state == "failed-deploy":
        run_id = _failed_deploy(repo)
    else:
        run_id = _killed_step(repo)
    status = git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    if status:
        sys.exit(f"error_repo: the tracked tree is not clean:\n{status}")
    if run_id:
        print(f"run={run_id}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in STATES:
        sys.exit(f"usage: error_repo.py <dst> <{'|'.join(STATES)}>")
    main(sys.argv[1], sys.argv[2])
