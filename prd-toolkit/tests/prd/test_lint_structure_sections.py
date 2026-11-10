"""lint-structure FR-022 and FR-023: prd.md's sections, the mandatory and optional files."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, symptom  # noqa: E402

D = "docs/prd/orders"
P = f"{D}/prd.md"


def test_missing_section(tmp_path, monkeypatch):
    """@prd T-022.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(86, "## 9. Version")
    check(o.run(), exit=1, contains_line=f"{P}:1: sections: missing section '## 9. Versioning'", stderr="")


def test_out_of_order_once(tmp_path, monkeypatch):
    """@prd T-022.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").swap(86, 94).swap(98, 108)
    check(o.run(), exit=1, count_of_line=(f"{P}:1: sections: sections are out of order", 1), stderr="")


def test_unexpected_numbered_section(tmp_path, monkeypatch):
    """@prd T-022.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").append("## 15. Appendix")
    check(o.run(), exit=1, contains_line=f"{P}:123: sections: unexpected section '## 15. Appendix'", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-009")
def test_unexpected_unnumbered_section(tmp_path, monkeypatch):
    """@prd T-022.4 known-failing E-009"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").append("## Notes")
    r = o.run()
    symptom(
        "unexpected section '## None. Notes'" in r.stdout,
        "E-009",
        "the heading is quoted as `## None. Notes`, not as written",
        r,
    )
    check(r, exit=1, contains_line=f"{P}:123: sections: unexpected section '## Notes'", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-014")
def test_duplicate_section(tmp_path, monkeypatch):
    """@prd T-022.5 known-failing E-014"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").append("## 9. Versioning")
    r = o.run()
    symptom(
        "sections are out of order" in r.stdout and "duplicate section" not in r.stdout,
        "E-014",
        "the repeated section is reported as `sections are out of order`, with no duplicate finding",
        r,
    )
    check(
        r,
        exit=1,
        contains_line=f"{P}:123: sections: duplicate section '## 9. Versioning'",
        not_contains="sections are out of order",
        stderr="",
    )


def test_mandatory_file_missing(tmp_path, monkeypatch):
    """@prd T-023.1"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("errors.md")
    check(o.run(), exit=1, contains_line=f"{D}/errors.md:0: sections: mandatory 'errors.md' is missing", stderr="")


def test_mandatory_folder_missing(tmp_path, monkeypatch):
    """@prd T-023.2"""
    o = Orders(tmp_path, monkeypatch)
    for name in ("api", "import", "nfr"):
        o.delete(f"test-cases/{name}.yaml")
    o.write("test-cases/notes.txt", "notes\n")
    check(o.run(), exit=1, contains_line=f"{D}/test-cases:0: sections: mandatory 'test-cases/' is missing", stderr="")


def test_mandatory_marked_not_applicable(tmp_path, monkeypatch):
    """@prd T-023.3"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("errors.md")
    o.lines("prd.md").insert_before(19, "- Not applicable: `errors.md` — no errors yet")
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:19: sections: mandatory 'errors.md' cannot be marked not applicable",
        not_contains="mandatory 'errors.md' is missing",
        stderr="",
    )


def test_optional_file_absent(tmp_path, monkeypatch):
    """@prd T-023.4"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/config.yaml")
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:1: sections: 'contracts/config.yaml' is absent and section 1 has no 'Not applicable: `contracts/config.yaml` — reason' line",
        stderr="",
    )


def test_optional_folder_empty(tmp_path, monkeypatch):
    """@prd T-023.5"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/dependencies/geocoder.yaml")
    assert (o.root / "contracts" / "dependencies").is_dir()
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:1: sections: 'contracts/dependencies/' is absent and section 1 has no 'Not applicable: `contracts/dependencies/` — reason' line",
        stderr="",
    )


def test_optional_file_not_applicable(tmp_path, monkeypatch):
    """@prd T-023.6"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/config.yaml")
    o.lines("prd.md").insert_before(19, "- Not applicable: `contracts/config.yaml` — no settings")
    check(o.run(), not_contains="'contracts/config.yaml' is absent", stderr="")


def test_events_slot_by_asyncapi(tmp_path, monkeypatch):
    """@prd T-023.7"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/events.md")
    o.lines("prd.md").insert_before(19, "- Not applicable: `contracts/asyncapi.yaml` — no message queues")
    check(o.run(), not_contains="'contracts/events.md' is absent", stderr="")


def test_folder_slot_without_slash(tmp_path, monkeypatch):
    """@prd T-023.8"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/dependencies/geocoder.yaml")
    assert (o.root / "contracts" / "dependencies").is_dir()
    o.lines("prd.md").insert_before(19, "- Not applicable: `contracts/dependencies` — no external services")
    check(o.run(), not_contains="'contracts/dependencies/' is absent", stderr="")
