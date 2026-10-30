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
    raw = (ROOT / "commands/prd-context.md").read_text()
    t = " ".join(raw.split())
    assert raw.startswith("---\ndescription: ") and "scripts/prd_context.py" in t
    assert "ask which PRD" in t
    assert "is the area: pass it as `--area <area>`" in t
    assert "`UJ-`, `FR-`, `NFR-`, `AC-`, `T-` or `E-`" in t and "never the area" in t
    assert "maps to its FR" in t
    assert "`implement` becomes `--for implement`" in t and "`--req <ID>[,<ID>" in t
    assert "On `prd-context-exit=1`" in t and "re-read the regions marked STALE" in t
    assert "On `prd-context-exit=2`" in t and "nothing printed" in t


def test_changing_pack_ids_are_requirement_ids():
    step1 = " ".join(section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**").split())
    step5 = " ".join(section(CHANGING, "5. **Approval, then commit.**", "## Red Flags").split())
    for s in (step1, step5):
        assert "only the UJ, FR and NFR IDs" in s and "AC, test case or error code to its requirement" in s


def test_changing_step_1_new_subproject_and_bug_fix():
    step1 = " ".join(section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**").split())
    assert "A new sub-project has no area yet: leave out `--area` and `--req`" in step1
    assert "`Touches:`" in step1 and "bug fix" in step1


def test_adopting_previews_keep_the_whole_block_and_source():
    text = " ".join(ADOPTING.read_text().split())
    assert text.count("the whole block and its `Source:` excerpt, as the `implement` pack prints them") == 1
    assert text.count("the whole block and its `Source:` excerpt, as the `--for implement --req <ID>` pack prints them") == 1
