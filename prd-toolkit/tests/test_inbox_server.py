"""The decision inbox server (0.8.2): every pending gate of a PRD across the worktrees, answered through gates.answer(by="form")."""
import json
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from inbox_fixture import AREA, PRD, SCRIPT, git, make_inbox_repo
from prdlint import confirm, formserver, gates, model

QUOTED = '"sí", then "no"'


class Inbox:
    def __init__(self, tmp_path):
        made = make_inbox_repo(tmp_path)
        self.repo, self.second, self.run_id = made["repo"].resolve(), made["second"].resolve(), made["run_id"]
        self.server, self.token = gates.make_inbox(self.repo / PRD)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.code = []
        self.thread = threading.Thread(target=lambda: self.code.append(formserver.run(self.server)))
        self.thread.start()

    def call(self, path, body=None, token=True):
        sep = "&" if "?" in path else "?"
        url = self.base + path + (f"{sep}token={self.token}" if token else "")
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            finally:
                e.close()

    def gates(self):
        status, doc = self.call("/gates")
        assert status == 200, doc
        return doc

    def group(self, root):
        return next(g for g in self.gates()["worktrees"] if Path(g["path"]) == Path(root))

    def gate(self, gate_id, root=None):
        return next(g for g in self.group(root or self.repo)["gates"] if g["id"] == gate_id)

    def post(self, gate_id, choice, words="", root=None, question=None, **extra):
        root = root or self.repo
        body = {"worktree": str(root), "gate": gate_id, "choice": choice, "words": words,
                "question": question if question is not None else self.gate(gate_id, root)["question"], **extra}
        return self.call("/answer", body)

    def log(self):
        return gates.read_log(self.repo)

    def stop(self):
        self.server.shutdown()
        self.thread.join(10)
        self.server.server_close()


