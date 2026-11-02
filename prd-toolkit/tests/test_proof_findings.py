"""Pins for the three findings of the 0.4 hello-world proof run (F1 Source kept, F2 comma IDs, F3 approval commit Refs)."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHANGING = ROOT / "skills/changing-prds/SKILL.md"
AUTHORING = ROOT / "skills/authoring-prds/SKILL.md"
COMMAND = ROOT / "commands/prd-build.md"
RUN = ROOT / "skills/building-from-prds/running-a-build.md"
NO_REFS = "`Refs: none (no behaviour change)`"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a)]


def test_f1_a_revised_block_keeps_its_source_line():
    step2 = between(flat(CHANGING), "2. **Edit the PRD.**", "3. **Bump the version**")
    assert "A revised block keeps its `Source:` line" in step2
    assert "never drop it" in step2


def test_f1_red_flag_quotes_the_dropped_source_excuse():
    flags = between(flat(CHANGING), "## Red Flags - STOP", "## Common Rationalizations")
    assert '"/prd-build rewrites it"' in flags and "`Source:`" in flags


def test_f2_build_ids_are_joined_with_commas_for_req():
    for text in (flat(COMMAND), flat(RUN)):
        assert "joined with commas" in text and "`--req FR-006,FR-001`" in text
        assert "never space-separated" in text


def test_f3_approval_commit_carries_refs_none():
    phase7 = [l for l in AUTHORING.read_text(encoding="utf-8").splitlines() if l.startswith("| 7 |")][0]
    phase7 = " ".join(phase7.split())
    assert "commit the folder and CLAUDE.md with " + NO_REFS in phase7


def test_f3_changing_commit_of_prd_and_claude_md_carries_refs_none():
    step5 = between(flat(CHANGING), "5. **Approval, then commit.**", "## Red Flags")
    assert "commit the PRD folder and CLAUDE.md with the trailer " + NO_REFS in step5


def test_r16_patch_row_and_bump_rule_name_the_two_exceptions():
    """Review: the Patch row and the bump rule carry the regression patch and the corrected-to-match test case."""
    text = flat(CHANGING)
    rule = between(text, "## Version rule", "**A regression patch.**")
    patch_row = between(rule, "| **Patch** |", "If any existing AC")
    assert "a regression patch for an `errors.md` entry" in patch_row
    assert "a test case or contract corrected to match its own unchanged AC" in patch_row
    bump = rule.split("If any existing AC", 1)[1]
    assert "Yes means major" in bump and "except the two patches in the Patch row" in bump
    assert "any other changed `expect`" in bump and "major" in bump
    corrected = between(text, "**A test case or contract corrected to match its AC.**", "## ID rules")
    assert "`invalid requirement`" in corrected and "no AC or behaviour changes" in corrected
    assert "`Refs: FR-001, E-003`" in corrected or "cite the entry" in corrected
