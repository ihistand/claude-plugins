"""Failing cases for the pack, language and judged-case rules (0.8.0); each task that adds a rule appends here."""
import pytest
from conftest import Case, edit, fired, lint

CASES = [
    Case("language-table", "unknown language", lambda root: edit(root, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: fr")),
    Case("pack-resolves", "malformed Pack line", lambda root: edit(root, "prd.md", "- Not used: message brokers, ORMs, front-end frameworks",
                                                                   "- Not used: message brokers, ORMs, front-end frameworks\n- Pack: document 1.0")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))
