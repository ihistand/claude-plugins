"""prd_deploy's engine: plan the runbook, check pre-flight, run steps, keep the log.

The only code that runs a runbook's commands. Commands run with `bash -c` at the repo root with
stdin closed, in their own process group so a timeout kills the whole tree.
"""
import json
import os
import signal
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import registry, trace
from .model import Prd, Step

EXIT = {"done": 0, "refused": 1, "usage": 2, "human": 3, "failed": 4}
TAIL = 4096
DEFAULT_TIMEOUT = 600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {(proc.stderr.strip().splitlines() or ['no output'])[0]}")
    return proc.stdout


def step_command(step: Step) -> str:
    """What `plan` shows for an agent step: its command, or `tests <levels>`."""
    return step.run if step.run is not None else "tests " + ", ".join(step.tests or [])


def plan_steps(prd: Prd, until: str | None) -> list[Step]:
    """The steps a run takes: all of them, or through the last step on `until`."""
    steps = list(prd.operations.steps)
    if until is None:
        return steps
    ends = [i for i, s in enumerate(steps) if s.env == until]
    if not ends:
        envs = list(dict.fromkeys(s.env for s in steps if s.env))
        raise ValueError(f"no step runs on {until}; environments with steps: {', '.join(envs) or 'none'}")
    return steps[: ends[-1] + 1]


def preflight(prd: Prd, repo_root: Path) -> list[str]:
    """Reasons a run must not start; empty when clear."""
    reasons: list[str] = []
    if _git(repo_root, "status", "--porcelain", "--untracked-files=no").strip():
        reasons.append("the tracked tree has changes")
    if registry.run(prd):
        reasons.append("prd_lint has findings")
    if trace.run_trace(prd, repo_root, None):
        reasons.append("prd_trace has findings")
    for b in prd.blocks:
        if b.status == "built":
            reasons.append(f"{b.id} is built; its tests have not passed (run /prd-build)")
    return reasons


def log_dir(repo_root: Path) -> Path:
    common = Path(_git(repo_root, "rev-parse", "--git-common-dir").strip())
    if not common.is_absolute():
        common = repo_root / common
    return common.resolve() / "prd-toolkit" / "deploys"


def new_run_id(repo_root: Path, until: str | None) -> str:
    base = f"{_now().astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{until or 'all'}"
    taken = log_dir(repo_root)
    taken.mkdir(parents=True, exist_ok=True)
    run_id, n = base, 1
    while True:
        try:
            with open(taken / f"{run_id}.jsonl", "x", encoding="utf-8"):
                return run_id  # the empty log reserves the id
        except FileExistsError:
            n += 1
            run_id = f"{base}-{n}"


def _log_path(repo_root: Path, run_id: str) -> Path:
    return log_dir(repo_root) / f"{run_id}.jsonl"


def append(repo_root: Path, run_id: str, record: dict) -> None:
    path = _log_path(repo_root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def start_run(prd: Prd, repo_root: Path, run_id: str, until: str | None) -> None:
    """Write the log header: the commit and PRD version the run is for."""
    append(repo_root, run_id, {
        "kind": "header", "run": run_id, "head": _git(repo_root, "rev-parse", "HEAD").strip(),
        "version": prd.frontmatter.get("version"), "until": until, "started": _iso(),
    })


def read_log(repo_root: Path, run_id: str) -> list[dict]:
    text = _log_path(repo_root, run_id).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _iso() -> str:
    return _now().astimezone(timezone.utc).isoformat()


def _tail(data: bytes) -> str:
    return data[-TAIL:].decode("utf-8", errors="replace")


def _execute(cmd: str, repo_root: Path, extra_env: dict[str, str], timeout: int) -> dict:
    """Run `cmd`; returns exit, full stdout bytes, stderr tail text and whether it timed out."""
    proc = subprocess.Popen(
        ["bash", "-c", cmd], cwd=repo_root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**{k: v for k, v in os.environ.items() if k != "TEST_ENV"}, **extra_env}, start_new_session=True,
    )
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            out, err = b"", b""
    stderr = _tail(err)
    if timed_out:
        stderr += ("" if not stderr or stderr.endswith("\n") else "\n") + f"timed out after {timeout} s"
    return {"exit": proc.returncode, "out": out, "stdout": _tail(out), "stderr": stderr, "timed_out": timed_out}


