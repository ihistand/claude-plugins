"""The confirmation form's answers file and local server."""
import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, model

from legacy import git

PAGE = "<html><body>stub</body></html>"


class Live:
    def __init__(self, tmp_path, idle_minutes=120, repo=None, request_timeout=30):
        self.repo, self.prd = repo or make_confirm_repo(tmp_path)
        self.start(idle_minutes, request_timeout)

    def start(self, idle_minutes=120, request_timeout=30):
        prd = model.load(self.prd)
        self.items = confirm.build_items(prd, "notes")
        self.server, self.token = confirm.make_server(prd, "notes", self.items, {"FR-001": "FR-001 adds."}, PAGE,
                                                      idle_minutes=idle_minutes, request_timeout=request_timeout)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.code = []
        self.thread = threading.Thread(target=lambda: self.code.append(confirm.run(self.server)))
        self.thread.start()

    def call(self, path, body=None, token=True):
        sep = "&" if "?" in path else "?"
        url = self.base + path + (f"{sep}token={self.token}" if token else "")
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.read()
            finally:
                e.close()

    def json(self, path, body=None, token=True):
        status, raw = self.call(path, body, token)
        return status, json.loads(raw)

    def stop(self):
        self.server.shutdown()
        self.thread.join(10)
        self.server.server_close()

    @property
    def file(self):
        return confirm.answers_path(self.repo, "notes")


@pytest.fixture
def live(tmp_path):
    made = []

    def make(**kw):
        lv = Live(tmp_path, **kw)
        made.append(lv)
        return lv

    yield make
    for lv in made:
        lv.stop()


def test_no_token_is_403_and_writes_nothing(live):
    lv = live()
    assert lv.call("/", token=False)[0] == 403
    assert lv.call("/items", token=False)[0] == 403
    assert lv.call("/answer", {"id": "FR-001", "decision": "confirm"}, token=False)[0] == 403
    status, _ = lv.call("/answer?token=wrong", {"id": "FR-001", "decision": "confirm"}, token=False)
    assert status == 403
    assert not lv.file.exists()
    assert lv.call("/")[0] == 200


def test_header_token_accepted_for_json(live):
    lv = live()
    req = urllib.request.Request(lv.base + "/items", headers={"X-Prd-Token": lv.token})
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.status == 200
    req = urllib.request.Request(lv.base + "/", headers={"X-Prd-Token": lv.token})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=10)
    assert e.value.code == 403
    e.value.close()


def test_page_is_html(live):
    lv = live()
    status, raw = lv.call("/")
    assert status == 200 and raw.decode() == PAGE


def test_answer_written_atomically_and_reloaded(live, tmp_path):
    lv = live()
    status, out = lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    assert status == 200 and "FR-001" not in out["open"]
    data = json.loads(lv.file.read_text())
    ans = data["answers"]["FR-001"]
    fp = {i.id: i for i in lv.items}["FR-001"].fingerprint
    assert data["prd"] == "notes" and data["area"] == "notes"
    assert data["commit"] == git(lv.repo, "rev-parse", "HEAD").strip()
    assert ans["decision"] == "confirm" and ans["fingerprint"] == fp and ans["at"].endswith("+00:00")
    assert not [p for p in lv.repo.iterdir() if ".tmp-" in p.name]
    lv.stop()
    lv.start()
    status, out = lv.json("/items")
    assert status == 200 and out["area"] == "notes"
    assert out["answers"]["FR-001"]["decision"] == "confirm"
    assert "FR-001" not in out["open"] and "FR-002" in out["open"]
    first = out["items"][0]
    assert first["id"] == "FR-001" and first["summary"] == "FR-001 adds." and first["fingerprint"] == fp
    assert out["items"][1]["summary"] is None


