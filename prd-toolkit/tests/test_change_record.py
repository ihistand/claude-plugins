"""prd_change.py record (0.8.1): the version, the §14 row and the §11 rows written from a PRD diff."""
import contextlib
import io
import json
import shutil
from pathlib import Path

import pytest
from conftest import edit
from deploy_fixture import deploy_repo
from doc_fixture import document_prd
from legacy import commit, git
from prd_change import main as change_main
from prd_lint import main as lint_main
from prdlint import change
from test_change_bump import NEW_TEST, PRD, append, expect_change, new_ac, new_block, drop_case

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
    assert r.row == "| 1.1.0 | 2026-11-04 | Repeat lookups; pending | FR-002, AC-002.3, T-002.3 |"
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
    assert ids == "FR-002, FR-009, AC-002.3, AC-009.1, T-002.1, T-002.3"


def test_section_11_rows_added_changed_removed(repo):
    prd = repo / PRD
    new_block(prd)
    edit(prd, "features/api.md", "### FR-009 Count orders\nStatus: proposed", "### FR-009 Count orders\nStatus: approved")
    edit(prd, "features/api.md", "### FR-002 Get an order", "### FR-002 Get one order")
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed")
    rec(repo, "major")
    md = prd_md(repo)
    assert "| FR-009 | Count orders | approved | features/api.md |  |\n" in md
    assert "| FR-002 | Get one order | verified | features/api.md | 1.0.0 |\n" in md
    assert "| FR-003 | Delete an order | removed | features/api.md |  |\n" in md


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
    edit(prd, "features/api.md", "### FR-009 Count orders\nStatus: proposed", "### FR-009 Count orders\nStatus: approved")
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
    assert doc["row"].startswith("| 1.1.0 | ") and doc["row"].endswith("| Repeat lookups; pending | FR-002, AC-002.3, T-002.3 |")
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
    assert r.row.endswith("| FR-002, T-002.2 |")


# --- R16: §11 statuses follow the blocks' Status: lines; R17: the IDs cell names each item's requirement ---

def test_a_revised_block_set_to_approved_is_approved_in_section_11(repo):
    prd = repo / PRD
    new_ac_with_test(prd)
    edit(prd, "features/api.md", "### FR-002 Get an order\nStatus: verified (since 1.0.0)", "### FR-002 Get an order\nStatus: approved")
    before = change.digest(prd)
    rec(repo)
    md = prd_md(repo)
    assert "| FR-002 | Get an order | approved | features/api.md |  |\n" in md
    assert "| FR-003 | Delete an order | verified | features/api.md | 1.0.0 |\n" in md
    assert lint_code(repo) == 0
    assert change.digest(prd) == before


def test_a_status_only_move_is_synced_to_section_11(repo):
    prd = repo / PRD
    new_ac_with_test(prd)
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: approved")
    rec(repo)
    md = prd_md(repo)
    assert "| FR-003 | Delete an order | approved | features/api.md |  |\n" in md
    assert lint_code(repo) == 0


def test_ids_cell_names_the_parent_of_each_ac_and_t_id_once(repo):
    """Neither block changes outside its ACs and cases, so FR-002 and FR-003 come only from their items."""
    prd = repo / PRD
    new_ac(prd)
    append(prd / "test-cases/api.yaml", NEW_TEST.replace("T-002.3", "T-003.3").replace("AC-002.1", "AC-003.1"))
    items = change.bump(repo, prd, "HEAD").items
    assert {i.id for i in items} == {"AC-002.3", "T-003.3"}
    r = rec(repo, "minor")
    assert r.row.split("|")[4].strip() == "FR-002, FR-003, AC-002.3, T-003.3"


