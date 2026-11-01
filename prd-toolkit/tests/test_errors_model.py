"""The 0.6 errors.md entry: new fields, derived state and the error-entries lint rule."""
import pytest
from conftest import edit, fired, lint
from prdlint import model

ENTRY = '''### E-002 Greeting drops a word
Detected: 2026-11-03, user report (/prd-error)
Classification: code bug
Confirmed: 2026-11-03, "yes, it's a code bug"
Touches: FR-001
Evidence: `greet "Ana Maria"` prints `Hello, Ana!`
  and exits 0
Diagnosis: AC-001.1 says the whole argument
Resolution: -
Recurrence of: E-001
'''


def msgs(prd):
    return {(f.rule, f.message) for f in lint(prd)}


def append(prd, text):
    p = prd / "errors.md"
    p.write_text(p.read_text().rstrip("\n") + "\n\n" + text)


def entry(prd, **repl):
    text = ENTRY
    for old, new in repl.items():
        old = old.replace("__", " ")
        assert old in text, old
        text = text.replace(old, new)
    append(prd, text)


def line_of(prd, needle):
    hits = [n for n, ln in enumerate((prd / "errors.md").read_text().split("\n"), 1) if needle in ln]
    return hits[-1]


def test_entry_fields(prd):
    append(prd, ENTRY)
    e = model.load(prd).errors_ledger["E-002"]
    assert (e.title, e.state, e.confirmed) == ("Greeting drops a word", "confirmed", ("2026-11-03", "yes, it's a code bug"))
    assert e.evidence == ['`greet "Ana Maria"` prints `Hello, Ana!`', "and exits 0"] and e.recurrence == "E-001"
    assert e.detected == "2026-11-03, user report (/prd-error)"
    assert e.diagnosis.startswith("AC-001.1") and e.resolution == "-"
    assert e.detected_line == line_of(prd, "Detected: 2026-11-03")
    assert e.confirmed_line == line_of(prd, "Confirmed:")
    assert e.evidence_line == line_of(prd, "Evidence:")
    assert e.classification_line == line_of(prd, "Classification: code bug")
    assert e.resolution_line == line_of(prd, "Resolution: -")


def test_classes():
    assert model.CLASSES == ("code bug", "spec gap", "invalid requirement", "environment", "standard", "unclassified")


def test_states(prd):
    append(prd, ENTRY.replace("Classification: code bug", "Classification: unclassified").replace("E-002", "E-003").split("Confirmed:")[0])
    append(prd, "### E-004 No class\nDetected: 2026-11-03, report\nResolution: -")
    append(prd, "### E-005 Proposed\nDetected: 2026-11-03, report\nClassification: spec gap\nResolution: -")
    append(prd, ENTRY.replace("E-002", "E-006"))
    led = model.load(prd).errors_ledger
    assert led["E-001"].state == "resolved"
    assert led["E-003"].state == "unclassified" and led["E-004"].state == "unclassified"
    assert led["E-005"].state == "proposed" and led["E-006"].state == "confirmed"


def test_fixture_ledger_is_clean(prd):
    assert "error-entries" not in fired(lint(prd))
    append(prd, ENTRY)
    assert "error-entries" not in fired(lint(prd))


def test_bad_detected(prd):
    entry(prd, **{"2026-11-03,__user__report__(/prd-error)": "yesterday"})
    n = line_of(prd, "Detected: yesterday")
    assert [(f.rule, f.message, f.line) for f in lint(prd) if f.rule == "error-entries"] == [
        ("error-entries", 'E-002: Detected: must be "<YYYY-MM-DD>, <source>"', n)]


def test_bad_confirmed(prd):
    entry(prd, **{'Confirmed: 2026-11-03, "yes, it\'s a code bug"': "Confirmed: yes"})
    f = [f for f in lint(prd) if f.rule == "error-entries"]
    assert [(x.message, x.line) for x in f] == [("E-002: Confirmed: must be '<YYYY-MM-DD>, \"<reply>\"'", line_of(prd, "Confirmed: yes"))]


def test_long_evidence(prd):
    extra = "".join(f"  line {i}\n" for i in range(19))
    entry(prd, **{"  and exits 0\n": "  and exits 0\n" + extra})
    f = [f for f in lint(prd) if f.rule == "error-entries"]
    assert [(x.message, x.line) for x in f] == [("E-002: Evidence: is 21 lines; at most 20", line_of(prd, "Evidence:"))]


def test_twenty_evidence_lines_pass(prd):
    extra = "".join(f"  line {i}\n" for i in range(18))
    entry(prd, **{"  and exits 0\n": "  and exits 0\n" + extra})
    assert "error-entries" not in fired(lint(prd))


def test_unknown_recurrence(prd):
    entry(prd, **{"Recurrence of: E-001": "Recurrence of: E-099"})
    f = [f for f in lint(prd) if f.rule == "error-entries"]
    assert [(x.message, x.line) for x in f] == [("E-002: Recurrence of: E-099 is not an entry", line_of(prd, "Recurrence of: E-099"))]


def test_confirmed_unclassified(prd):
    entry(prd, **{"Classification: code bug": "Classification: unclassified", "Resolution: -": "Resolution: -"})
    f = [f for f in lint(prd) if f.rule == "error-entries"]
    assert [(x.message, x.line) for x in f] == [("E-002: Confirmed: on an unclassified entry", line_of(prd, "Confirmed:"))]


def test_unknown_class(prd):
    entry(prd, **{"Classification: code bug": "Classification: typo"})
    f = [f for f in lint(prd) if f.rule == "error-entries"]
    assert [(x.message, x.line) for x in f] == [(
        "E-002: Classification: 'typo' is not one of code bug, spec gap, invalid requirement, environment, standard, unclassified",
        line_of(prd, "Classification: typo"))]
