"""Routing: /prd-context, the changing-prds and adopting-prds wording, and the managed block."""
import re
from pathlib import Path

from conftest import edit
from prdlint import model
import prd_block
from test_adopting_skill import SKILL as ADOPTING
from test_adoption_file import adopt

ROOT = Path(__file__).parent.parent
CHANGING = ROOT / "skills/changing-prds/SKILL.md"

BULLET = ("To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD\n"
          "  files only to edit them. Build an approved change with `/prd-build <area> <IDs>`. Code\n"
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
    assert "<scripts>/prd_context.py" in step1 and 'echo "prd-context-exit=$?"' in step1
    assert "Read whole PRD files only to edit them" in CHANGING.read_text()
    assert "Grep the PRD folder for each ID" not in step1
    assert "as your first look at the PRD, run the pack" in " ".join(step1.split())
    rule6 = " ".join(section(CHANGING, "6. **Read whole PRD files", "## Version rule").split())
    assert "Run the pack before you open any PRD file" in rule6 and "`cat`, `head`, `sed` or `grep`" in rule6
    assert "Test cases and other areas' files come from the pack" not in rule6
    assert "Another area's files come from the pack, never from a read" in rule6
    assert "the area's own test cases are opened only to revise them in step 2" in rule6


def test_changing_step_5_hands_off_to_prd_build():
    step5 = section(CHANGING, "5. **Approval, then commit.**", "## Red Flags")
    assert "/prd-build <area> <changed IDs>" in step5 and "Code written outside `/prd-build`" in step5


def test_adopting_previews_come_from_the_implement_pack():
    how = section(ADOPTING, "**How to ask.**", "**The checklist file.**")
    assert "--for implement --req" in how and "prd-context-exit" in how
    checklist = section(ADOPTING, "**The checklist file.**", "When every requirement")
    assert "--for implement --req" in checklist


def test_command_maps_arguments():
    raw = (ROOT / "commands/prd-context.md").read_text()
    t = " ".join(raw.split())
    assert raw.startswith("---\ndescription: ") and "<scripts>/prd_context.py" in t
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


def test_changing_rule_6_lets_a_dismissal_quote_a_prd_line():
    rule6 = " ".join(section(CHANGING, "6. **Read whole PRD files", "## Version rule").split())
    assert "or reading a PRD line to quote it verbatim when dismissing a dry-run question, as step 4 requires" in rule6


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


def test_changing_step_5_keeps_the_refresh_for_code_outside_prd_build():
    step5 = " ".join(section(CHANGING, "5. **Approval, then commit.**", "## Red Flags").split())
    after = step5[step5.index("Code written outside `/prd-build`"):]
    assert "/prd-context <area> <changed IDs> implement" in after
    assert "After the code commit, run the implement pack again" in after
    assert "rewrite each STALE `Source:` of a changed block as `<path>:<line> @<new short sha>` and commit the PRD" in after
    assert "provenance, not behaviour" in after and "no version bump and no §14 row" in after
    assert "the status stays Approved with no re-approval" in after


def test_block_names_hook_install():
    assert "Run `.prd-toolkit/prd_hooks.py install` once per clone" in (ROOT / "templates/claude-block.md").read_text()


def test_block_renders_the_install_command_with_the_prd_path(prd):
    """R38: the block names the real PRD path, and the command sits on one line (no broken code span)."""
    block = prd_block.render_block(model.load(prd), "docs/prd/orders")
    assert "`uv run --script .prd-toolkit/prd_hooks.py install docs/prd/orders`" in block
    assert "<slug>" not in block


def test_format_source_and_statuses():
    t = " ".join((ROOT / "references/prd-format.md").read_text().split())
    assert "where the code that implements the block is" in t and "A status move is progress, not behaviour" in t


# --- Task 11: existing text learns deploying (spec sections 3 and 9) ---

AUTHORING = ROOT / "skills/authoring-prds/SKILL.md"
RUNNING_BUILD = ROOT / "skills/building-from-prds/running-a-build.md"
FORMAT = ROOT / "references/prd-format.md"
SPEC_BASE = ROOT.parent / "docs/superpowers/specs/2026-10-29-prd-toolkit-design.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_authoring_interview_asks_for_deploying():
    t = flat(AUTHORING)
    assert "which environment is production" in t and "the smoke cases" in t
    assert "(actor: agent|human) (env: <environment>)" in t
    assert "`(actor: human)` runbook steps" in t  # the registered-skill rule stays
    assert "passes the `runbook-steps`, `runbook-env`, `production-gate`, `runbook-tests` and `drift-rows` rules" in t


def test_adoption_writes_the_runbook_as_built():
    t = flat(ADOPTING)
    step0 = " ".join(section(ADOPTING, "- **Fill the project-wide sections from the repo**", "- **Test roots:**").split())
    assert "writes the runbook as-built, from the repo's deploy scripts, CI files and docs" in step0
    assert "Environments with the `Production` column" in step0 and "offer the `## Drift` table" in step0
    assert "from the deploy scripts, CI files and docs the extractor read" not in t
    assert "writes the runbook as-built" in t and "`[NEEDS CLARIFICATION]` for a command it cannot find" in t
    assert "offer the `## Drift` table" in t


def test_build_close_leaves_deploy_gate_tests_to_prd_deploy():
    t = flat(RUNNING_BUILD)
    assert "deploy-gate tests run at `/prd-deploy`" in t


def test_block_names_the_deployer():
    t = (ROOT / "templates/claude-block.md").read_text()
    assert "/prd-deploy" in t and "never run a runbook command yourself" in " ".join(t.split())


def test_format_has_the_runbook_grammar():
    t = flat(FORMAT)
    assert "`N. <title> (actor: agent|human) (env: <environment>)`" in t
    assert "(actor: agent)` or `(actor: human)` on the step's first line" not in t  # the 0.4 text
    for word in ("`Run:`", "`Check:`", "`Rollback:`", "`Do:`", "prints `<text>`", "`tests <level>[, <level>]`",
                 "| Environment | URL | Production |", "## Deployed", "| Environment | PRD version | Commit | Date | Run |",
                 "## Drift", "| Environment | Check | Introspection command |", "`version` or `config`",
                 "`smoke`", "Gate `deploy`", "`runbook-steps`", "`runbook-env`", "`production-gate`",
                 "`runbook-tests`", "`drift-rows`"):
        assert word in t, word


def test_format_unclassified_and_migration_row():
    t = flat(FORMAT)
    assert "unclassified" in t and "only on an open entry" in t
    assert "format: runbook steps (prd-toolkit 0.5)" in t


def test_base_spec_revision_notes():
    t = " ".join(SPEC_BASE.read_text(encoding="utf-8").split())
    assert "Revised in prd-toolkit 0.5: `prd-deployer` is replaced by `prd_deploy.py` and `running-a-deploy.md`" in t
    assert "Revised in prd-toolkit 0.5: the `drift` row loses its `schema.sql` half until 0.6" in t


# --- R21: no Bash command holds ${CLAUDE_PLUGIN_ROOT}, which is empty there ---

R21_FILES = ["agents/prd-builder.md", "commands/prd-context.md", "commands/prd-status.md",
             "skills/adopting-prds/SKILL.md", "skills/authoring-prds/SKILL.md",
             "skills/building-from-prds/SKILL.md", "skills/building-from-prds/running-a-build.md",
             "skills/changing-prds/SKILL.md"]


def test_r21_no_bash_command_holds_plugin_root():
    for rel in R21_FILES:
        t = (ROOT / rel).read_text(encoding="utf-8")
        assert '"${CLAUDE_PLUGIN_ROOT}/scripts/' not in t, rel
        assert "${CLAUDE_PLUGIN_ROOT}/scripts/" not in t, rel
        assert "<scripts>/" in t, rel


def test_r21_each_file_says_which_script():
    for rel in R21_FILES:
        if rel == "agents/prd-builder.md":
            continue
        t = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        assert "`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call" in t, rel
        assert "a literal absolute path" in t and "two directories above" in t, rel
        assert "Base directory for this skill" in t, rel


def test_r21_adopted_repos_use_the_vendored_copy_and_unadopted_the_plugin():
    for rel in ("skills/changing-prds/SKILL.md", "skills/building-from-prds/SKILL.md",
                "skills/building-from-prds/running-a-build.md", "skills/adopting-prds/SKILL.md",
                "commands/prd-context.md", "commands/prd-status.md"):
        t = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        assert "`<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/` directory" in t, rel
    t = " ".join((ROOT / "skills/adopting-prds/SKILL.md").read_text(encoding="utf-8").split())
    assert "A first adoption has no `.prd-toolkit/` until the hooks install, so it uses the plugin path" in t
    for rel in ("skills/authoring-prds/SKILL.md",):
        t = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        assert "has no `.prd-toolkit/` until the hooks install" in t, rel
        assert "`<scripts>` is the plugin's `scripts` directory" in t, rel


def test_r21_command_wording_and_load_only_for_the_path():
    for rel in ("commands/prd-context.md", "commands/prd-status.md"):
        t = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        assert "when a prd-toolkit skill loads" in t and "when the skill loads a prd-toolkit skill" not in t, rel
        assert "loaded only to read its base directory" in t and "none of its steps are followed" in t, rel


def test_r21_every_scripts_call_is_vendored():
    """Scan, do not list: a script a text calls through <scripts> must be one the hooks vendor."""
    from prdlint import hooks
    called = set()
    for rel in R21_FILES:
        called |= set(re.findall(r"<scripts>/(\w+\.py)", (ROOT / rel).read_text(encoding="utf-8")))
    called |= set(re.findall(r"<scripts>/(\w+\.py)", (ROOT / "skills/deploying-from-prds/running-a-deploy.md").read_text(encoding="utf-8")))
    assert called and "prd_block.py" in called
    assert called <= set(hooks.VENDORED), called - set(hooks.VENDORED)


def test_gap_rule_keeps_its_end():
    assert "Do not guess or read the code to fill the gap." in " ".join((ROOT / "templates/claude-block.md").read_text().split())


def test_format_repeated_label_reported():
    assert "one per label; a repeated label is ignored" not in flat(FORMAT)
    assert "one per label; lint reports a repeated label (`runbook-steps`), and the first is used" in flat(FORMAT)


def test_04_spec_notes_the_scripts_line():
    t = " ".join((ROOT.parent / "docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md").read_text(encoding="utf-8").split())
    assert "Revised in prd-toolkit 0.5 (R21): the dispatch also carries a `Scripts:` line" in t


def test_r21_builder_gets_the_scripts_path_in_its_prompt():
    for rel in ("agents/prd-builder.md", "skills/building-from-prds/SKILL.md", "skills/building-from-prds/running-a-build.md"):
        t = (ROOT / rel).read_text(encoding="utf-8")
        assert "Scripts: <scripts directory, as an absolute path>" in t or rel.startswith("agents"), rel
    b = " ".join((ROOT / "agents/prd-builder.md").read_text(encoding="utf-8").split())
    assert "the `Scripts:` line when your prompt has one; otherwise the Which-script rule of the `building-from-prds` skill" in b
    assert "run nothing" not in b
