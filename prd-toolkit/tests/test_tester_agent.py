"""The prd-tester agent, the testing-from-prds skill and the skills that dispatch it."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENT = ROOT / "agents/prd-tester.md"
SKILL = ROOT / "skills/testing-from-prds/SKILL.md"
DISPATCHERS = [ROOT / f"skills/{n}/SKILL.md" for n in ("authoring-prds", "changing-prds")]
SKILL_DESCRIPTION = (
    "Use when writing or running tests from a PRD folder (docs/prd/) without reading the code - a dry run of "
    "sampled T-ids, a characterization suite for an adopted area, or the tests for new or changed T-ids; or "
    "when dispatched as prd-tester"
)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def test_agent_tools_are_exactly_the_guarded_file_and_bash_tools():
    fm = frontmatter(AGENT)
    assert fm["name"] == "prd-tester"
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert tools == ["Read", "Glob", "Grep", "Write", "Edit", "Bash"]
    # every tool the agent has is one the guard's matcher covers; an unguarded tool would escape it
    hooks = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    matcher = set(hooks["hooks"]["PreToolUse"][0]["matcher"].split("|"))
    assert set(tools) <= matcher


def test_agent_preloads_the_skill_and_names_both_modes():
    fm = frontmatter(AGENT)
    assert fm["skills"] == "prd-toolkit:testing-from-prds"
    assert "dry run" in fm["description"] and "suite" in fm["description"]


def test_skill_frontmatter_is_pinned():
    fm = frontmatter(SKILL)
    assert fm == {"name": "testing-from-prds", "description": SKILL_DESCRIPTION}


def test_skill_keeps_the_report_format_and_results_values():
    text = SKILL.read_text(encoding="utf-8")
    for heading in ("QUESTIONS", "TESTS", "HARNESS CHOICES", "FILES READ", "RESULTS"):
        assert heading in text
    for value in ("`<T-id>: pass`", "`<T-id>: fail: <one line>`", "`<T-id>: known-failing E-nnn`"):
        assert value in text


def test_skill_states_the_harness_command_shape_in_both_places():
    for path in (SKILL, ROOT / "references/prd-format.md"):
        text = path.read_text(encoding="utf-8")
        assert "one simple command" in text, path
        for word in ("`cd`", "`env`", "`sh`", "`bash`", "`zsh`", "`eval`", "`exec`", "`&&`"):
            assert word in text, (path, word)


def test_dispatching_reference_has_the_caller_integrity_check():
    text = (ROOT / "skills/testing-from-prds/dispatching.md").read_text(encoding="utf-8")
    assert "git status --porcelain" in text and "git write-tree" in text
    assert "restore nothing" in text.lower()


def test_dispatching_skills_use_the_agent():
    for path in DISPATCHERS:
        assert "prd-toolkit:prd-tester" in path.read_text(encoding="utf-8"), path


def test_dry_run_prompt_says_it_is_the_fallback():
    head = (ROOT / "skills/authoring-prds/dry-run-prompt.md").read_text(encoding="utf-8").split("```")[0]
    assert "fallback" in head.lower() and "prd-tester" in head


DISPATCHING = ROOT / "skills/testing-from-prds/dispatching.md"


def test_dispatching_reference_pins_the_dry_run_directory_and_its_cleanup():
    text = DISPATCHING.read_text(encoding="utf-8")
    assert "<first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/" in text
    assert "scratchpad>/prd-dry-run" not in text  # one dry-run location, interactive or headless
    steps = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    last_no, last_title = steps[-1]
    assert last_title.lower().startswith("delete the run's directory")
    cleanup = text.split(f"{last_no}. **{last_title}**", 1)[1]
    assert "pass or fail" in cleanup and "integrity check failed" in cleanup
    assert "stale `.prd-dry-run-*`" in text  # removed before the dispatch
    assert "exempts only the run's own `.prd-dry-run-<YYYYMMDDTHHMMSS>/`" in text
    assert "no harness command runs during a dry run" in text


def test_skill_points_callers_at_the_dispatching_reference():
    text = SKILL.read_text(encoding="utf-8")
    assert "## When you dispatch prd-tester" not in text
    assert "dispatching.md" in text


def test_dispatchers_use_the_fallback_only_when_prd_tester_is_unavailable():
    for path in DISPATCHERS + [ROOT / "skills/authoring-prds/dry-run-prompt.md"]:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "testing-from-prds/dispatching.md" in text, path
    for path in DISPATCHERS:
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "Only when `prd-tester` is not in the Agent tool's list" in text, path
        # the fallback sentence follows that condition, in the same sentence
        cond = text.index("Only when `prd-tester` is not in the Agent tool's list")
        span = text[cond:text.index("dry-run-prompt.md", cond)]
        assert ". " not in span and "general-purpose" in span, path
        assert "delete" in text.lower() and "cleanup" in text.lower(), path


def test_rule_one_depends_on_the_mode_in_skill_and_agent():
    for path in (SKILL, AGENT):
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "In a dry run, read only the PRD folder and your own dry-run directory" in text, path
        assert "do not list or read the test roots" in text, path
        assert "In a suite, you may also read the helpers testing.md names and the test files that cite one of your T-ids" in text, path


def test_suite_results_lines_have_exactly_three_forms():
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    assert "one line per dispatched T-id" in text
    assert "`<T-id>: pass`, `<T-id>: fail: <one line>` or `<T-id>: known-failing E-nnn`" in text
    assert "Anything else goes in a note after the lines" in text


def test_prd_format_lists_the_same_blocked_chains_as_the_skill():
    for path in (SKILL, ROOT / "references/prd-format.md"):
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "`&&`, `||`, `;` or `|`" in text, path


def test_authoring_phase_six_states_what_the_guard_enforces():
    text = (ROOT / "skills/authoring-prds/SKILL.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| 6 |"))
    assert "reads only the PRD folder" not in row
    assert "reads in the PRD folder, the dry-run directory and the test roots" in row
    assert "writes only to the test roots and the scratch directory" in row


# --- the guard, replayed with the hook input keys logged live from a prd-tester subagent ---

GUARD = ROOT / "scripts/prd_tester_guard.py"


def live_envelope(repo: Path, tool: str, tool_input: dict) -> str:
    """The key set a `claude -p` subagent's PreToolUse input carried live: no scratchpad_dir."""
    return json.dumps({
        "agent_id": "a7818a8c4680beba5", "agent_type": "prd-toolkit:prd-tester", "cwd": str(repo),
        "effort": "medium", "hook_event_name": "PreToolUse", "permission_mode": "acceptEdits",
        "prompt_id": "p", "session_id": "s", "tool_input": tool_input, "tool_name": tool,
        "tool_use_id": "toolu_x", "transcript_path": str(repo.parent / "t.jsonl"),
    })


