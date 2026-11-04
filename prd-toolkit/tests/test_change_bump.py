"""prd_change.py bump (0.8.1): the version level proposed from a PRD diff."""
import contextlib
import io
import json
import re
import shutil
import subprocess

import pytest
from conftest import edit
from deploy_fixture import deploy_repo
from legacy import commit, git
from prd_change import main as change_main
from prdlint import change

PRD = "docs/prd/orders"
NEW_TEST = "\nT-002.3:\n  ac: AC-002.1\n  level: integration\n  target: op:getOrder\n  expect:\n    errors: []\n"
OPEN_ERROR = "\n### E-002 Lookup returned a stale status\nDetected: 2026-10-30, test failure in T-002.1\nClassification: code bug\nTouches: FR-002\nResolution: open\n"


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = change_main(list(argv))
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    from conftest import PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return deploy_repo(tmp_path)


def run_bump(repo, base="HEAD"):
    code, out, err = call("bump", str(repo / PRD), "--base", base, "--json")
    assert code == 0, err
    return json.loads(out)


def append(path, text):
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def drop_error_code(prd):
    p = prd / "contracts/errors.yaml"
    p.write_text(re.sub(r"^IMPORT_EMPTY:\n(?:  .*\n)+", "", p.read_text(), flags=re.M), encoding="utf-8")


def new_ac(prd):
    edit(prd, "features/api.md", "ORDER_NOT_FOUND.\nErrors: ORDER_NOT_FOUND", "ORDER_NOT_FOUND.\n- AC-002.3 When a rep requests an order twice, the API shall answer both calls.\nErrors: ORDER_NOT_FOUND")


def new_ac_with_test(prd):
    new_ac(prd)
    append(prd / "test-cases/api.yaml", NEW_TEST.replace("AC-002.1", "AC-002.3"))


def new_block(prd):
    append(prd / "features/api.md", "\n### FR-009 Count orders\nStatus: proposed\nAcceptance (EARS):\n- AC-009.1 When asked, the API shall count orders.\n")


def known_error(prd):
    append(prd / "errors.md", OPEN_ERROR)


def regression_test(prd):
    append(prd / "test-cases/api.yaml", NEW_TEST)


def expect_change(prd):
    edit(prd, "test-cases/api.yaml", "body: {id: 1, order_key: K-1000, customer_id: 1, status: open}", "body: {id: 1, order_key: K-1000, customer_id: 1, status: closed}")


def ac_text_change(prd):
    edit(prd, "features/api.md", "shall respond 404 with", "shall respond 410 with")


def ac_and_test_change(prd):
    ac_text_change(prd)
    edit(prd, "test-cases/api.yaml", "status: 404", "status: 410")


