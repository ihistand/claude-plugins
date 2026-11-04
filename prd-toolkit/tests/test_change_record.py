"""prd_change.py record (0.8.1): the version, the §14 row and the §11 rows written from a PRD diff."""
import contextlib
import io
import json

import pytest
from conftest import edit
from deploy_fixture import deploy_repo
from prd_change import main as change_main
from prd_lint import main as lint_main
from prdlint import change
from test_change_bump import PRD, append, expect_change, new_ac, new_block, drop_case

TODAY = "2026-11-04"


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = change_main(list(argv))
    return code, out.getvalue(), err.getvalue()


CASE = """
T-002.3:
  ac: AC-002.3
  level: integration
  target: op:getOrder
  environment: ci
  identity: test-rep
  preconditions: [customers/two_customers, orders/one_existing]
  input:
    id: 1
  expect:
    output: {status: 200}
    effects: []
    errors: []
    leaks: none
"""


def new_ac_with_test(prd):
    """A lint-clean new AC with its case, cited on FR-002's Tests line."""
    new_ac(prd)
    append(prd / "test-cases/api.yaml", CASE)
    edit(prd, "features/api.md", "T-002.2 [integration]", "T-002.2 [integration], T-002.3 [integration]")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def rec(repo, level="minor", text="Add a rule", base="HEAD", today=TODAY):
    return change.record(repo, repo / PRD, base, level, text, today)


def prd_md(repo):
    return (repo / PRD / "prd.md").read_text(encoding="utf-8")


def lint_code(repo):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return lint_main([str(repo / PRD)])


def test_needs_judgment_level_is_refused(repo):
    new_ac_with_test(repo / PRD)
    code, _, err = call("record", str(repo / PRD), "--base", "HEAD", "--bump", "needs-judgment", "--change", "x")
    assert code == 1 and err.strip() == "refused: a needs-judgment bump must be decided first"


def test_a_level_below_the_diff_is_refused(repo):
    new_ac_with_test(repo / PRD)
    before = prd_md(repo)
    code, _, err = call("record", str(repo / PRD), "--base", "HEAD", "--bump", "patch", "--change", "x")
    assert code == 1 and err.strip() == "refused: the diff needs minor, not patch"
    assert prd_md(repo) == before


def test_judgment_accepts_any_level_at_or_above_the_other_items(repo):
    prd = repo / PRD
    new_ac(prd)
    expect_change(prd)  # a minor item and a judgment item
    with pytest.raises(change.ChangeError, match="the diff needs minor, not patch"):
        rec(repo, "patch")
    assert rec(repo, "major").version == "2.0.0"


def test_judgment_with_only_judgment_items_floors_at_patch(repo):
    expect_change(repo / PRD)
    assert rec(repo, "patch").version == "1.0.1"


def test_minor_record_writes_version_updated_row_and_ids(repo):
    new_ac_with_test(repo / PRD)
    r = rec(repo, text="Repeat lookups")
    assert r.version == "1.1.0"
    assert r.row == "| 1.1.0 | 2026-11-04 | Repeat lookups; pending | AC-002.3, T-002.3 |"
    md = prd_md(repo)
    assert "\nversion: 1.1.0\n" in md and "\nupdated: 2026-11-04\n" in md and "\nstatus: Approved\n" in md
    assert md.rstrip().endswith(r.row)
    assert lint_code(repo) == 0


def test_ids_are_deduplicated_and_in_natural_order(repo):
    prd = repo / PRD
    new_block(prd)
    new_ac_with_test(prd)
    expect_change(prd)
    edit(prd, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order")
    r = rec(repo, "major")
    ids = r.row.split("|")[4].strip()
    assert ids == "FR-002, FR-009, AC-002.3, T-002.1, T-002.3"


def test_section_11_rows_added_changed_removed(repo):
    prd = repo / PRD
    new_block(prd)
    edit(prd, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order")
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed")
    rec(repo, "major")
    md = prd_md(repo)
    assert "| FR-009 | Count orders | approved | features/api.md |  |\n" in md
    assert "| FR-002 | Get one order | verified | features/api.md | 1.0.0 |\n" in md
    assert "| FR-003 | Delete an order | removed | features/api.md | 1.0.0 |\n" in md


def test_record_twice_gives_the_same_file(repo):
    new_ac_with_test(repo / PRD)
    first = rec(repo)
    once = prd_md(repo)
    second = rec(repo)
    assert second == first and prd_md(repo) == once
    rows = [ln for ln in once.splitlines() if ln.startswith("| 1.1.0 |")]
    assert len(rows) == 1


def test_second_run_replaces_the_row_and_recomputes_section_11(repo):
    prd = repo / PRD
    new_block(prd)
    rec(repo, "minor", text="First words")
    edit(prd, "features/api.md", "### FR-009 Count orders", "### FR-009 Count all orders")
    r = rec(repo, "minor", text="Second words")
    md = prd_md(repo)
    assert md.count("| 1.1.0 |") == 1 and "Second words; pending" in md and "First words" not in md
    assert md.count("| FR-009 | Count") == 1 and "| FR-009 | Count all orders | approved |" in md
    assert r.version == "1.1.0"


def test_version_comes_from_the_base_not_the_working_tree(repo):
    new_ac_with_test(repo / PRD)
    edit(repo / PRD, "prd.md", "\nversion: 1.0.0\n", "\nversion: 7.7.7\n")
    assert rec(repo).version == "1.1.0"


def test_digest_is_the_same_before_and_after_record(repo):
    new_ac_with_test(repo / PRD)
    before = change.digest(repo / PRD)
    rec(repo)
    assert change.digest(repo / PRD) == before


def test_cli_text_and_json(repo):
    new_ac_with_test(repo / PRD)
    code, out, err = call("record", str(repo / PRD), "--base", "HEAD", "--bump", "minor", "--change", "Repeat lookups", "--json")
    assert code == 0, err
    doc = json.loads(out)
    assert doc["kind"] == "change.record" and doc["version"] == "1.1.0"
    assert doc["row"].startswith("| 1.1.0 | ") and doc["row"].endswith("| Repeat lookups; pending | AC-002.3, T-002.3 |")
    code, out, _ = call("record", str(repo / PRD), "--base", "HEAD", "--bump", "minor", "--change", "Repeat lookups")
    assert code == 0 and out.startswith("1.1.0\n")


def test_cli_rejects_a_bad_level(repo):
    code, _, _ = call("record", str(repo / PRD), "--base", "HEAD", "--bump", "huge", "--change", "x")
    assert code == 2


def test_a_missing_base_is_one_line_usage_error(repo):
    code, _, err = call("record", str(repo / PRD), "--base", "nope", "--bump", "minor", "--change", "x")
    assert code == 2 and err.strip() == "bump: nope has no docs/prd/orders"


def test_change_text_may_not_break_the_table(repo):
    new_ac_with_test(repo / PRD)
    with pytest.raises(change.ChangeError, match="one non-empty line"):
        rec(repo, text="a | b")


def test_removed_test_case_id_is_listed(repo):
    drop_case(repo / PRD)
    r = rec(repo, "patch")
    assert r.row.endswith("| T-002.2 |")
