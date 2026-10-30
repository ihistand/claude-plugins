"""Routing: /prd-context, the changing-prds and adopting-prds wording, and the managed block."""
from pathlib import Path

from conftest import edit
from prdlint import model
import prd_block
from test_adopting_skill import SKILL as ADOPTING
from test_adoption_file import adopt

ROOT = Path(__file__).parent.parent
CHANGING = ROOT / "skills/changing-prds/SKILL.md"

BULLET = ("To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD\n"
          "  files only to edit them. Before writing code for an approved change, run `/prd-context <area>\n"
          "  <IDs> implement`. Code implements the PRD; it never defines behaviour the PRD lacks.")


def section(path: Path, start: str, end: str) -> str:
    text = path.read_text(encoding="utf-8")
    a = text.index(start)
    return text[a:text.index(end, a)]


def add_required_skills(prd: Path, n: int) -> None:
    row = "| plans | superpowers:writing-plans | required |\n"
    extra = "".join(f"| Skill {i} | example:skill-{i} | required |\n" for i in range(n))
    edit(prd, "prd.md", row, row + extra)


def test_block_bullet():
    t = (ROOT / "templates/claude-block.md").read_text()
    assert BULLET in t and "Read the PRD, not the code, to learn" not in t


def test_block_stays_small(prd):
    adopt(prd, "".join(f"| area-{i:02} | adopted | `src/a{i}/**` |\n" for i in range(20)))
    add_required_skills(prd, 4)
    assert len(prd_block.render_block(model.load(prd), "docs/prd/orders").encode()) < 1536


def test_changing_step_1_runs_the_decide_pack():
    step1 = section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**")
    assert "scripts/prd_context.py" in step1 and 'echo "prd-context-exit=$?"' in step1
    assert "Read whole PRD files only to edit them" in CHANGING.read_text()
    assert "Grep the PRD folder for each ID" not in step1


def test_changing_step_5_hands_off_the_implement_pack():
    step5 = section(CHANGING, "5. **Approval, then commit.**", "## Red Flags")
    assert "/prd-context <area> <changed IDs> implement" in step5


def test_adopting_previews_come_from_the_implement_pack():
    how = section(ADOPTING, "**How to ask.**", "**The checklist file.**")
    assert "--for implement --req" in how and "prd-context-exit" in how
    checklist = section(ADOPTING, "**The checklist file.**", "When every requirement")
    assert "--for implement --req" in checklist


def test_command_maps_arguments():
    t = (ROOT / "commands/prd-context.md").read_text()
    assert t.startswith("---\ndescription: ") and "scripts/prd_context.py" in t
    assert "--for implement" in t and "--req" in t and "prd-context-exit" in t