@pytest.fixture
def inbox(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    box = Inbox(tmp_path)
    yield box
    box.stop()


def snapshot(*roots):
    out = {}
    for root in roots:
        for p in Path(root).rglob("*"):
            if p.is_file() and ".git" not in p.relative_to(root).parts:
                out[p.as_posix()] = p.read_bytes()
    return out


def head(root):
    return git(root, "rev-parse", "HEAD").strip()


# --- the listing ---

def test_every_request_needs_the_token(inbox):
    assert inbox.call("/gates", token=False)[0] == 403
    assert inbox.call("/answer", {}, token=False)[0] == 403
    assert inbox.call(f"/adoption/{AREA}/items?wt={inbox.repo}", token=False)[0] == 403


def test_the_page_is_served_with_the_csp(inbox):
    with urllib.request.urlopen(f"{inbox.base}/?token={inbox.token}", timeout=10) as r:
        assert r.status == 200 and r.headers["Content-Type"].startswith("text/html")
        assert r.headers["Content-Security-Policy"] == formserver.CSP
        assert b"<html" in r.read()
    status, doc = inbox.call("/ping")
    assert status == 200 and doc == {"ok": True}


def test_gates_groups_each_worktree_with_its_own_error_class_gate(inbox):
    doc = inbox.gates()
    groups = doc["worktrees"]
    assert [Path(g["path"]) for g in groups] == [inbox.repo, inbox.second]
    assert [g["branch"] for g in groups] == ["main", "feature-x"]
    first, second = ({x["id"] for x in g["gates"]} for g in groups)
    assert "error-class:E-003" in first and "error-class:E-003" in second
    assert {"approval:main", f"deploy-step:{inbox.run_id}:3", "signoff:T-001.4", f"adoption:{AREA}"} <= first
    assert not any(i.startswith("approval:") for i in second)
    assert doc["answers"] == []


def test_the_approval_gate_carries_the_verdict_the_versions_and_the_diff(inbox):
    g = inbox.gate("approval:main")
    v = json.loads((inbox.repo / PRD / ".prd-review.json").read_text(encoding="utf-8"))
    for key in ("restate", "touches", "bump", "impact", "dry_run"):
        assert g[key] == v[key], key
    base = git(inbox.repo, "merge-base", "HEAD", "main").strip()
    assert g["version"] == {"from": "1.0.0", "to": model.load(inbox.repo / PRD).frontmatter["version"]}
    assert g["version"]["to"] != "1.0.0"
    assert g["diff"] == git(inbox.repo, "diff", base, "--", PRD) and g["diff"]
    assert g["diff_truncated"] is False


def test_the_cards_of_the_other_kinds_carry_the_fields_the_page_renders(inbox):
    e = inbox.gate("error-class:E-003")
    assert e["class"] == "code bug" and e["diagnosis"] == "wrong key"
    d = inbox.gate(f"deploy-step:{inbox.run_id}:3")
    assert (d["run"], d["step"]) == (inbox.run_id, 3)
    assert d["env"] == "production" and d["actor"] == "human" and d["do"] and "check" in d
    s = inbox.gate("signoff:T-001.4")
    assert s["tid"] == "T-001.4" and s["owner"] and "input" in s and "expect" in s
    assert inbox.gate(f"adoption:{AREA}")["area"] == AREA


def test_a_deploy_step_gate_shows_once_in_the_first_group(inbox):
    gate_id = f"deploy-step:{inbox.run_id}:3"
    first, second = ({g["id"] for g in grp["gates"]} for grp in inbox.gates()["worktrees"])
    assert gate_id in first and gate_id not in second
    assert gate_id in {g.id for g in gates.list_gates(model.load(inbox.second / PRD), inbox.second)}  # still pending there


def test_wait_in_the_second_worktree_sees_a_deploy_step_answered_from_the_first(inbox):
    gate_id, box = f"deploy-step:{inbox.run_id}:3", {}

    def waiting():
        box["r"] = gates.wait_gate(inbox.repo / PRD, gate_id, worktree=inbox.second, timeout=30, poll=0.05)

    t = threading.Thread(target=waiting)
    t.start()
    time.sleep(0.5)
    status, out = inbox.post(gate_id, "send", "deploy production")
    assert status == 200, out
    t.join(40)
    [line] = inbox.log()
    assert line["worktree"] == str(inbox.repo)
    code, outcome = box["r"]
    assert code == 0 and outcome["reply"] == "deploy production (form)" and outcome["worktree"] == str(inbox.second)


def test_a_broken_gate_shows_the_error_and_keeps_the_group(inbox, monkeypatch):
    def broken(*a, **k):
        raise ValueError("the verdict cannot be read")

    monkeypatch.setattr(gates, "_approval_card", broken)
    first, second = inbox.gates()["worktrees"]
    assert Path(first["path"]) == inbox.repo and first["gates"] == [] and first["error"] == "ValueError: the verdict cannot be read"
    assert "error" not in second and "error-class:E-003" in {g["id"] for g in second["gates"]}


def test_a_diff_over_200_kb_is_cut(inbox):
    from inbox_fixture import verdict

    big = inbox.repo / PRD / "contracts/custom/sample.lkml"
    big.write_text(big.read_text(encoding="utf-8") + "# padding line\n" * 20000, encoding="utf-8")
    verdict(inbox.repo)  # the review again, for the new digest
    g = inbox.gate("approval:main")
    full = git(inbox.repo, "diff", git(inbox.repo, "merge-base", "HEAD", "main").strip(), "--", PRD)
    assert len(full.encode("utf-8")) > 200 * 1024
    assert g["diff_truncated"] is True and len(g["diff"].encode("utf-8")) <= 200 * 1024 and full.startswith(g["diff"])


def test_script_text_comes_back_as_text_inside_json(inbox):
    g = inbox.gate("error-class:E-003")
    assert g["evidence"] == [f"T-001.3 fails: {SCRIPT}"]
    status, items = inbox.call(f"/adoption/{AREA}/items?wt={inbox.repo}")
    assert status == 200 and SCRIPT in items["items"][0]["text"]


# --- POST /answer, one kind and button per fixture (R19/R21: an error-class or signoff commit withdraws the approval) ---

def owner_text(box, kind):
    if kind == "approval":
        return git(box.repo, "log", "-1", "--format=%B")
    if kind == "approval-changes":
        return json.loads((box.repo / PRD / ".prd-review.json").read_text(encoding="utf-8"))["owner"]["reply"]
    if kind == "error-class":
        return (box.repo / PRD / "errors.md").read_text(encoding="utf-8")
    if kind == "deploy-step":
        from prdlint import deploy
        return "\n".join(r["reply"] for r in deploy.read_log(box.repo, box.run_id) if r.get("kind") == "confirm")
    return (box.repo / PRD / "testing.md").read_text(encoding="utf-8")


CASES = [
    ("approval:main", "approval", "approve", "ship it", {}, "Approve: ship it (form)", "approve"),
    ("approval:main", "approval-changes", "changes", "  not yet  ", {}, "Request changes: not yet (form)", "changes"),
    ("error-class:E-003", "error-class", "confirm", "", {}, "Confirm the class (form)", "confirm"),
    ("error-class:E-003", "error-class", "correct", "the PRD never says", {"class": "spec gap"},
     "Correct it to spec gap: the PRD never says (form)", "correct"),
    ("deploy-step", "deploy-step", "send", "deploy production", {}, "deploy production (form)", "confirm"),
    ("signoff:T-001.4", "signoff", "pass", "", {}, "Pass (form)", "pass"),
]


@pytest.mark.parametrize("gate_id,kind,button,words,extra,reply,choice", CASES, ids=[f"{c[1]}-{c[2]}" for c in CASES])
def test_each_button_reaches_the_owner_and_the_log(inbox, gate_id, kind, button, words, extra, reply, choice):
    if gate_id == "deploy-step":
        gate_id = f"deploy-step:{inbox.run_id}:3"
    assert gates.build_reply(kind.split("-changes")[0], button, words, extra.get("class"))[0] == reply
    status, out = inbox.post(gate_id, button, words, **extra)
    assert status == 200, out
    assert out["gate"] == gate_id and out["result"]["exit"] == 0
    if kind != "signoff":  # a Sign-offs row has no reply column: the reply lives in the log only
        assert reply in owner_text(inbox, kind)
    if gate_id == "error-class:E-003" and button == "correct":
        assert "Classification: spec gap" in owner_text(inbox, kind)
    if kind == "signoff":
        assert "| T-001.4 | Sample Owner |" in owner_text(inbox, kind) and "| pass |" in owner_text(inbox, kind)
    [line] = inbox.log()
    assert line["by"] == "form" and line["reply"] == reply and line["gate"] == gate_id and line["choice"] == choice
    assert line["worktree"] == str(inbox.repo)
    assert inbox.gates()["answers"] == [line]
    assert gate_id not in {g["id"] for g in inbox.group(inbox.repo)["gates"]}


def test_build_reply_maps_every_button():
    assert gates.build_reply("approval", "approve", "") == ("Approve (form)", {"choice": "approve"})
    assert gates.build_reply("approval", "changes", "x") == ("Request changes: x (form)", {"choice": "changes"})
    assert gates.build_reply("error-class", "confirm", " ok ") == ("Confirm the class: ok (form)", {"choice": "confirm"})
    assert gates.build_reply("error-class", "correct", "w", "code bug") == ("Correct it to code bug: w (form)", {"choice": "correct", "cls": "code bug"})
    assert gates.build_reply("deploy-step", "send", " go \n") == ("go (form)", {})
    assert gates.build_reply("signoff", "pass", "") == ("Pass (form)", {"result": "pass"})
    assert gates.build_reply("signoff", "fail", "broken") == ("Fail: broken (form)", {"result": "fail"})
    for kind, button, cls in (("approval", "changes", None), ("error-class", "correct", "spec gap"), ("error-class", "correct", None),
                              ("deploy-step", "send", None), ("signoff", "fail", None)):
        with pytest.raises(gates.NeedsWords):
            gates.build_reply(kind, button, "  ", cls)
    with pytest.raises(gates.NeedsWords):
        gates.build_reply("error-class", "correct", "words", None)
    with pytest.raises(gates.Refused):
        gates.build_reply("approval", "pass", "")
    with pytest.raises(gates.Refused, match="must be one of"):
        gates.build_reply("error-class", "correct", "words", "nonsense")


def test_a_button_that_needs_words_or_a_class_is_400_and_writes_nothing(inbox):
    before, heads = snapshot(inbox.repo, inbox.second), head(inbox.repo)
    for gate_id, button, extra in (("approval:main", "changes", {}), ("error-class:E-003", "correct", {"class": "spec gap"}),
                                   (f"deploy-step:{inbox.run_id}:3", "send", {}), ("signoff:T-001.4", "fail", {})):
        status, out = inbox.post(gate_id, button, "   ", **extra)
        assert status == 400 and out["error"], (gate_id, out)
    status, out = inbox.post("error-class:E-003", "correct", "it is a spec gap")
    assert status == 400 and "class" in out["error"]
    assert snapshot(inbox.repo, inbox.second) == before and head(inbox.repo) == heads
    assert inbox.log() == [] and not gates.log_path(inbox.repo).exists()


def test_a_changed_gate_or_question_is_409_and_a_missing_question_400(inbox):
    shown = inbox.gate("error-class:E-003")
    errors = inbox.repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8").replace("Classification: code bug\nTouches: FR-001\nEvidence",
                                                                 "Classification: environment\nTouches: FR-001\nEvidence"), encoding="utf-8")
    before = snapshot(inbox.repo)
    status, out = inbox.post("error-class:E-003", "confirm", question=shown["question"])
    assert status == 409 and out["error"] == "refused: the gate changed; list again"
    status, _ = inbox.post("signoff:T-001.4", "pass", question="Some other question?")
    assert status == 409
    body = {"worktree": str(inbox.repo), "gate": "signoff:T-001.4", "choice": "pass", "words": ""}
    status, out = inbox.call("/answer", body)
    assert status == 400 and "question" in out["error"]
    assert snapshot(inbox.repo) == before and inbox.log() == []


