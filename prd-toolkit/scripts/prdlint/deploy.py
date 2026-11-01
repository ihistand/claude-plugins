"""prd_deploy's engine: plan the runbook, check pre-flight, run steps, keep the log.

The only code that runs a runbook's commands. Commands run with `bash -c` at the repo root with
stdin closed, in their own process group so a timeout kills the whole tree.
"""
import json
import os
import re
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


def _agent_record(step: Step, repo_root: Path, timeout: int, mark) -> dict:
    env = {"PRD_ENV": step.env or ""}
    rec = {"command": step.run, "started": _iso()}
    mark(command=step.run)  # written before the command starts; if it fails the command does not run
    first = _execute(step.run, repo_root, env, timeout)
    rec.update(exit=first["exit"], stdout=first["stdout"], stderr=first["stderr"])
    ok = first["exit"] == 0 and not first["timed_out"]
    if ok and step.check is not None:
        mark(command=step.check, check=True)
        c = _execute(step.check, repo_root, env, timeout)
        rec["check"] = {"command": step.check, "exit": c["exit"], "stdout": c["stdout"], "stderr": c["stderr"]}
        ok = c["exit"] == 0 and not c["timed_out"] and (step.prints is None or _prints_ok(c["out"], step.prints))
        if c["exit"] == 0 and not c["timed_out"] and not ok:
            rec["check"]["stderr"] = (c["stderr"] + f"\nno stdout line equals {step.prints!r}").lstrip("\n")
    rec["result"] = "pass" if ok else "fail"
    rec["ended"] = _iso()
    return rec


def _tests_records(prd: Prd, step: Step, repo_root: Path, timeout: int, mark) -> list[dict]:
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
            mark(level=level, command=command)
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
        def mark(**extra):
            append(repo_root, run_id, {"kind": "start", "step": step.number, "env": step.env, **extra, "at": _iso()})

        try:
            recs = _tests_records(prd, step, repo_root, timeout, mark) if step.tests is not None else [_agent_record(step, repo_root, timeout, mark)]
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


class Refused(Exception):
    """A resume or rollback condition failed; `reasons` are printed one per `refused:` line."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def check_run_id(run_id: str) -> str:
    """A run id names a log file under the deploys folder, so it may not name a path."""
    if not RUN_ID.fullmatch(run_id):
        raise ValueError(f"not a run id: {run_id!r}")
    return run_id


RUN_ID = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*")


def _load_log(repo_root: Path, run_id: str) -> tuple[dict, list[dict]]:
    """The header and the records after it; ValueError when the run has no usable log."""
    check_run_id(run_id)
    try:
        recs = read_log(repo_root, run_id)
    except FileNotFoundError:
        raise ValueError(f"no log for run {run_id}") from None
    except (ValueError, OSError) as e:
        raise ValueError(f"cannot read the log of run {run_id}: {e}") from None
    if not recs or recs[0].get("kind") != "header":
        raise ValueError(f"the log of run {run_id} has no header")
    return recs[0], recs[1:]


def _last_step(recs: list[dict]) -> dict | None:
    steps = [r for r in recs if r.get("kind") == "step"]
    return steps[-1] if steps else None


def _confirmed(recs: list[dict], step: int) -> bool:
    return any(r.get("kind") == "confirm" and r.get("step") == step for r in recs)


def confirm(repo_root: Path, run_id: str, step: int, reply: str) -> None:
    """Record the reply to the human step the run stopped at. ValueError (a usage error) when it cannot."""
    _, recs = _load_log(repo_root, run_id)
    last = _last_step(recs)
    if last is None or last.get("step") != step or last.get("result") != "human":
        raise ValueError(f"step {step} is not the human step this run stopped at")
    if not reply.strip():
        raise ValueError("the reply is empty")
    if _confirmed(recs, step):
        raise ValueError(f"step {step} already has a confirm record")
    append(repo_root, run_id, {"kind": "confirm", "step": step, "reply": reply, "at": _iso()})


def _moved(prd: Prd, repo_root: Path, header: dict) -> list[str]:
    """Why the run no longer matches the repo; empty when it still does. Check this before reading the runbook."""
    reasons = []
    if _git(repo_root, "rev-parse", "HEAD").strip() != header.get("head"):
        reasons.append("HEAD moved since the run started")
    if prd.frontmatter.get("version") != header.get("version"):
        reasons.append("the PRD version changed since the run started")
    if _git(repo_root, "status", "--porcelain", "--untracked-files=no").strip():
        reasons.append("the tracked tree has changes")  # the runbook is read from the working tree
    return reasons


def _used_or_unfinished(recs: list[dict]) -> list[str]:
    """A confirm is used once, and a command that was started is never run again."""
    reasons = []
    last_confirm = {}
    for i, r in enumerate(recs):
        if r.get("kind") == "confirm":
            last_confirm[r.get("step")] = i
    for n, i in last_confirm.items():
        if any(r.get("kind") == "resume" and r.get("step") == n for r in recs[i + 1:]):
            reasons.append(f"step {n}'s confirm was already used")
    for i, r in enumerate(recs):
        if r.get("kind") == "start" and not r.get("rollback") and not any(x.get("kind") == "step" for x in recs[i + 1:]):
            reasons.append(f"step {r.get('step')} started and did not finish; check the environment, then start a new run")
            break
    return list(dict.fromkeys(reasons))


def begin_resume(repo_root: Path, run_id: str, step: int) -> None:
    """Use up the confirm of `step`; nothing may run if this fails."""
    append(repo_root, run_id, {"kind": "resume", "step": step, "at": _iso()})


def resume_problems(prd: Prd, repo_root: Path, run_id: str) -> list[str]:
    """Reasons the run may not continue; empty when it may. ValueError when the run has no usable log."""
    header, recs = _load_log(repo_root, run_id)
    reasons = _moved(prd, repo_root, header)
    reasons += _used_or_unfinished(recs)
    failed = next((r for r in recs if r.get("kind") == "step" and r.get("result") == "fail"), None)
    last = _last_step(recs)
    if failed is not None:
        reasons.append(f"step {failed['step']} failed; a failed run ends (start a new run)")
    elif last is None:
        reasons.append("the run has no step records")
    elif last.get("result") == "human":
        if not _confirmed(recs, last["step"]):
            reasons.append(f"step {last['step']} has no confirm record")
    else:
        try:
            final = plan_steps(prd, header.get("until"))[-1].number
        except (ValueError, IndexError):
            final = None
        reasons.append("the run is done" if last["step"] == final else f"the run did not stop at a human step (last step {last['step']})")
    return reasons


def resume_point(repo_root: Path, run_id: str) -> tuple[int, str | None]:
    """The confirmed human step to continue after, and the run's `until`."""
    header, recs = _load_log(repo_root, run_id)
    last = _last_step(recs)
    return (last["step"] if last else 0), header.get("until")


