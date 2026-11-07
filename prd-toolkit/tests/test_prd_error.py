"""prd_error.py: the errors.md writes (new, propose, confirm, resolve, list) and /prd-status by state."""
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE
from prdlint import deploy, errors, model, status

TODAY = date(2026, 11, 3)
SCRIPT = Path(__file__).resolve().parent.parent / "scripts/prd_error.py"
TEMPLATE = Path(__file__).resolve().parent.parent / "templates/prd/errors.md"


def ledger(prd):
    return model.load(prd).errors_ledger


def new(prd, **kw):
    args = dict(title="Greeting drops a word", source="user report (/prd-error)", touches=["FR-001"],
                evidence=["`greet x` prints y"], today=TODAY)
    args.update(kw)
    return errors.new(model.load(prd), args["title"], args["source"], args["touches"], args["evidence"], args["today"])


def refused(fn, *a, **kw):
    with pytest.raises(deploy.Refused) as e:
        fn(*a, **kw)
    return e.value.reasons


def test_new_appends_next_number(prd):
    assert new(prd) == "E-002"
    e = ledger(prd)["E-002"]
    assert (e.detected, e.classification, e.state, e.resolution) == ("2026-11-03, user report (/prd-error)", "unclassified", "unclassified", "-")
    assert (e.diagnosis, e.recurrence, e.evidence, e.touches[0][0]) == ("-", "-", ["`greet x` prints y"], "FR-001")
    assert ledger(prd)["E-001"].open is False


def test_new_number_is_max_plus_one(prd):
    text = (prd / "errors.md").read_text().rstrip("\n")
    (prd / "errors.md").write_text(text + "\n\n### E-009 b\nClassification: code bug\n\n### E-004 c\nClassification: code bug\n")
    assert new(prd) == "E-010"


def test_new_replaces_placeholder(prd):
    (prd / "errors.md").write_text(TEMPLATE.read_text())
    assert new(prd) == "E-001"
    text = (prd / "errors.md").read_text()
    assert "No entries yet" not in text and list(ledger(prd)) == ["E-001"]
    assert text.startswith("<!-- Format") and "# Error ledger" in text


def test_new_refuses_unknown_touches(prd):
    assert refused(new, prd, touches=["FR-999"]) == ["Touches: FR-999 is not defined in the PRD"]


def test_new_refuses_long_evidence(prd):
    assert refused(new, prd, evidence=[f"l{i}" for i in range(21)]) == ["Evidence: is 21 lines; at most 20"]
    assert list(ledger(prd)) == ["E-001"]


def test_new_without_touches_or_evidence(prd):
    assert new(prd, touches=[], evidence=[]) == "E-002"
    e = ledger(prd)["E-002"]
    assert e.touches == [] and e.evidence == []
    assert "Touches:" not in "\n".join(errors.entry_lines(model.load(prd), "E-002"))


def test_new_multiline_evidence_round_trips(prd):
    new(prd, evidence=["$ greet x", "  indented", "Hello"])
    assert ledger(prd)["E-002"].evidence == ["$ greet x", "  indented", "Hello"]


def test_deploy_source_passes_deploy_close(prd):
    run = "20261103T101010Z-ab12"
    new(prd, source=f"deploy run {run}, failed step 1")
    detected = "Detected: " + ledger(prd)["E-002"].detected
    assert deploy.detected_names_failure(detected, run, 1)
    assert not deploy.detected_names_failure(detected, run, 2)


def test_propose_then_confirm(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "code bug", "AC-001.1 says whole name", None)
    assert ledger(prd)["E-002"].state == "proposed"
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    e = ledger(prd)["E-002"]
    assert e.state == "confirmed" and e.confirmed == ("2026-11-03", "yes")
    assert '\nConfirmed: 2026-11-03, "yes"\n' in (prd / "errors.md").read_text()
    assert (e.classification, e.diagnosis, e.recurrence) == ("code bug", "AC-001.1 says whole name", "-")


def test_propose_writes_recurrence_and_canonical_order(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "spec gap", "d", "E-001")
    errors.confirm(model.load(prd), "E-002", "ok", TODAY)
    keys = [ln.split(":")[0] for ln in errors.entry_lines(model.load(prd), "E-002")[1:]]
    assert keys == ["Detected", "Classification", "Confirmed", "Touches", "Evidence", "Diagnosis", "Resolution", "Recurrence of"]
    assert ledger(prd)["E-002"].recurrence == "E-001"


