"""prd_gates.py wait and the answer log (0.8.2): the owner's answer, from any client, reaches the waiting skill."""
import contextlib
import io
import json
import threading
import time
from pathlib import Path

from prd_gates import main as gates_main
from prdlint import gates, model
from test_change_approve import recorded, repo  # noqa: F401  (fixtures)
from test_gates_answer import QUOTED, adopt, add_errors, branch
from test_gates_list import PRD, entry


def load(repo):
    return model.load(repo / PRD)


def answer(repo, gate, reply, **kw):
    return gates.answer(load(repo), repo, gate, reply, **kw)


def waiting(repo, gate, **kw):
    """Start wait_gate in a thread; return (thread, box)."""
    box = {}

    def run():
        box["r"] = gates.wait_gate(repo / PRD, gate, poll=0.05, **kw)

    t = threading.Thread(target=run)
    t.start()
    time.sleep(0.4)
    return t, box


def test_an_answer_reaches_wait_verbatim_with_one_log_line(repo):
    add_errors(repo, entry(3, "code bug"))
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    answer(repo, "error-class:E-003", QUOTED, by="cli")
    t.join(25)
    code, out = box["r"]
    assert code == 0
    assert out["reply"] == QUOTED and out["by"] == "cli" and out["choice"] == "confirm" and out["gate"] == "error-class:E-003"
    assert out["worktree"] == str(repo.resolve())
    assert len(gates.read_log(repo)) == 1


def test_a_refused_answer_writes_no_line(repo):
    add_errors(repo, entry(3, "code bug"))
    try:
        answer(repo, "error-class:E-003", "  ")
    except gates.Refused:
        pass
    else:
        raise AssertionError("not refused")
    assert gates.read_log(repo) == [] and not gates.log_path(repo).exists()


def test_a_gate_answered_before_wait_starts_exits_1_at_once(repo):
    add_errors(repo, entry(3, "code bug"))
    answer(repo, "error-class:E-003", "ok")
    time.sleep(1.1)
    start = time.monotonic()
    code, out = gates.wait_gate(repo / PRD, "error-class:E-003", poll=0.05)
    assert code == 1 and out["choice"] is None and time.monotonic() - start < 1


def test_a_gate_that_disappears_unanswered_exits_1(repo):
    add_errors(repo, entry(3, "code bug"))
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    errors = repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8").replace("E-003", "E-099"), encoding="utf-8")
    t.join(25)
    code, out = box["r"]
    assert code == 1 and out["choice"] is None and out["reply"] is None


def test_timeout_on_a_pending_gate_exits_3(repo):
    add_errors(repo, entry(3, "code bug"))
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gates_main(["wait", str(repo / PRD), "error-class:E-003", "--timeout", "1"])
    assert code == 3 and out.getvalue() == ""


def test_approval_changes_outcome(recorded):
    gate = f"approval:{branch(recorded)}"
    t, box = waiting(recorded, gate, timeout=20)
    answer(recorded, gate, "tighten FR-2", choice="changes", by="form")
    t.join(25)
    code, out = box["r"]
    assert code == 0 and out["choice"] == "changes" and out["reply"] == "tighten FR-2" and out["by"] == "form"


def test_adoption_logs_done_only(tmp_path):
    repo, prd, p, items = adopt(tmp_path)
    for i in items:
        d = {"requirement": "confirm", "bug": "intended", "question": "answer", "marker": "answer"}[i.kind]
        gates.answer(model.load(prd), repo, "adoption:notes", "ok", item=i.id, choice=d)
    assert gates.read_log(repo) == []
    gates.answer(model.load(prd), repo, "adoption:notes", "Done (form)", choice="done", by="form")
    log = gates.read_log(repo)
    assert len(log) == 1 and log[0]["choice"] == "done" and log[0]["gate"] == "adoption:notes" and log[0]["by"] == "form"


def test_wait_starts_with_no_log_file(repo):
    add_errors(repo, entry(3, "code bug"))
    assert not gates.log_path(repo).exists()
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    answer(repo, "error-class:E-003", "yes")
    t.join(25)
    assert box["r"][0] == 0 and gates.log_path(repo).exists()


def test_log_line_shape_and_a_junk_line_is_skipped(repo):
    add_errors(repo, entry(3, "code bug"))
    answer(repo, "error-class:E-003", "yes")
    with gates.log_path(repo).open("a", encoding="utf-8") as f:
        f.write("not json\n")
    log = gates.read_log(repo)
    assert len(log) == 1
    assert list(log[0]) == ["at", "prd", "worktree", "gate", "choice", "reply", "by"] and log[0]["prd"] == "orders"
    assert gates.log_path(repo).parent == gates.common_dir(repo) and gates.common_dir(repo).is_absolute()


