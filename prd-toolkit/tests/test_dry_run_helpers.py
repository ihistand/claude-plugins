"""0.8.2, spec section 17 fixes 1 to 3: a dry run imports a pack's helpers, a harness states its traceback rule,
and a dry run that failed only on Harness conventions keeps the PRD `In review`.

Each pin carries a sentence an agent must meet; the RED baselines are in evals/BASELINE.md (Task 13).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/testing-from-prds/SKILL.md"
DRY_RUN = ROOT / "skills/authoring-prds/dry-run-prompt.md"
AGENT = ROOT / "agents/prd-tester.md"
TEMPLATE = ROOT / "templates/prd/testing.md"
FORMAT = ROOT / "references/prd-format.md"
CHECKLIST = ROOT / "references/quality-checklist.md"
AUTHORING = ROOT / "skills/authoring-prds/SKILL.md"
ADOPTING = ROOT / "skills/adopting-prds/SKILL.md"

NEVER_WRITTEN = (
    "A helper the area's pack ships (stated in the pack's `harness`) is never written: in every mode, a dry run "
    "included, the test imports it from the vendored pack, as the Harness says."
)
TRACEBACK = (
    "Say how a failure report avoids printing the values a test passes: for pytest, the harness commands carry "
    "`--tb=short`, or each helper that takes a value sets `__tracebackhide__ = True`; another harness names its own "
    "equivalent."
)
CHECK = "The Leaks slot says how a failure's traceback is kept free of test values."


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_a_pack_helper_is_never_written_in_any_mode():
    for p in (SKILL, DRY_RUN, AGENT):
        assert NEVER_WRITTEN in flat(p), p


def test_the_write_them_yourself_rule_names_its_exception():
    s = flat(SKILL)
    assert "Test helpers that testing.md names, other than one a pack ships," in s
    assert "without looking whether they exist" in s  # stays, for a helper no pack ships


def test_the_dry_run_prompt_helper_paragraph_has_the_exception_too():
    block = re.search(r"^```\n(.*?)^```", DRY_RUN.read_text(encoding="utf-8"), re.S | re.M).group(1)
    assert "Test helpers that <PRD_DIR>/testing.md names, other than one a pack ships," in " ".join(block.split())


def test_the_leaks_slot_and_its_format_description_say_how_tracebacks_stay_clean():
    for p in (TEMPLATE, FORMAT):
        assert TRACEBACK in flat(p), p


def test_the_template_leaks_slot_keeps_its_marker():
    t = TEMPLATE.read_text(encoding="utf-8")
    leaks = [line for line in t.splitlines() if line.startswith("- **Leaks.**")]
    assert len(leaks) == 1 and "[NEEDS CLARIFICATION:" in leaks[0] and "traceback" in leaks[0]


def test_the_checklist_asks_about_the_traceback():
    assert f"- [ ] {CHECK}" in CHECKLIST.read_text(encoding="utf-8")


def test_a_harness_only_round_is_in_authoring_and_adopting():
    for p in (AUTHORING, ADOPTING):
        s = flat(p)
        for phrase in ("harness-only", "stays `In review`", "in one batch", "on a fresh sample"):
            assert phrase in s, (p, phrase)
    assert "A failed dry run is a gap: write each question into the file it names" in flat(AUTHORING)  # full round stays