def test_confirm_collapses_reply(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", 'yes, "code bug"\nfor sure', TODAY)
    assert ledger(prd)["E-002"].confirmed == ("2026-11-03", 'yes, "code bug" for sure')


def test_confirm_with_class(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "it is a spec gap", TODAY, cls="spec gap")
    assert ledger(prd)["E-002"].classification == "spec gap"


def test_confirm_refusals(prd):
    new(prd)
    assert refused(errors.confirm, model.load(prd), "E-002", "yes", TODAY) == ["E-002 is unclassified; propose a class first"]
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    assert refused(errors.confirm, model.load(prd), "E-002", "yes", TODAY) == ["E-002 is already confirmed"]
    with pytest.raises(ValueError):
        errors.confirm(model.load(prd), "E-002", "  \n ", TODAY)
    assert refused(errors.confirm, model.load(prd), "E-009", "yes", TODAY) == ["E-009 is not an entry"]


def test_propose_refusals(prd):
    new(prd)
    with pytest.raises(ValueError):
        errors.propose(model.load(prd), "E-002", "unclassified", "d", None)
    with pytest.raises(ValueError):
        errors.propose(model.load(prd), "E-002", "bogus", "d", None)
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    assert refused(errors.propose, model.load(prd), "E-002", "spec gap", "d", None) == ["E-002 is confirmed; its class is settled"]


def confirmed(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)


def resolution(prd):
    return ledger(prd)["E-002"].resolution


def test_resolve_forms(prd):
    confirmed(prd)
    errors.resolve(model.load(prd), "E-002", t="T-001.3", level="unit", version="1.2.1", commit="a1b2c3d", run=None, not_a_defect=None)
    assert resolution(prd) == "T-001.3 [unit], PRD 1.2.1, fixed in a1b2c3d" and ledger(prd)["E-002"].state == "resolved"
    for kw, want in (
        (dict(t=None, level=None, version="1.2.1", commit=None, run="20261103T101010Z-ab12", not_a_defect=None), "-, PRD 1.2.1, run 20261103T101010Z-ab12"),
        (dict(t="T-001.3", level=None, version="1.2.1", commit=None, run="r1", not_a_defect=None), "T-001.3, PRD 1.2.1, run r1"),
        (dict(t=None, level=None, version="", commit=None, run=None, not_a_defect="works as specified"), "not a defect: works as specified"),
    ):
        (prd / "errors.md").write_text((prd / "errors.md").read_text().replace(f"Resolution: {resolution(prd)}", "Resolution: -"))
        errors.resolve(model.load(prd), "E-002", **kw)
        assert resolution(prd) == want


def test_resolve_unconfirmed(prd):
    new(prd)
    kw = dict(t="T-001.3", level="unit", version="1.2.1", commit="a1b2c3d", run=None, not_a_defect=None)
    assert refused(errors.resolve, model.load(prd), "E-002", **kw) == ["E-002 is not confirmed"]


def test_resolve_bad_forms(prd):
    confirmed(prd)
    base = dict(t="T-001.3", level="unit", version="1.2.1", commit="a1b2c3d", run=None, not_a_defect=None)
    for bad in (dict(commit="xyz"), dict(commit="abc12"), dict(version="1.2"), dict(t="T-1"), dict(t=None), dict(run="r1"),
                dict(commit=None), dict(level=None)):
        with pytest.raises(ValueError):
            errors.resolve(model.load(prd), "E-002", **{**base, **bad})
    assert resolution(prd) == "-"


def test_list(prd):
    new(prd)
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    assert errors.list_lines(model.load(prd), False) == [
        "E-001 resolved code bug - Empty import file crashed the importer",
        "E-002 confirmed code bug FR-001 Greeting drops a word"]
    assert errors.list_lines(model.load(prd), True) == ["E-002 confirmed code bug FR-001 Greeting drops a word"]


def test_status_open_errors_by_state(prd):
    new(prd)
    new(prd, title="Other", touches=[])
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    texts = [i.text for i in status._open_errors(model.load(prd))]
    assert texts == ["E-002 confirmed code bug — Greeting drops a word", "E-003 unclassified — Other"]


def run(prd, *args):
    import os
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)


