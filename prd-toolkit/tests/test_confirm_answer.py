"""prd_confirm.py answer, done and open: writers of the answers file that are not the form."""
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, model
from test_confirm_cli import SCRIPT, URL, WAIT, call, first_line, procs, serve  # noqa: F401  (procs is a fixture)

REPLY = 'sí, "yes"\nthen "no" — ¿ok?'


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8",
                          cwd=cwd, timeout=WAIT)


def answer(prd, item, decision, reply="settled", *extra):
    return run("answer", str(prd), "notes", item, "--decision", decision, f"--reply={reply}", *extra)


def data(repo):
    return json.loads(confirm.answers_path(repo, "notes").read_text(encoding="utf-8"))


def kind_decision(item):
    return {"requirement": "confirm", "bug": "intended", "question": "answer", "marker": "answer"}[item.kind]


def answer_all_by_cli(prd, items):
    for i in items:
        r = answer(prd, i.id, kind_decision(i))
        assert r.returncode == 0, r.stderr


def test_cli_answer_writes_the_form_record_plus_the_verbatim_reply(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = {i.id: i for i in confirm.build_items(model.load(prd), "notes")}
    r = answer(prd, "FR-001", "ask", REPLY)
    assert r.returncode == 0 and r.stdout == "answered FR-001\n" and r.stderr == ""
    d = data(repo)
    assert set(d) == {"prd", "area", "commit", "answers"} and d["area"] == "notes" and d["prd"] == "notes"
    e = d["answers"]["FR-001"]
    assert e["reply"] == REPLY and e["text"] == REPLY.strip() and e["decision"] == "ask"
    assert set(e) == {"decision", "text", "reply", "fingerprint", "where", "served", "at"}
    assert e["fingerprint"] == items["FR-001"].fingerprint and e["served"] == items["FR-001"].text


def test_correction_is_the_text_and_the_reply_stays_verbatim(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    r = answer(prd, "FR-001", "correct", REPLY, "--correction", "Empty notes are rejected.")
    assert r.returncode == 0, r.stderr
    e = data(repo)["answers"]["FR-001"]
    assert e["text"] == "Empty notes are rejected." and e["reply"] == REPLY


def test_form_and_cli_records_have_the_same_shape(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    server, token = confirm.make_server(p, "notes", items, {}, "<html></html>")
    state = server.state
    try:
        state.answer({"id": "FR-001", "decision": "ask", "text": "why"})
    finally:
        server.server_close()
    form = data(repo)["answers"]["FR-001"]
    assert answer(prd, "FR-002", "ask", "why").returncode == 0
    cli = data(repo)["answers"]["FR-002"]
    assert set(cli) - set(form) == {"reply"} and set(form) <= set(cli)


def test_a_decision_not_allowed_for_the_kind_refuses(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    r = answer(prd, "FR-001", "intended")
    assert r.returncode == 1 and r.stdout == "" and r.stderr.startswith("refused: ")
    assert not confirm.answers_path(repo, "notes").exists()
    r = answer(prd, "FR-001", "bogus")
    assert r.returncode == 1 and r.stderr.startswith("refused: ")


def test_an_empty_reply_or_unknown_item_refuses(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    for reply in ("", "   "):
        r = answer(prd, "FR-001", "confirm", reply)
        assert r.returncode == 1 and r.stderr.startswith("refused: "), reply
    r = answer(prd, "FR-999", "confirm")
    assert r.returncode == 1 and r.stderr.startswith("refused: ")
    assert not confirm.answers_path(repo, "notes").exists()


def test_usage_errors_exit_2(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    assert run("answer", str(prd), "notes", "FR-001").returncode == 2  # no --decision, no --reply
    assert run("answer", str(tmp_path / "missing"), "notes", "FR-001", "--decision", "confirm", "--reply=x").returncode == 2
    assert run("done", str(prd)).returncode == 2
    assert run("open", str(prd)).returncode == 2


def test_status_counts_the_cli_answer(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    assert answer(prd, "FR-001", "confirm").returncode == 0
    r = run("status", str(prd), "--area", "notes")
    assert r.stdout.splitlines()[0] == "1/5" and "open FR-001" not in r.stdout


def test_a_form_save_and_a_cli_answer_never_lose_each_other(tmp_path, procs):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    p = serve(procs, prd)
    m = URL.match(first_line(p))
    base, token = f"http://127.0.0.1:{m.group(1)}", m.group(2)
    form_items = [i for i in items if i.kind == "requirement"]
    cli_items = [i for i in items if i.kind == "question"]
    assert form_items and cli_items
    fi, ci = form_items[0], cli_items[0]
    for n in range(20):
        confirm.answers_path(repo, "notes").unlink(missing_ok=True)
        results = {}
        start = threading.Barrier(2)

        def post():
            start.wait(WAIT)
            results["form"] = call(base, token, "/answer", {"id": fi.id, "decision": "ask", "text": f"form {n}"})[0]

        def cli():
            start.wait(WAIT)
            results["cli"] = answer(prd, ci.id, "answer", f"cli {n}").returncode

        threads = [threading.Thread(target=post), threading.Thread(target=cli)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(WAIT)
        assert results == {"form": 200, "cli": 0}, n
        saved = data(repo)["answers"]
        assert set(saved) == {fi.id, ci.id}, n
        assert saved[fi.id]["text"] == f"form {n}" and saved[ci.id]["reply"] == f"cli {n}"


def test_done_is_refused_while_an_item_is_open(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    r = run("done", str(prd), "notes")
    assert r.returncode == 1 and r.stdout == "" and r.stderr.startswith("refused: ") and "FR-001" in r.stderr
    assert not confirm.answers_path(repo, "notes").exists()
    answer_all_by_cli(prd, items[:-1])
    assert run("done", str(prd), "notes").returncode == 1
    assert "done" not in data(repo)


def test_done_is_refused_for_an_answer_whose_fingerprint_changed(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    answer_all_by_cli(prd, items)
    d = data(repo)
    d["answers"]["FR-001"]["fingerprint"] = "stale"
    confirm.save_answers(confirm.answers_path(repo, "notes"), d)
    r = run("done", str(prd), "notes")
    assert r.returncode == 1 and "FR-001" in r.stderr and "done" not in data(repo)


def test_done_writes_true_and_keeps_the_other_keys(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    answer_all_by_cli(prd, items)
    d = data(repo)
    d["summaries"] = {"FR-001": "FR-001 adds a note."}
    confirm.save_answers(confirm.answers_path(repo, "notes"), d)
    r = run("done", str(prd), "notes")
    assert r.returncode == 0 and r.stdout == "done notes\n"
    d = data(repo)
    assert d["done"] is True and d["summaries"] == {"FR-001": "FR-001 adds a note."} and len(d["answers"]) == 5


def finished(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    answer_all_by_cli(prd, items)
    assert run("done", str(prd), "notes").returncode == 0
    return repo, prd, items


def test_an_answer_after_done_removes_it(tmp_path):
    repo, prd, _ = finished(tmp_path)
    assert answer(prd, "FR-001", "ask", "wait").returncode == 0
    assert "done" not in data(repo)


def test_an_undo_after_done_removes_it_and_the_form_keeps_the_keys(tmp_path):
    repo, prd, items = finished(tmp_path)
    p = model.load(prd)
    server, _ = confirm.make_server(p, "notes", confirm.build_items(p, "notes"), {}, "<html></html>")
    try:
        server.state.undo({"id": "FR-001"})
        d = data(repo)
        assert "done" not in d and "FR-001" not in d["answers"] and len(d["answers"]) == 4
    finally:
        server.server_close()


def test_a_form_save_keeps_summaries_and_done(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    confirm.save_answers(confirm.answers_path(repo, "notes"),
                         {"prd": "notes", "area": "notes", "commit": "x", "summaries": {"FR-001": "FR-001 adds."},
                          "answers": {}, "extra": [1]})
    server, _ = confirm.make_server(p, "notes", items, {}, "<html></html>")
    try:
        server.state.answer({"id": "FR-002", "decision": "confirm"})
        server.state.answer({"id": "Q-01", "decision": "fix", "text": "none"})
    finally:
        server.server_close()
    d = data(repo)
    assert d["summaries"] == {"FR-001": "FR-001 adds."} and d["extra"] == [1] and set(d["answers"]) == {"FR-002", "Q-01"}
    assert answer(prd, "FR-001", "confirm").returncode == 0
    assert data(repo)["summaries"] == {"FR-001": "FR-001 adds."}


def test_the_forms_done_writes_done_true(tmp_path, procs):
    repo, prd = make_confirm_repo(tmp_path)
    items = confirm.build_items(model.load(prd), "notes")
    p = serve(procs, prd)
    m = URL.match(first_line(p))
    base, token = f"http://127.0.0.1:{m.group(1)}", m.group(2)
    assert call(base, token, "/done", {})[0] == 409 and not confirm.answers_path(repo, "notes").exists()
    for i in items:
        body = {"id": i.id, "decision": kind_decision(i)}
        if body["decision"] == "answer":
            body["text"] = "settled"
        assert call(base, token, "/answer", body)[0] == 200
    assert "done" not in data(repo)
    assert call(base, token, "/done", {})[0] == 200
    assert p.wait(WAIT) == 0
    assert data(repo)["done"] is True


def summaries_file(tmp_path, obj):
    f = tmp_path / "s.json"
    f.write_text(json.dumps(obj), encoding="utf-8")
    return f


def test_open_writes_the_file_with_summaries_and_no_answers(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    (repo / ".git/info/exclude").unlink(missing_ok=True)
    f = summaries_file(tmp_path, {"FR-001": "FR-001 adds a note."})
    r = run("open", str(prd), "--area", "notes", "--summaries", str(f))
    path = confirm.answers_path(repo, "notes")
    assert r.returncode == 0 and Path(r.stdout.strip()).resolve() == path.resolve()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    assert data(repo) == {"prd": "notes", "area": "notes", "commit": head, "summaries": {"FR-001": "FR-001 adds a note."},
                          "answers": {}}
    assert confirm.EXCLUDE_LINE in (repo / ".git/info/exclude").read_text().splitlines()
    assert run("status", str(prd), "--area", "notes").stdout.splitlines()[0] == "0/5"


def test_open_without_summaries_writes_an_empty_object(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    assert run("open", str(prd), "--area", "notes").returncode == 0
    assert data(repo)["summaries"] == {}


def test_open_refuses_an_existing_file_and_leaves_its_answers(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    assert answer(prd, "FR-001", "confirm").returncode == 0
    before = confirm.answers_path(repo, "notes").read_bytes()
    r = run("open", str(prd), "--area", "notes")
    assert r.returncode == 1 and r.stderr.startswith("refused: ") and r.stdout == ""
    assert confirm.answers_path(repo, "notes").read_bytes() == before


def test_open_refuses_an_area_with_no_item_and_bad_summaries(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    r = run("open", str(prd), "--area", "nope")
    assert r.returncode == 1 and r.stderr.startswith("refused: ")
    for obj, why in (({"FR-001": "no id here"}, "does not mention FR-001"), ({"FR-099": "FR-099 x"}, "names no item"),
                     ({"FR-001": "FR-001 " + "x" * 400}, "over 400"), ({"FR-001": 3}, "must be text")):
        r = run("open", str(prd), "--area", "notes", "--summaries", str(summaries_file(tmp_path, obj)))
        assert r.returncode == 1 and why in r.stderr, obj
    assert not confirm.answers_path(repo, "notes").exists()


def test_serve_shows_the_summaries_of_the_file_and_summaries_flag_wins(tmp_path, procs):
    repo, prd = make_confirm_repo(tmp_path)
    f = summaries_file(tmp_path, {"FR-001": "FR-001 from the file."})
    assert run("open", str(prd), "--area", "notes", "--summaries", str(f)).returncode == 0
    p = serve(procs, prd)
    m = URL.match(first_line(p))
    base, token = f"http://127.0.0.1:{m.group(1)}", m.group(2)
    listing = call(base, token, "/items")[1]
    assert {i["id"]: i["summary"] for i in listing["items"]}["FR-001"] == "FR-001 from the file."
    g = summaries_file(tmp_path, {"FR-001": "FR-001 from the flag."})
    before = confirm.answers_path(repo, "notes").read_bytes()
    q = serve(procs, prd, "--summaries", str(g))
    m = URL.match(first_line(q))
    listing = call(f"http://127.0.0.1:{m.group(1)}", m.group(2), "/items")[1]
    assert {i["id"]: i["summary"] for i in listing["items"]}["FR-001"] == "FR-001 from the flag."
    assert call(f"http://127.0.0.1:{m.group(1)}", m.group(2), "/answer", {"id": "FR-002", "decision": "confirm"})[0] == 200
    assert data(repo)["summaries"] == {"FR-001": "FR-001 from the file."} and before != b""


# ---- fix round 1 ----

def test_blank_correction_is_refused(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    r = answer(prd, "FR-001", "correct", "reply", "--correction", "   ")
    assert r.returncode == 1 and r.stderr.strip() == "refused: --correction is empty"
    assert not confirm.answers_path(repo, "notes").exists()


def test_the_reply_is_utf8_on_disk_not_escaped(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    assert answer(prd, "FR-001", "ask", REPLY).returncode == 0
    raw = confirm.answers_path(repo, "notes").read_text(encoding="utf-8")
    assert "sí" in raw and "¿ok?" in raw and "\\u00" not in raw


def test_corrupt_file_refuses_answer_and_done_with_exit_1(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    confirm.answers_path(repo, "notes").write_text("{nope")
    for r in (answer(prd, "FR-001", "confirm"), run("done", str(prd), "notes")):
        assert r.returncode == 1 and r.stderr.startswith("refused: ")


def test_serve_names_the_answers_file_when_its_summaries_are_stale(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    assert run("open", str(prd), "--area", "notes").returncode == 0
    d = data(repo)
    d["summaries"] = {"FR-099": "FR-099 is gone."}
    confirm.save_answers(confirm.answers_path(repo, "notes"), d)
    r = run("serve", str(prd), "--area", "notes", "--no-open")
    assert r.returncode == 2 and ".prd-confirm-notes.json" in r.stderr and "FR-099" in r.stderr
    assert "answers file" in r.stderr


def test_a_done_that_finds_an_item_open_is_not_reported_done(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    server, _ = confirm.make_server(p, "notes", items, {}, "<html></html>")
    state = server.state
    try:
        assert state.finish() == [i.id for i in items] and state.end is None
        assert "done" not in (data(repo) if confirm.answers_path(repo, "notes").exists() else {})
        for i in items:
            state.answer({"id": i.id, "decision": kind_decision(i), "text": "settled"})
        assert state.finish() == [] and state.end == "done" and data(repo)["done"] is True
    finally:
        server.server_close()


def test_the_directory_lock_makes_a_form_save_and_a_cli_answer_wait(tmp_path):
    """Hold the directory flock ourselves: neither writer may write until we let go."""
    import fcntl
    import os
    import time
    repo, prd = make_confirm_repo(tmp_path)
    f = summaries_file(tmp_path, {"FR-001": "FR-001 adds a note."})
    assert run("open", str(prd), "--area", "notes", "--summaries", str(f)).returncode == 0
    path = confirm.answers_path(repo, "notes")
    seed = path.read_bytes()
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    server, token = confirm.make_server(p, "notes", items, {}, "<html></html>")
    runner = threading.Thread(target=lambda: confirm.run(server), daemon=True)
    runner.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    posted = threading.Event()
    result = []

    def post():
        result.append(call(base, token, "/answer", {"id": "FR-001", "decision": "ask", "text": "form"})[0])
        posted.set()

    fd = os.open(repo, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX)
    held = True
    child = None
    try:
        child = subprocess.Popen([sys.executable, str(SCRIPT), "answer", str(prd), "notes", "Q-01", "--decision", "answer",
                                  "--reply=cli"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        poster = threading.Thread(target=post, daemon=True)
        poster.start()
        deadline = time.monotonic() + 8  # a window to observe, not a synchronisation: unlocked, both finish well inside it
        while time.monotonic() < deadline:
            assert not posted.is_set() and child.poll() is None and path.read_bytes() == seed
            posted.wait(0.1)
        fcntl.flock(fd, fcntl.LOCK_UN)
        held = False
        poster.join(WAIT)
        out, err = child.communicate(timeout=WAIT)
        assert result == [200] and child.returncode == 0, err
        d = data(repo)
        assert set(d["answers"]) == {"FR-001", "Q-01"} and d["summaries"] == {"FR-001": "FR-001 adds a note."}
    finally:
        if held:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        if child is not None and child.poll() is None:
            child.kill()
            child.communicate()
        server.shutdown()
        runner.join(WAIT)
        server.server_close()


def test_the_thread_lock_serialises_in_process_writers(tmp_path, monkeypatch):
    """Both writers read before either writes unless the lock stops it; a lost update would drop an answer."""
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    monkeypatch.setattr(confirm, "fcntl", None)  # the directory flock would also serialise; test the thread lock alone
    real = confirm.load_answers
    both_read = threading.Barrier(2)

    def load_then_meet(path):
        got = real(path)
        try:
            both_read.wait(3)  # only an unlocked pair gets here together
        except threading.BrokenBarrierError:
            pass
        return got

    monkeypatch.setattr(confirm, "load_answers", load_then_meet)
    errors = []

    def go(item, decision):
        try:
            confirm.record_answer(p, "notes", item, decision, "reply " + item, None, repo)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=go, args=a) for a in (("FR-001", "confirm"), ("Q-01", "answer"))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(WAIT)
    assert errors == []
    assert set(data(repo)["answers"]) == {"FR-001", "Q-01"}
