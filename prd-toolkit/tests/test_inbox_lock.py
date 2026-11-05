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
