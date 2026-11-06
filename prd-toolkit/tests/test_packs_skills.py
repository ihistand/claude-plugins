"""prd-toolkit 0.8.0 skill and agent text for packs, languages and judged cases (spec section 9, R-1).

Each pin carries one sentence or command an agent must meet; the RED baselines it answers are in
evals/baselines/packs-and-judged.md (D1 to D5).
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILLS = ROOT / "skills"
AUTHORING = SKILLS / "authoring-prds/SKILL.md"
DRY_RUN = SKILLS / "authoring-prds/dry-run-prompt.md"
ADOPTING = SKILLS / "adopting-prds/SKILL.md"
TESTING = SKILLS / "testing-from-prds/SKILL.md"
DISPATCHING = SKILLS / "testing-from-prds/dispatching.md"
TESTER = ROOT / "agents/prd-tester.md"
BUILDING = SKILLS / "building-from-prds/SKILL.md"
RUNNING = SKILLS / "building-from-prds/running-a-build.md"
BUILDER = ROOT / "agents/prd-builder.md"
CHANGING = SKILLS / "changing-prds/SKILL.md"
ERRORS = SKILLS / "handling-errors/SKILL.md"

# --list-packs echoes its own tag (R26): `prd-lint-exit=0` belongs to a lint of the PRD folder, and graders read it
GATE = '; echo "prd-list-packs-exit=$?"'
# --list-packs always runs from the plugin's own scripts (final review 1a): a vendored copy lists only what it vendored
LIST_PACKS = "uv run --script <plugin scripts>/prd_lint.py --list-packs" + GATE
PLUGIN_SCRIPTS = ("`<plugin scripts>` is the plugin's own `scripts` directory as a literal absolute path, even in a "
                  "repository that has `.prd-toolkit/`: `--list-packs` lists what is on this machine and is not a gate, "
                  "and a vendored copy lists only the packs it vendored")
JUDGE = "uv run --script .prd-toolkit/prd_judge.py <prd dir> <T-id> <output file>"
REFUSAL = "retargeting an area is a conversion, which a later prd-toolkit release brings"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.count(f"\n{heading}\n") == 1, heading
    a = text.index(f"\n{heading}\n") + 1
    level = heading.split(" ", 1)[0]
    b = text.find(f"\n{level} ", a + 1)
    return " ".join(text[a:b if b > 0 else len(text)].split())


def phase_row(n: int) -> str:
    """The cell text of authoring's phase table row n."""
    for line in AUTHORING.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {n} | "):
            return line
    raise AssertionError(f"no phase {n} row")


# ---------------------------------------------------------------- authoring-prds (D1, D2)

def test_authoring_phase_1_lists_packs_as_one_bash_call():
    row = phase_row(1)
    assert f"`{LIST_PACKS}`" in row and "its own Bash call" in row
    assert PLUGIN_SCRIPTS in row
    assert "`<name> <version> (<source>) — <description>`" in row


PROFILE = "`- Profile: [ASSUMPTION A-nn: <pack>, language <code>, output language <code>; <basis>]`"
OUTPUT_RULE = "`- Output language: <code>` only when the outputs' language differs from `language:`"


def test_authoring_phase_1_proposes_the_profile_as_one_assumption():
    row = " ".join(phase_row(1).split())
    for s in ("the default pack", "`language:`", "the output language", PROFILE, "indexed `open` in §12",
              "`- Pack: <name> <X.Y.Z> (<source>)`", OUTPUT_RULE, "phase 4 decides it like any assumption"):
        assert s in row, s
    assert "as `proposed` rows" not in row  # R27.2: one mechanism, the assumption


def test_authoring_profile_lines_use_the_same_mechanism():
    s = section(AUTHORING, "### Applying the pack")
    assert PROFILE in s and OUTPUT_RULE in s and "indexed `open` in §12" in s


def test_authoring_phase_2_applies_the_pack():
    s = section(AUTHORING, "### Applying the pack")
    for needle in ("after copying the template",
                   "drop each contract the pack does not use",  # 1: Not applicable lines
                   "``- Not applicable: `<file>` — <reason>``",
                   "add each of the pack's contract types to §7 with the Validator cell `pack`",  # 2
                   "and write its files",
                   "fill the Levels rows and the Harness slots from the pack's `levels` and `harness`",  # 3
                   "write every prose line in the PRD's `language:`",  # 4
                   "`Cuando`", "`deberá`"):
        assert needle in s, needle
    assert "Applying the pack" in phase_row(2)


def test_authoring_pack_types_are_never_custom_types():
    s = flat(AUTHORING)
    assert "Never declare a custom contract type, or write a validator, for an output a listed pack covers" in s


