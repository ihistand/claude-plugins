"""prd_gates.py answer (0.8.1): one reply for one gate, passed to the script that owns the decision."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from confirm_fixture import make_confirm_repo
from prd_gates import main as gates_main
from prdlint import confirm, model
from test_change_approve import DRY, FILES, REPLY, recorded, repo, snapshot  # noqa: F401  (fixtures)
from test_change_approve import git as git_out
from test_gates_list import PRD, by_id, entry, human_stop, listed

TODAY_RE = r"\d{4}-\d{2}-\d{2}"
QUOTED = '"sí", then "no"'


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gates_main(list(argv))
    return code, out.getvalue(), err.getvalue()


def answer(prd, gate, reply, *extra):
    return call("answer", str(prd), gate, f"--reply={reply}", *extra)


def doc_of(out):
    doc = json.loads(out)
    assert list(doc)[:2] == ["interface", "kind"] and doc["kind"] == "gates.answer"
    return doc


def refuse(prd, gate, reply, *extra, why="refused: the gate changed; list again"):
    code, out, err = answer(prd, gate, reply, *extra)
    assert code == 1 and out == "" and err.strip() == why, (code, out, err)


def add_errors(repo, *entries):
    errors = repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + "".join(entries), encoding="utf-8")


def branch(repo):
    return git_out(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()


# --- error-class ---

def test_error_class_confirm_reaches_errors_md_verbatim(repo):
    add_errors(repo, entry(3, "code bug"))
    code, out, err = answer(repo / PRD, "error-class:E-003", QUOTED, "--json")
    assert code == 0, err
    doc = doc_of(out)
    assert doc["gate"] == "error-class:E-003" and doc["result"]["exit"] == 0 and isinstance(doc["result"]["stdout"], list)
    assert f'Confirmed: ' in (repo / PRD / "errors.md").read_text(encoding="utf-8")
    assert f', "{QUOTED}"\n' in (repo / PRD / "errors.md").read_text(encoding="utf-8")
    assert "error-class:E-003" not in by_id(listed(repo / PRD))


def test_error_class_multiline_reply_is_the_ledgers_one_line_form(repo):
    add_errors(repo, entry(3, "code bug"))
    assert answer(repo / PRD, "error-class:E-003", 'yes, "sí"\nthen "no"')[0] == 0
    assert 'Confirmed: ' in (repo / PRD / "errors.md").read_text(encoding="utf-8")
    assert ', "yes, "sí" then "no""\n' in (repo / PRD / "errors.md").read_text(encoding="utf-8")


def test_error_class_correct_needs_a_class_and_sets_it(repo):
    add_errors(repo, entry(3, "code bug"))
    refuse(repo / PRD, "error-class:E-003", "no", "--choice", "correct", why="refused: --choice correct needs --class")
    assert answer(repo / PRD, "error-class:E-003", "it is a spec gap", "--choice", "correct", "--class", "spec gap")[0] == 0
    text = (repo / PRD / "errors.md").read_text(encoding="utf-8")
    assert "Classification: spec gap" in text and "Confirmed:" in text


def test_a_reply_that_starts_with_a_dash_is_not_an_option(repo):
    add_errors(repo, entry(3, "code bug"))
    assert answer(repo / PRD, "error-class:E-003", "--class is what I said")[0] == 0
    assert ', "--class is what I said"\n' in (repo / PRD / "errors.md").read_text(encoding="utf-8")


def test_error_class_gone_gate_is_refused(repo):
    add_errors(repo, entry(3, "code bug", confirmed=True))
    refuse(repo / PRD, "error-class:E-003", "yes")
    refuse(repo / PRD, "error-class:E-099", "yes")


# --- deploy-step ---

def test_deploy_step_reply_reaches_the_log_verbatim(repo):
    run_id = human_stop(repo)
    code, out, err = answer(repo / PRD, f"deploy-step:{run_id}:3", REPLY, "--json")
    assert code == 0, err
    assert doc_of(out)["result"]["exit"] == 0
    from prdlint import deploy
    recs = deploy.read_log(repo, run_id)
    assert [r["reply"] for r in recs if r.get("kind") == "confirm"] == [REPLY]
    assert listed(repo / PRD) == []


# --- Review Focus 4: a PRD path with a space ---

@pytest.fixture
def spaced(repo, tmp_path):
    dest = tmp_path / "My Repos" / "repo"
    dest.parent.mkdir()
    shutil.move(str(repo), str(dest))
    git_out(dest, "mv", PRD, "docs/prd/my prd")
    git_out(dest, "commit", "-q", "-m", "move the PRD")
    return dest, dest / "docs/prd/my prd"


def test_a_prd_path_with_a_space_works_for_error_class(spaced):
    repo, prd = spaced
    add_errors_at(prd, entry(3, "code bug"))
    code, out, err = answer(prd, "error-class:E-003", QUOTED)
    assert code == 0, err
    assert f', "{QUOTED}"\n' in (prd / "errors.md").read_text(encoding="utf-8")


def test_a_prd_path_with_a_space_works_for_deploy_step(spaced):
    repo, prd = spaced
    from prdlint import deploy
    run_id = deploy.new_run_id(repo, None)
    deploy.start_run(model.load(prd), repo, run_id, None)
    deploy.append(repo, run_id, {"kind": "step", "step": 3, "env": "production", "actor": "human", "command": None, "exit": None,
                                 "stdout": "", "stderr": "", "started": "t", "ended": "t", "result": "human"})
    code, out, err = answer(prd, f"deploy-step:{run_id}:3", REPLY)
    assert code == 0, err
    assert [r["reply"] for r in deploy.read_log(repo, run_id) if r.get("kind") == "confirm"] == [REPLY]


def add_errors_at(prd, *entries):
    errors = prd / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + "".join(entries), encoding="utf-8")


# --- signoff ---

def drop_signoff(repo):
    testing = repo / PRD / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |\n", ""), encoding="utf-8")
    return testing


def test_signoff_appends_the_row_to_testing_md(repo):
    testing = drop_signoff(repo)
    code, out, err = answer(repo / PRD, "signoff:T-001.4", QUOTED, "--result", "pass", "--json")
    assert code == 0, err
    import datetime
    row = f"| T-001.4 | Sample Owner | {datetime.date.today().isoformat()} | pass |"
    assert row in testing.read_text(encoding="utf-8").splitlines()
    assert doc_of(out)["result"] == {"stdout": [row], "exit": 0}
    assert "signoff:T-001.4" not in by_id(listed(repo / PRD))


def test_signoff_result_is_required_and_choice_must_agree(repo):
    testing = drop_signoff(repo)
    before = testing.read_bytes()
    refuse(repo / PRD, "signoff:T-001.4", "ok", why="refused: signoff needs --result pass|fail")
    refuse(repo / PRD, "signoff:T-001.4", "ok", "--result", "pass", "--choice", "fail", why="refused: --choice fail disagrees with --result pass")
    refuse(repo / PRD, "signoff:T-001.4", "ok", "--result", "maybe", why="refused: --result must be pass or fail")
    assert testing.read_bytes() == before
    assert answer(repo / PRD, "signoff:T-001.4", "ok", "--choice", "fail", "--result", "fail")[0] == 0
    assert "| fail |" in testing.read_text(encoding="utf-8")


def test_signoff_fills_a_row_with_no_result(repo):
    testing = repo / PRD / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |", "| T-001.4 | Sample Owner | 2026-10-29 |  |"), encoding="utf-8")
    assert answer(repo / PRD, "signoff:T-001.4", "ok", "--result", "pass")[0] == 0
    rows = [ln for ln in testing.read_text(encoding="utf-8").splitlines() if ln.startswith("| T-001.4")]
    assert len(rows) == 1 and rows[0].endswith("| pass |")


# --- approval ---

def test_approval_approve_commits_with_the_reply_verbatim(recorded):
    gate = f"approval:{branch(recorded)}"
    code, out, err = answer(recorded / PRD, gate, REPLY, "--json")
    assert code == 0, err
    assert doc_of(out)["result"]["exit"] == 0
    body = git_out(recorded, "log", "-1", "--format=%B")
    assert f'Reply: "{REPLY}"' in body or REPLY.strip() in body
    assert DRY in body
    assert not (recorded / PRD / ".prd-review.json").exists()


def test_approval_changes_writes_the_verdict_and_commits_nothing(recorded):
    gate = f"approval:{branch(recorded)}"
    head, before = git_out(recorded, "rev-parse", "HEAD"), snapshot(recorded)
    code, out, err = answer(recorded / PRD, gate, REPLY, "--choice", "changes", "--json")
    assert code == 0, err
    assert doc_of(out)["gate"] == gate
    assert git_out(recorded, "rev-parse", "HEAD") == head
    after = snapshot(recorded)
    assert {k for k in after if after[k] != before.get(k)} | (set(before) - set(after)) == {f"{PRD}/.prd-review.json"}
    v = json.loads((recorded / PRD / ".prd-review.json").read_text(encoding="utf-8"))
    assert v["ready"] is False and v["blockers"][-1] == f"owner: {REPLY}"
    assert v["owner"]["choice"] == "changes" and v["owner"]["reply"] == REPLY and v["owner"]["at"].endswith("+00:00")
    old = json.loads(before[f"{PRD}/.prd-review.json"])
    assert {k: v[k] for k in old if k not in ("ready", "blockers")} == {k: old[k] for k in old if k not in ("ready", "blockers")}
    assert old["blockers"] == v["blockers"][:-1]
    assert listed(recorded / PRD) == []  # not ready, so the gate is gone
    assert not [p for p in (recorded / PRD).iterdir() if p.name.startswith(".tmp")]


def test_approval_changes_refuses_an_empty_reply_and_a_gate_not_pending(recorded):
    gate = f"approval:{branch(recorded)}"
    before = snapshot(recorded)
    refuse(recorded / PRD, gate, "  \n", "--choice", "changes", why="refused: the reply is empty")
    assert snapshot(recorded) == before
    assert answer(recorded / PRD, gate, "not yet", "--choice", "changes")[0] == 0
    refuse(recorded / PRD, gate, "again", "--choice", "changes")  # no longer pending
    refuse(recorded / PRD, gate, "again")  # approve of a gone gate, too


def test_approval_is_refused_when_the_prd_changed_after_the_review(recorded):
    gate = f"approval:{branch(recorded)}"
    p = recorded / PRD / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8").replace("### FR-002 Get an order", "### FR-002 Get one order"), encoding="utf-8")
    refuse(recorded / PRD, gate, "yes")


# --- adoption ---

def adopt(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    confirm.open_file(p, "notes", items, {}, repo)
    return repo, prd, p, items


def test_adoption_answers_an_item_with_the_reply_verbatim(tmp_path):
    repo, prd, p, items = adopt(tmp_path)
    req = next(i for i in items if i.kind == "requirement")
    code, out, err = answer(prd, "adoption:notes", REPLY, "--item", req.id, "--choice", "confirm", "--json")
    assert code == 0, err
    assert doc_of(out)["result"]["exit"] == 0
    data = json.loads(confirm.answers_path(repo, "notes").read_text(encoding="utf-8"))
    assert data["answers"][req.id]["reply"] == REPLY and data["answers"][req.id]["decision"] == "confirm"
    assert req.id not in by_id(listed(prd))["adoption:notes"]["items"]


def test_adoption_correction_and_decision_checks(tmp_path):
    repo, prd, p, items = adopt(tmp_path)
    req = next(i for i in items if i.kind == "requirement")
    refuse(prd, "adoption:notes", "ok", why="refused: an adoption answer needs --item with --choice, or --choice done")
    refuse(prd, "adoption:notes", "ok", "--item", req.id, why="refused: an adoption answer needs --item with --choice, or --choice done")
    refuse(prd, "adoption:notes", "ok", "--item", req.id, "--choice", "intended", why=f"refused: {req.id} cannot be answered intended; allowed: {', '.join(sorted(confirm.ALLOWED['requirement']))}")
    refuse(prd, "adoption:notes", "ok", "--item", "NOPE-1", "--choice", "confirm", why="refused: unknown item 'NOPE-1'")
    assert answer(prd, "adoption:notes", "the real text", "--item", req.id, "--choice", "correct", "--correction", QUOTED)[0] == 0
    entry_ = json.loads(confirm.answers_path(repo, "notes").read_text(encoding="utf-8"))["answers"][req.id]
    assert entry_["text"] == QUOTED and entry_["reply"] == "the real text"


def test_adoption_done_is_refused_while_an_item_is_open_then_the_gate_is_gone(tmp_path):
    repo, prd, p, items = adopt(tmp_path)
    code, out, err = answer(prd, "adoption:notes", "all settled", "--choice", "done")
    assert code == 1 and err.startswith("refused:") and out == ""
    for i in items:
        d = {"requirement": "confirm", "bug": "intended", "question": "answer", "marker": "answer"}[i.kind]
        assert answer(prd, "adoption:notes", "ok", "--item", i.id, "--choice", d)[0] == 0
    code, out, err = answer(prd, "adoption:notes", "all settled", "--choice", "done", "--json")
    assert code == 0, err
    assert doc_of(out)["result"]["exit"] == 0
    assert "adoption:notes" not in by_id(listed(prd))
    refuse(prd, "adoption:notes", "again", "--choice", "done")


# --- refusals before anything runs ---

def test_an_empty_reply_is_refused_before_anything_runs(repo):
    add_errors(repo, entry(3, "code bug"))
    before = snapshot(repo)
    for reply in ("", "   ", "\n\t "):
        refuse(repo / PRD, "error-class:E-003", reply, why="refused: the reply is empty")
    assert snapshot(repo) == before


def test_a_changed_question_is_refused(repo):
    add_errors(repo, entry(3, "code bug"))
    q = by_id(listed(repo / PRD))["error-class:E-003"]["question"]
    assert answer(repo / PRD, "error-class:E-003", "yes", f"--question={q} (stale)")[0] == 1
    before = snapshot(repo)
    refuse(repo / PRD, "error-class:E-003", "yes", f"--question={q} (stale)")
    assert snapshot(repo) == before
    assert answer(repo / PRD, "error-class:E-003", "yes", f"--question={q}")[0] == 0


def test_a_choice_the_gate_does_not_offer_is_refused(repo):
    add_errors(repo, entry(3, "code bug"))
    refuse(repo / PRD, "error-class:E-003", "yes", "--choice", "approve", why="refused: error-class:E-003 offers confirm, correct, not approve")


def test_text_mode_prints_the_owners_stdout_and_exits_with_its_code(repo):
    add_errors(repo, entry(3, "code bug"))
    code, out, err = answer(repo / PRD, "error-class:E-003", "yes")
    assert code == 0 and out.strip() and err == ""
    code, out, err = answer(repo / PRD, "deploy-step:nope:1", "yes")
    assert code == 1


def test_an_owner_refusal_exits_1(repo):
    add_errors(repo, entry(3, "code bug"))
    # the entry is confirmed behind the gate's back: the owner refuses ("already confirmed") for a gate that was listed
    from prdlint import gates
    orig = gates.list_gates
    listing = orig(model.load(repo / PRD), repo)
    assert any(g.id == "error-class:E-003" for g in listing)
    assert answer(repo / PRD, "error-class:E-003", "first")[0] == 0
    code, out, err = answer(repo / PRD, "error-class:E-003", "second", "--json")
    assert code == 1  # gone: refused by gates itself
