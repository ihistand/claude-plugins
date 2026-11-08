"""0.8.4 skill text: the skills stage both READMEs, offer §2's two parts and publish three tabs; the tester never
draws on a README (spec §5, §6, §7, §8, §12); and the skill halves of §16's fixes 1 and 3."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
AUTHORING = ROOT / "skills/authoring-prds/SKILL.md"
ADOPTING = ROOT / "skills/adopting-prds/SKILL.md"
CHANGING = ROOT / "skills/changing-prds/SKILL.md"
CHANGE_SET = ROOT / "skills/coordinating-prds/running-a-change-set.md"
TESTING = ROOT / "skills/testing-from-prds/SKILL.md"
AGENT = ROOT / "agents/prd-tester.md"
PUBLISHING = ROOT / "skills/publishing-prds/SKILL.md"
RUN = ROOT / "skills/building-from-prds/running-a-build.md"
BUILDING = ROOT / "skills/building-from-prds/SKILL.md"
EVAL = ROOT / "evals/tester-ignores-readme"
EDITED = (AUTHORING, ADOPTING, CHANGING, CHANGE_SET, TESTING, AGENT, PUBLISHING, RUN, BUILDING)

PARENT = "`docs/prd/README.md` when it exists"
README_RULE = ("The PRD folder's root `README.md` is a guide generated from the PRD, never a source for a test "
               "or a question.")


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a)]


# --- spec §6: each skill that commits after prd_block.py stages both READMEs ---

def _phase(n: int) -> str:
    line = [ln for ln in AUTHORING.read_text(encoding="utf-8").splitlines() if ln.startswith(f"| {n} |")][0]
    return " ".join(line.split())


def test_authoring_approval_stages_the_parent_readme():
    seven = _phase(7)
    assert "writes the CLAUDE.md block and both READMEs" in seven
    assert "commit the folder, " + PARENT + ", and CLAUDE.md with `Refs: none (no behaviour change)`" in seven


def test_adopting_step_5_commit_stages_the_parent_readme():
    four = between(flat(ADOPTING), "4. **Approval.**", "5. **Hooks and CI.**")
    commit = four.split("Then commit the PRD folder", 1)[1]
    assert PARENT in commit and "CLAUDE.md together" in commit


def test_changing_step_5_names_the_parent_readme_on_both_routes():
    step5 = between(flat(CHANGING), "5. **Approval, then commit.**", "## Red Flags")
    approve = between(step5, "`approve` does all three", "**Inside a change set**")
    assert "stages " + PARENT in approve
    inside = between(step5, "**Inside a change set**", "Only now may code change")
    assert PARENT in inside


def test_change_set_member_commit_stages_the_parent_readme():
    three = flat(CHANGE_SET).split("in Order each member's approval commit", 1)[1].split("4. **Build in order.**", 1)[0]
    assert "the commit of the PRD folder, " + PARENT + " and CLAUDE.md" in three


# --- spec §5: the tester never draws on the README ---

def test_the_readme_rule_is_in_the_skill_and_the_agent():
    rules = between(flat(TESTING), "## Non-negotiable rules", "## Citations")
    assert README_RULE in rules
    fallback = between(flat(AGENT), "keep to these rules:", "The prompt gives the mode")
    assert README_RULE in fallback


# --- spec §7: §2's two parts are offered, never required ---

def test_authoring_phase_2_offers_both_parts_and_requires_neither():
    detail = between(flat(AUTHORING), "### Phase 2 in detail", "### Applying the pack")
    part = between(detail, "**§2's two optional parts:**", "- **")
    for s in ("`Principles:`", "`Getting started:`", "from what the user has said", "Neither is required",
              "`Principios:`", "`Primeros pasos:`"):
        assert s in part, s
    assert "NEEDS CLARIFICATION" in part  # named only to say neither part takes one


def test_adoption_bootstrap_offers_both_parts_and_requires_neither():
    boot = between(flat(ADOPTING), "### 0. Bootstrap", "### 1. Bound")
    part = between(boot, "**§2's two optional parts:**", "- **")
    for s in ("`Principles:`", "`Getting started:`", "from what the user has said", "Neither is required",
              "authoring phase 2"):
        assert s in part, s


# --- no ${CLAUDE_PLUGIN_ROOT} inside a Bash command in any file this task edits ---

def test_no_plugin_root_inside_a_bash_command():
    for p in EDITED:
        text = p.read_text(encoding="utf-8")
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            assert "${CLAUDE_PLUGIN_ROOT}" not in block, p.name
        for span in re.findall(r"`([^`\n]+)`", text):
            if span.split(" ", 1)[0] in ("uv", "grep", "git", "python3", "bash", "ls", "mkdir"):
                assert "${CLAUDE_PLUGIN_ROOT}" not in span, (p.name, span)


# --- §16 fix 1: a regression marker comes off with its symptom ---

SYMPTOM = "and its `symptom:` line when it has one, and no other test-case line"


def test_fix1_both_removals_take_the_symptom_line_too():
    r = flat(RUN)
    four = between(r, "**`--fixes E-nnn` only: the deploy-gate lines.**", "5. **Run.**")
    assert "whose test case is at a deploy-gate level, " + SYMPTOM in four
    five = between(r, "**`--fixes E-nnn` only: the build-gate and unit lines.**", "6. **Reconcile**")
    assert "a unit T-id on the builder's UNIT lines), " + SYMPTOM in five


def test_fix1_callers_red_flag_says_the_same():
    flags = between(flat(BUILDING), "## Red Flags - STOP", "## Common Rationalizations")
    bullet = between(flags, "I didn't add a known-failing marker", "Resolving the entry after a `--fixes` build")
    assert "each with its case's `symptom:` line when it has one, and no other test-case line" in bullet
    assert "symptom: needs known-failing: on the same case" in bullet  # the lint failure a lone removal causes


# --- §16 fix 3: search with the Grep tool, or a checked Bash grep naming each path ---

def _rule6() -> str:
    rules = between(flat(TESTING), "## Non-negotiable rules", "## Citations")
    return between(rules, " 6. ", " 7. **")


def _agent_search() -> str:
    """The fallback list's search bullet, flattened."""
    raw = AGENT.read_text(encoding="utf-8").split("\nThe prompt gives the mode", 1)[0]
    bullet = [b for b in raw.split("\n- ") if b.startswith("Search the PRD folder")]
    assert len(bullet) == 1
    return " ".join(bullet[0].split())