def notes_repo(tmp_path: Path) -> Path:
    from legacy import make_legacy_repo
    repo = make_legacy_repo(tmp_path / "legacy")
    prd = repo / "docs/prd/notes"
    prd.mkdir(parents=True)
    (prd / "prd.md").write_text("# notes\n", encoding="utf-8")
    (prd / "testing.md").write_text(
        "# Testing\n\n## Levels\n\n| Level | Harness command | Environment |\n|---|---|---|\n"
        "| integration | `uv run pytest tests` | local |\n\n## Harness\n\n"
        "- **Layout.** `tests/test_<area>.py`. Test roots: `tests/`.\n", encoding="utf-8")
    return repo


def guard(stdin: str):
    import subprocess
    import sys
    return subprocess.run([sys.executable, str(GUARD)], input=stdin, capture_output=True, text=True)


def test_live_envelope_read_of_src_is_blocked(tmp_path):
    repo = notes_repo(tmp_path)
    r = guard(live_envelope(repo, "Read", {"file_path": str(repo / "src/notes/app.py")}))
    assert r.returncode == 2, r.stderr
    assert r.stderr.startswith("prd-tester may only read under: "), r.stderr


def test_live_envelope_write_into_the_dry_run_directory_is_allowed(tmp_path):
    repo = notes_repo(tmp_path)
    target = repo / "tests/.prd-dry-run-x/t.py"
    r = guard(live_envelope(repo, "Write", {"file_path": str(target), "content": "x = 1\n"}))
    assert r.returncode == 0, r.stderr
    r = guard(live_envelope(repo, "Bash", {"command": f"mkdir -p {target.parent}"}))
    assert r.returncode == 0, r.stderr


def test_every_written_test_cites_its_t_id_in_skill_and_agent():
    # prd_trace.py counts `@prd <T-id>` citations, so an uncited test leaves its T-id untested
    for path in (SKILL, AGENT):
        text = " ".join(path.read_text(encoding="utf-8").split())
        assert "Every test you write carries an `@prd <T-id>` citation for the T-id it covers" in text, path