def test_a_nul_in_the_words_is_400_with_the_refusal(inbox):
    before = snapshot(inbox.repo)
    status, out = inbox.post("approval:main", "approve", "yes\x00no")
    assert status == 400 and "NUL" in out["error"]
    assert snapshot(inbox.repo) == before and inbox.log() == []


def test_a_signoff_sends_result_only(inbox, monkeypatch):
    seen = []
    real = gates.answer

    def spy(*a, **kw):
        seen.append(kw)
        return real(*a, **kw)

    monkeypatch.setattr(gates, "answer", spy)
    status, out = inbox.post("signoff:T-001.4", "pass", "", **{"class": "code bug", "item": "E-003"})
    assert status == 200, out
    [kw] = seen
    assert kw["result"] == "pass" and kw.get("cls") is None and kw.get("item") is None and kw.get("choice") is None
    assert kw["by"] == "form" and isinstance(kw["question"], str) and kw["question"]


def test_a_signoff_fail_keeps_the_words_in_the_log_and_the_outcome(inbox):
    box = {}

    def waiting():
        box["r"] = gates.wait_gate(inbox.repo / PRD, "signoff:T-001.4", timeout=30, poll=0.05)

    t = threading.Thread(target=waiting)
    t.start()
    time.sleep(0.5)
    status, out = inbox.post("signoff:T-001.4", "fail", "the order page shows closed")
    assert status == 200, out
    t.join(40)
    reply = "Fail: the order page shows closed (form)"
    assert "| T-001.4 | Sample Owner |" in owner_text(inbox, "signoff") and "| fail |" in owner_text(inbox, "signoff")
    [line] = inbox.log()
    assert line["reply"] == reply and line["choice"] == "fail" and line["by"] == "form"
    code, outcome = box["r"]
    assert code == 0 and outcome["reply"] == reply and outcome["by"] == "form"