def test_authoring_phase_3_asks_the_packs_clarify_questions():
    row = phase_row(3)
    assert "the pack's `clarify.md`" in row and "category 1 asks the target profile" in row


def test_authoring_judged_case_follows_rubrics_md():
    s = section(AUTHORING, "### Applying the pack")
    assert "the pack's `rubrics.md`" in s and "`rubric:`" in s and "`threshold:`" in s and "no `output:`" in s


def test_authoring_rubric_wrong_vs_correct_pair():
    t = AUTHORING.read_text(encoding="utf-8")
    pair = t[t.index("WRONG  (test-cases/guide.yaml"):]
    pair = pair[:pair.index("```")]
    wrong, correct = pair.split("CORRECT", 1)
    assert "- The guide is clear" in wrong and "- Install reads well" in wrong
    assert "- Each step in Install names one action the reader performs" in correct
    assert "is clear" not in correct and "reads well" not in correct


def test_authoring_red_flags_for_rubrics_and_packs():
    s = section(AUTHORING, "## Red Flags - STOP")
    assert "A rubric item no quote can prove" in s
    assert "A custom contract type and a hand-written validator for a document" in s
    assert f"`--list-packs`" in s


def test_authoring_dry_run_may_sample_judged_tids():
    row = " ".join(phase_row(6).split())
    assert "A judged T-id is not unit and may be sampled" in row
    assert "never a score" in row


# ---------------------------------------------------------------- adopting-prds

def test_adopting_proposes_a_pack_from_the_boundary():
    s = flat(ADOPTING)
    assert "propose a pack from the area's Boundary files" in s
    assert f"`{LIST_PACKS}`" in s and PLUGIN_SCRIPTS in s
    assert "write the area's `Target:` line on the user's confirmation" in s
    assert "`Target: pack <name> <X.Y.Z> (<source>)[, output language <code>]`" in s


# ---------------------------------------------------------------- the tester (D3)

def test_tester_skill_judged_case_calls_prd_judge_with_three_positionals():
    s = section(TESTING, "## A judged case")
    assert f"`{JUDGE}`" in s
    assert "all three positionals" in s and "asserts exit 0 and nothing else" in s
    assert '"docs/prd/greet", "T-010.2", "docs/guide/install.md"' in s  # the worked call
    assert "You never grade the output yourself" in s
    assert "is not a QUESTION" in s  # the call is the toolkit's; testing.md need not spell it out


def test_tester_skill_red_flag_for_grading():
    s = section(TESTING, "## Red Flags - STOP")
    assert "I checked the guide myself" in s
    assert "A `prd_judge.py` call with no output file" in s
    assert "The guide may not pass" in s  # the caller's verdict, observed in an eval run with the skill unfired


def test_tester_skill_dry_run_judges_writability_never_a_score():
    s = section(TESTING, "## A judged case")
    assert "A dry run may sample a judged T-id: it is not `unit`" in s
    assert "whether the test could be written from the PRD alone, never a score" in s


def test_dispatching_names_the_judged_call_and_never_a_score():
    s = flat(DISPATCHING)
    assert f"`{JUDGE}`" in s
    assert "whether the test could be written from the PRD alone, never a score" in s
    assert "A judged test that grades the output itself" in s


def test_tester_agent_fallback_names_the_judged_call():
    s = flat(TESTER)
    assert f"`{JUDGE}`" in s and "assert exit 0" in s and "never grade the output yourself" in s


# ---------------------------------------------------------------- the builder (D4, R-1)

def test_builder_skill_states_the_builder_tests_none_exception():
    s = section(BUILDING, "## An area whose pack says `builder-tests: none`")
    for needle in ("`.prd-toolkit/packs/<name>/`",
                   "write each output its contracts name",
                   "each `outline` entry's `path`",
                   "`audience`, `purpose`, `sections`, `terms` and `length`",
                   "and the area's judged rubric items as the content brief",
                   "run the §5 standards linters that apply",
                   "in place of writing unit tests first",
                   "Prose you can write from the outline is not a PRD gap",
                   "A real gap is one the outline and the rubric do not answer",
                   "never the PRD folder, never a tester's test",
                   "never the pack's `checks` level"):
        assert needle in s, needle


def test_builder_rule_2_points_at_the_exception():
    assert ("2. **Write the unit tests first**, except on an area whose pack says `builder-tests: none`"
            in BUILDING.read_text(encoding="utf-8"))


def test_builder_red_flags_for_the_exception():
    s = section(BUILDING, "## Red Flags - STOP")
    assert "The exception on an area whose pack says `unit`" in s
    assert "the PRD sets the guide's structure but not what goes in it" in s