def test_record_keeps_a_crlf_prd_md_crlf(repo):
    new_ac_with_test(repo / PRD)
    md = repo / PRD / "prd.md"
    md.write_bytes(md.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    done = rec(repo)
    data = md.read_bytes()
    assert data.count(b"\n") == data.count(b"\r\n")
    assert (done.row + "\r\n").encode() in data and b"\r\nversion: 1.1.0\r\n" in data


def test_a_usage_error_document_takes_its_kind_from_the_subcommand(repo):
    code, out, err = call("bump", str(repo / PRD), "--base", "nope", "--json")
    assert code == 2 and json.loads(out) == {"interface": 1, "kind": "change.bump", "error": f"bump: nope has no {PRD}"}
    code, out, _ = call("record", str(repo / PRD), "--base", "HEAD", "--json")  # argparse: --bump and --change missing
    assert code == 2 and json.loads(out)["kind"] == "change.record"
    code, out, _ = call("ids", "next", str(repo / PRD), "--json")
    assert code == 2 and json.loads(out)["kind"] == "change.ids"
    code, out, _ = call("--json", "--bogus")  # no subcommand parses: the script's kind
    assert code == 2 and json.loads(out)["kind"] == "change"


# --- 0.8.3: E-016 a live block's Since; (j) the IDs a changed contract item cites ---

LIVE = "Status: live (since 1.1.0)"


def row_cells(repo, id_):
    line = next(l for l in prd_md(repo).splitlines() if l.startswith(f"| {id_} |"))
    return [c.strip() for c in line.strip("|").split("|")]


def test_record_writes_since_for_an_added_live_block(repo):
    prd = repo / PRD
    new_block(prd)
    edit(prd, "features/api.md", "### FR-009 Count orders\nStatus: proposed", f"### FR-009 Count orders\n{LIVE}")
    rec(repo)
    assert row_cells(repo, "FR-009")[2:] == ["live", "features/api.md", "1.1.0"]


def test_record_writes_since_when_an_existing_block_becomes_live(repo):
    prd = repo / PRD
    new_ac_with_test(prd)
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", f"### FR-003 Delete an order\n{LIVE}")
    rec(repo)
    assert row_cells(repo, "FR-003")[2:] == ["live", "features/api.md", "1.1.0"]
    assert lint_code(repo) == 0


def test_record_clears_since_when_a_live_block_returns_to_approved(repo):
    prd = repo / PRD
    new_ac_with_test(prd)
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: approved")
    rec(repo)
    assert row_cells(repo, "FR-003")[2:] == ["approved", "features/api.md", ""]
    assert lint_code(repo) == 0


def test_record_keeps_since_on_an_unchanged_removed_row(repo):
    prd = repo / PRD
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed")
    edit(prd, "prd.md", "| FR-003 | Delete an order | verified | features/api.md | 1.0.0 |", "| FR-003 | Delete an order | removed | features/api.md | 1.0.0 |")
    commit(repo, "remove FR-003", "docs")
    new_ac_with_test(prd)
    rec(repo)
    assert row_cells(repo, "FR-003")[2:] == ["removed", "features/api.md", "1.0.0"]


def ids_cell(r):
    return r.row.split("|")[4].strip()


def test_contract_only_change_lists_the_cited_requirement(repo):
    prd = repo / PRD
    edit(prd, "contracts/errors.yaml", "The file is zero bytes or has only a header line.", "The file is zero bytes or has only a header line (FR-001).")
    r = rec(repo, "patch")
    assert ids_cell(r) == "FR-001"


def test_openapi_operation_change_lists_its_x_prd_ids(repo):
    prd = repo / PRD
    edit(prd, "contracts/openapi.yaml", "x-prd-ids: [FR-002, AC-002.1, AC-002.2, NFR-004]", "x-prd-ids: [FR-002, AC-002.1]")
    r = rec(repo, "patch")
    assert ids_cell(r) == "FR-002"


def test_removed_contract_item_reads_its_citations_at_the_base(repo):
    from legacy import git

    prd = repo / PRD
    edit(prd, "contracts/errors.yaml", "The file is zero bytes or has only a header line.", "The file is zero bytes or has only a header line (FR-001).")
    git(repo, "commit", "-qam", "cite")
    p = prd / "contracts/errors.yaml"
    text = p.read_text()
    a = text.index("IMPORT_EMPTY:")
    b = text.index("ORDER_NOT_FOUND:")
    p.write_text(text[:a] + text[b:])
    r = rec(repo, "major")
    assert ids_cell(r) == "FR-001"


def test_contract_change_citing_nothing_keeps_dash(repo):
    prd = repo / PRD
    edit(prd, "contracts/errors.yaml", "status: 404", "status: 410")
    r = rec(repo, "patch")
    assert ids_cell(r) == "-"


def test_changed_contract_item_keeps_an_id_only_the_base_has(repo):
    """0.8.4 fix 5: an ID that is a block in either PRD is added: FR-003 is a block of the base only, already
    `removed` there (so no item of this change names it) and gone from the working tree."""
    import re

    prd = repo / PRD
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed")
    edit(prd, "prd.md", "| FR-003 | Delete an order | verified | features/api.md | 1.0.0 |", "| FR-003 | Delete an order | removed | features/api.md | 1.0.0 |")
    commit(repo, "remove FR-003", "docs")
    api = prd / "features/api.md"
    api.write_text(re.sub(r"### FR-003 .*?(?=\n### |\Z)", "", api.read_text(), flags=re.S), encoding="utf-8")
    edit(prd, "contracts/errors.yaml", "The file is zero bytes or has only a header line.", "The file is zero bytes or has only a header line (FR-003).")
    r = rec(repo, "major")
    assert "FR-003" in ids_cell(r).split(", ")


# --- 0.8.5 spec 6: prd_change.py pack moves a PRD to a new pack version ---

NOTES = "notes@market"
NOTES_PRD = "docs/prd/guide"  # the document PRD of doc_fixture, moved from the built-in document pack to notes-pack
PACK_AT = "- Pack: notes-pack {v} (notes@market)"
TARGET_AT = "Target: pack notes-pack {v} (notes@market), output language en"
PACK_ROW = "| 1.0.1 | 2026-11-04 | pack notes-pack 0.1.0 → 0.1.1; pending | - |"
PACKS = Path(__file__).parent.parent / "packs"
PACK_RULE = "a changed version on a `Pack:` or `Target: pack` line, the pack's name and source unchanged"


def notes_source(tmp_path, version="0.1.1"):
    """A plugin `notes@market` whose prd-packs/ holds notes-pack at `version` (the document pack renamed); returns the plugins file."""
    folder = tmp_path / "notes-plugin/prd-packs/notes-pack"
    shutil.copytree(PACKS / "document", folder)
    text = (folder / "pack.yaml").read_text(encoding="utf-8")
    (folder / "pack.yaml").write_text(text.replace("pack: document", "pack: notes-pack").replace("version: 1.0.0", f"version: {version}"), encoding="utf-8")
    plugins = {"superpowers@superpowers-marketplace": [{}], NOTES: [{"scope": "user", "installPath": str(tmp_path / "notes-plugin"), "version": "1.0.0"}]}
    path = tmp_path / "notes-plugins.json"
    path.write_text(json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")
    return path


def notes_prd(tmp_path, version="0.1.0", target_version=None):
    """A git repo at tmp_path/notes holding the document PRD, naming notes-pack in §1 and on the install area's Target: line, committed."""
    repo = tmp_path / "notes"
    prd = document_prd(repo)
    edit(prd, "prd.md", "- Pack: document 1.0.0 (prd-toolkit)", PACK_AT.format(v=version))
    edit(prd, "features/install.md", "# Install\n", "# Install\n\n" + TARGET_AT.format(v=target_version or version) + "\n")
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "the guide", "docs")
    return repo


@pytest.fixture
def notes_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(notes_source(tmp_path)))
    return notes_prd(tmp_path)


