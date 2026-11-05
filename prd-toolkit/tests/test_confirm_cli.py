"""prd_confirm.py serve and status, run as subprocesses."""
import errno
import json
import re
import signal
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, model

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/prd_confirm.py"
# Every wait below is a deadline for a hung child, not an expected duration: the full suite loads the machine
# until a child needs tens of seconds to start. A generous deadline fails nothing that passes on a quiet machine.
WAIT = 180
URL = re.compile(r"^url=http://127\.0\.0\.1:(\d+)/\?token=([0-9a-f]{64})$")


def _sigint_default():
    """A child started from a background job inherits SIGINT ignored, and Python then never installs its handler,
    so a test that sends SIGINT would wait out its whole deadline. Start every child with the default."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def popen(cmd, **kw):
    return subprocess.Popen(cmd, preexec_fn=_sigint_default, **kw)


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=cwd, timeout=WAIT)


@pytest.fixture
def procs():
    started = []
    yield started
    for p in started:
        if p.poll() is None:
            p.kill()
        p.wait()
        for s in (p.stdout, p.stderr):
            if s:
                s.close()


def serve(procs, prd, *extra):
    p = popen([sys.executable, str(SCRIPT), "serve", str(prd), "--area", "notes", "--no-open", *extra],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    procs.append(p)
    return p


def first_line(p, timeout=WAIT):
    """The child's first stdout line, read with a deadline so a hung child fails the test instead of hanging it."""
    got = []
    reader = threading.Thread(target=lambda: got.append(p.stdout.readline()), daemon=True)
    reader.start()
    reader.join(timeout)
    if reader.is_alive():
        p.kill()
        reader.join(5)
        pytest.fail(f"no stdout line within {timeout} s")
    return got[0].strip()


def call(base, token, path, body=None):
    req = urllib.request.Request(f"{base}{path}?token={token}", data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=WAIT) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_serve_prints_url_first_and_serves_until_done(tmp_path, procs):
    repo, prd = make_confirm_repo(tmp_path)
    p = serve(procs, prd)
    m = URL.match(first_line(p))
    assert m, "first stdout line is the url line"
    base, token = f"http://127.0.0.1:{m.group(1)}", m.group(2)
    status, listing = call(base, token, "/items")
    assert status == 200 and len(listing["items"]) == 5
    assert call(base, token, "/done", {})[0] == 409
    for item in listing["items"]:
        decision = {"requirement": "confirm", "bug": "intended", "question": "answer", "marker": "answer"}[item["kind"]]
        body = {"id": item["id"], "decision": decision}
        if decision == "answer":
            body["text"] = "settled"
        assert call(base, token, "/answer", body)[0] == 200
    assert call(base, token, "/done", {})[0] == 200
    assert p.wait(WAIT) == 0


def test_serve_excludes_the_answers_file_and_page_is_served(tmp_path, procs):
    repo, prd = make_confirm_repo(tmp_path)
    p = serve(procs, prd)
    m = URL.match(first_line(p))
    with urllib.request.urlopen(f"http://127.0.0.1:{m.group(1)}/?token={m.group(2)}", timeout=WAIT) as r:
        assert b"<title>" in r.read()
    assert confirm.EXCLUDE_LINE in (repo / ".git/info/exclude").read_text().splitlines()