def test_running_a_build_dispatches_the_builder_for_a_document_area():
    s = flat(RUNNING)
    assert "an area whose pack says `builder-tests: none`" in s
    assert "`Unit T-ids: none`" in s and "dispatch the builder all the same" in s
    assert "\"write the unit tests first\" adds no unit T-id" in s
    assert "dismissed by an exact quote of the outline entry or the rubric item" in s


def test_builder_agent_fallback_states_the_exception():
    s = flat(BUILDER)
    assert "`builder-tests: none`" in s and "each `outline` entry's `path`" in s
    assert "run the §5 standards linters that apply" in s and "not a PRD gap" in s


# ---------------------------------------------------------------- changing-prds (D5)

def test_changing_lists_packs_before_calling_one_missing():
    s = section(CHANGING, "## Packs and retargeting")
    assert f"`{LIST_PACKS}`" in s and "its own Bash call" in s and PLUGIN_SCRIPTS in s
    assert "Before you say a pack is missing" in s
    assert "So does a pack vendored in `.prd-toolkit/packs/<name>/` (its `pack.yaml`), which lint reads before any other copy." in s


def test_changing_refuses_a_retarget_verbatim():
    s = section(CHANGING, "## Packs and retargeting")
    assert f"`{REFUSAL}`" in s
    assert "`built`, `verified` or `live`" in s
    assert "no `/prd-change`, no version bump, no edit and no plan to move a status back" in s
    assert "An output-language change, or a pack change on an area with no `built`, `verified` or `live` block" in s


def test_changing_description_routes_a_pack_switch():
    head = CHANGING.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    assert "switching an area or the PRD to another pack or output language (its Target: or Pack: line)" in head


def test_changing_red_flag_for_a_planned_retarget():
    s = section(CHANGING, "## Red Flags - STOP")
    assert "That would make this a major bump" in s and "I can't find a pack called" in s


# ---------------------------------------------------------------- handling-errors

def test_handling_errors_maps_judge_exit_2_to_environment():
    s = flat(ERRORS)
    assert "A `prd_judge.py` exit 2" in s and "is proposed as `environment`" in s


# ---------------------------------------------------------------- R26: --list-packs has its own exit tag

def test_no_list_packs_command_echoes_the_lint_tag():
    files = sorted(SKILLS.glob("*/*.md")) + sorted((ROOT / "agents").glob("*.md"))
    lines = [(p.name, line) for p in files for line in p.read_text(encoding="utf-8").splitlines() if "--list-packs;" in line]
    assert lines, "no --list-packs command found"
    for name, line in lines:
        assert 'echo "prd-list-packs-exit=$?"' in line and "prd-lint-exit" not in line, (name, line)


def test_list_packs_never_runs_the_vendored_copy():
    """Final review 1a: the vendored prd_lint.py lists only .prd-toolkit/packs/, so `document` goes missing there."""
    files = sorted(SKILLS.glob("*/*.md")) + sorted((ROOT / "agents").glob("*.md"))
    lines = [(p.name, line) for p in files for line in p.read_text(encoding="utf-8").splitlines() if "--list-packs;" in line]
    for name, line in lines:
        assert "<plugin scripts>/prd_lint.py --list-packs" in line, (name, line)
        assert ".prd-toolkit/prd_lint.py --list-packs" not in line and "<scripts>/prd_lint.py --list-packs" not in line, (name, line)


def test_builder_finds_the_manifest_in_the_three_places():
    for path in (BUILDING, BUILDER, RUNNING):
        s = flat(path)
        assert "`.prd-toolkit/packs/<name>/`" in s and "the toolkit's `packs/<name>/`" in s, path.name
        assert "`<installPath>/prd-packs/<name>/`" in s, path.name
        assert "that `--list-packs` resolves" not in s, path.name  # --list-packs prints no path (R27.1)


def test_tester_example_runs_the_judge_from_the_repository_root():
    s = section(TESTING, "## A judged case")
    assert "cwd=ROOT" in s and 'ROOT = Path(__file__).resolve().parents[2]' in s


# ---------------------------------------------------------------- R20: no plugin-root variable in a command

def _commands(text: str) -> list[str]:
    blocks = re.findall(r"```(?:bash)?\n(.*?)```", text, re.S)
    spans = re.findall(r"`((?:uv run|git|rm|ls|mkdir|find|diff|python3?) [^`]*)`", text)
    return [b for b in blocks] + spans


def test_no_plugin_root_variable_inside_a_command():
    files = sorted(SKILLS.glob("*/*.md")) + sorted((ROOT / "agents").glob("*.md"))
    found = [(p.name, c) for p in files for c in _commands(p.read_text(encoding="utf-8")) if "CLAUDE_PLUGIN_ROOT" in c]
    assert found == []
    # the new commands are among those checked
    every = " ".join(c for p in files for c in _commands(p.read_text(encoding="utf-8")))
    assert LIST_PACKS in every and JUDGE in every
