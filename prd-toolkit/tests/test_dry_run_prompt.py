"""The shared dry-run prompt separates PRD gaps from the tester's own harness choices.

Found in the 0.1 acceptance run: on a new project the harness helpers testing.md names do not
exist yet, so a tester asked about their internals every round and the gate never converged.
"""
import re
from pathlib import Path

PROMPT = Path(__file__).parent.parent / "skills" / "authoring-prds" / "dry-run-prompt.md"


def prompt_block() -> str:
    return re.search(r"^```\n(.*?)^```", PROMPT.read_text(encoding="utf-8"), re.S | re.M).group(1)


def test_tester_writes_missing_helpers_itself():
    block = prompt_block()
    assert "do not exist yet" in block and "write them yourself" in block


def test_helper_internals_are_harness_choices_not_questions():
    block = prompt_block()
    assert "HARNESS CHOICES" in block
    assert block.index("1. QUESTIONS") < block.index("3. HARNESS CHOICES") < block.index("4. FILES READ")


def test_pass_terms_review_harness_choices():
    after = PROMPT.read_text(encoding="utf-8").split("```")[-1]
    assert "HARNESS CHOICES" in after and "contradicts" in after


SKILLS = Path(__file__).parent.parent / "skills"


def test_pass_terms_allow_dismissal_only_by_exact_quote():
    # found in the 0.1 acceptance run: six dry runs, real gaps fell to 2, yet a model tester
    # re-asked 5-7 answered questions every run, so "QUESTIONS is none" could never pass
    after = PROMPT.read_text(encoding="utf-8").split("```")[-1]
    assert "DISMISSED" in after and "exact" in after and "quote" in after


def test_both_skills_flag_a_dismissal_without_a_quote():
    for skill in ("authoring-prds", "changing-prds"):
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "dismissed without an exact quote" in text, skill
