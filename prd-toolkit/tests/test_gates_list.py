"""prd_gates.py list (0.8.1): every pending human decision of a PRD in one shape."""
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
from prdlint import change, confirm, deploy, gates, model
from test_change_approve import DRY, recorded, repo, verdict  # noqa: F401  (fixtures)

PRD = "docs/prd/orders"
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gates_main(list(argv))
    return code, out.getvalue(), err.getvalue()


def listed(prd, *extra):
    code, out, err = call("list", str(prd), "--json", *extra)
    assert code == 0, err
    doc = json.loads(out)
    assert list(doc)[:2] == ["interface", "kind"] and doc["kind"] == "gates"
    return doc["gates"]


def by_id(gs):
    return {g["id"]: g for g in gs}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def entry(n, cls, confirmed=False, evidence=()):
    ev = "".join(f"{'Evidence: ' if i == 0 else '  '}{line}\n" for i, line in enumerate(evidence))
    return (f"\n### E-{n:03d} Importer reads the wrong key\nDetected: 2026-11-04, test failure in T-001.3\nClassification: {cls}\n"
            + (f'Confirmed: 2026-11-04, "yes"\n' if confirmed else "") + "Touches: FR-001\n" + ev + "Diagnosis: wrong key\nResolution: open\n")


# --- error-class ---

def test_a_proposed_entry_is_a_gate_and_a_confirmed_one_is_not(repo):
    errors = repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + entry(3, "code bug", evidence=["T-001.3 fails: expected 1, got 0"]) + entry(4, "spec gap", confirmed=True), encoding="utf-8")
    gs = by_id(listed(repo / PRD))
    assert set(gs) == {"error-class:E-003"}
    g = gs["error-class:E-003"]
    assert g["kind"] == "error-class" and g["title"] == "Importer reads the wrong key"
    assert g["question"] == "Proposed class: code bug. Confirm it, or correct it to another class."
    assert g["evidence"] == ["T-001.3 fails: expected 1, got 0"] and g["choices"] == ["confirm", "correct"]
    assert g["source"].startswith("errors.md:") and "path" not in g and "items" not in g


def test_evidence_is_capped_at_20_lines(repo):
    errors = repo / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + entry(3, "code bug", evidence=[f"line {n}" for n in range(25)]), encoding="utf-8")
    ev = listed(repo / PRD)[0]["evidence"]
    assert ev == [f"line {n}" for n in range(20)]


# --- deploy-step ---

def human_stop(repo):
    prd = model.load(repo / PRD)
    run_id = deploy.new_run_id(repo, None)
    deploy.start_run(prd, repo, run_id, None)
    deploy.append(repo, run_id, {"kind": "step", "step": 3, "env": "production", "actor": "human", "command": None, "exit": None,
                                 "stdout": "", "stderr": "", "started": "t", "ended": "t", "result": "human"})
    return run_id


