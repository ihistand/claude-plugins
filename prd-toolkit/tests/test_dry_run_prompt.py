"""The shared dry-run prompt separates PRD gaps from the tester's own harness choices.

Found in the 0.1 acceptance run: on a new project the harness helpers testing.md names do not
exist yet, so a tester asked about their internals every round and the gate never converged.
"""
import re
from pathlib import Path

import pytest

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


LINT_SKILLS = [Path(__file__).parent.parent / f"skills/{n}/SKILL.md" for n in ("authoring-prds", "changing-prds")]
LINT_CMD = 'prd_lint.py" docs/prd/<slug>; echo "prd-lint-exit=$?"'


@pytest.mark.parametrize("skill", LINT_SKILLS, ids=lambda p: p.parent.name)
def test_skill_lint_command_echoes_its_exit_code(skill):
    text = skill.read_text(encoding="utf-8")
    assert LINT_CMD in text
    # the lint-exit-0 eval grader matches this literal; skill text must never hold it
    assert "prd-lint-exit=0" not in text
    for line in text.splitlines():
        if "prd_lint.py" in line and "--sample-tids" not in line:
            assert 'echo "prd-lint-exit=$?"' in line, line
        if "lint" in line.lower() and re.search(r"\bexits? 0\b", line):
            assert "prd-lint-exit" in line, f"a gate must name the echoed value: {line}"
    assert RULE in text


RULE = ("The gate is the `prd-lint-exit=` value lint prints: `0` clean, `1` violations, `2` usage or internal "
        "error. Ignore the Bash call's own success; the trailing echo always succeeds.")


def test_authoring_copies_the_template_with_read_and_write_not_cp():
    """A sandbox that denies the plugin folder as a copy source blocks `cp -R`; Read and Write are granted tools."""
    text = (SKILLS / "authoring-prds/SKILL.md").read_text(encoding="utf-8")
    assert "cp -R" not in text
    copy = re.search(r"^- \*\*Copy:\*\*.*?(?=^- \*\*)", text, re.S | re.M)
    assert copy, "no '- **Copy:**' bullet in phase 2"
    copy = " ".join(copy.group(0).split())
    for word in ("Read", "Write", "`${CLAUDE_PLUGIN_ROOT}/templates/prd/`", "`docs/prd/<slug>/`", "same relative path"):
        assert word in copy, word


def test_authoring_description_covers_a_no_questions_request():
    """A "do not ask me questions" prompt once talked a run out of the skill ("that skill interviews you")."""
    text = (SKILLS / "authoring-prds/SKILL.md").read_text(encoding="utf-8")
    desc = re.search(r"^description: (.*)$", text, re.M).group(1)
    assert "when the user says not to ask questions, writes that folder with every unknown marked" in desc
    assert desc.startswith("Use when the user wants a PRD, product spec or requirements document written")
    assert len(desc) <= 1024
