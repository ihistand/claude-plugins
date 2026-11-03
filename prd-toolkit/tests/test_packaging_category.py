"""F-a: the authoring interview asks about packaging, and the eval case for it is well formed."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CATEGORIES = (ROOT / "references/clarify-categories.md").read_text(encoding="utf-8")
CHECKLIST = (ROOT / "references/quality-checklist.md").read_text(encoding="utf-8")
SKILL = (ROOT / "skills/authoring-prds/SKILL.md").read_text(encoding="utf-8")


def _category_lines():
    return re.findall(r"^\d+\. (.*)$", CATEGORIES.split("## Scoring")[0], re.M)


def test_packaging_category_names_the_four_things():
    line = next((l for l in _category_lines() if l.startswith("Packaging:")), "")
    for word in ("build backend", "package layout", "entry points", "install command"):
        assert word in line, word


def test_the_category_count_heading_and_skill_agree():
    n = len(_category_lines())
    words = {13: "thirteen"}
    assert n == 13
    assert f"## The {words[n]} categories" in CATEGORIES
    assert f"all {words[n]} categories" in SKILL


def test_checklist_asks_about_packaging():
    line = next((l for l in CHECKLIST.splitlines() if "build backend" in l), "")
    assert line.startswith("- [ ] If the project ships code, does ") and line.endswith("?")
    for word in ("package layout", "entry points", "install command"):
        assert word in line, word


def test_packaging_is_asked_whenever_the_project_ships_code():
    line = next(l for l in _category_lines() if l.startswith("Packaging:"))
    assert "whenever the project ships code" in line and "Not applicable" in line
    assert "whenever the project ships code" in SKILL and "category 13" in SKILL
    check = next(l for l in CHECKLIST.splitlines() if "build backend" in l)
    assert "ships code" in check and "Not applicable" in check


SENTENCE = ("for a project that ships code, each of the four packaging elements is either stated or written "
            "as its own `[NEEDS CLARIFICATION: <element> …]` marker in section 1, never left out")


def test_each_packaging_element_is_stated_or_marked_never_left_out():
    flat = lambda s: " ".join(s.split()).lower()
    assert flat(SENTENCE) in flat(CATEGORIES)
    assert flat(SENTENCE) in flat(SKILL)