def test_cli_exit_codes(prd):
    r = run(prd, "new", str(prd), "--title", "Greeting drops a word", "--source", "user report", "--touches", "FR-001")
    assert (r.returncode, r.stdout.strip()) == (0, "E-002")
    r = run(prd, "new", str(prd), "--title", "x", "--source", "s", "--touches", "FR-999")
    assert r.returncode == 1 and r.stderr.strip() == "refused: Touches: FR-999 is not defined in the PRD" and r.stdout == ""
    r = run(prd, "confirm", str(prd), "E-002", "--reply", "yes")
    assert r.returncode == 1 and "refused: E-002 is unclassified" in r.stderr
    r = run(prd, "propose", str(prd), "E-002", "--class", "bogus", "--diagnosis", "d")
    assert r.returncode == 2 and r.stdout == ""
    r = run(prd, "frobnicate", str(prd))
    assert r.returncode == 2 and r.stdout == ""
    r = run(prd, "list", str(prd.parent / "nowhere"))
    assert r.returncode == 2 and r.stdout == ""


def test_cli_full_loop_and_list(prd, tmp_path):
    ev = tmp_path / "ev.txt"
    ev.write_text("$ greet x\nbad\n")
    assert run(prd, "new", str(prd), "--title", "T", "--source", "s", "--evidence-file", str(ev)).stdout.strip() == "E-002"
    assert run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "d", "--recurrence", "E-001").returncode == 0
    assert run(prd, "confirm", str(prd), "E-002", "--reply", 'yes "x"\nok').returncode == 0
    r = run(prd, "resolve", str(prd), "E-002", "--t", "T-001.3", "--version", "1.0.1", "--commit", "abcdef1")
    assert r.returncode == 0, r.stderr
    assert resolution(prd) == "T-001.3 [integration], PRD 1.0.1, fixed in abcdef1" or resolution(prd).startswith("T-001.3 [")
    assert run(prd, "list", str(prd), "--open").stdout == ""
    assert run(prd, "list", str(prd)).stdout.splitlines()[-1].startswith("E-002 resolved code bug")
    r = run(prd, "resolve", str(prd), "E-002", "--t", "T-999.9", "--version", "1.0.1", "--commit", "abcdef1")
    assert r.returncode == 1 and "T-999.9" in r.stderr


def test_propose_touches_writes_canonical_order(prd):
    new(prd, touches=[])
    errors.propose(model.load(prd), "E-002", "code bug", "d", None, ["FR-001"])
    errors.confirm(model.load(prd), "E-002", "ok", TODAY)
    keys = [ln.split(":")[0] for ln in errors.entry_lines(model.load(prd), "E-002")[1:]]
    assert keys == ["Detected", "Classification", "Confirmed", "Touches", "Evidence", "Diagnosis", "Resolution", "Recurrence of"]
    assert ledger(prd)["E-002"].touches[0][0] == "FR-001"


def test_propose_touches_replaces_an_existing_line(prd):
    new(prd, touches=["FR-001"])
    errors.propose(model.load(prd), "E-002", "code bug", "d", None, ["FR-001", "FR-002"])
    entry = (prd / "errors.md").read_text().split("### E-002", 1)[1]
    assert entry.count("Touches:") == 1 and "Touches: FR-001, FR-002\n" in entry
    assert [t for t, *_ in ledger(prd)["E-002"].touches] == ["FR-001", "FR-002"]


def test_propose_without_touches_leaves_the_line_alone(prd):
    new(prd, touches=["FR-001"])
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    assert [t for t, *_ in ledger(prd)["E-002"].touches] == ["FR-001"]


def test_propose_refuses_unknown_touches_and_writes_nothing(prd):
    new(prd, touches=[])
    before = (prd / "errors.md").read_text()
    assert refused(errors.propose, model.load(prd), "E-002", "code bug", "d", None, ["FR-999"]) == ["Touches: FR-999 is not defined in the PRD"]
    assert (prd / "errors.md").read_text() == before