def test_required_text(live):
    lv = live()
    assert lv.json("/answer", {"id": "FR-001", "decision": "correct"})[0] == 400
    assert lv.json("/answer", {"id": "FR-001", "decision": "correct", "text": "  "})[0] == 400
    assert lv.json("/answer", {"id": "FR-001", "decision": "correct", "acs": {"AC-009.1": "x"}})[0] == 400
    status, _ = lv.json("/answer", {"id": "FR-001", "decision": "correct", "acs": {"AC-001.1": "new"}})
    assert status == 200
    assert lv.json("/answer", {"id": "FR-002", "decision": "ask", "text": ""})[0] == 400
    assert lv.json("/answer", {"id": "FR-002", "decision": "bug"})[0] == 400
    assert lv.json("/answer", {"id": "Q-01", "decision": "answer"})[0] == 400
    assert lv.json("/answer", {"id": "Q-01", "decision": "fix"})[0] == 200
    assert lv.json("/answer", {"id": "config.yaml:NOTES_LIMIT.owner", "decision": "answer", "text": "ops"})[0] == 200


def test_decision_not_allowed_for_kind(live):
    lv = live()
    status, out = lv.json("/answer", {"id": "FR-001", "decision": "intended"})
    assert status == 400 and "error" in out
    assert lv.json("/answer", {"id": "FR-001", "decision": "nonsense"})[0] == 400
    assert lv.json("/answer", {"id": "NOPE", "decision": "confirm"})[0] == 400
    assert lv.json("/answer", {"id": "E-001", "decision": "confirm"})[0] == 400
    assert lv.json("/answer", {"id": "FR-001"})[0] == 400
    assert not lv.file.exists()


def test_oversized_body_is_413(live):
    lv = live()
    status, _ = lv.json("/answer", {"id": "FR-001", "decision": "correct", "text": "x" * (1024 * 1024 + 10)})
    assert status == 413
    assert not lv.file.exists()


def test_undo(live):
    lv = live()
    lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    status, out = lv.json("/undo", {"id": "FR-001"})
    assert status == 200 and "FR-001" in out["open"]
    assert "FR-001" not in json.loads(lv.file.read_text())["answers"]
    assert lv.json("/undo", {"id": "NOPE"})[0] == 400


def answer_all(lv):
    for i in lv.items:
        d = {"requirement": "confirm", "bug": "intended", "question": "fix", "marker": "answer"}[i.kind]
        body = {"id": i.id, "decision": d}
        if d == "answer":
            body["text"] = "ops"
        assert lv.json("/answer", body)[0] == 200


def test_done_refused_then_accepted(live):
    lv = live()
    status, out = lv.json("/done", {})
    assert status == 409 and out["open"] == [i.id for i in lv.items]
    answer_all(lv)
    status, out = lv.json("/done", {})
    assert status == 200
    lv.thread.join(10)
    assert lv.code == [0]


def test_idle_timeout_returns_3(live):
    lv = live(idle_minutes=0.01)
    lv.thread.join(15)
    assert lv.code == [3]


def test_changed_since_answered_counts_open(live):
    lv = live()
    answer_all(lv)
    lv.stop()
    f = lv.prd / "features/notes.md"
    f.write_text(f.read_text().replace("grow by one", "grow by two"))
    lv.start()
    status, out = lv.json("/items")
    assert out["open"] == ["FR-001"]
    status, out = lv.json("/done", {})
    assert status == 409 and out["open"] == ["FR-001"]
    assert lv.json("/answer", {"id": "FR-001", "decision": "confirm"})[0] == 200
    assert lv.json("/done", {})[0] == 200


