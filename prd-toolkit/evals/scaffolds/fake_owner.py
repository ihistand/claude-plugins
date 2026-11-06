"""A stand-in owner for the decision-inbox evals (0.8.2): it answers one gate once the session is waiting on it, then
closes the inbox, as an owner who clicks and closes the tab.

Usage (from a case's scaffold.sh, in the eval workspace):
    python3 -B <this file> <repo> <slug> <gate id> <after s> <cap s> [-- <answer flags>...]

It detaches at once (the scaffold returns) and logs to `<git common dir>/fake-owner.log`. It waits until the
session ran `prd_gates.py serve` (`<git common dir>/prd-inbox-<slug>.json` names a live process) or runs a
`prd_gates.py wait` in <repo> (the eval sandbox may refuse the inbox its port, so the owner then answers through the
CLI, as `wait` allows), then <after> seconds more, then runs the vendored
`prd_gates.py answer docs/prd/<slug> <gate id> <answer flags>` (no flags: it answers nothing), then sends SIGTERM to
the inbox. A session that neither serves nor waits gets no answer.

At <cap> seconds from the start it gives up: it stops any inbox of the slug and every `prd_gates.py wait` whose
working directory is <repo>, so a session waiting on a gate nobody will answer still ends inside its eval timeout.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def _common(repo: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo,
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _inbox_pid(lock: Path) -> int | None:
    try:
        pid = json.loads(lock.read_text(encoding="utf-8")).get("pid")
    except (OSError, ValueError, AttributeError):
        return None
    return pid if isinstance(pid, int) and pid > 0 and _alive(pid) else None


def _waits_in(repo: Path) -> list[int]:
    """The pids of `prd_gates.py wait` processes whose working directory is the repo."""
    found = subprocess.run(["pgrep", "-f", r"prd_gates\.py.* wait "], capture_output=True, text=True).stdout.split()
    mine = []
    for pid in found:
        cwd = subprocess.run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"], capture_output=True, text=True).stdout
        paths = [line[1:] for line in cwd.splitlines() if line.startswith("n")]
        if paths and os.path.realpath(paths[0]) == os.path.realpath(repo):
            mine.append(int(pid))
    return mine


def _term(pid: int, log) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"{time.strftime('%H:%M:%S')} SIGTERM {pid}", file=log, flush=True)
    except OSError as e:
        print(f"{time.strftime('%H:%M:%S')} SIGTERM {pid} failed: {e}", file=log, flush=True)


def run(repo: Path, slug: str, gate: str, after: float, cap: float, flags: list[str], log) -> None:
    lock = _common(repo) / f"prd-inbox-{slug}.json"
    start, seen = time.monotonic(), None
    print(f"{time.strftime('%H:%M:%S')} watching {lock} for {gate}", file=log, flush=True)
    while time.monotonic() - start < cap:
        pid = _inbox_pid(lock)
        if seen is None and (pid or _waits_in(repo)):
            seen = time.monotonic()
            print(f"{time.strftime('%H:%M:%S')} session waiting: inbox pid {pid}", file=log, flush=True)
        if seen is not None and time.monotonic() - seen >= after:
            if flags:
                r = subprocess.run(["uv", "run", "--quiet", "--script", ".prd-toolkit/prd_gates.py", "answer",
                                    f"docs/prd/{slug}", gate, *flags], cwd=repo, capture_output=True, text=True)
                print(f"{time.strftime('%H:%M:%S')} answer exit {r.returncode}: {r.stdout}{r.stderr}", file=log, flush=True)
                time.sleep(3)  # let `wait` read the log line before the inbox goes
            pid = _inbox_pid(lock)
            if pid:
                _term(pid, log)
            return
        time.sleep(1)
    print(f"{time.strftime('%H:%M:%S')} cap reached", file=log, flush=True)
    pid = _inbox_pid(lock)
    if pid:
        _term(pid, log)
    for w in _waits_in(repo):
        _term(w, log)


def main(argv: list[str]) -> None:
    flags = argv[argv.index("--") + 1:] if "--" in argv else []
    head = argv[:argv.index("--")] if "--" in argv else argv
    if len(head) != 5:
        sys.exit("usage: fake_owner.py <repo> <slug> <gate id> <after s> <cap s> [-- <answer flags>...]")
    repo, slug, gate, after, cap = Path(head[0]).resolve(), head[1], head[2], float(head[3]), float(head[4])
    log_path = _common(repo) / "fake-owner.log"
    if os.fork():  # the scaffold's process returns at once
        return
    os.setsid()
    if os.fork():
        os._exit(0)
    devnull = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(devnull, fd)
    with log_path.open("a", encoding="utf-8") as log:
        try:
            run(repo, slug, gate, after, cap, flags, log)
        except Exception as e:  # noqa: BLE001 - a stand-in owner never raises into anything
            print(f"{time.strftime('%H:%M:%S')} error: {e!r}", file=log, flush=True)
    os._exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
