"""formserver: the token, body cap, CSP, run loop and page assembly shared by the confirm form and the inbox."""
import json
import os
import signal
import stat
import threading
import urllib.error
import urllib.request

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, formserver, model


class State:
    def __init__(self):
        self.hits = 0


class H(formserver.Handler):
    def route(self, method, route, query):
        self.server.state.hits += 1
        if method == "GET":
            self.send_page("<html>x</html>")
        else:
            self.send_json(200, self.body_json())


def start(idle_minutes=120):
    state = State()
    server, token = formserver.make_server(H, idle_minutes=idle_minutes, state=state)
    out = []
    t = threading.Thread(target=lambda: out.append(formserver.run(server)))
    t.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    return server, token, base, state, t, out


def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read(), e.headers
        finally:
            e.close()


@pytest.fixture
def live():
    server, token, base, state, t, out = start()
    yield server, token, base, state, t, out
    server.shutdown()
    t.join(10)
    server.server_close()


def test_no_token_and_wrong_token_are_403_and_change_nothing(live):
    server, token, base, state, *_ = live
    assert fetch(base + "/x")[0] == 403
    assert fetch(base + "/x?token=wrong")[0] == 403
    assert fetch(base + "/x?token=wrong", b"{}")[0] == 403
    assert state.hits == 0
    assert fetch(f"{base}/x?token={token}")[0] == 200 and state.hits == 1


def test_binds_loopback_and_token_is_urlsafe(live):
    server, token, *_ = live
    assert server.server_address[0] == "127.0.0.1"
    assert len(token) == 32 and token.replace("-", "").replace("_", "").isalnum()


def test_page_carries_the_csp(live):
    _, token, base, *_ = live
    status, body, headers = fetch(f"{base}/x?token={token}")
    assert status == 200 and headers["Content-Security-Policy"] == formserver.CSP
    assert body == b"<html>x</html>"


def test_body_cap_is_413_and_json_roundtrips(live):
    _, token, base, state, *_ = live
    assert fetch(f"{base}/x?token={token}", b"x" * (formserver.MAX_BODY + 1))[0] == 413
    assert formserver.MAX_BODY == 1024 * 1024
    assert fetch(f"{base}/x?token={token}", b"{nope")[0] == 400
    status, body, _ = fetch(f"{base}/x?token={token}", json.dumps({"a": 1}).encode())
    assert status == 200 and json.loads(body) == {"a": 1}


def test_idle_returns_3():
    server, _, _, _, t, out = start(idle_minutes=0.05 / 60)
    t.join(15)
    server.server_close()
    assert out == [3]


def test_sigterm_from_a_thread_returns_3():
    def stop(*_):
        raise KeyboardInterrupt  # what prd_confirm.py's handler does

    server, _ = formserver.make_server(H, state=State())
    old = signal.signal(signal.SIGTERM, stop)
    timer = threading.Timer(0.2, lambda: os.kill(os.getpid(), signal.SIGTERM))
    timer.start()
    try:
        assert formserver.run(server) == 3
    finally:
        signal.signal(signal.SIGTERM, old)
        timer.join()
        server.server_close()


def test_finish_returns_0():
    server, _, _, _, t, out = start()
    server.finish()
    t.join(10)
    server.server_close()
    assert out == [0]


def test_assemble_replaces_only_the_include_line(tmp_path):
    (tmp_path / "p.html").write_text("<p>panel</p>\n  <b>x</b>\n", encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_bytes(b"<a>\r\n   <!-- include: p.html -->\n<!-- include: p.html --> tail\n<z>\n")
    assert formserver.assemble(page) == "<a>\r\n<p>panel</p>\n  <b>x</b>\n<!-- include: p.html --> tail\n<z>\n"


def test_assemble_honours_include_dir_and_missing_raises(tmp_path):
    inc = tmp_path / "inc"
    inc.mkdir()
    (inc / "p.html").write_text("P", encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("a\n<!-- include: p.html -->\nb\n", encoding="utf-8")
    assert formserver.assemble(page, inc) == "a\nP\nb\n"
    with pytest.raises(formserver.PageError, match="include p.html not found"):
        formserver.assemble(page)


def test_includes_do_not_nest(tmp_path):
    (tmp_path / "p.html").write_text("<!-- include: q.html -->", encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("<!-- include: p.html -->\n", encoding="utf-8")
    assert "<!-- include: q.html -->" in formserver.assemble(page)


def test_write_json_atomic_mode_and_no_temp(tmp_path):
    f = tmp_path / "a.json"
    formserver.write_json_atomic(f, {"k": 1}, mode=0o600)
    assert json.loads(f.read_text()) == {"k": 1}
    assert stat.S_IMODE(f.stat().st_mode) == 0o600
    assert [p.name for p in tmp_path.iterdir()] == ["a.json"]


def test_confirm_reexports():
    assert confirm.CSP == formserver.CSP and confirm.MAX_BODY == formserver.MAX_BODY


def test_confirm_form_answer_keeps_summaries_and_reopens_done(tmp_path):
    repo, prd_dir = make_confirm_repo(tmp_path)
    prd = model.load(prd_dir)
    items = confirm.build_items(prd, "notes")
    path = confirm.answers_path(repo, "notes")
    confirm.save_answers(path, {"prd": "notes", "area": "notes", "commit": "x", "done": True,
                                "summaries": {"FR-001": "FR-001 adds."}, "answers": {}})
    server, token = confirm.make_server(prd, "notes", items, {}, "<html></html>")
    t = threading.Thread(target=lambda: confirm.run(server))
    t.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, *_ = fetch(f"{base}/answer?token={token}", json.dumps({"id": "FR-002", "decision": "confirm"}).encode())
        assert status == 200
        d = json.loads(path.read_text())
        assert d["summaries"] == {"FR-001": "FR-001 adds."} and "done" not in d and "FR-002" in d["answers"]
        for i in items:
            body = {"id": i.id, "decision": {"requirement": "confirm", "bug": "intended", "question": "intended",
                                              "marker": "answer"}[i.kind]}
            if i.kind == "marker":
                body["text"] = "ok"
            fetch(f"{base}/answer?token={token}", json.dumps(body).encode())
        assert fetch(f"{base}/done?token={token}", b"{}")[0] == 200
        t.join(10)
        assert json.loads(path.read_text())["done"] is True
    finally:
        server.shutdown()
        t.join(10)
        server.server_close()


def test_ping_is_200_with_the_token_and_403_without_touching(live):
    server, token, base, state, *_ = live
    status, body, _ = fetch(f"{base}/ping?token={token}")
    assert status == 200 and json.loads(body) == {"ok": True} and state.hits == 0
    server.last = before = server.last - 30
    assert fetch(f"{base}/ping")[0] == 403 and fetch(f"{base}/ping?token=wrong")[0] == 403
    assert server.last == before
    fetch(f"{base}/ping?token={token}")
    assert server.last > before