def test_concurrent_posts_keep_valid_json(live):
    lv = live()
    ids = [i.id for i in lv.items]
    results = []

    def post(n):
        item = lv.items[n % len(lv.items)]
        decision = {"requirement": "ask", "bug": "ask", "question": "answer", "marker": "answer"}[item.kind]
        results.append(lv.json("/answer", {"id": item.id, "decision": decision, "text": f"q{n}"})[0])

    threads = [threading.Thread(target=post, args=(n,)) for n in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert results == [200] * 20
    data = json.loads(lv.file.read_text())
    assert set(data["answers"]) == set(ids)


def test_second_server_does_not_drop_answers(live, tmp_path):
    lv = live()
    lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    second = Live(tmp_path, repo=(lv.repo, lv.prd))
    try:
        assert second.json("/answer", {"id": "FR-002", "decision": "confirm"})[0] == 200
        assert lv.json("/answer", {"id": "Q-01", "decision": "fix"})[0] == 200
    finally:
        second.stop()
    assert set(json.loads(lv.file.read_text())["answers"]) == {"FR-001", "FR-002", "Q-01"}


def test_exclude_line_once(tmp_path):
    repo, _ = make_confirm_repo(tmp_path)
    info = repo / ".git/info"
    (info / "exclude").unlink(missing_ok=True)
    if info.exists() and not any(info.iterdir()):
        info.rmdir()
    confirm.ensure_excluded(repo)
    confirm.ensure_excluded(repo)
    lines = (repo / ".git/info/exclude").read_text().splitlines()
    assert lines.count("/.prd-confirm-*.json") == 1


def test_exclude_goes_to_common_dir_of_a_worktree(tmp_path):
    repo, _ = make_confirm_repo(tmp_path)
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "other")
    confirm.ensure_excluded(wt)
    assert "/.prd-confirm-*.json" in (repo / ".git/info/exclude").read_text().splitlines()