def test_cli_wait_prints_one_outcome_document(repo):
    add_errors(repo, entry(3, "code bug"))
    answer(repo, "error-class:E-003", "yes")  # answered before: exit 1, still a document
    time.sleep(1.1)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = gates_main(["wait", str(repo / PRD), "error-class:E-003"])
    doc = json.loads(out.getvalue())
    assert code == 1 and list(doc)[:2] == ["interface", "kind"] and doc["kind"] == "gates.outcome"
    assert list(doc)[2:] == ["gate", "worktree", "choice", "reply", "by", "at"]


def test_an_answer_in_the_same_second_as_the_start_is_returned(repo, monkeypatch):
    add_errors(repo, entry(3, "code bug"))
    monkeypatch.setattr(gates, "_now", lambda: "2026-11-05T12:00:00Z")
    answer(repo, "error-class:E-003", "just before")
    code, out = gates.wait_gate(repo / PRD, "error-class:E-003", poll=0.05)
    assert code == 0 and out["reply"] == "just before"


# --- Task 5 fix round 1: the answering marker closes the race between the owner's write and its log line ---

def slow_owner(monkeypatch, delay=2.5, exit_code=0, leave=True):
    """The error-class owner writes (the gate leaves the list), then takes `delay` s before it returns `exit_code`."""
    real = gates.ANSWERERS["error-class"]

    def owner(prd, gate, reply, **kw):
        out = real(prd, gate, reply, **kw) if leave else {"stdout": [], "exit": 0}
        time.sleep(delay)
        return {**out, "exit": exit_code}

    monkeypatch.setitem(gates.ANSWERERS, "error-class", owner)


def test_a_slow_owner_still_reaches_wait_with_its_choice(repo, monkeypatch):
    add_errors(repo, entry(3, "code bug"))
    slow_owner(monkeypatch, delay=gates.GRACE + 1.5)
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    answer(repo, "error-class:E-003", "slow but sure", by="form")
    t.join(25)
    code, out = box["r"]
    assert code == 0 and out["choice"] == "confirm" and out["reply"] == "slow but sure"
    assert not any(gates.answering_dir(repo).glob("*"))  # the marker is gone after the log line


def test_the_marker_is_keyed_on_the_worktree_and_gate_and_holds_the_pid(repo, monkeypatch):
    add_errors(repo, entry(3, "code bug"))
    seen = {}
    real = gates.ANSWERERS["error-class"]

    def owner(prd, gate, reply, **kw):
        path = gates.answering_path(repo, "error-class:E-003")
        seen["exists"], seen["pid"] = path.is_file(), path.read_text(encoding="utf-8").strip()
        return real(prd, gate, reply, **kw)

    monkeypatch.setitem(gates.ANSWERERS, "error-class", owner)
    answer(repo, "error-class:E-003", "yes")
    import hashlib, os
    key = hashlib.sha1(f"{repo.resolve()}\0error-class:E-003".encode()).hexdigest()
    assert gates.answering_path(repo, "error-class:E-003").name == key
    assert seen == {"exists": True, "pid": str(os.getpid())}
    # a deploy step is repo-wide, as its log match is: keyed on the gate id alone
    assert gates.answering_path(repo, "deploy-step:r:3").name == hashlib.sha1("\0deploy-step:r:3".encode()).hexdigest()


def test_a_dead_pid_marker_does_not_hang_wait(repo):
    import subprocess, sys
    add_errors(repo, entry(3, "code bug"))
    dead = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True).stdout.strip()
    path = gates.answering_path(repo, "error-class:E-003")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dead + "\n", encoding="utf-8")
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    start = time.monotonic()
    errors = repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8").replace("E-003", "E-099"), encoding="utf-8")
    t.join(25)
    assert box["r"][0] == 1 and time.monotonic() - start < gates.GRACE + 2


def test_a_failed_owner_removes_the_marker_and_wait_goes_on_as_today(repo, monkeypatch):
    add_errors(repo, entry(3, "code bug"))
    slow_owner(monkeypatch, delay=0.5, exit_code=1, leave=False)  # nothing written: the gate stays pending
    t, box = waiting(repo, "error-class:E-003", timeout=3)
    answer(repo, "error-class:E-003", "fails")
    assert not any(gates.answering_dir(repo).glob("*"))
    t.join(10)
    assert box["r"][0] == 3  # still pending: wait keeps waiting, as today


def test_a_failed_owner_whose_gate_left_exits_1(repo, monkeypatch):
    add_errors(repo, entry(3, "code bug"))
    slow_owner(monkeypatch, delay=0.5, exit_code=1)  # it wrote, then failed: no log line
    t, box = waiting(repo, "error-class:E-003", timeout=20)
    answer(repo, "error-class:E-003", "fails late")
    t.join(25)
    assert box["r"][0] == 1 and box["r"][1]["choice"] is None
    assert not any(gates.answering_dir(repo).glob("*"))
