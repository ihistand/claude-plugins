"""Known-failing tests mark themselves: the tester skill, agent, adoption route, format reference and README."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/testing-from-prds/SKILL.md"
AGENT = ROOT / "agents/prd-tester.md"
ADOPT = ROOT / "skills/adopting-prds/SKILL.md"
FORMAT = ROOT / "references/prd-format.md"
README = ROOT / "README.md"
SPEC04 = ROOT.parent / "docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_tester_writes_strict_expected_failure():  # (a)
    s = flat(SKILL)
    assert "known-failing: E-nnn" in s and "strict" in s
    assert "xfail(strict=True)" in s and "test.failing" in s


def test_tester_tags_the_citation():  # (b)
    for p in (SKILL, AGENT):
        assert "@prd <T-id> known-failing <E-nnn>" in flat(p), p


def test_marker_way_recorded_under_harness_choices():  # (c)
    s = flat(SKILL)
    assert "HARNESS CHOICES" in s and "how you marked" in s


def test_results_line_stays_known_failing():  # (d)
    s = flat(SKILL)
    assert "`<T-id>: known-failing E-nnn`" in s
    assert "xfail" in s and "still reports" in s


def test_fixes_write_round_removes_marker_and_tag():  # (e)
    for p in (SKILL, AGENT):
        s = flat(p)
        assert "--fixes" in s and "regression test" in s, p
        assert "removes the marker and the tag" in s, p


def test_adoption_real_bug_route_marks_test():
    s = flat(ADOPT)
    assert "known-failing <E-nnn>" in s and "strict" in s


def test_format_reference_documents_tag():
    s = flat(FORMAT)
    assert "@prd <T-id> known-failing <E-nnn>" in s and "strict" in s


def test_readme_no_longer_says_job_is_red():
    s = flat(README)
    assert "stays red" not in s and "until 0.6" not in s
    assert "known-failing" in s and "mark themselves" in s


def test_04_spec_limit_revised():
    s = flat(SPEC04)
    assert "Revised in prd-toolkit 0.6: known-failing tests mark themselves; see the 0.6 design §8" in s
    assert "until 0.6" not in s


def test_r21_tester_unmarks_a_deploy_gate_regression_test_too():
    t = " ".join((ROOT / "skills/testing-from-prds/SKILL.md").read_text(encoding="utf-8").split())
    assert "a deploy-gate regression test too (it is run at `/prd-deploy`" in t


R1 = ("In a write or a suite you may read the vendored pack's files under `.prd-toolkit/packs/`; "
      "in a dry run, only its `pack.yaml`.")
R2 = ("A harness run longer than the Bash tool's timeout runs in the background; read its `<id>.output` file, "
      "and never another task's output.")
R3 = ("A helper a pack ships is stated in the pack's `harness` (the Assertions or Fixtures slot) with its parameters, "
      "their types and the shape of its result. A shipped helper whose shapes are not stated is a dry-run question, "
      "not a HARNESS CHOICE.")


def test_the_tester_reads_its_background_output_and_the_vendored_pack():  # 0.8.2, spec section 14
    for p in (SKILL, AGENT):
        s = flat(p)
        assert R1 in s and R2 in s, p
    assert "the guard lets you read only an `<id>.output` file there" in flat(SKILL)


def test_a_shipped_helpers_shapes_are_stated_in_the_pack_or_asked():
    for p in (FORMAT, ROOT / "references/contract-types.md"):
        assert R3 in flat(p), p


def test_a_shipped_helper_is_asked_about_never_stood_in_for():
    for p in (SKILL, AGENT):
        s = flat(p)
        assert "A shipped helper whose shapes are not stated is a dry-run question, not a HARNESS CHOICE" in s or \
            "A helper a pack ships whose shapes are not stated is a dry-run question, not a HARNESS CHOICE" in s, p
        assert "stand-in" in s, p