def test_open_ids_pure(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    ans = {"answers": {items[0].id: {"decision": "confirm", "fingerprint": items[0].fingerprint},
                       items[1].id: {"decision": "confirm", "fingerprint": "stale"}}}
    assert confirm.open_ids(items, ans) == [i.id for i in items[1:]]
    assert confirm.load_answers(repo / "missing.json") == {}


def raw(lv, head: bytes, body: bytes = b"", wait=5.0):
    """Send raw bytes; return (status, body) of the reply, or (None, b"") when the server just closed."""
    with socket.create_connection(("127.0.0.1", lv.server.server_address[1]), timeout=wait) as c:
        c.sendall(head + body)
        buf = b""
        try:
            while chunk := c.recv(65536):
                buf += chunk
        except OSError:
            pass
    if not buf:
        return None, b""
    status = int(buf.split(b" ", 2)[1])
    return status, buf.split(b"\r\n\r\n", 1)[1]


def post_head(lv, length=None, path="/answer"):
    h = f"POST {path}?token={lv.token} HTTP/1.0\r\n"
    if length is not None:
        h += f"Content-Length: {length}\r\n"
    return (h + "\r\n").encode()


def test_malformed_requests_get_json_errors(live):
    lv = live()
    assert raw(lv, post_head(lv, 5), b"{nope")[0] == 400
    assert raw(lv, post_head(lv, 2), b"[]")[0] == 400
    assert raw(lv, post_head(lv, -5))[0] == 400
    assert raw(lv, post_head(lv))[0] == 400  # no Content-Length on a POST
    assert raw(lv, post_head(lv, 3), b"abc")[0] == 400
    for body in ({"id": ["a"], "decision": "confirm"}, {"id": "FR-001", "decision": ["confirm"]},
                 {"id": "FR-001", "decision": "correct", "text": 5},
                 {"id": "FR-001", "decision": "correct", "acs": ["AC-001.1"]},
                 {"id": "FR-001", "decision": "correct", "acs": {"AC-001.1": 7}},
                 {"id": {"a": 1}, "decision": "confirm"}):
        status, out = lv.json("/answer", body)
        assert status == 400 and "error" in out, body
    assert lv.json("/undo", {"id": ["a"]})[0] == 400
    assert not lv.file.exists()
    assert lv.json("/items")[0] == 200


def test_short_body_times_out_with_408(live):
    lv = live(request_timeout=0.3)
    t = time.monotonic()
    status, _ = raw(lv, post_head(lv, 100), b"{}")
    assert status in (408, None) and time.monotonic() - t < 3
    assert lv.json("/items")[0] == 200


def test_unexpected_error_is_500_and_changes_nothing(live, monkeypatch, capfd):
    lv = live()

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(confirm, "save_answers", boom)
    status, out = lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    assert status == 500 and out == {"error": "internal error"}
    assert "Traceback" not in capfd.readouterr().err
    assert not lv.file.exists()


def test_corrupt_answers_file_refuses_server(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    f = confirm.answers_path(repo, "notes")
    for bad in ("{not json", "[1]", ""):
        f.write_text(bad)
        p = model.load(prd)
        with pytest.raises(confirm.Refused, match="is not valid JSON; move it aside to start over"):
            confirm.make_server(p, "notes", confirm.build_items(p, "notes"), {}, PAGE)
        assert f.read_text() == bad
    f.unlink()
    assert confirm.load_answers(f) == {}


def test_corrupt_answers_file_midrun_is_500_and_kept(live):
    lv = live()
    lv.file.write_text("{broken")
    status, out = lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    assert status == 500 and "not valid JSON" in out["error"]
    assert lv.file.read_text() == "{broken"
    assert lv.json("/undo", {"id": "FR-001"})[0] == 500
    assert lv.file.read_text() == "{broken"


def test_unauthenticated_requests_do_not_keep_server_alive(live):
    lv = live(idle_minutes=0.03)  # 1.8 s
    start = time.monotonic()
    while lv.thread.is_alive() and time.monotonic() - start < 6:
        try:
            req = urllib.request.Request(f"{lv.base}/items")
            urllib.request.urlopen(req, timeout=0.5)
        except urllib.error.HTTPError as e:
            e.close()
        except OSError:  # the server stopped between the check and the request
            break
        time.sleep(0.1)
    lv.thread.join(3)
    assert lv.code == [3] and time.monotonic() - start < 5


def test_client_gone_before_error_reply_prints_nothing(live, capfd):
    lv = live()
    port = lv.server.server_address[1]
    for _ in range(20):
        c = socket.create_connection(("127.0.0.1", port))
        c.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, b"\x01\x00\x00\x00\x00\x00\x00\x00")  # reset on close
        c.sendall(post_head(lv, 5, path="/answer").replace(lv.token.encode(), b"wrong") + b"{nope")
        c.close()
    time.sleep(0.3)
    assert lv.json("/items")[0] == 200
    assert capfd.readouterr().err == ""


def test_short_body_then_client_closes_is_400(live):
    lv = live()
    with socket.create_connection(("127.0.0.1", lv.server.server_address[1]), timeout=5) as c:
        c.sendall(post_head(lv, 10) + b"abc")
        c.shutdown(socket.SHUT_WR)
        buf = b""
        while chunk := c.recv(65536):
            buf += chunk
    assert int(buf.split(b" ", 2)[1]) == 400
    assert not lv.file.exists()


def test_other_routes_without_token_are_403(live):
    lv = live()
    lv.json("/answer", {"id": "FR-001", "decision": "confirm"})
    before = lv.file.read_text()
    assert lv.call("/undo", {"id": "FR-001"}, token=False)[0] == 403
    assert lv.call("/done", {}, token=False)[0] == 403
    assert lv.call("/nowhere", token=False)[0] == 403
    assert lv.file.read_text() == before
    assert lv.json("/nowhere")[0] == 404


def test_correct_with_blank_acs_is_refused_and_blanks_dropped(live):
    lv = live()
    assert lv.json("/answer", {"id": "FR-001", "decision": "correct", "acs": {"AC-001.1": "  "}})[0] == 400
    status, _ = lv.json("/answer", {"id": "FR-001", "decision": "correct",
                                    "acs": {"AC-001.1": " new ", "AC-001.2": " "}})
    assert status == 200
    assert json.loads(lv.file.read_text())["answers"]["FR-001"]["acs"] == {"AC-001.1": "new"}


def test_ctrl_c_returns_3(tmp_path, monkeypatch):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    server, _ = confirm.make_server(p, "notes", confirm.build_items(p, "notes"), {}, PAGE)
    try:
        def interrupt(*a, **k):
            raise KeyboardInterrupt

        monkeypatch.setattr(server, "serve_forever", interrupt)
        assert confirm.run(server) == 3
    finally:
        server.server_close()