def rollback(prd: Prd, repo_root: Path, run_id: str, step: int, timeout: int) -> int:
    """Run failed step `step`'s Rollback once and log it; returns the command's exit code (-1 when it never ran to an exit).

    ValueError for a usage problem, Refused when HEAD or the PRD version moved.
    """
    header, recs = _load_log(repo_root, run_id)
    last = _last_step(recs)
    if last is None or last.get("step") != step or last.get("result") != "fail":
        raise ValueError(f"step {step} is not the failed step of this run")
    reasons = _moved(prd, repo_root, header)
    if reasons:
        raise Refused(reasons)
    target = next((s for s in prd.operations.steps if s.number == step), None)
    if target is None or not target.rollback:
        raise ValueError(f"step {step} has no Rollback")
    if any(r.get("kind") == "start" and r.get("rollback") and r.get("step") == step for r in recs):
        raise ValueError(f"step {step}'s rollback was already started")
    if any(r.get("kind") == "rollback" and r.get("step") == step for r in recs):
        raise ValueError(f"step {step} was already rolled back")
    started = _iso()
    try:
        append(repo_root, run_id, {"kind": "start", "step": step, "env": target.env, "rollback": True, "command": target.rollback, "at": started})
    except Exception as e:
        raise ValueError(f"could not record the rollback start, so it was not run: {e}") from None
    try:
        r = _execute(target.rollback, repo_root, {"PRD_ENV": target.env or ""}, timeout)
        rec = {"exit": r["exit"], "stdout": r["stdout"], "stderr": r["stderr"], "ok": r["exit"] == 0 and not r["timed_out"]}
    except Exception as e:  # the command could not even start
        rec = {"exit": None, "stdout": "", "stderr": f"{type(e).__name__}: {e}", "ok": False}
    ok = rec.pop("ok")
    append(repo_root, run_id, {"kind": "rollback", "step": step, "command": target.rollback, **rec, "started": started, "ended": _iso()})
    print(f"rollback step {step} {target.env}: {'pass' if ok else 'fail'}", flush=True)
    return 0 if ok else (rec["exit"] if rec["exit"] not in (None, 0) else -1)
