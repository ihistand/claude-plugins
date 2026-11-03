"""Failing cases for the pack, language and judged-case rules (0.8.0); each task that adds a rule appends here."""
import pytest
from conftest import Case, edit, fired, lint
from doc_fixture import document_prd

CASES = [
    Case("language-table", "unknown language", lambda root: edit(root, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: fr")),
    Case("pack-resolves", "malformed Pack line", lambda root: edit(root, "prd.md", "- Not used: message brokers, ORMs, front-end frameworks",
                                                                   "- Not used: message brokers, ORMs, front-end frameworks\n- Pack: document 1.0")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


# --- judged-case ---------------------------------------------------------------------------------------------------

def _judged(tmp_path, old=None, new=None):
    root = document_prd(tmp_path)
    if old is not None:
        edit(root, "test-cases/install.yaml", old, new)
    return [f for f in lint(root) if f.rule in ("judged-case", "sufficiency")]


RUBRIC = "rubric:\n      - Each step in Install names one action the reader performs\n      - No step relies on a tool that Requirements does not list\n"


def test_judged_case_passes_without_output(tmp_path):
    assert _judged(tmp_path) == []


@pytest.mark.parametrize("new", ["rubric: []\n", 'rubric: "x"\n', 'rubric: ["", "a"]\n', "rubric: [1]\n"])
def test_rubric_shape(tmp_path, new):
    got = _judged(tmp_path, RUBRIC, new)
    assert [f.message for f in got] == ["T-001.2: rubric must be a non-empty list of non-empty strings"]


@pytest.mark.parametrize("new", ["", "    threshold: 0\n", "    threshold: 1.5\n", '    threshold: "0.8"\n', "    threshold: true\n"])
def test_threshold(tmp_path, new):
    got = _judged(tmp_path, "    threshold: 0.67\n", new)
    assert [f.message for f in got] == ["T-001.2: threshold must be a number in (0, 1]"]


@pytest.mark.parametrize("v", ["0", "2.5", "true", '"3"'])
def test_runs(tmp_path, v):
    got = _judged(tmp_path, "    threshold: 0.67\n", f"    threshold: 1\n    runs: {v}\n")
    assert [f.message for f in got] == ["T-001.2: runs must be an integer of at least 1"]


def test_runs_and_threshold_bounds_pass(tmp_path):
    assert _judged(tmp_path, "    threshold: 0.67\n", "    threshold: 1\n    runs: 1\n") == []


def test_judged_case_has_no_output(tmp_path):
    got = _judged(tmp_path, "    threshold: 0.67\n", "    threshold: 0.67\n    output: {x: y}\n")
    assert [f.message for f in got] == ["T-001.2: a judged case has no expect.output"]


def test_missing_rubric_is_not_judged(tmp_path):
    got = _judged(tmp_path, "    " + RUBRIC, "")
    assert [f.rule for f in got] == ["sufficiency"] and "output" in got[0].message


def _make_judged(root):
    edit(root, "test-cases/api.yaml", "    output:\n      status: 200\n      body: {id: 1, order_key: K-1000, customer_id: 1, status: open}",
         "    rubric: x")


CASES.append(Case("judged-case", "rubric not a list", _make_judged))
