"""Pins from the 0.4 final review: R38's hooks-and-CI instructions and the text minors 11-13."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILLS = ROOT / "skills"
BUILD_SKILL = SKILLS / "building-from-prds/SKILL.md"
RUN = SKILLS / "building-from-prds/running-a-build.md"
AUTHORING = SKILLS / "authoring-prds/SKILL.md"
ADOPTING = SKILLS / "adopting-prds/SKILL.md"
README = ROOT / "README.md"

PLUGIN_PATH = "~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts"  # R22: a shell does not set CLAUDE_PLUGIN_ROOT
INSTALL = f"uv run --script {PLUGIN_PATH}/prd_hooks.py install docs/prd/<slug>"  # the README: no Bash tool there
CI = f"uv run --script {PLUGIN_PATH}/prd_hooks.py ci --github docs/prd/<slug>"
SKILL_INSTALL = "uv run --script <scripts>/prd_hooks.py install docs/prd/<slug>"  # skills: R21


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a)]


# --- R38 (a): the README's Hooks and CI section ---

def test_readme_hooks_and_ci_section():
    t = README.read_text(encoding="utf-8")
    s = " ".join(between(t, "## Hooks and CI", "\n## ", ).split()) if t.count("## Hooks and CI") == 1 else ""
    assert s, "README needs one '## Hooks and CI' section"
    assert INSTALL in s and "commit `.prd-toolkit/`" in s
    assert "uv run --script .prd-toolkit/prd_hooks.py install docs/prd/<slug>" in s  # per clone
    assert "ci --github" in s and "ci --gitlab" in s and "include:" in s
    assert f"{PLUGIN_PATH}/prd_hooks.py check docs/prd/<slug>" in s and "After a plugin upgrade" in s
    assert "uninstall" in s
    assert "uv" in s and "bare runner" in s
    assert "known-failing" in s and "0.6" in s  # R37
    assert "commit --amend" in s and "commit-refs" in s  # minor 10


# --- R38 (c) and minor 13: authoring phase 7 and adopting step 5 offer, and ask the Gate ---

def test_authoring_phase_7_offers_hooks_and_ci_on_a_yes():
    row = flat(AUTHORING).split("| 7 | **Approval.**", 1)[1].split("| Explicit user approval |", 1)[0]
    assert "offer to install the hooks and generate CI" in row
    assert SKILL_INSTALL in row and "ci --github docs/prd/<slug>" in row and "--gitlab" in row
    assert "only on the user's explicit yes" in row


def test_adopting_step_5_offers_hooks_and_ci_on_a_yes():
    step = " ".join(between(ADOPTING.read_text(encoding="utf-8"), "### 5. Gate and approve", "## When the user pushes").split())
    assert "offer to install the hooks and generate CI" in step
    assert SKILL_INSTALL in step and "ci --github docs/prd/<slug>" in step and "--gitlab" in step
    assert "only on the user's explicit yes" in step


def test_levels_gate_is_asked_not_defaulted():
    for path in (AUTHORING, ADOPTING):
        t = flat(path)
        assert "ask the user which Gate (`build` or `deploy`) each level runs at" in t, path.name
        assert "never keep the template's Gate silently" in t, path.name


# --- minor 11: building text drift ---

def test_builder_is_not_you_after_the_caller_block():
    t = flat(BUILD_SKILL)
    assert "The builder (you)" not in t and "A build has three roles. The builder writes the code" in t


def test_verified_evidence_names_the_close_sources():
    t = flat(BUILD_SKILL)
    assert "the full run is the only evidence for `verified`" not in t
    assert ("the close's three sources are the only evidence for `verified`: the builder's UNIT lines, "
            "the tester's suite RESULTS and your own full run") in t


def test_third_round_sentence_appears_once():
    t = flat(RUN)
    assert t.count("After a third failed round on one T-id the build stops and reports it to the user.") == 1
    assert "The build stops when a T-id's third round fails." not in t


def test_no_orphan_dispute_line():
    assert not [line for line in RUN.read_text(encoding="utf-8").splitlines() if line.strip() == "dispute,"]


def test_one_turn_carve_out_and_dirty_tree_stop():
    t = flat(RUN)
    one = t.split("**One turn.**", 1)[1].split("1. **Preflight.**", 1)[0]
    assert "before step 2, the caller may stop to ask the user" in one
    stops = t.split("**Stops.**", 1)[1].split("Any stop after the builder's merge", 1)[0]
    assert "a dirty working tree in step 1" in stops


# --- minor 12: README, manifests, web, agent ---

def test_readme_build_command_row():
    t = README.read_text(encoding="utf-8")
    assert "| `/prd-build <area> <IDs>` |" in t and "/prd-build [IDs]" not in t


def test_description_has_no_double_and():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert "code, and skills to author" not in plugin["description"]
    assert "a test agent that cannot read your code, skills to author, adopt and change it, and a builder" in plugin["description"]


def test_web_testing_skill_names_write():
    js = (ROOT.parent / "web/src/data/plugins.js").read_text()
    m = re.search(r"name: 'testing-from-prds', description: '([^']*)'", js)
    assert m and "dry runs, writes and suites" in m.group(1)


def test_tester_agent_description_comma_before_write():
    t = (ROOT / "agents/prd-tester.md").read_text(encoding="utf-8")
    assert "and not run), a write (" in t and "and not run) a write" not in t


def test_levels_build_gate_never_collects_deploy_gate_paths():
    for path in (AUTHORING, ADOPTING):
        t = flat(path)
        assert ("A build-gate Harness command never collects a deploy-gate level's test path (`pytest tests` "
                "collects `tests/system`): give each level its own path. Lint reports an overlap (`test-level`).") in t, path.name