def test_a_run_stopped_at_a_human_step_is_a_gate_until_confirmed(repo):
    run_id = human_stop(repo)
    g = by_id(listed(repo / PRD))[f"deploy-step:{run_id}:3"]
    assert g["kind"] == "deploy-step" and g["choices"] == ["confirm"] and g["source"] == "operations.md"
    assert "Approve production" in g["title"] and 'reply "deploy production"' in g["question"]
    r = subprocess.run([sys.executable, str(SCRIPTS / "prd_deploy.py"), "confirm", str(repo / PRD), "--run", run_id, "--step", "3", "--reply", "deploy production"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert listed(repo / PRD) == []


def test_another_prds_run_is_not_listed(repo):
    run_id = human_stop(repo)
    log = deploy.log_dir(repo) / f"{run_id}.jsonl"
    log.write_text(log.read_text(encoding="utf-8").replace('"prd": "docs/prd/orders"', '"prd": "docs/prd/other"'), encoding="utf-8")
    assert listed(repo / PRD) == []


# --- signoff ---

def test_an_acceptance_case_without_a_signoff_row_is_a_gate(repo):
    assert listed(repo / PRD) == []
    testing = repo / PRD / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |\n", ""), encoding="utf-8")
    g = by_id(listed(repo / PRD))["signoff:T-001.4"]
    assert g["kind"] == "signoff" and g["choices"] == ["pass", "fail"] and "Sample Owner" in g["question"]
    assert g["evidence"][0].startswith("Make an import file") and g["source"].startswith("test-cases/import.yaml:")


def test_a_signoff_row_with_no_result_is_still_a_gate(repo):
    testing = repo / PRD / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |", "| T-001.4 | Sample Owner | 2026-10-29 |  |"), encoding="utf-8")
    assert "signoff:T-001.4" in by_id(listed(repo / PRD))


# --- adoption ---

def adopt(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    p = model.load(prd)
    items = confirm.build_items(p, "notes")
    confirm.open_file(p, "notes", items, {}, repo)
    return repo, prd, p, items


def test_adoption_is_pending_until_done(tmp_path):
    repo, prd, p, items = adopt(tmp_path)
    g = by_id(listed(prd))["adoption:notes"]
    assert g["kind"] == "adoption" and g["items"] == [i.id for i in items] and g["source"] == ".prd-confirm-notes.json"
    assert g["choices"][-1] == "done" and {"confirm", "correct", "bug", "ask", "intended", "fix", "answer"} >= set(g["choices"][:-1])
    assert "confirm" in g["choices"] and len(g["choices"]) == len(set(g["choices"]))
    for i in items:  # every item answered: still listed, no open item
        confirm.record_answer(p, "notes", i.id, sorted(confirm.ALLOWED[i.kind])[0], "ok", None, repo)
    g = by_id(listed(prd))["adoption:notes"]
    assert g["items"] == [] and g["choices"] == ["done"]
    confirm.mark_done(p, "notes", items, repo)
    assert "adoption:notes" not in by_id(listed(prd))


def test_no_answers_file_or_an_area_not_extracted_is_no_gate(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    assert listed(prd) == []
    p = model.load(prd)
    confirm.open_file(p, "notes", confirm.build_items(p, "notes"), {}, repo)
    adoption = prd / "adoption.md"
    adoption.write_text(adoption.read_text(encoding="utf-8").replace("extracted", "confirmed"), encoding="utf-8")
    assert listed(prd) == []


# --- approval ---

def test_a_ready_verdict_whose_digest_matches_and_is_pending_is_a_gate(recorded):
    g = by_id(listed(recorded / PRD))
    key = f"approval:{git(recorded, 'rev-parse', '--abbrev-ref', 'HEAD').strip()}"
    assert set(g) == {key} and g[key]["kind"] == "approval" and g[key]["choices"] == ["approve", "changes"]
    assert g[key]["source"] == ".prd-review.json" and DRY in g[key]["evidence"]


def test_a_changed_prd_removes_the_approval_gate(recorded):
    p = recorded / PRD / "features/api.md"
    p.write_text(p.read_text(encoding="utf-8").replace("### FR-002 Get an order", "### FR-002 Get one order"), encoding="utf-8")
    assert listed(recorded / PRD) == []


def test_no_verdict_or_not_ready_or_changes_is_no_gate(recorded):
    verdict(recorded, ready=False, blockers=["owner: not yet"],
            owner={"choice": "changes", "reply": "not yet", "at": "2026-11-04T00:00:00+00:00"})
    assert listed(recorded / PRD) == []
    (recorded / PRD / ".prd-review.json").unlink()
    assert listed(recorded / PRD) == []


def test_an_approved_change_is_no_gate(recorded):
    code = subprocess.run([sys.executable, str(SCRIPTS / "prd_change.py"), "approve", str(recorded / PRD), "--reply", "yes", "--dry-run", DRY],
                          capture_output=True, text=True, encoding="utf-8")
    assert code.returncode == 0, code.stderr
    assert listed(recorded / PRD) == []


def test_a_verdict_with_no_pending_row_is_no_gate(recorded):
    md = recorded / PRD / "prd.md"
    md.write_text(md.read_text(encoding="utf-8").replace("; pending |", "; dry run T-002.3, 0 open |"), encoding="utf-8")
    verdict(recorded)  # digest again, for the edited prd.md
    assert listed(recorded / PRD) == []


def test_worktrees_lists_the_approval_gate_of_another_worktree(recorded):
    other = recorded.parent / "wt"
    git(recorded, "worktree", "add", "-q", "-b", "feature-x", str(other))
    shutil.copytree(recorded / PRD, other / PRD, dirs_exist_ok=True)  # the same recorded change and verdict, in the second worktree
    main_branch = git(recorded, "rev-parse", "--abbrev-ref", "HEAD").strip()
    gs = by_id(listed(recorded / PRD, "--worktrees"))
    assert set(gs) == {f"approval:{main_branch}", "approval:feature-x"}
    assert Path(gs["approval:feature-x"]["path"]).resolve() == other.resolve()
    assert Path(gs[f"approval:{main_branch}"]["path"]).resolve() == recorded.resolve()
    assert set(by_id(listed(recorded / PRD))) == {f"approval:{main_branch}"}  # without the flag, this worktree only
    assert "path" not in by_id(listed(recorded / PRD))[f"approval:{main_branch}"]


# --- order, text, JSON ---

def test_kind_order_then_id_and_the_text_form(recorded):
    errors = recorded / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + entry(9, "code bug") + entry(3, "code bug"), encoding="utf-8")
    testing = recorded / PRD / "testing.md"
    testing.write_text(testing.read_text(encoding="utf-8").replace("| T-001.4 | Sample Owner | 2026-10-29 | pass |\n", ""), encoding="utf-8")
    verdict(recorded)
    ids = [g["id"] for g in listed(recorded / PRD)]
    branch = git(recorded, "rev-parse", "--abbrev-ref", "HEAD").strip()
    assert ids == [f"approval:{branch}", "error-class:E-003", "error-class:E-009", "signoff:T-001.4"]
    code, out, err = call("list", str(recorded / PRD))
    assert code == 0 and err == ""
    lines = out.splitlines()
    assert [ln.split(" ", 1)[0] for ln in lines] == ids and lines[1] == "error-class:E-003 Importer reads the wrong key"


def test_no_gate_prints_nothing_and_json_has_an_empty_list(repo):
    assert call("list", str(repo / PRD)) == (0, "", "")
    doc = json.loads(call("list", str(repo / PRD), "--json")[1])
    assert doc == {"interface": 1, "kind": "gates", "prd": "orders", "gates": []}


def test_usage_errors_exit_2_with_a_json_error(tmp_path):
    code, out, err = call("list", str(tmp_path / "nope"), "--json")
    assert code == 2 and json.loads(out)["kind"] == "gates" and "error" in json.loads(out)
    assert call("--interface") == (0, "1\n", "")
    code, out, _ = call("--json", "--bogus")
    assert code == 2 and json.loads(out)["kind"] == "gates"


def test_gate_dataclass_shape():
    g = gates.Gate("a", "approval", "t", "q", [], ["x"], "s")
    assert g.path is None and g.items is None


# --- final review: a verdict of the wrong shape is no gate, never a crash ---

MALFORMED = [
    {"touches": None}, {"touches": "AC-002.3"}, {"touches": 5}, {"touches": {"a": 1}},
    {"dry_run": "dry run"}, {"dry_run": ["x"]}, {"dry_run": None}, {"dry_run": {"record": 5}},
    {"restate": 5}, {"restate": ["r"]}, {"blockers": "none"}, {"digest": 5}, {"impact": []}, {"bump": "minor"},
    {"head": 1}, {"kind": 1}, {"interface": "1"}, {"owner": "me"},
]


def _write_verdict(recorded, over, drop=()):
    verdict(recorded, **over)
    path = recorded / PRD / ".prd-review.json"
    v = json.loads(path.read_text(encoding="utf-8"))
    for key in drop:
        v.pop(key)
    path.write_text(json.dumps(v), encoding="utf-8")


def test_a_well_formed_verdict_beside_an_error_entry_is_two_gates(recorded):
    errors = recorded / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + entry(3, "code bug"), encoding="utf-8")
    _write_verdict(recorded, {})
    assert [g["kind"] for g in listed(recorded / PRD)] == ["approval", "error-class"]


@pytest.mark.parametrize("over,drop", [(o, ()) for o in MALFORMED] + [({}, ("touches",)), ({}, ("dry_run",))],
                         ids=[next(iter(o)) + "=" + repr(next(iter(o.values()))) for o in MALFORMED] + ["touches-missing", "dry_run-missing"])
def test_a_verdict_of_the_wrong_shape_is_no_gate_and_the_others_stay(recorded, over, drop):
    errors = recorded / PRD / "errors.md"
    errors.write_text(errors.read_text(encoding="utf-8") + entry(3, "code bug"), encoding="utf-8")
    _write_verdict(recorded, over, drop)
    code, out, err = call("list", str(recorded / PRD), "--json")
    assert code == 0, err
    assert [g["id"] for g in json.loads(out)["gates"]] == ["error-class:E-003"]
    code, out, err = call("list", str(recorded / PRD))
    assert code == 0 and out.startswith("error-class:E-003 "), (out, err)


# --- the approval card's diff base in a repository with no main (0.8.2 final review M5) ---

def _git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
                          cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def _trunk_repo(path):
    path.mkdir()
    _git(path, "init", "-q", "-b", "trunk")
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "a")
    return path


def _change_on_a_branch(repo):
    _git(repo, "checkout", "-q", "--no-track", "-b", "feat")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    _git(repo, "add", "b.txt")
    _git(repo, "commit", "-q", "-m", "b")


def test_the_diff_base_ignores_origin_head(tmp_path):
    from prdlint import gates

    origin = _trunk_repo(tmp_path / "origin")
    _git(tmp_path, "clone", "-q", str(origin), "clone")
    repo = tmp_path / "clone"
    _change_on_a_branch(repo)  # no upstream and no main: origin/HEAD alone no longer names a base
    assert _git(repo, "branch", "--list", "main") == ""
    assert gates._diff_base(repo) is None


def test_the_diff_base_ignores_the_default_branch(tmp_path):
    from prdlint import gates

    repo = _trunk_repo(tmp_path / "repo")
    _git(repo, "config", "init.defaultBranch", "trunk")
    _change_on_a_branch(repo)  # no remote, no main
    assert gates._diff_base(repo) is None


def test_the_diff_base_is_the_verdicts_base_else_main(tmp_path):
    from prdlint import gates

    repo = _trunk_repo(tmp_path / "repo")
    _git(repo, "branch", "main")
    first = _git(repo, "rev-parse", "HEAD")
    _change_on_a_branch(repo)
    assert gates._diff_base(repo) == "main"
    assert gates._diff_base(repo, {"base": first}) == first
    assert gates._diff_base(repo, {"base": "0" * 40}) == "main"


# --- (c) a multi-line refs, and a mistyped base, make the verdict the wrong shape ---

def test_multiline_refs_is_no_gate(recorded):
    _write_verdict(recorded, {"refs": "FR-001, FR-002"})
    assert len(listed(recorded / PRD)) == 1
    for bad in ("FR-001\nFR-002", "FR-001\rFR-002"):
        _write_verdict(recorded, {"refs": bad})
        assert listed(recorded / PRD) == []
    _write_verdict(recorded, {"base": 5})
    assert listed(recorded / PRD) == []
    _write_verdict(recorded, {"base": "0" * 40})
    assert len(listed(recorded / PRD)) == 1
