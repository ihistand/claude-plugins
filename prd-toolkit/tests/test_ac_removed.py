"""AC-level removal: `- AC-nnn.n (removed in X.Y.Z) <original text>` keeps the ID, retires the criterion."""
import re

from conftest import edit, fired, lint

from prdlint.model import load

AC3 = "- AC-001.3 If the import file is empty"
AC3_REMOVED = "- AC-001.3 (removed in 1.1.0) If the import file is empty"
TESTS_001 = "Tests: T-001.1 [integration], T-001.2 [integration], T-001.3 [unit], T-001.4 [acceptance]"


def _drop_t001_3(root):
    path = root / "test-cases/import.yaml"
    text, n = re.subn(r"(?m)^T-001\.3:\n(?:[ ].*\n|\n)*?(?=^\S|\Z)", "", path.read_text(), count=1)
    assert n == 1
    path.write_text(text)
    edit(root, "features/import.md", TESTS_001, TESTS_001.replace(" T-001.3 [unit],", ""))


def test_removed_prefix_is_parsed_and_stripped(prd):
    edit(prd, "features/import.md", AC3, AC3_REMOVED)
    acs = {a.id: a for b in load(prd).blocks for a in b.acs}
    assert acs["AC-001.3"].removed is True
    assert acs["AC-001.3"].text.startswith("If the import file is empty")
    assert acs["AC-001.2"].removed is False


def test_removed_ac_without_a_test_case_lints_clean(prd):
    edit(prd, "features/import.md", AC3, AC3_REMOVED)
    _drop_t001_3(prd)
    assert lint(prd) == []


def test_test_case_citing_a_removed_ac_fires_removed_reused(prd):
    edit(prd, "features/import.md", AC3, AC3_REMOVED)
    messages = [f.message for f in lint(prd) if f.rule == "id-removed-reused"]
    assert any("T-001.3" in m and "AC-001.3" in m for m in messages)


def test_removed_ac_that_is_not_ears_lints_clean(prd):
    edit(
        prd,
        "features/import.md",
        "- AC-001.3 If the import file is empty, the importer shall finish with status `empty`,\n  log `IMPORT_EMPTY` and insert no rows.",
        "- AC-001.3 (removed in 1.1.0) Empty files finish fast with status `empty` and log `IMPORT_EMPTY`.",
    )
    _drop_t001_3(prd)
    assert lint(prd) == []


def test_removed_ac_skips_vague_word(prd):
    edit(prd, "features/import.md", AC3, AC3_REMOVED + " and fast")
    _drop_t001_3(prd)
    assert "vague-word" not in fired(lint(prd))


def test_removed_nfr_ac_continuation_skips_vague_word(prd):
    edit(
        prd,
        "nfr.md",
        "under 50 requests/s.\n",
        "under 50 requests/s.\n- AC-004.2 (removed in 1.1.0) The API shall stay\n  fast and robust.\n",
    )
    assert lint(prd) == []