OLD_RULE = "never with Bash `cat`, `grep`, `head`, `sed` or `find`"


def test_fix3_rule_6_and_the_agent_allow_a_checked_grep():
    for text in (_rule6(), _agent_search()):
        assert OLD_RULE not in text
        for s in ("with the Grep tool", "when there is none, with Bash `grep` naming each path",
                  "Never Bash `cat`, `head`, `sed` or `find`", "ugrep", "--include='*.py'", "`-R`"):
            assert s in text, s
    assert OLD_RULE not in flat(TESTING) and OLD_RULE not in flat(AGENT)


def test_fix3_rule_6_lists_the_guards_options():
    six = _rule6()
    for s in ("`-r -n -l -L -c -i -w -x -v -o -q -s -H -h -E -F`", "`-e <pattern>`", "`-f <file>`",
              "`-m`, `-A`, `-B` or `-C <n>`", "`--include=<glob>`", "`--exclude=<glob>`",
              "every option before the pattern (the first operand)", "in a write or a suite"):
        assert s in six, s
    assert "every option before the first path" not in flat(TESTING)


# --- the eval: the tester, given a README that states a behaviour no feature file states, never draws on it ---

def test_the_eval_exists_with_its_graders():
    for f in ("case.yaml", "scaffold.sh", "prompt.md"):
        assert (EVAL / f).is_file(), f
    assert yaml.safe_load((EVAL / "case.yaml").read_text(encoding="utf-8"))["name"] == "tester-ignores-readme"
    assert {p.stem for p in (EVAL / "graders").glob("*.md")} == {
        "tester-dispatched", "test-written", "no-write-from-readme", "no-edit-from-readme", "report-never-cites-readme"}
    scaffold = (EVAL / "scaffold.sh").read_text(encoding="utf-8")
    assert 'scaffolds/deploy_repo.py" "$PWD" ready' in scaffold and "Bonjour" in scaffold
    prompt = (EVAL / "prompt.md").read_text(encoding="utf-8")
    assert "Mode: write" in prompt and "T-002.1" in prompt and "T-002.2" in prompt
    assert "README" not in prompt and "French" not in prompt
    assert "| `tester-ignores-readme`" in (ROOT / "evals/BASELINE.md").read_text(encoding="utf-8")


# --- fix round 1: the run lists name the checked grep; options come before the pattern ---

def test_fix3_every_run_list_names_the_checked_grep():
    t = flat(TESTING)
    overview = between(t, "## Overview", "## The three modes")
    assert "`uv run python -m py_compile` or a checked `grep` (rule 6) on allowed paths" in overview
    rules = between(t, "## Non-negotiable rules", "## Citations")
    five = between(rules, " 5. **", " 6. **")
    assert "you run only `ls`, `mkdir`, `uv run python -m py_compile` and a checked `grep` (rule 6)" in five
    a = flat(AGENT)
    assert "`uv run python -m py_compile` and a checked `grep` only" in a


def test_fix3_agent_options_before_the_pattern_and_glob_wording():
    a = _agent_search()
    assert "every option before the pattern (the first operand)" in a
    assert "every option before the first path" not in flat(AGENT)
    assert "an unquoted glob in a pattern or a path is refused" in a
    assert "zsh stops on one that matches no file" in a