def notes_md(repo, rel="prd.md"):
    return (repo / NOTES_PRD / rel).read_text(encoding="utf-8")


def notes_lint(repo):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return lint_main([str(repo / NOTES_PRD)])


def test_pack_moves_every_line_and_records_a_pending_patch(notes_repo):
    r = change.pack(notes_repo, notes_repo / NOTES_PRD, "notes-pack", "0.1.1", TODAY)
    assert r == change.Recorded("1.0.1", PACK_ROW)
    md = notes_md(notes_repo)
    assert PACK_AT.format(v="0.1.1") + "\n" in md and PACK_AT.format(v="0.1.0") not in md
    assert TARGET_AT.format(v="0.1.1") + "\n" in notes_md(notes_repo, "features/install.md")  # the source and the output language are kept
    assert "\nversion: 1.0.1\n" in md and "\nupdated: 2026-11-04\n" in md and md.rstrip().endswith(PACK_ROW)
    assert notes_lint(notes_repo) == 0


def test_pack_cli_text_and_json(notes_repo):
    code, out, err = call("pack", str(notes_repo / NOTES_PRD), "notes-pack", "0.1.1")
    assert code == 0 and err == "" and out.startswith("1.0.1\n| 1.0.1 | ") and out.endswith("| pack notes-pack 0.1.0 → 0.1.1; pending | - |\n")
    git(notes_repo, "checkout", "-q", "--", "docs")
    code, out, err = call("pack", str(notes_repo / NOTES_PRD), "notes-pack", "0.1.1", "--json")
    doc = json.loads(out)
    assert code == 0 and err == "" and (doc["kind"], doc["version"]) == ("change.pack", "1.0.1")
    assert doc["row"].endswith("| pack notes-pack 0.1.0 → 0.1.1; pending | - |")
    code, out, _ = call("pack", str(notes_repo / NOTES_PRD), "notes-pack", "1.2", "--json")
    assert code == 2 and json.loads(out) == {"interface": 1, "kind": "change.pack", "error": "pack: 1.2 is not a version X.Y.Z"}


