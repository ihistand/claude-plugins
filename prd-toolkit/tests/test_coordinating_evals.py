"""Structure of the seven coordinating-prds (0.7) eval cases: files present, the scaffold runs a link_repo state,
every grader is well formed and one of them is the fired (or not-fired) skill grader or a behaviour grader that
can fail (a max of 0 or a not_contains)."""
import re
import stat
from pathlib import Path

import pytest

EVALS = Path(__file__).parent.parent / "evals"
CASES = {
    "coordinating-trigger": "linked",
    "coordinating-resume-trigger": "cs-running",
    "coordinating-not-for-one-repo": "linked",
    "changing-hands-off-to-change-set": "linked",
    "change-set-no-snapshot-edit": "cs-running",
    "change-set-waits-for-upstream": "cs-running",
    "change-set-no-push": "cs-running",
}


@pytest.mark.parametrize("name,state", CASES.items())
def test_case_files(name, state):
    d = EVALS / name
    assert f"name: {name}" in (d / "case.yaml").read_text(encoding="utf-8")
    assert 'scaffold_script: scaffold.sh' in (d / "case.yaml").read_text(encoding="utf-8")
    prompt = (d / "prompt.md").read_text(encoding="utf-8")
    assert re.match(r"---\nmax_turns: \d+\n", prompt) and "Do not ask me questions" in prompt
    scaffold = d / "scaffold.sh"
    text = scaffold.read_text(encoding="utf-8")
    assert scaffold.stat().st_mode & stat.S_IXUSR
    assert f'link_repo.py" "$client" {state} --upstream "$greet"' in text
    graders = sorted((d / "graders").glob("*.md"))
    assert graders
    for g in graders:
        head = g.read_text(encoding="utf-8").split("---")[1]
        assert re.search(r"^type: (tool_used|regex)$", head, re.M), g


@pytest.mark.parametrize("name", CASES)
def test_every_case_has_a_grader_that_can_fail(name):
    heads = [g.read_text(encoding="utf-8").split("---")[1] for g in (EVALS / name / "graders").glob("*.md")]
    assert any(re.search(r"^min: [1-9]", h, re.M) or re.search(r"^max: 0", h, re.M) or "not_contains" in h
               for h in heads)


FORBIDDEN = r"/Users/|/private/|/tmp/claude|scratchpad|c-green|gitlab\.com|rotoplas|ihistand"


def _forbidden_words() -> str:
    return "acu" + "antia"  # spelled in two parts so this file does not hold the name itself


def test_no_scratch_or_host_text_in_cases_and_baseline():
    files = [f for name in CASES for f in (EVALS / name).rglob("*") if f.is_file()]
    files.append(EVALS / "baselines/coordinating-prds.md")
    for f in files:
        assert not re.search(FORBIDDEN + "|" + _forbidden_words(), f.read_text(encoding="utf-8"), re.I), f
