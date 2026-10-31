"""The build's two mechanical checks: what the builder touched, and what the tester reported."""
import os
import re
import subprocess
from pathlib import Path

from .model import Prd
from .trace import CITE, BadRange

RESULT = re.compile(r"^(T-\d{3}\.\d+): (pass|fail: .+|known-failing E-\d+)$")
_LINE_TID = re.compile(r"^(T-\d{3}\.\d+)\b")


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, encoding="utf-8", errors="replace", timeout=60)


def _show(root: Path, rev: str, path: str) -> str:
    p = _git(root, "show", f"{rev}:{path}")
    return p.stdout if p.returncode == 0 else ""  # absent at that end is fine


def diff_findings(prd: Prd, repo_root: Path, rng: str) -> list[str]:
    if ".." not in rng:
        raise BadRange(f"bad range {rng}: expected <base>..<head>")
    base, head = rng.split("..", 1)
    proc = _git(repo_root, "diff", "--name-status", "-M", "-z", rng)
    if proc.returncode != 0:
        raise BadRange(f"bad range {rng}: {(proc.stderr.strip().splitlines() or ['git diff failed'])[0]}")
    fields = proc.stdout.split("\0")
    paths: list[str] = []
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i]
        n = 2 if status[0] in "RC" else 1
        paths += fields[i + 1:i + 1 + n]
        i += 1 + n
    prefix = Path(os.path.relpath(prd.root.resolve(), repo_root.resolve())).as_posix()
    levels = {tc.id: tc.data.get("level") for tc in prd.test_cases}
    findings: list[str] = []
    for path in dict.fromkeys(paths):
        if prefix == "." or path == prefix or path.startswith(prefix + "/"):
            findings.append(f"{path}: the builder may not edit the PRD folder")
            continue
        cited: dict[str, None] = {}
        for rev in (base or "HEAD", head or "HEAD"):
            for m in CITE.finditer(_show(repo_root, rev, path)):
                cited[m.group(1)] = None
        # a T-id with no test case is treated as non-unit: a tester owns anything not proven unit
        non_unit = [t for t in cited if levels.get(t) != "unit"]
        if non_unit:
            findings.append(f"{path} cites {', '.join(non_unit)}, a tester's test: the builder may not edit it")
    return findings


def results_findings(report: str, tids: list[str]) -> list[str]:
    lines = report.split("\n")
    start = next((n for n, line in enumerate(lines) if "RESULTS" in line), None)
    findings: list[str] = []
    seen: set[str] = set()
    for line in lines[start + 1:] if start is not None else []:
        line = line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        m = _LINE_TID.match(line)
        if not m:
            continue
        tid = m.group(1)
        if tid not in tids:
            findings.append(f"{tid} was not dispatched")
        elif not RESULT.match(line):
            findings.append(f"{tid}: not one of pass, fail: <reason>, known-failing E-nnn")
        seen.add(tid)
    for tid in tids:
        if tid not in seen:
            findings.append(f"{tid} has no RESULTS line")
    return findings
