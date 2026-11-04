"""prd_change.py ids next and digest (0.8.1)."""
import contextlib
import io
import json
import subprocess

import pytest
from conftest import edit
from prd_change import main as change_main
from prdlint import change, hooks, model


def call(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = change_main(list(argv))
    return code, out.getvalue(), err.getvalue()


def nxt(prd, kind):
    return change.next_id(model.load(prd), kind)


def test_next_fr_counts_both_kinds(prd):
    assert nxt(prd, "FR") == "FR-005" and nxt(prd, "NFR") == "NFR-005"


def test_next_fr_counts_a_removed_requirement(prd):
    (prd / "features/api.md").write_text((prd / "features/api.md").read_text() + "\n### FR-006 Gone\nStatus: removed\n", encoding="utf-8")
    assert nxt(prd, "FR") == "FR-007"


def test_next_ac_counts_removed_acs(prd):
    edit(prd, "features/import.md", "- AC-001.3 If the import file", "- AC-001.3 (removed in 1.1.0) If the import file")
    assert nxt(prd, "AC-001") == "AC-001.4"
    edit(prd, "features/import.md", "Errors: IMPORT_DUPLICATE", "- AC-001.6 (removed in 1.1.0) Old.\nErrors: IMPORT_DUPLICATE")
    assert nxt(prd, "AC-001") == "AC-001.7"


def test_next_ac_finds_an_nfr_block(prd):
    assert nxt(prd, "AC-004") == "AC-004.2"


def test_next_t_counts_ids_only_in_a_changelog_cell(prd):
    assert nxt(prd, "T-002") == "T-002.3"
    edit(prd, "prd.md", "| 1.0.0 | 2026-10-29 | Initial release |", "| 1.0.1 | 2026-10-30 | dropped T-002.7 |")
    assert nxt(prd, "T-002") == "T-002.3"  # the cell is IDs, not Change
    edit(prd, "prd.md", "| 1.0.1 | 2026-10-30 | dropped T-002.7 | UJ-01,", "| 1.0.1 | 2026-10-30 | dropped | T-002.7, UJ-01,")
    assert nxt(prd, "T-002") == "T-002.8"


def test_next_t_counts_tests_lines(prd):
    assert nxt(prd, "T-001") == "T-001.5"


def test_next_uj(prd):
    assert nxt(prd, "UJ") == "UJ-02"
    (prd / "features/api.md").write_text((prd / "features/api.md").read_text() + "\n### UJ-02 Another\nStatus: removed\n", encoding="utf-8")
    assert nxt(prd, "UJ") == "UJ-03"


@pytest.mark.parametrize("kind", ["AC-099", "T-099"])
def test_unknown_block_refuses(prd, kind):
    with pytest.raises(change.ChangeError, match=r"no block FR-099 or NFR-099"):
        nxt(prd, kind)


def test_bad_kind_refuses(prd):
    with pytest.raises(change.ChangeError):
        nxt(prd, "XX")


def test_cli_ids_next_text_and_json(prd):
    assert call("ids", "next", str(prd), "FR") == (0, "FR-005\n", "")
    code, out, _ = call("ids", "next", str(prd), "FR", "--json")
    assert code == 0 and json.loads(out) == {"interface": 1, "kind": "change.ids", "next": "FR-005"}
    assert json.loads(call("--json=1", "ids", "next", str(prd), "FR")[1])["next"] == "FR-005"


def test_cli_refusal_exit_1(prd):
    code, out, err = call("ids", "next", str(prd), "AC-099")
    assert (code, out, err) == (1, "", "refused: no block FR-099 or NFR-099\n")


def test_cli_interface_and_usage(prd):
    assert call("--interface") == (0, "1\n", "")
    assert call()[0] == 2
    assert call("ids", "next", str(prd.parent / "nope"), "FR")[0] == 2
    code, out, _ = call("ids", "next", "--json", "--bogus")
    assert code == 2 and json.loads(out)["error"]


def test_digest_ignores_version_updated_and_tables(prd):
    base = change.digest(prd)
    edit(prd, "prd.md", "version: 1.0.0", "version: 1.1.0")
    edit(prd, "prd.md", "updated: 2026-10-29", "updated: 2026-11-03")
    assert change.digest(prd) == base
    edit(prd, "prd.md", "| NFR-004 | Order lookup latency | live |", "| NFR-004 | Order lookup latency | built |")
    edit(prd, "prd.md", "| 1.0.0 | 2026-10-29 | Initial release |", "| 1.1.0 | 2026-11-03 | x; pending | FR-009 |\n| 1.0.0 | 2026-10-29 | Initial release |")
    assert change.digest(prd) == base
    (prd / ".prd-review.json").write_text("{}", encoding="utf-8")
    assert change.digest(prd) == base


def test_digest_changes_with_an_ac_and_is_stable(prd):
    base = change.digest(prd)
    assert len(base) == 64 and change.digest(prd) == base
    edit(prd, "features/api.md", "return the order with its status.", "return the order.")
    assert change.digest(prd) != base


def test_digest_changes_with_status_and_headings(prd):
    base = change.digest(prd)
    edit(prd, "prd.md", "status: Approved", "status: In review")
    assert change.digest(prd) != base


def test_digest_covers_git_files_only(prd, tmp_path):
    root = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".gitignore").write_text("scratch.txt\n", encoding="utf-8")
    base = change.digest(prd)
    (prd / "scratch.txt").write_text("x", encoding="utf-8")
    assert change.digest(prd) == base
    (prd / "new.txt").write_text("x", encoding="utf-8")
    assert change.digest(prd) != base
    (prd / "__pycache__").mkdir()
    (prd / "__pycache__/a.pyc").write_text("x", encoding="utf-8")
    (prd / ".hidden").write_text("x", encoding="utf-8")
    d = change.digest(prd)
    (prd / "__pycache__/a.pyc").write_text("y", encoding="utf-8")
    (prd / ".hidden").write_text("y", encoding="utf-8")
    assert change.digest(prd) == d
    (prd / ".gitkeep").write_text("", encoding="utf-8")
    assert change.digest(prd) != d


def test_cli_digest(prd):
    code, out, _ = call("digest", str(prd))
    assert code == 0 and out == change.digest(prd) + "\n"
    doc = json.loads(call("digest", str(prd), "--json")[1])
    assert doc == {"interface": 1, "kind": "change.digest", "digest": change.digest(prd)}


def test_vendored_and_gitignore(tmp_path):
    assert "prd_change.py" in hooks.VENDORED
    (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")
    hooks._ignore_record(tmp_path)
    hooks._ignore_record(tmp_path)
    assert (tmp_path / ".gitignore").read_text() == "build/\n.prd-judge/\n.prd-review.json\n"
