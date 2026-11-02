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
    assert line.startswith("- [ ] Does ") and line.endswith("?")
    for word in ("package layout", "entry points", "install command"):
        assert word in line, word