def test_cli_propose_touches(prd):
    run(prd, "new", str(prd), "--title", "T", "--source", "s")
    r = run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "d", "--touches", "FR-999")
    assert r.returncode == 1 and r.stderr.strip() == "refused: Touches: FR-999 is not defined in the PRD" and r.stdout == ""
    r = run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "d", "--touches", "FR-001")
    assert r.returncode == 0, r.stderr
    assert "Touches: FR-001\n" in (prd / "errors.md").read_text().split("### E-002", 1)[1]


def _errors_bytes(prd):
    return (prd / "errors.md").read_bytes()


def _propose(prd, diagnosis):
    return run(prd, "propose", str(prd), "E-001", "--class", "code bug", "--diagnosis", diagnosis)


def _entry_unclassified(prd):
    assert run(prd, "new", str(prd), "--title", "t", "--source", "s", "--touches", "FR-001").stdout.strip() == "E-002"


def test_propose_with_bare_placeholder_in_diagnosis_is_refused_unchanged(prd):
    _entry_unclassified(prd)
    before = _errors_bytes(prd)
    r = run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "prints usage: greet <name>")
    assert r.returncode == 1 and r.stdout == ""
    lines = r.stderr.strip().splitlines()
    assert lines[0].startswith("refused: the entry would fail lint: errors.md:") and ": placeholder: " in lines[0]
    assert "put quoted output in backticks" in lines[-1]
    assert _errors_bytes(prd) == before


def test_propose_with_backticked_diagnosis_is_written(prd):
    _entry_unclassified(prd)
    r = run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "prints `usage: greet <name>`")
    assert r.returncode == 0, r.stderr
    assert ledger(prd)["E-002"].state == "proposed"


def test_new_with_placeholder_in_evidence_is_written(prd, tmp_path):
    ev = tmp_path / "ev.txt"
    ev.write_text('Actual: prints "usage: greet <name>", exit 2\n')
    r = run(prd, "new", str(prd), "--title", "t", "--source", "s", "--evidence-file", str(ev))
    assert r.returncode == 0, r.stderr


def test_new_with_placeholder_in_title_is_refused(prd):
    before = _errors_bytes(prd)
    r = run(prd, "new", str(prd), "--title", "prints <name>", "--source", "s")
    assert r.returncode == 1 and "refused: the entry would fail lint: errors.md:" in r.stderr
    assert _errors_bytes(prd) == before


def test_existing_findings_elsewhere_do_not_block_a_write(prd):
    _entry_unclassified(prd)
    text = (prd / "errors.md").read_text()
    (prd / "errors.md").write_text(text.replace("### E-002 t", "### E-002 bare <name> title"))
    r = run(prd, "propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "plain words")
    assert r.returncode == 0, r.stderr
    r = run(prd, "confirm", str(prd), "E-002", "--reply", "yes")
    assert r.returncode == 0, r.stderr


def test_parse_touches():
    assert errors.parse_touches("") == []
    assert errors.parse_touches(" - ") == ["-"]
    assert errors.parse_touches("FR-001, UJ-01") == ["FR-001", "UJ-01"]
    for raw in ("-,FR-001", "-, FR-001"):
        assert refused(errors.parse_touches, raw) == ["Touches: - cannot be combined with IDs"]


def test_new_touches_dash(prd):
    new(prd, touches=["-"])
    text = (prd / "errors.md").read_text()
    assert "Touches: -\n" in text and ledger(prd)["E-002"].touches == []


def test_propose_touches_dash(prd):
    new(prd, touches=[])
    errors.propose(model.load(prd), "E-002", "code bug", "d", None, ["-"])
    assert "Touches: -\n" in (prd / "errors.md").read_text()


def test_no_touches_writes_no_line(prd):
    new(prd, touches=[])
    assert "Touches:" not in (prd / "errors.md").read_text()


def test_cli_touches_dash(prd):
    r = run(prd, "new", str(prd), "--title", "T", "--source", "s", "--touches", " - ")
    assert (r.returncode, r.stdout.strip()) == (0, "E-002")
    assert "Touches: -\n" in (prd / "errors.md").read_text()
    for raw in ("-,FR-001", "-, FR-001"):
        r = run(prd, "new", str(prd), "--title", "T", "--source", "s", "--touches", raw)
        assert r.returncode == 1 and r.stderr.strip() == "refused: Touches: - cannot be combined with IDs"
