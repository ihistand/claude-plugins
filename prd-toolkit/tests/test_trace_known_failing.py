"""known-failing-tags (R37): a known-failing test case and the citation tag agree, and the tag names an open entry."""
from pathlib import Path

from test_trace import block, build, rules
from prdlint import model, trace

ERRORS = """# Errors

### E-001 Search is case sensitive
Detected: 2026-10-01
Resolution: T-001.1 [unit], PRD 1.0.0, fixed in abc1234

### E-002 Count is off by one
Detected: 2026-10-02
Resolution:
"""


def case(kf: str | None) -> str:
    extra = f"  known-failing: {kf}\n" if kf else ""
    return f"T-001.1:\n  ac: AC-001.1\n{extra}"


def make(tmp_path: Path, kf: str | None, cite: str, ledger: str = ERRORS) -> Path:
    """A PRD whose only case T-001.1 carries `kf`, and one test file whose citation line is `cite`."""
    prd = build(tmp_path, features={"notes": block("FR-001", "live", ["T-001.1"])})
    (prd / "test-cases").mkdir(exist_ok=True)
    (prd / "test-cases/x.yaml").write_text(case(kf), encoding="utf-8")
    (prd / "errors.md").write_text(ledger, encoding="utf-8")
    repo = model.repo_root(prd)
    (repo / "tests/test_notes.py").write_text(f'def test_a():\n    """{cite}"""\n', encoding="utf-8")
    return prd


def run(prd: Path):
    loaded = model.load(prd)
    return [f for f in trace.run_trace(loaded, model.repo_root(prd), None) if f.rule == "known-failing-tags"]


def test_rule_is_registered():
    assert trace.TRACE_RULES == ("t-implemented", "test-cites-live", "commit-refs", "status-current", "known-failing-tags")


def test_case_without_tagged_citation_is_reported_at_the_case(tmp_path):
    prd = make(tmp_path, "E-002", "@prd T-001.1")
    f = run(prd)
    assert [x.message for x in f] == ["T-001.1 is known-failing on E-002 but no citation is tagged `known-failing E-002`"]
    assert f[0].file == "test-cases/x.yaml" and f[0].line == 1


def test_tag_on_a_case_that_is_not_known_failing_is_reported_at_the_tag(tmp_path):
    prd = make(tmp_path, None, "@prd T-001.1 known-failing E-002")
    f = run(prd)
    assert [x.message for x in f] == ["tags T-001.1 known-failing E-002, but its test case is not known-failing on E-002"]
    assert f[0].file.endswith("tests/test_notes.py") and f[0].line == 2


def test_tag_naming_another_entry_than_the_case_is_reported(tmp_path):
    prd = make(tmp_path, "E-002", "@prd T-001.1 known-failing E-001")
    msgs = [x.message for x in run(prd)]
    assert "tags T-001.1 known-failing E-001, but its test case is not known-failing on E-001" in msgs
    assert "T-001.1 is known-failing on E-002 but no citation is tagged `known-failing E-002`" in msgs


def test_tag_naming_a_resolved_entry_is_reported(tmp_path):
    prd = make(tmp_path, "E-001", "@prd T-001.1 known-failing E-001")
    assert [x.message for x in run(prd)] == ["tags T-001.1 known-failing E-001, which is resolved"]


def test_matching_tag_on_an_open_entry_is_clean(tmp_path):
    assert run(make(tmp_path, "E-002", "@prd T-001.1 known-failing E-002")) == []


def test_no_known_failing_anywhere_is_clean(tmp_path):
    assert run(make(tmp_path, None, "@prd T-001.1")) == []


def test_loosely_written_tag_counts(tmp_path):  # Review Focus 4
    assert run(make(tmp_path, "E-002", "@prd T-001.1  known-failing: E-002")) == []


def test_longer_tid_never_satisfies_a_shorter_one(tmp_path):  # Review Focus 4
    prd = make(tmp_path, "E-002", "@prd T-001.10 known-failing E-002")
    assert [x.message for x in run(prd)] == ["T-001.1 is known-failing on E-002 but no citation is tagged `known-failing E-002`"]


def test_tagged_citations_map_pair_to_places_and_citations_is_unchanged(tmp_path):
    prd = make(tmp_path, "E-002", "@prd T-001.1 known-failing E-002")
    loaded, root = model.load(prd), model.repo_root(prd)
    assert trace.tagged_citations(loaded, root) == {("T-001.1", "E-002"): [("tests/test_notes.py", 2)]}
    assert trace.citations(loaded, root) == {"T-001.1": [("tests/test_notes.py", 2)]}


def test_rule_is_part_of_run_trace_output(tmp_path):
    prd = make(tmp_path, "E-002", "@prd T-001.1")
    loaded = model.load(prd)
    assert "known-failing-tags" in rules(trace.run_trace(loaded, model.repo_root(prd), None))
