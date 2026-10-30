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
          "  <IDs> implement`; after the code commit, run it again and refresh each STALE `Source:`. Code\n"
          "  implements the PRD; it never defines behaviour the PRD lacks.")


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
    assert "as your first look at the PRD, run the pack" in " ".join(step1.split())
    rule6 = " ".join(section(CHANGING, "6. **Read whole PRD files", "## Version rule").split())
    assert "Run the pack before you open any PRD file" in rule6 and "`cat`, `head`, `sed` or `grep`" in rule6
    assert "Test cases and other areas' files come from the pack" not in rule6
    assert "Another area's files come from the pack, never from a read" in rule6
    assert "the area's own test cases are opened only to revise them in step 2" in rule6


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
    assert "A bug fix runs the pack with its entry's ID, `--req E-nnn`" in step1
    assert "on its entry's `Touches:` line" not in step1


def test_adopting_previews_keep_the_whole_block_and_source():
    text = " ".join(ADOPTING.read_text().split())
    assert text.count("the whole block and its `Source:` excerpt, as the `implement` pack prints them") == 1
    assert text.count("the whole block and its `Source:` excerpt, as the `--for implement --req <ID>` pack prints them") == 1


def test_changing_step_1_finds_an_unknown_area_or_ids_from_the_pack():
    step1 = " ".join(section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**").split())
    assert "If you do not know the area, run the repo pack first (no `--area`)" in step1
    assert "if you do not know the IDs, run the area pack (`--area` only) and list the touched IDs from it" in step1


def test_changing_rule_6_lets_step_0_read_section_14():
    rule6 = " ".join(section(CHANGING, "6. **Read whole PRD files", "## Version rule").split())
    assert "except step 0's check of §14" in rule6


def test_changing_step_2_refreshes_each_stale_source():
    step2 = " ".join(section(CHANGING, "2. **Edit the PRD.**", "3. **Bump the version**").split())
    assert "STALE" in step2 and "`<path>:<current line> @<HEAD short sha>`" in step2


def test_command_maps_an_error_entry_by_its_touches_line_and_handles_ids_without_area():
    t = " ".join((ROOT / "commands/prd-context.md").read_text().split())
    assert "the requirement it cites" not in t
    assert "an `E-nnn` maps to the IDs on its `Touches:` line" not in t
    assert "Pass only UJ, FR, NFR and E IDs" in t and "an `E-nnn` passes as it is" in t
    assert "IDs with no area" in t and "the area each ID's block lives in" in t and "or ask" in t


def test_shipped_text_has_no_stale_milestone():
    t = (ROOT / "skills/testing-from-prds/SKILL.md").read_text()
    assert "building (0.4)" in t and "building (0.3)" not in t


def test_readme_links_every_spec():
    t = (ROOT / "README.md").read_text()
    for spec in ("2026-10-29-prd-toolkit-design.md", "2026-10-29-prd-toolkit-0.2-design.md", "2026-10-30-prd-toolkit-0.3-design.md"):
        assert f"(../docs/superpowers/specs/{spec})" in t and (ROOT.parent / "docs/superpowers/specs" / spec).is_file()


NO_FILTER = "Never pipe, filter or truncate the pack's output (no `| head`, no `| grep`)"


def test_pack_output_is_never_filtered():
    step1 = " ".join(section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**").split())
    command = " ".join((ROOT / "commands/prd-context.md").read_text().split())
    how = " ".join(section(ADOPTING, "**How to ask.**", "**The checklist file.**").split())
    for text in (step1, command, how):
        assert NO_FILTER in text and "the filter's status" in text


def test_changing_step_5_refreshes_sources_after_the_code_commit():
    step5 = " ".join(section(CHANGING, "5. **Approval, then commit.**", "## Red Flags").split())
    after = step5[step5.index("/prd-context <area> <changed IDs> implement"):]
    assert "After the code commit, run the implement pack again" in after
    assert "rewrite each STALE `Source:` of a changed block as `<path>:<line> @<new short sha>` and commit the PRD" in after
    assert "provenance, not behaviour" in after and "no version bump and no §14 row" in after