def test_status_counts_open_items(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    r = run("status", str(prd), "--area", "notes")
    assert r.returncode == 0 and r.stdout.splitlines()[0] == "0/5"
    answers = {i.id: {"decision": "confirm", "fingerprint": i.fingerprint, "at": "2026-11-03T00:00:00+00:00"} for i in items[:2]}
    confirm.save_answers(confirm.answers_path(repo, "notes"), {"area": "notes", "answers": answers})
    r = run("status", str(prd), "--area", "notes")
    assert r.returncode == 0 and r.stderr == ""
    assert r.stdout.splitlines() == ["2/5"] + [f"open {i.id}" for i in items[2:]]
    assert len(r.stdout.splitlines()) == 4


def test_status_counts_a_changed_answer_as_open(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    answers = {i.id: {"decision": "confirm", "fingerprint": "stale" if n == 0 else i.fingerprint} for n, i in enumerate(items)}
    confirm.save_answers(confirm.answers_path(repo, "notes"), {"area": "notes", "answers": answers})
    r = run("status", str(prd), "--area", "notes")
    assert r.stdout.splitlines() == ["4/5", f"open {items[0].id}"]


def test_status_starts_no_server_and_exits_2_on_errors(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    for args in (["status", str(prd), "--area", "nope"], ["status", str(tmp_path / "missing"), "--area", "notes"],
                 ["status", str(prd)], []):
        r = run(*args)
        assert r.returncode == 2 and r.stdout == "", args


def test_unknown_area_exits_2(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    r = run("serve", str(prd), "--area", "nope", "--no-open")
    assert r.returncode == 2 and r.stdout == ""
    assert r.stderr.startswith("prd_confirm: ") and "nope" in r.stderr


def test_bad_summaries_exit_2(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    f = tmp_path / "s.json"
    f.write_text(json.dumps({"FR-001": "this one does not name its item"}))
    r = run("serve", str(prd), "--area", "notes", "--no-open", "--summaries", str(f))
    assert r.returncode == 2 and r.stdout == ""
    assert r.stderr.strip() == "prd_confirm: summary for FR-001 does not mention FR-001"


def test_corrupt_answers_file_exits_2(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    confirm.answers_path(repo, "notes").write_text("{nope")
    r = run("serve", str(prd), "--area", "notes", "--no-open")
    assert r.returncode == 2 and r.stdout == "" and r.stderr.startswith("prd_confirm: ")


def test_port_in_use_exits_2(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        r = run("serve", str(prd), "--area", "notes", "--no-open", "--port", str(port))
    assert r.returncode == 2 and r.stdout == ""
    assert r.stderr.strip() == f"prd_confirm: port {port} is in use"


def test_usage_error_exits_2(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    r = run("serve", str(prd), "--area", "notes", "--port", "abc")
    assert r.returncode == 2 and r.stdout == ""


def test_sigint_exits_3(tmp_path, procs):
    _, prd = make_confirm_repo(tmp_path)
    p = serve(procs, prd, "--idle-minutes", "10")  # long: only the signal may end it
    assert URL.match(first_line(p))
    p.send_signal(signal.SIGINT)
    assert p.wait(WAIT) == 3


def test_idle_exits_3(tmp_path, procs):
    _, prd = make_confirm_repo(tmp_path)
    p = serve(procs, prd, "--idle-minutes", "0.01")
    assert URL.match(first_line(p))
    assert p.wait(WAIT) == 3


def test_a_failing_browser_is_ignored(tmp_path, procs, monkeypatch):
    _, prd = make_confirm_repo(tmp_path)
    sc = tmp_path / "sitecustomize.py"
    sc.write_text("import webbrowser\ndef _boom(*a, **k):\n    raise RuntimeError('no browser')\nwebbrowser.open = _boom\n")
    env = {"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"}
    p = popen([sys.executable, str(SCRIPT), "serve", str(prd), "--area", "notes"], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    procs.append(p)
    assert URL.match(first_line(p))
    p.send_signal(signal.SIGINT)
    assert p.wait(WAIT) == 3 and p.stderr.read() == ""


def test_token_shape_is_64_hex(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    server, token = confirm.make_server(p, "notes", confirm.build_items(p, "notes"), {}, "<html></html>")
    server.server_close()
    assert re.fullmatch(r"[0-9a-f]{64}", token)


def test_page_path_from_the_plugin():
    assert confirm.page_path() == SCRIPT.parent.parent / "templates/confirm/form.html"
    assert confirm.page_path().is_file()


# ---- final-review fix ----

def test_first_line_fails_a_hung_child():
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], stdout=subprocess.PIPE, text=True)
    try:
        with pytest.raises(pytest.fail.Exception, match="no stdout line"):
            first_line(p, timeout=0.5)
        assert p.wait(WAIT) != 0
    finally:
        p.stdout.close()


def test_sigterm_exits_3(tmp_path, procs):
    _, prd = make_confirm_repo(tmp_path)
    p = serve(procs, prd)
    assert URL.match(first_line(p))
    p.terminate()
    assert p.wait(WAIT) == 3
    assert p.stderr.read() == ""


def test_exclude_is_written_before_a_refusal(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    (repo / ".git/info/exclude").unlink(missing_ok=True)
    r = run("serve", str(prd), "--area", "nope", "--no-open")
    assert r.returncode == 2
    assert confirm.EXCLUDE_LINE in (repo / ".git/info/exclude").read_text().splitlines()


def test_ctrl_c_while_opening_the_browser_exits_3(tmp_path, procs):
    _, prd = make_confirm_repo(tmp_path)
    sc = tmp_path / "sitecustomize.py"
    sc.write_text("import webbrowser\ndef _stop(*a, **k):\n    raise KeyboardInterrupt\nwebbrowser.open = _stop\n")
    env = {"PYTHONPATH": str(tmp_path), "PATH": "/usr/bin:/bin"}
    p = popen([sys.executable, str(SCRIPT), "serve", str(prd), "--area", "notes"], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    procs.append(p)
    assert URL.match(first_line(p))
    assert p.wait(WAIT) == 3 and p.stderr.read() == ""


def test_a_bind_failure_other_than_in_use_names_its_reason(tmp_path, monkeypatch, capsys):
    import prd_confirm

    _, prd = make_confirm_repo(tmp_path)

    def refuse(*a, **k):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(confirm, "make_server", refuse)
    assert prd_confirm.main(["serve", str(prd), "--area", "notes", "--no-open", "--port", "80"]) == 2
    out = capsys.readouterr()
    assert out.out == "" and out.err.strip() == "prd_confirm: cannot bind port 80: Permission denied"

    def in_use(*a, **k):
        raise OSError(errno.EADDRINUSE, "Address already in use")

    monkeypatch.setattr(confirm, "make_server", in_use)
    assert prd_confirm.main(["serve", str(prd), "--area", "notes", "--no-open", "--port", "80"]) == 2
    assert capsys.readouterr().err.strip() == "prd_confirm: port 80 is in use"