def test_dispatching_commands_are_one_simple_command_with_literal_paths():
    """Headless don't-ask mode has denied an `rm` compound and a computed path; one denial can end the run."""
    text = DISPATCHING.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    assert blocks, "no bash command blocks"
    for block in blocks:
        for line in block.splitlines():
            for bad in ("$(", "&&", "||", " | ", ";", "${", "$S", "<("):
                assert bad not in line, (bad, line)
            assert not re.search(r"\s<\s", line), ("stdin redirect", line)
    flat = " ".join(text.split())
    assert "One command per Bash call" in flat and "literal" in flat
    assert "mktemp -d" in flat and "git diff --name-only <tree-before SHA> <tree-after SHA>" in flat
    assert "rm -rf <first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/" in flat


def test_adopting_points_at_the_one_command_rule():
    text = " ".join((ROOT / "skills/adopting-prds/SKILL.md").read_text(encoding="utf-8").split())
    four = text.split("### 4. Characterize", 1)[1].split("### 5.", 1)[0]
    gates = text.split("1. **Gates.**", 1)[1].split("2. **The adoption-map row.**", 1)[0]
    for part in (four, gates):
        assert "one command per bash call" in part.lower(), part[:80]


# --- final fix wave ---

def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_skill_sends_a_caller_to_dispatch_the_agent_first():
    """Loaded in the caller's own session, the skill runs unguarded: its first Overview line says dispatch."""
    text = SKILL.read_text(encoding="utf-8")
    overview = text.split("## Overview\n", 1)[1].lstrip("\n")
    first = overview.split("\n\n", 1)[0]
    assert " ".join(first.split()) == (
        "If you are not running as the `prd-toolkit:prd-tester` agent, do not write these tests yourself: "
        "dispatch it as `dispatching.md` says.")


def test_glob_and_grep_always_get_a_path():
    for path in (SKILL, AGENT):
        assert "Always give Glob and Grep a `path` inside the PRD folder or your directory." in _flat(path), path


def test_tester_asserts_the_prds_recorded_closed_window_values():
    rule2 = _flat(SKILL).split("2. **Every expected value comes from the PRD.**", 1)[1].split("3. **", 1)[0]
    assert "closed window" in rule2 and "they are the PRD's values" in rule2


def test_dispatching_one_command_rule_names_the_observed_failure_and_the_gate_form():
    text = _flat(DISPATCHING)
    rule = text.split("**One command per Bash call, with literal paths.**", 1)[1].split("1. **", 1)[0]
    assert "a compound with `rm`" in rule and "a path built from a variable or `$(…)`" in rule
    assert '`; echo "prd-lint-exit=$?"`' in rule and "observed to run" in rule


def test_dispatching_names_the_pytest_caches():
    text = _flat(DISPATCHING)
    assert "`.pytest_cache/`" in text and "`__pycache__/`" in text and "`-p no:cacheprovider`" in text
    assert "git-ignored" in text


def test_dispatching_says_how_to_dispatch_and_what_the_check_misses():
    text = _flat(DISPATCHING)
    step3 = text.split("3. **Dispatch**", 1)[1].split("4. **", 1)[0]
    assert "Dispatch with the Agent tool; under `claude --agent` the `skills:` preload does not load." in step3
    assert ("An edit to a file that was already in the PRD folder and is git-ignored is not caught; PRD files "
            "are tracked by design.") in text


def test_dispatching_suite_tids_are_every_non_unit_case():
    text = _flat(DISPATCHING)
    assert ("A suite's T-id list is every non-unit T-id in `test-cases/<area>.yaml`, which the caller reads; "
            "`--sample-tids` is for dry runs only.") in text


def test_dispatching_covers_a_remote_harness():
    text = _flat(DISPATCHING)
    para = text.split("**A remote harness.**", 1)[1].split("1. **", 1)[0]
    for phrase in ("only sees committed code", "the tester writes the tests in `Mode: suite`",
                   "The caller, never the tester, publishes them", "never a deploy",
                   "asks the user first", "fresh snapshot", "re-dispatches `Mode: suite`",
                   "MCP tools are never in prd-tester's tools", "Bash harness command"):
        assert phrase in para, phrase


RULE_TOOLS = (
    "Read and search the PRD folder and your own directory with the Read, Glob and Grep tools, "
    "never with Bash `cat`, `grep`, `head`, `sed` or `find`; the guard blocks those."
)


def test_rule_reads_with_the_tools_not_bash_in_skill_and_agent():
    # the guard allows only harness commands, ls, mkdir and py_compile through Bash
    skill_rules = _flat(SKILL).split("## Non-negotiable rules", 1)[1].split("## Citations", 1)[0]
    agent_rules = _flat(AGENT).split("keep to these rules:", 1)[1].split("The prompt gives the mode", 1)[0]
    assert RULE_TOOLS in skill_rules
    assert RULE_TOOLS in agent_rules