# --- the adoption routes ---

def adoption(box, verb, root, body=None):
    if verb == "done" and body is None:  # Done sends the adoption gate's question, as the page shows it
        body = {"question": box.gate(f"adoption:{AREA}", root)["question"]}
    return box.call(f"/adoption/{AREA}/{verb}?wt={root}", body if body is not None else ({} if verb != "items" else None))


def test_adoption_through_the_second_worktree_touches_only_its_file(inbox):
    first = confirm.answers_path(inbox.repo, AREA)
    first_before = first.read_bytes()
    status, items = adoption(inbox, "items", inbox.second)
    assert status == 200 and [i["id"] for i in items["items"]] == ["E-003"] and items["open"] == ["E-003"]
    assert items["items"][0]["summary"] == "E-003: the importer reads the wrong key."
    status, out = adoption(inbox, "answer", inbox.second, {"id": "E-003", "decision": "bug", "text": "a real bug"})
    assert status == 200 and out["open"] == []
    status, out = adoption(inbox, "done", inbox.second)
    assert status == 200 and out["open"] == []
    data = json.loads(confirm.answers_path(inbox.second, AREA).read_text(encoding="utf-8"))
    assert data["done"] is True and data["summaries"] == {"E-003": "E-003: the importer reads the wrong key."}
    assert data["answers"]["E-003"]["decision"] == "bug"
    assert first.read_bytes() == first_before
    [line] = inbox.log()
    assert line["gate"] == f"adoption:{AREA}" and line["choice"] == "done" and line["reply"] == "Done (form)"
    assert line["by"] == "form" and line["worktree"] == str(inbox.second)
    assert f"adoption:{AREA}" not in {g["id"] for g in inbox.group(inbox.second)["gates"]}
    assert f"adoption:{AREA}" in {g["id"] for g in inbox.group(inbox.repo)["gates"]}
    # an answer after done removes it: the gate is pending again
    status, _ = adoption(inbox, "answer", inbox.second, {"id": "E-003", "decision": "ask", "text": "is it?"})
    assert status == 200
    assert "done" not in json.loads(confirm.answers_path(inbox.second, AREA).read_text(encoding="utf-8"))
    assert f"adoption:{AREA}" in {g["id"] for g in inbox.group(inbox.second)["gates"]}


