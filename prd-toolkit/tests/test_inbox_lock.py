"""The inbox lock file (0.8.2): one live inbox per PRD, found from every worktree, gone when the inbox stops."""
import contextlib
import io
import json
import os
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from inbox_fixture import PRD, make_inbox_repo
from prd_gates import main as gates_main
from prdlint import formserver, gates

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gates_main(list(argv))
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def made(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    m = make_inbox_repo(tmp_path)
    m["repo"], m["second"] = m["repo"].resolve(), m["second"].resolve()
    return m


class Serving:
    """`prd_gates.py serve --no-open` in its own process; `url` is its first stdout line."""

    def __init__(self, prd_dir, *extra):
        self.proc = subprocess.Popen([sys.executable, str(SCRIPTS / "prd_gates.py"), "serve", str(prd_dir), "--no-open", *extra],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        first = self.proc.stdout.readline()
        assert first.startswith("url="), (first, self.proc.stderr.read() if self.proc.poll() is not None else "")
        self.url = first.strip()[len("url="):]

    def stop(self):
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
        code = self.proc.wait(30)
        self.proc.stdout.close()
        self.proc.stderr.close()
        return code


@pytest.fixture
def serving():
    started = []

    def start(prd_dir, *extra):
        s = Serving(prd_dir, *extra)
        started.append(s)
        return s

    yield start
    for s in started:
        s.stop()


def dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def test_serve_writes_the_lock_and_refuses_a_second_inbox(made, serving):
    repo = made["repo"]
    s = serving(repo / PRD)
    path = gates.inbox_path(repo, "orders")
    assert path == gates.common_dir(repo) / "prd-inbox-orders.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert set(rec) == {"pid", "port", "token", "started", "prd"} and rec["prd"] == "orders" and rec["pid"] == s.proc.pid
    assert s.url == f"http://127.0.0.1:{rec['port']}/?token={rec['token']}"
    assert gates.live_inbox(repo, "orders") == rec
    code, out, err = call("serve", str(repo / PRD), "--no-open")
    assert code == 1 and out == "" and err.strip() == f"prd_gates: an inbox is already serving at {s.url}"
    assert json.loads(path.read_text(encoding="utf-8")) == rec


def test_rf4_the_second_worktree_finds_the_inbox_of_the_first(made, serving):
    s = serving(made["repo"] / PRD)
    rec = gates.live_inbox(made["second"], "orders")
    assert rec is not None and s.url.endswith(f"?token={rec['token']}")
    code, _, err = call("serve", str(made["second"] / PRD), "--no-open")
    assert code == 1 and s.url in err


def write_lock(repo, **rec):
    path = gates.inbox_path(repo, "orders")
    path.write_text(json.dumps({"pid": os.getpid(), "port": 9, "token": "t", "started": "2026-11-05T00:00:00Z", "prd": "orders", **rec}),
                    encoding="utf-8")
    return path


def test_a_dead_pid_is_not_live_and_its_file_goes(made, serving):
    repo = made["repo"]
    path = write_lock(repo, pid=dead_pid())
    assert gates.live_inbox(repo, "orders") is None and not path.exists()
    write_lock(repo, pid=dead_pid())
    s = serving(repo / PRD)
    assert json.loads(path.read_text(encoding="utf-8"))["pid"] == s.proc.pid


def test_a_wrong_token_is_not_live_and_its_file_goes(made, serving):
    repo = made["repo"]
    server, token = gates.make_inbox(repo / PRD)
    t = threading.Thread(target=formserver.run, args=(server,))
    t.start()
    try:
        path = gates.inbox_path(repo, "orders")
        assert gates.live_inbox(repo, "orders")["token"] == token
        write_lock(repo, port=server.server_address[1], token="wrong")
        assert gates.live_inbox(repo, "orders") is None and not path.exists()
        for bad in ("{not json", "[]", '{"pid": "x"}'):
            path.write_text(bad, encoding="utf-8")
            assert gates.live_inbox(repo, "orders") is None and not path.exists()
        s = serving(repo / PRD)
        assert json.loads(path.read_text(encoding="utf-8"))["pid"] == s.proc.pid
    finally:
        server.shutdown()
        t.join(10)
        server.server_close()
    assert path.exists()  # the in-process inbox removes only its own lock


def test_the_file_is_gone_after_serve_exits(made, serving):
    repo = made["repo"]
    s = serving(repo / PRD)
    path = gates.inbox_path(repo, "orders")
    assert path.exists()
    assert s.stop() == 3
    assert not path.exists()
    s = serving(repo / PRD, "--idle-minutes", "0.02")
    assert s.proc.wait(30) == 3 and not path.exists()


def test_make_inbox_writes_the_lock_and_removes_it_when_run_returns(made):
    repo = made["repo"]
    server, token = gates.make_inbox(repo / PRD, idle_minutes=0.01)
    path = gates.inbox_path(repo, "orders")
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec["token"] == token and rec["port"] == server.server_address[1] and rec["pid"] == os.getpid()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    try:
        assert formserver.run(server) == 3
    finally:
        server.server_close()
    assert not path.exists()


def test_gate_not_pending_is_refused_and_a_pending_one_is_in_the_url(made, serving):
    repo = made["repo"]
    code, out, err = call("serve", str(repo / PRD), "--no-open", "--gate", "error-class:E-999")
    assert code == 1 and out == "" and err.strip() == "prd_gates: error-class:E-999 is not pending"
    assert not gates.inbox_path(repo, "orders").exists()
    s = serving(repo / PRD, "--gate", "error-class:E-003")
    assert s.url.endswith("#gate=error-class:E-003") and "/?token=" in s.url


def test_a_port_in_use_is_exit_2_and_no_prd_is_exit_2(made, tmp_path):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        code, _, err = call("serve", str(made["repo"] / PRD), "--no-open", "--port", str(busy.getsockname()[1]))
    assert code == 2 and "in use" in err
    assert not gates.inbox_path(made["repo"], "orders").exists()
    assert call("serve", str(tmp_path), "--no-open")[0] == 2


def test_ping_answers_with_the_token_only(made):
    server, token = gates.make_inbox(made["repo"] / PRD)
    t = threading.Thread(target=formserver.run, args=(server,))
    t.start()
    try:
        import urllib.error
        import urllib.request

        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(f"{base}/ping?token={token}", timeout=10) as r:
            assert r.status == 200 and json.loads(r.read()) == {"ok": True}
        server.last = before = time.monotonic() - 50
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"{base}/ping?token=wrong", timeout=10)
        assert e.value.code == 403
        e.value.close()
        assert server.last == before
    finally:
        server.shutdown()
        t.join(10)
        server.server_close()


# --- proof fix wave: a `serve --gate` that finds a live inbox stands by and takes it over at the same URL ---

GATE = "error-class:E-003"
# The test-only hook: `prd_gates.py serve` run through this wrapper with STANDBY_POLL, STANDBY_LINGER and
# TAKEOVER_SETTLE shortened (argv[1] the scripts folder, argv[2] "poll,linger,settle"), so the suite stays fast.
HOOK = ("import sys; sys.path.insert(0, sys.argv.pop(1)); import prd_gates; "
        "prd_gates.STANDBY_POLL, prd_gates.STANDBY_LINGER, prd_gates.TAKEOVER_SETTLE = map(float, sys.argv.pop(1).split(',')); "
        "sys.exit(prd_gates.main(sys.argv[1:]))")


class Standby:
    """`prd_gates.py serve --no-open --gate <id>` through HOOK; its stdout and stderr lines are collected as they come."""

    def __init__(self, prd_dir, gate=GATE, timing="0.2,1.5,1.0", extra=()):
        self.proc = subprocess.Popen([sys.executable, "-c", HOOK, str(SCRIPTS), timing, "serve", str(prd_dir), "--no-open", "--gate", gate,
                                      *extra],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.out, self.err = [], []
        self.readers = [threading.Thread(target=self._read, args=(s, box), daemon=True)
                        for s, box in ((self.proc.stdout, self.out), (self.proc.stderr, self.err))]
        for r in self.readers:
            r.start()

    @staticmethod
    def _read(stream, box):
        for line in stream:
            box.append(line.rstrip("\n"))

    def until(self, test, timeout=20.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if test():
                return True
            time.sleep(0.05)
        return False

    def stop(self):
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
        code = self.proc.wait(30)
        for r in self.readers:
            r.join(5)
        return code


@pytest.fixture
def standby():
    started = []

    def start(prd_dir, *a, **kw):
        s = Standby(prd_dir, *a, **kw)
        started.append(s)
        return s

    yield start
    for s in started:
        s.stop()


def ping(port, token):
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/ping?token={token}", timeout=5) as r:
            return r.status
    except Exception:  # noqa: BLE001
        return None


def lock(repo):
    try:
        return json.loads(gates.inbox_path(repo, "orders").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def standing_by(s, url):
    assert s.until(lambda: s.err), "no line on stderr"
    assert s.err[0] == f"prd_gates: an inbox is already serving at {url}"
    time.sleep(0.6)  # a few standby ticks
    assert s.proc.poll() is None and s.out == []


def test_make_inbox_uses_a_given_token(made):
    server, token = gates.make_inbox(made["repo"] / PRD, token="given-token")
    try:
        assert token == "given-token" and server.token == "given-token"
        assert json.loads(gates.inbox_path(made["repo"], "orders").read_text(encoding="utf-8"))["token"] == "given-token"
    finally:
        server.server_close()


def test_standby_takes_over_at_the_same_url_when_the_inbox_stops(made, serving, standby):
    repo = made["repo"]
    a = serving(repo / PRD)
    rec = lock(repo)
    b = standby(repo / PRD)
    standing_by(b, a.url)
    assert a.stop() == 3
    assert b.until(lambda: b.out), (b.err, b.proc.poll())
    assert b.out == [f"url={a.url}#gate={GATE}"]
    assert ping(rec["port"], rec["token"]) == 200
    assert lock(repo)["pid"] == b.proc.pid and lock(repo)["token"] == rec["token"] and lock(repo)["port"] == rec["port"]
    assert b.proc.poll() is None
    assert b.stop() == 3 and lock(repo) is None


def test_two_standbys_one_takes_over_the_other_stands_by(made, serving, standby):
    repo = made["repo"]
    a = serving(repo / PRD)
    rec = lock(repo)
    b, c = standby(repo / PRD), standby(repo / PRD)
    standing_by(b, a.url)
    standing_by(c, a.url)
    assert a.stop() == 3
    assert b.until(lambda: (lock(repo) or {}).get("pid") in (b.proc.pid, c.proc.pid) and ping(rec["port"], rec["token"]) == 200)
    time.sleep(2.5)  # past the loser's settle time: it must still be standing by
    holder = lock(repo)["pid"]
    won, lost = (b, c) if holder == b.proc.pid else (c, b)
    assert won.out == [f"url={a.url}#gate={GATE}"] and lost.out == []
    assert won.proc.poll() is None and lost.proc.poll() is None
    assert len(lost.err) == 1  # the already-serving line only
    # round 1: the hand-off chains: the winner stops, and the other takes over at the same URL in its turn
    assert won.stop() == 3
    assert lost.until(lambda: lost.out), (lost.err, lost.proc.poll())
    assert lost.out == [f"url={a.url}#gate={GATE}"]
    assert ping(rec["port"], rec["token"]) == 200 and lock(repo)["pid"] == lost.proc.pid
    assert lost.proc.poll() is None


def test_standby_exits_1_after_the_linger_once_its_gate_is_answered(made, serving, standby):
    from prdlint import model

    repo = made["repo"]
    a = serving(repo / PRD)
    b = standby(repo / PRD)
    standing_by(b, a.url)
    done = gates.answer(model.load(repo / PRD), repo, GATE, "yes", by="cli")
    assert done["result"]["exit"] == 0
    answered = time.monotonic()
    assert b.proc.wait(20) == 1
    assert time.monotonic() - answered >= 1.5  # the linger: `wait` reports first
    assert b.err == [f"prd_gates: an inbox is already serving at {a.url}", f"prd_gates: {GATE} is not pending"]
    assert b.out == [] and a.proc.poll() is None


def test_standby_exits_2_when_the_port_is_held_after_the_inbox_stops(made, standby):
    # The inbox runs in this process, then stops serving: its lock goes, but its socket stays bound, so the port is held
    # by a socket that is no inbox (nothing answers on it and no lock names it) when the standby tries to take over.
    repo = made["repo"]
    server, token = gates.make_inbox(repo / PRD)
    port = server.server_address[1]
    t = threading.Thread(target=formserver.run, args=(server,))
    t.start()
    try:
        b = standby(repo / PRD)
        standing_by(b, f"http://127.0.0.1:{port}/?token={token}")
        server.shutdown()
        t.join(10)
        assert lock(repo) is None
        assert b.proc.wait(20) == 2
        assert b.until(lambda: len(b.err) == 2)
        assert b.err[1].startswith(f"prd_gates: cannot take over the inbox at port {port}: ") and len(b.err[1]) > len(f"... port {port}: ")
        assert b.out == []
    finally:
        server.shutdown()  # returns at once when the server already stopped
        t.join(10)
        server.server_close()


def test_sigterm_while_standing_by_exits_3(made, serving, standby):
    a = serving(made["repo"] / PRD)
    b = standby(made["repo"] / PRD)
    standing_by(b, a.url)
    assert b.stop() == 3 and b.out == []
    assert lock(made["repo"])["pid"] == a.proc.pid  # the inbox it stood behind is untouched


# --- fix round 1: a standby's lifetime bound, the settle on its URL, a PRD that fails to load ---

def test_a_standby_stops_after_its_idle_bound_as_an_idle_inbox_does(made, serving, standby):
    # an idle inbox (serve --idle-minutes) prints no line of its own and exits 3; a standby bounded the same way does too
    a = serving(made["repo"] / PRD)
    b = standby(made["repo"] / PRD, extra=("--idle-minutes", "0.03"))
    assert b.until(lambda: b.err)
    begun = time.monotonic()
    assert b.proc.wait(20) == 3
    assert time.monotonic() - begun >= 1.0  # about 1.8 s of standing by, not at once
    assert b.until(lambda: not any(r.is_alive() for r in b.readers))
    assert b.err == [f"prd_gates: an inbox is already serving at {a.url}"] and b.out == []
    assert a.proc.poll() is None and lock(made["repo"])["pid"] == a.proc.pid


def test_a_standby_whose_url_still_answers_keeps_standing_by(made, standby):
    # the inbox serves on, but its lock is gone (as when a slow ping dropped it): the bind fails, and the URL answers
    repo = made["repo"]
    server, token = gates.make_inbox(repo / PRD)
    port = server.server_address[1]
    t = threading.Thread(target=formserver.run, args=(server,))
    t.start()
    try:
        b = standby(repo / PRD)
        standing_by(b, f"http://127.0.0.1:{port}/?token={token}")
        gates.inbox_path(repo, "orders").unlink()
        time.sleep(3.0)  # several ticks, each past the 1 s settle time
        assert b.proc.poll() is None and b.out == [] and len(b.err) == 1
    finally:
        server.shutdown()
        t.join(10)
        server.server_close()


def test_a_takeover_while_the_prd_fails_to_load_keeps_standing_by(made, serving, standby):
    repo = made["repo"]
    a = serving(repo / PRD)
    b = standby(repo / PRD)
    standing_by(b, a.url)
    prd_md = repo / PRD / "prd.md"
    moved = prd_md.with_name("prd.md.away")
    prd_md.rename(moved)
    try:
        assert a.stop() == 3
        time.sleep(2.0)  # several takeover attempts, each with no PRD to load
        assert b.proc.poll() is None and b.out == [] and len(b.err) == 1, b.err
    finally:
        moved.rename(prd_md)
    assert b.until(lambda: b.out), (b.err, b.proc.poll())  # the next look takes over
    assert b.out == [f"url={a.url}#gate={GATE}"]