def _prints_ok(out: bytes, text: str) -> bool:
    want = text.strip()
    return any(line.strip() == want for line in out.decode("utf-8", errors="replace").splitlines())


def _agent_record(step: Step, repo_root: Path, timeout: int) -> dict:
    env = {"PRD_ENV": step.env or ""}
    rec = {"command": step.run, "started": _iso()}
    first = _execute(step.run, repo_root, env, timeout)
    rec.update(exit=first["exit"], stdout=first["stdout"], stderr=first["stderr"])
    ok = first["exit"] == 0 and not first["timed_out"]
    if ok and step.check is not None:
        c = _execute(step.check, repo_root, env, timeout)
        rec["check"] = {"command": step.check, "exit": c["exit"], "stdout": c["stdout"], "stderr": c["stderr"]}
        ok = c["exit"] == 0 and not c["timed_out"] and (step.prints is None or _prints_ok(c["out"], step.prints))
        if c["exit"] == 0 and not c["timed_out"] and not ok:
            rec["check"]["stderr"] = (c["stderr"] + f"\nno stdout line equals {step.prints!r}").lstrip("\n")
    rec["result"] = "pass" if ok else "fail"
    rec["ended"] = _iso()
    return rec


def _tests_records(prd: Prd, step: Step, repo_root: Path, timeout: int) -> list[dict]:
    """One record per level, stopping at the first failure."""
    recs = []
    if not step.tests:
        now = _iso()
        return [{"command": None, "exit": None, "stdout": "", "stderr": "tests step names no levels", "started": now, "ended": now, "result": "fail"}]
    for level in step.tests:
        command = prd.testing.commands.get(level)
        rec = {"level": level, "command": command, "started": _iso()}
        if not command:
            rec.update(exit=None, stdout="", stderr=f"no Harness command for level {level}", result="fail")
        else:
            r = _execute(command, repo_root, {"PRD_ENV": step.env or "", "TEST_ENV": step.env or ""}, timeout)
            rec.update(exit=r["exit"], stdout=r["stdout"], stderr=r["stderr"], result="pass" if r["exit"] == 0 and not r["timed_out"] else "fail")
        rec["ended"] = _iso()
        recs.append(rec)
        if rec["result"] == "fail":
            break
    return recs


def run_steps(prd: Prd, repo_root: Path, run_id: str, steps: list[Step], start: int, timeout: int) -> tuple[str, int]:
    """Run `steps` numbered `start` onward, logging and printing each. Returns (state, step number reached)."""
    reached = start
    for step in steps:
        if step.number < start:
            continue
        reached = step.number
        base = {"kind": "step", "step": step.number, "env": step.env, "actor": step.actor}
        if step.actor == "human":
            now = _iso()
            append(repo_root, run_id, {**base, "command": None, "exit": None, "stdout": "", "stderr": "", "started": now, "ended": now, "result": "human"})
            print(f"step {step.number} human {step.env}: human", flush=True)
            return "human", step.number
        try:
            recs = _tests_records(prd, step, repo_root, timeout) if step.tests is not None else [_agent_record(step, repo_root, timeout)]
        except Exception as e:  # a command could not even start: record it as a failed step
            now = _iso()
            recs = [{"command": step_command(step), "exit": None, "stdout": "", "stderr": f"{type(e).__name__}: {e}", "started": now, "ended": now, "result": "fail"}]
        try:
            for rec in recs:
                append(repo_root, run_id, {**base, **rec})
        except Exception as e:
            print(f"prd_deploy: could not write the log: {e}", file=sys.stderr)
            recs = [{"result": "fail"}]
        passed = bool(recs) and all(r["result"] == "pass" for r in recs)
        print(f"step {step.number} {step.actor} {step.env}: {'pass' if passed else 'fail'}", flush=True)
        if not passed:
            if step.rollback:
                print(f"rollback: `{step.rollback}`", flush=True)
            return "failed", step.number
    return "done", reached