def test_adoption_done_is_409_while_an_item_is_open_or_changed(inbox):
    status, out = adoption(inbox, "done", inbox.repo)
    assert status == 409 and out["open"] == ["E-003"]
    assert adoption(inbox, "answer", inbox.repo, {"id": "E-003", "decision": "intended"})[0] == 200
    errors = inbox.repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8").replace("Diagnosis: wrong key", "Diagnosis: the wrong column"), encoding="utf-8")
    status, out = adoption(inbox, "done", inbox.repo)
    assert status == 409 and out["open"] == ["E-003"]
    assert "done" not in json.loads(confirm.answers_path(inbox.repo, AREA).read_text(encoding="utf-8"))
    assert inbox.log() == []


def test_adoption_done_needs_the_question_and_refuses_a_changed_one(inbox):
    assert adoption(inbox, "answer", inbox.repo, {"id": "E-003", "decision": "intended"})[0] == 200
    shown = inbox.gate(f"adoption:{AREA}")["question"]
    before = confirm.answers_path(inbox.repo, AREA).read_bytes()
    for body in ({}, {"question": None}, {"question": 3}):
        status, out = adoption(inbox, "done", inbox.repo, body)
        assert status == 400 and "question" in out["error"], body
    status, out = adoption(inbox, "done", inbox.repo, {"question": shown + " (old)"})
    assert status == 409 and out["error"] == "refused: the gate changed; list again"
    assert confirm.answers_path(inbox.repo, AREA).read_bytes() == before and inbox.log() == []
    status, out = adoption(inbox, "done", inbox.repo, {"question": shown})
    assert status == 200 and inbox.log()[0]["reply"] == "Done (form)"


def test_adoption_undo_and_bad_answers(inbox):
    assert adoption(inbox, "answer", inbox.repo, {"id": "NOPE", "decision": "bug", "text": "x"})[0] == 400
    assert adoption(inbox, "answer", inbox.repo, {"id": "E-003", "decision": "confirm"})[0] == 400
    assert adoption(inbox, "answer", inbox.repo, {"id": "E-003", "decision": "bug"})[0] == 400
    assert adoption(inbox, "answer", inbox.repo, {"id": "E-003", "decision": "intended"})[0] == 200
    status, out = adoption(inbox, "undo", inbox.repo, {"id": "E-003"})
    assert status == 200 and out["open"] == ["E-003"]
    assert inbox.call(f"/adoption/nope/items?wt={inbox.repo}")[0] == 404