# rule index in change.BUMP_RULES -> [(mutator, expected id, expected level, expected change)]
CASES = {
    0: [(new_ac, "AC-002.3", "minor", "added"), (new_block, "FR-009", "minor", "added")],
    1: [(new_ac_with_test, "T-002.3", "minor", "added")],
    2: [
        (lambda p: edit(p, "features/api.md", "- AC-002.2 If the order", "- AC-002.2 (removed in 1.1.0) If the order"), "AC-002.2", "major", "removed"),
        (lambda p: edit(p, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed"), "FR-003", "major", "removed"),
    ],
    3: [(drop_error_code, "IMPORT_EMPTY", "major", "removed")],
    4: [(ac_text_change, "AC-002.2", "needs judgment", "changed")],
    5: [
        (lambda p: edit(p, "features/api.md", "If the order id does not exist, the API shall respond 404 with error ORDER_NOT_FOUND.", "if the order id does not exist the API shall respond 404, with error ORDER_NOT_FOUND"), "AC-002.2", "patch", "changed"),
        (lambda p: edit(p, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order"), "FR-002", "patch", "changed"),
        (lambda p: edit(p, "features/api.md", "Flow: 1. Caller sends GET", "Flow: 1. A caller sends GET"), "FR-002", "patch", "changed"),
        (lambda p: edit(p, "features/import.md", "Edge cases: the same key twice", "Edge cases: one key twice"), "FR-001", "patch", "changed"),
        (lambda p: edit(p, "prd.md", "A customer's request for goods", "A customer's request to buy goods"), "glossary", "patch", "changed"),
    ],
    6: [(expect_change, "T-002.1", "needs judgment", "changed"),
        (lambda p: edit(p, "contracts/errors.yaml", "status: 404", "status: 410"), "ORDER_NOT_FOUND", "needs judgment", "changed")],
    7: [(ac_and_test_change, "T-002.2", "major", "changed")],
    8: [(lambda p: (known_error(p), commit_now(p), regression_test(p)), "T-002.3", "patch", "added")],
    9: [(regression_test, "T-002.3", "needs judgment", "added")],
    10: [(lambda p: edit(p, "operations.md", "## Drift", "## Drift\n\nNew words."), "operations.md", "needs judgment", "changed")],
}
PARAMS = [(i, *case) for i, cases in CASES.items() for case in cases]


def commit_now(prd):
    """Commit what is on disk so far, so a precondition is part of the base."""
    repo = prd.parents[2]
    commit(repo, "precondition", "docs")


def test_every_rule_has_a_case():
    assert set(CASES) == set(range(len(change.BUMP_RULES)))
    assert [lvl for _, lvl in change.BUMP_RULES] == ["minor", "minor", "major", "major", "needs judgment", "patch", "needs judgment", "major", "patch", "needs judgment", "needs judgment"]


@pytest.mark.parametrize("index,mutate,item_id,level,kind", PARAMS, ids=[f"rule{p[0]}-{p[3]}" for p in PARAMS])
def test_each_rule(repo, index, mutate, item_id, level, kind):
    mutate(repo / PRD)
    doc = run_bump(repo)
    hits = [i for i in doc["items"] if i["id"] == item_id]
    assert len(hits) == 1, doc
    item = hits[0]
    assert (item["level"], item["change"]) == (level, kind)
    want = f"unclassified change in {item['file']}" if index == 10 else change.BUMP_RULES[index][0]
    assert item["reason"] == want
    assert item["line"] >= 0 and item["file"]


def test_wording_only_is_patch_and_an_added_word_needs_judgment(repo):
    prd = repo / PRD
    edit(prd, "features/import.md", "the importer shall skip the row", "The importer shall skip the row!")
    doc = run_bump(repo)
    assert [(i["id"], i["level"]) for i in doc["items"]] == [("AC-001.2", "patch")] and doc["level"] == "patch"
    edit(prd, "features/import.md", "The importer shall skip the row!", "The importer shall quietly skip the row")
    doc = run_bump(repo)
    assert [(i["id"], i["level"]) for i in doc["items"]] == [("AC-001.2", "needs judgment")] and doc["level"] == JUDGMENT


JUDGMENT = "needs judgment"


def test_mixed_minor_and_judgment_lists_both(repo):
    prd = repo / PRD
    new_ac(prd)
    expect_change(prd)
    doc = run_bump(repo)
    assert doc["level"] == JUDGMENT
    assert {(i["id"], i["level"]) for i in doc["items"]} == {("AC-002.3", "minor"), ("T-002.1", JUDGMENT)}


def test_highest_level_wins(repo):
    prd = repo / PRD
    new_ac(prd)
    edit(prd, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order")
    assert run_bump(repo)["level"] == "minor"
    edit(prd, "features/api.md", "- AC-003.2 If a rep", "- AC-003.2 (removed in 1.1.0) If a rep")
    assert run_bump(repo)["level"] == "major"


def test_ignored_lines_do_not_appear(repo):
    prd = repo / PRD
    edit(prd, "prd.md", "version: 1.0.0", "version: 1.1.0")
    edit(prd, "prd.md", "updated: 2026-10-29", "updated: 2026-11-03")
    edit(prd, "prd.md", "status: Approved", "status: In review")
    edit(prd, "prd.md", "| NFR-004 | Order lookup latency | verified |", "| NFR-004 | Order lookup latency | live |")
    edit(prd, "prd.md", "| 1.0.0 | 2026-10-29 | Initial release |", "| 1.1.0 | 2026-11-03 | x; pending | FR-009 |\n| 1.0.0 | 2026-10-29 | Initial release |")
    edit(prd, "features/api.md", "### FR-002 Get an order\nStatus: verified (since 1.0.0)", "### FR-002 Get an order\nStatus: live (since 1.0.0)\nSource: src/api.py:10")
    (prd / ".prd-review.json").write_text("{}", encoding="utf-8")
    doc = run_bump(repo)
    assert doc["items"] == [] and doc["level"] == "patch"


def test_text_output_one_line_per_item(repo):
    prd = repo / PRD
    new_ac(prd)
    expect_change(prd)
    code, out, err = call("bump", str(prd), "--base", "HEAD")
    assert code == 0 and err == ""
    lines = out.splitlines()
    assert lines[-1] == "level needs judgment" and len(lines) == 3
    assert re.fullmatch(r"minor AC-002\.3 features/api\.md:\d+ a new block or AC", lines[0])
    assert re.fullmatch(r"needs judgment T-002\.1 test-cases/api\.yaml:\d+ a changed test case or contract item under an unchanged AC", lines[1])


def test_json_document_shape(repo):
    new_ac(repo / PRD)
    doc = run_bump(repo)
    assert doc["interface"] == 1 and doc["kind"] == "change.bump" and doc["level"] == "minor"
    assert set(doc["items"][0]) == {"id", "file", "line", "change", "level", "reason"}


def test_contract_items_by_kind(prd):
    from prdlint import model

    items = change.contract_items(model.load(prd))
    assert {"getOrder", "deleteOrder"} <= set(items["contracts/openapi.yaml"])
    assert "import_orders" in items["contracts/events.md"]
    assert {"orders", "customers"} <= set(items["contracts/schema.sql"])
    assert {"IMPORT_EMPTY", "ORDER_NOT_FOUND"} <= set(items["contracts/errors.yaml"])
    assert "IMPORT_BATCH_SIZE" in items["contracts/config.yaml"]
    assert set(items["contracts/permissions.yaml"]) == {"contracts/permissions.yaml"}
    assert not any(k.startswith("contracts/fixtures/") for k in items)


def test_a_nonexistent_ref_exits_2_with_one_line(repo):
    assert call("bump", str(repo / PRD), "--base", "no-such-ref") == (2, "", f"bump: no-such-ref has no {PRD}\n")
    code, out, err = call("bump", str(repo / PRD), "--base", "no-such-ref", "--json")
    assert code == 2 and json.loads(out)["error"] == f"bump: no-such-ref has no {PRD}"


def test_a_ref_before_the_prd_folder_existed_exits_2_with_one_line(tmp_path, monkeypatch):
    from conftest import FIXTURE, PLUGINS_FILE

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("hi\n", encoding="utf-8")
    commit(repo, "first", "README.md")
    shutil.copytree(FIXTURE, repo / PRD)
    commit(repo, "second", "docs")
    assert call("bump", str(repo / PRD), "--base", "HEAD")[0] == 0
    code, out, err = call("bump", str(repo / PRD), "--base", "HEAD~1")
    assert (code, out, err) == (2, "", f"bump: HEAD~1 has no {PRD}\n")


def test_outside_a_repository_exits_2(prd):
    code, out, err = call("bump", str(prd), "--base", "HEAD")
    assert code == 2 and out == "" and err.count("\n") == 1 and "git repository" in err


def test_base_may_be_a_branch_and_the_tree_is_not_touched(repo):
    git(repo, "branch", "before")
    new_ac(repo / PRD)
    commit(repo, "more", "docs")
    assert run_bump(repo, "before")["level"] == "minor"
    assert run_bump(repo, "HEAD")["items"] == []
    assert subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout == ""