def test_bump_reads_each_moved_pack_line_as_a_patch(notes_repo):
    change.pack(notes_repo, notes_repo / NOTES_PRD, "notes-pack", "0.1.1", TODAY)
    result = change.bump(notes_repo, notes_repo / NOTES_PRD, "HEAD")
    md_line = notes_md(notes_repo).split("\n").index(PACK_AT.format(v="0.1.1")) + 1
    api_line = notes_md(notes_repo, "features/install.md").split("\n").index(TARGET_AT.format(v="0.1.1")) + 1
    assert result.level == "patch"
    assert [(i.level, i.id, i.file, i.line, i.reason) for i in result.items] == [
        ("patch", "notes-pack", "prd.md", md_line, PACK_RULE), ("patch", "notes-pack", "features/install.md", api_line, PACK_RULE)]
    code, out, _ = call("bump", str(notes_repo / NOTES_PRD), "--base", "HEAD")
    assert code == 0 and out.splitlines()[0] == f"patch notes-pack prd.md:{md_line} {PACK_RULE}" and out.endswith("level patch\n")


def test_a_pack_line_with_a_new_source_still_needs_judgment(notes_repo):
    edit(notes_repo / NOTES_PRD, "prd.md", PACK_AT.format(v="0.1.0"), "- Pack: notes-pack 0.1.1 (notes@elsewhere)")
    assert change.bump(notes_repo, notes_repo / NOTES_PRD, "HEAD").level == "needs judgment"


def test_a_target_line_moving_its_language_too_still_needs_judgment(notes_repo):
    edit(notes_repo / NOTES_PRD, "features/install.md", TARGET_AT.format(v="0.1.0"), "Target: pack notes-pack 0.1.1 (notes@market), output language es")
    items = change.bump(notes_repo, notes_repo / NOTES_PRD, "HEAD").items
    assert [(i.id, i.level) for i in items] == [("notes-pack", "patch"), ("features/install.md", "needs judgment")]


def pack_refused(repo, why, name="notes-pack", version="0.1.1", prd=NOTES_PRD):
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in (repo / prd).rglob("*") if p.is_file()}
    code, out, err = call("pack", str(repo / prd), name, version)
    assert (code, out) == (1, "") and err == f"refused: {why}\n", (code, err)
    assert {p.relative_to(repo).as_posix(): p.read_bytes() for p in (repo / prd).rglob("*") if p.is_file()} == before


def test_pack_refuses_a_pack_no_line_names(notes_repo):
    pack_refused(notes_repo, "no Pack: or Target: pack line names other-pack", name="other-pack")