def test_a_path_that_is_not_a_worktree_is_404(inbox, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert inbox.call(f"/adoption/{AREA}/items?wt={elsewhere}")[0] == 404
    assert adoption(inbox, "answer", elsewhere, {"id": "E-003", "decision": "intended"})[0] == 404
    assert inbox.call(f"/adoption/{AREA}/items")[0] == 400
    body = {"worktree": str(elsewhere), "gate": "error-class:E-003", "choice": "confirm", "words": "", "question": "q"}
    assert inbox.call("/answer", body)[0] == 404
    assert inbox.log() == []


# --- Review Focus ---

def test_rf1_words_reach_the_owner_and_the_log_verbatim_once(inbox):
    words = f"{QUOTED}\nship it"
    reply = f"Approve: {words} (form)"
    body = {"worktree": str(inbox.repo), "gate": "approval:main", "choice": "approve", "words": f"  {words}\n",
            "question": inbox.gate("approval:main")["question"]}
    status, out = inbox.call("/answer", body)
    assert status == 200, out
    assert f'Reply: "{reply}"' in git(inbox.repo, "log", "-1", "--format=%B")
    [line] = inbox.log()
    assert line["reply"] == reply and line["reply"].count(" (form)") == 1
    status, _ = inbox.call("/answer", body)  # the same body again: the gate is gone
    assert status == 409
    assert len(inbox.log()) == 1


def test_rf2_two_answers_at_once_one_wins(inbox):
    question = inbox.gate("approval:main")["question"]
    statuses = []
    barrier = threading.Barrier(2)

    def go():
        barrier.wait()
        statuses.append(inbox.post("approval:main", "approve", "yes", question=question)[0])

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(120)
    assert sorted(statuses) == [200, 409]
    assert len(inbox.log()) == 1


def test_rf3_a_removed_worktree_drops_its_group(inbox):
    subprocess.run(["git", "worktree", "remove", "--force", str(inbox.second)], cwd=inbox.repo, check=True, capture_output=True)
    doc = inbox.gates()
    assert [Path(g["path"]) for g in doc["worktrees"]] == [inbox.repo]


def test_adoption_routes_raise_refused_and_the_confirm_form_uses_them(tmp_path):
    from confirm_fixture import make_confirm_repo

    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    routes = confirm.AdoptionRoutes(p, "notes", repo)
    listing = routes.items()
    assert listing["area"] == "notes" and listing["open"] == [i["id"] for i in listing["items"]]
    for bad in ({"id": "NOPE", "decision": "confirm"}, {"id": "FR-001", "decision": "nonsense"}, {"id": "FR-001", "decision": "correct"}):
        with pytest.raises(confirm.Refused):
            routes.answer(bad)
    with pytest.raises(confirm.Refused):
        routes.undo({"id": ["x"]})
    with pytest.raises(confirm.StillOpen):
        routes.done()
    assert "FR-001" not in routes.answer({"id": "FR-001", "decision": "confirm"})["open"]
    assert "FR-001" in routes.undo({"id": "FR-001"})["open"]
    server, _ = confirm.make_server(p, "notes", confirm.build_items(p, "notes"), {}, "<html></html>")
    try:
        assert isinstance(server.state.routes, confirm.AdoptionRoutes)
    finally:
        server.server_close()


def test_a_class_not_in_the_list_is_400_before_anything_runs(inbox):
    before = snapshot(inbox.repo)
    status, out = inbox.post("error-class:E-003", "correct", "it is something else", **{"class": "not a class"})
    assert status == 400 and "spec gap" in out["error"]
    assert snapshot(inbox.repo) == before and inbox.log() == []


def test_an_owner_refusal_is_400_with_its_words(inbox, monkeypatch):
    monkeypatch.setattr(gates, "_run", lambda *a: {"stdout": [], "exit": 1, "stderr": ["refused: lint exits 1"]})
    status, out = inbox.post(f"deploy-step:{inbox.run_id}:3", "send", "deploy production")
    assert status == 400 and out["result"]["exit"] == 1 and out["error"] == "refused: lint exits 1"
    assert inbox.log() == []


def test_a_deploy_step_its_owner_refuses_is_400_with_its_words(inbox, monkeypatch):
    # another session confirms step 3 between the listing and prd_deploy.py confirm, which then refuses (its exit 2)
    from prdlint import deploy

    real = gates._run

    def raced(*argv):
        deploy.append(inbox.repo, inbox.run_id, {"kind": "confirm", "step": 3, "reply": "elsewhere", "at": "t"})
        return real(*argv)

    monkeypatch.setattr(gates, "_run", raced)
    status, out = inbox.post(f"deploy-step:{inbox.run_id}:3", "send", "deploy production")
    assert (status, out["result"]["exit"]) == (400, 2)
    assert out["error"] == "prd_deploy: step 3 already has a confirm record"
    assert inbox.log() == []


def test_a_deploy_step_tool_error_stays_500(inbox, monkeypatch):
    monkeypatch.setattr(gates, "_run", lambda *a: {"stdout": [], "exit": 2, "stderr": ["prd_deploy: internal error: OSError: disk"]})
    status, out = inbox.post(f"deploy-step:{inbox.run_id}:3", "send", "deploy production")
    assert status == 500 and out["error"] == "prd_deploy: internal error: OSError: disk"
