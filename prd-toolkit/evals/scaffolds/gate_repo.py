"""Build the start repo for the decision-inbox evals (0.8.2): the `greet` repo of deploy_repo.py with one gate
pending, so `prd_gates.py list` shows it.

Usage (from the eval workspace; never write into the plugin tree):
    python3 -B <this file> <dst> <approval|proposed>

approval   `ready` plus the CLAUDE.md block, then a recorded and reviewed change, uncommitted as changing-prds
           leaves it before step 5: FR-001 gains AC-001.3 (`greet` with no name prints `<GREETING>, World!`) and
           the unit case T-001.3, FR-001 `approved`, the PRD `In review` at 1.1.0 with its `pending` §14 row
           (written by the vendored `prd_change.py record`), and a ready `.prd-review.json` whose digest is the
           PRD's. The gate is `approval:main`.
proposed   error_repo.py's `bug`, then E-001 recorded and proposed as a `code bug` by the vendored
           `prd_error.py`, each write committed as running-an-error.md steps 1 and 3 commit it. The gate is
           `error-class:E-001`.

The last stdout line is `gate=<id>`. The tracked tree is clean in `proposed`; in `approval` only the PRD folder
holds changes. The vendored `.prd-toolkit/` comes from the plugin tree this file sits in.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

import deploy_repo  # noqa: E402
import error_repo  # noqa: E402
from legacy import commit, git  # noqa: E402

STATES = ("approval", "proposed")
PRD = "docs/prd/greet"
AC = ("- AC-001.2 When `greet <name>` runs, it shall print `<GREETING>, <name>!`, taking GREETING from the settings "
      "file of its install.\n")
NEW_AC = "- AC-001.3 When `greet` runs with no name, it shall print `<GREETING>, World!`.\n"
CASE = """
T-001.3:
  ac: AC-001.3
  level: unit
  refs: ["testing.md#Harness"]
  target: code:greet.cli.main
  environment: local
  identity: none
  preconditions: []
  input:
    settings_file: '{"GREETING": "Hi"}'
    name: ""
  expect:
    output: "Hi, World!"
    effects: []
    errors: []
    leaks: none
"""
RECORD = "no dry run (unit only)"


def _ok(r, what: str) -> str:
    if r.returncode != 0:
        sys.exit(f"gate_repo: {what} exited {r.returncode}:\n{r.stdout}{r.stderr}")
    return r.stdout


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        sys.exit(f"gate_repo: {path.name} changed; update the scaffold ({old!r} not found)")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _tool(repo: Path, name: str, *args: str):
    return deploy_repo._tool(repo, str(repo / ".prd-toolkit" / name), *args)


def _approval(repo: Path) -> str:
    deploy_repo.main(str(repo), "ready")
    error_repo._claude_md(repo, "2026-01-05T18:00:00+0000")
    prd = repo / PRD
    feature = prd / "features/greet.md"
    _replace(feature, AC, AC + NEW_AC)
    _replace(feature, "Tests: T-001.1 [unit], T-001.2 [unit]", "Tests: T-001.1 [unit], T-001.2 [unit], T-001.3 [unit]")
    _replace(feature, "### FR-001 Print a greeting\nStatus: verified (since 1.0.0)", "### FR-001 Print a greeting\nStatus: approved")
    cases = prd / "test-cases/greet.yaml"
    cases.write_text(cases.read_text(encoding="utf-8").rstrip("\n") + "\n" + CASE, encoding="utf-8")
    _replace(prd / "prd.md", "\nstatus: Approved\n", "\nstatus: In review\n")
    _ok(_tool(repo, "prd_change.py", "record", PRD, "--base", "HEAD", "--bump", "minor",
              "--change", "greet with no name greets the World"), "prd_change record")
    _ok(_tool(repo, "prd_lint.py", PRD), "prd_lint")
    digest = _ok(_tool(repo, "prd_change.py", "digest", PRD), "prd_change digest").strip().splitlines()[-1]
    verdict = {"interface": 1, "kind": "review", "head": git(repo, "rev-parse", "HEAD").strip(), "digest": digest,
               "restate": "`greet` with no name prints the greeting to the World.",
               "touches": ["FR-001", "AC-001.3", "T-001.3"], "impact": {"exit": 0, "lines": []},
               "bump": {"level": "minor", "decided": []},
               "dry_run": {"tids": [], "open": 0, "dismissed": 0, "record": RECORD}, "ready": True, "blockers": []}
    (prd / ".prd-review.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    return "approval:main"


def _proposed(repo: Path) -> str:
    error_repo.main(str(repo), "bug")
    out = _ok(_tool(repo, "prd_error.py", "new", PRD, "--title", "greet ignores GREETING in the settings file",
                    "--source", "user report (/prd-error)", "--touches", "FR-001"), "prd_error new")
    eid = out.strip().splitlines()[-1].split()[0]
    commit(repo, f"docs(prd): record {eid}\n\nRefs: {eid}", "docs", date="2026-01-07T12:00:00+0000")
    _ok(_tool(repo, "prd_error.py", "propose", PRD, eid, "--class", "code bug", "--touches", "FR-001",
              "--diagnosis", "`main` reads the settings key `greeting`, but AC-001.2 says `greet <name>` prints "
                             "`<GREETING>, <name>!`, taking GREETING from the settings file of its install."),
        "prd_error propose")
    commit(repo, f"docs(prd): propose {eid}\n\nRefs: {eid}", "docs", date="2026-01-07T13:00:00+0000")
    status = git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    if status:
        sys.exit(f"gate_repo: the tracked tree is not clean:\n{status}")
    return f"error-class:{eid}"


def main(dst: str, state: str) -> None:
    repo = Path(dst).resolve()
    gate = _approval(repo) if state == "approval" else _proposed(repo)
    listed = _ok(_tool(repo, "prd_gates.py", "list", PRD), "prd_gates list")
    if not any(line.split(" ", 1)[0] == gate for line in listed.splitlines()):
        sys.exit(f"gate_repo: {gate} is not pending:\n{listed}")
    print(f"gate={gate}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in STATES:
        sys.exit(f"usage: gate_repo.py <dst> <{'|'.join(STATES)}>")
    main(sys.argv[1], sys.argv[2])