def test_pack_refuses_a_prd_on_the_built_in_default(repo):
    pack_refused(repo, "no Pack: or Target: pack line names service", name="service", version="1.0.1", prd=PRD)


def test_pack_refuses_a_version_the_source_does_not_hold(notes_repo, tmp_path):
    folder = tmp_path / "notes-plugin/prd-packs/notes-pack"
    pack_refused(notes_repo, f"pack notes-pack 0.1.2 (notes@market) not found; looked in: {folder}/ (holds 0.1.1)", version="0.1.2")


def test_pack_refuses_an_uncommitted_prd_folder(notes_repo):
    edit(notes_repo / NOTES_PRD, "nfr.md", "# Non-functional requirements", "# Non-functional requirements (none)")
    pack_refused(notes_repo, "docs/prd/guide has uncommitted changes; commit or set them aside first")


def test_pack_refuses_an_untracked_file_in_the_prd_folder(notes_repo):
    (notes_repo / NOTES_PRD / "notes.md").write_text("x\n", encoding="utf-8")
    pack_refused(notes_repo, "docs/prd/guide has uncommitted changes; commit or set them aside first")


def test_pack_refuses_a_move_to_the_version_already_named(notes_repo):
    pack_refused(notes_repo, "every line naming notes-pack already names 0.1.0", version="0.1.0")


def test_pack_refuses_lines_that_disagree(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(notes_source(tmp_path)))
    repo = notes_prd(tmp_path, target_version="0.0.9")
    pack_refused(repo, "the lines naming notes-pack disagree on its version or source")


@pytest.mark.parametrize("version", ["0.1", "v0.1.1", "0.1.1-rc1", ""])
def test_pack_refuses_a_bad_version_as_usage(notes_repo, version):
    code, out, err = call("pack", str(notes_repo / NOTES_PRD), "notes-pack", version)
    assert code == 2 and out == "" and err == f"pack: {version} is not a version X.Y.Z\n"


def test_a_pack_record_that_fails_leaves_every_line_as_it_was(notes_repo):
    edit(notes_repo / NOTES_PRD, "prd.md", "| Version | Date | Change | IDs |\n|---|---|---|---|\n| 1.0.0 | 2026-11-03 | Initial release | FR-001 |\n", "")
    commit(notes_repo, "no changelog table", "docs")
    pack_refused(notes_repo, "§14 has no changelog table")


def test_a_status_only_change_records_the_block(repo):
    prd = repo / PRD
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: verified (since 1.0.0)", "### FR-003 Delete an order\nStatus: approved")
    r = rec(repo, "patch")
    assert r.version == "1.0.1" and r.row.endswith("| FR-003 |")


def test_a_new_block_records_its_acs_and_test_cases(repo):
    prd = repo / PRD
    append(prd / "features/api.md", "\n### FR-012 Count orders\nStatus: proposed\nAcceptance (EARS):\n- AC-012.1 When asked, the API shall count orders.\nTests: T-012.1 [integration]\n")
    append(prd / "test-cases/api.yaml", CASE.replace("T-002.3", "T-012.1").replace("AC-002.3", "AC-012.1"))
    r = rec(repo, "minor")
    assert r.version == "1.1.0" and r.row.endswith("| FR-012, AC-012.1, T-012.1 |")


def test_a_removed_block_keeps_its_deleted_test_id(repo):
    import re
    from prdlint import model

    prd = repo / PRD
    edit(prd, "nfr.md", "### NFR-004 Order lookup latency\nStatus: verified (since 1.0.0)", "### NFR-004 Order lookup latency\nStatus: removed")
    p = prd / "test-cases/nfr.yaml"
    p.write_text(re.sub(r"^T-004\.2:\n(?:[ \t]+.*\n|\n)*", "", p.read_text(), flags=re.M), encoding="utf-8")
    r = rec(repo, "major")
    assert r.version == "2.0.0" and r.row.endswith("| NFR-004, AC-004.1, T-004.1, T-004.2 |")
    assert change.next_id(model.load(prd), "T-004") == "T-004.3"
