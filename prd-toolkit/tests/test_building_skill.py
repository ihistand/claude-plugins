"""The building-from-prds skill, its caller procedure running-a-build.md, the prd-builder agent and /prd-build."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/building-from-prds/SKILL.md"
RUN = ROOT / "skills/building-from-prds/running-a-build.md"
AGENT = ROOT / "agents/prd-builder.md"
COMMAND = ROOT / "commands/prd-build.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


# --- the brief's pins ---

def test_frontmatter():
    t = SKILL.read_text(encoding="utf-8")
    assert t.startswith("---\nname: building-from-prds\ndescription: Use when ")
    a = AGENT.read_text(encoding="utf-8")
    assert "name: prd-builder" in a and "skills: prd-toolkit:building-from-prds" in a and "tools: Read, Glob, Grep, Write, Edit, Bash" in a


def test_builder_rules():
    t = SKILL.read_text(encoding="utf-8")
    for s in ["--for implement", "unit tests first", "never edit the PRD", "never edit a test that cites a non-unit T-id",
              "Refs:", "QUESTIONS", "SOURCES", "If you are not running as the `prd-toolkit:prd-builder` agent"]:
        assert s in t, s


def test_report_fields_in_order():
    t = SKILL.read_text(encoding="utf-8")
    at = [t.index(f) for f in ("CHANGES", "UNIT", "SOURCES", "QUESTIONS", "COMMIT")]
    assert at == sorted(at)


def test_procedure_steps():
    t = RUN.read_text(encoding="utf-8")
    for s in ["isolation: worktree", "Mode: write", "Mode: suite", "prd_build_check.py", "--diff", "--results",
              'echo "prd-build-check-exit=$?"', "three rounds", "no version bump, no §14 row"]:
        assert s in t, s


def test_reconcile_table_and_quote_rule():
    t = RUN.read_text(encoding="utf-8")
    assert "| code bug |" in t and "| test misread |" in t and "| PRD gap |" in t
    assert "A classification without its quote does not count." in t


def test_no_worktree_fallback():
    assert "When the Agent tool offers no worktree isolation, dispatch the builder first" in RUN.read_text(encoding="utf-8")


def test_command():
    t = COMMAND.read_text(encoding="utf-8")
    assert t.startswith("---\ndescription: ") and "running-a-build.md" in t


# --- frontmatter, shape and the hand-offs ---

def test_frontmatter_parses_and_triggers_on_implement_requests():
    fm = frontmatter(SKILL)
    assert set(fm) == {"name", "description"}
    d = fm["description"]
    for s in ("docs/prd/", "/prd-build", "prd-builder", "implement FR-"):
        assert s in d, s
    for path in (SKILL, AGENT, COMMAND):
        for value in frontmatter(path).values():
            assert ": " not in value and " #" not in value, (path, value)  # plain YAML scalars


def test_agent_frontmatter_is_exact_and_names_worktree():
    fm = frontmatter(AGENT)
    assert fm["name"] == "prd-builder"
    assert [t.strip() for t in fm["tools"].split(",")] == ["Read", "Glob", "Grep", "Write", "Edit", "Bash"]
    assert fm["skills"] == "prd-toolkit:building-from-prds"
    body = flat(AGENT)
    assert "If the skill's text is not in your context" in body
    for s in ("never edit the PRD", "never edit a test that cites a non-unit T-id", "Refs:", "unit tests first",
              "CHANGES, UNIT, SOURCES, QUESTIONS, COMMIT"):
        assert s in body, s


def test_skill_sends_a_caller_to_running_a_build_first():
    text = SKILL.read_text(encoding="utf-8")
    overview = text.split("## Overview\n", 1)[1].lstrip("\n")
    first = " ".join(overview.split("\n\n", 1)[0].split())
    assert first.startswith("If you are not running as the `prd-toolkit:prd-builder` agent")
    assert "running-a-build.md" in first


def test_skill_has_the_changing_prds_shape():
    text = SKILL.read_text(encoding="utf-8")
    heads = ["## Overview", "## Non-negotiable rules", "## The report", "## Red Flags - STOP",
             "## Common Rationalizations", "## Related skills"]
    at = [text.index(h) for h in heads]
    assert at == sorted(at)
    assert "Violating the letter of these rules is violating the spirit." in text


def test_builder_prompt_is_the_spec_prompt():
    t = RUN.read_text(encoding="utf-8")
    prompt = "Mode: build\nPRD: docs/prd/<slug>/\nArea: <area>\nIDs: <UJ, FR and NFR IDs>\nUnit T-ids: <one per line, with its test-case file>"
    assert prompt in t
    assert prompt in SKILL.read_text(encoding="utf-8")  # the builder sees the prompt it is given


def test_gate_forms_in_both_files():
    for path in (SKILL, RUN):
        t = path.read_text(encoding="utf-8")
        for line in t.splitlines():
            for script, gate in (("prd_context.py", "prd-context-exit"), ("prd_lint.py", "prd-lint-exit"),
                                 ("prd_trace.py", "prd-trace-exit"), ("prd_build_check.py", "prd-build-check-exit")):
                if f'"${{CLAUDE_PLUGIN_ROOT}}/scripts/{script}"' in line:
                    assert f'echo "{gate}=$?"' in line, (path.name, line)
    t = RUN.read_text(encoding="utf-8")
    assert '--diff <base>..<builder branch>; echo "prd-build-check-exit=$?"' in t
    assert '--results <SNAP>/suite-report.md --tids <T-id>,<T-id>; echo "prd-build-check-exit=$?"' in t


def test_procedure_commands_are_one_per_call_with_literal_paths():
    text = RUN.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    assert blocks, "no bash command blocks"
    for block in blocks:
        for line in block.splitlines():
            if not line.strip():
                continue
            head = line.split("; echo \"", 1)[0]  # the gate form is the one allowed `;`
            for bad in ("$(", "&&", "||", " | ", ";", "$S", "<("):
                assert bad not in head, (bad, line)
    flat_text = flat(RUN)
    assert "One command per Bash call, with literal paths." in flat_text


def test_procedure_has_the_eight_steps_in_order():
    text = RUN.read_text(encoding="utf-8")
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    names = [t.rstrip(".").lower() for _, t in titles]
    for want in ("preflight", "snapshot", "dispatch both in one message", "check the state", "run", "reconcile",
                 "full run", "close"):
        assert any(n.startswith(want) for n in names), (want, names)
    assert [int(n) for n, _ in titles] == list(range(1, len(titles) + 1))


def test_procedure_references_dispatching_steps_not_copies():
    t = flat(RUN)
    assert "dispatching.md` step 2" in t and "dispatching.md` step 4" in t
    assert "git write-tree" not in t  # referenced, not copied


def test_procedure_tester_rounds_and_misread_line():
    t = flat(RUN)
    assert 'Misread: <T-id>: "<verbatim quote of the test case\'s ac: line and the expect entry>"' in t
    assert "a `write` report that holds RESULTS fails the round" in t
    assert "Mode: write" in t and "Mode: suite" in t


def test_procedure_reconcile_record_and_stop():
    t = flat(RUN)
    assert "statuses stay as they are" in t and "/prd-change" in t
    assert "the builder may now read the failing test" in t
    assert "After three rounds on one T-id the build stops and reports it to the user." in t
    assert "A non-empty QUESTIONS stops the build" in t


def test_procedure_close_moves_block_and_index_row_together():
    t = flat(RUN)
    close = t.split("8. **Close", 1)[1]
    for s in ("`approved → built`", "`built → verified`", "§11", "the block and its §11 index row together",
              "Source: <path>:<line> @<short sha>", "no version bump, no §14 row, no re-approval",
              "the PRD status stays `Approved`", "Refs: <IDs>"):
        assert s in close, s
    assert "`live`" in close  # named as what the close never writes


# --- one pin per baseline failure (evals/baselines/building-from-prds.md "Failures to write against") ---

def test_failure_1_builder_writes_the_testers_tests():
    t = flat(SKILL)
    assert "A test in your diff for a T-id that is not on your `Unit T-ids:` list" in t
    assert "add the integration test (with the `@prd T-003.2` docstring) and rerun" in t  # the caller's version
    assert "| \"I'll write the integration test too, it's quicker.\" |" in t


def test_failure_2_behaviour_ahead_of_the_prd():
    t = flat(SKILL)
    assert "left untouched per \"PRD can follow\"; it now needs: AC-002.1 amended" in t
    assert "added an untagged test (no T-id yet, since the PRD doesn't cover accents)" in t
    assert "| \"It's tiny; the PRD can follow.\" |" in t


def test_failure_3_out_of_scope_fix_as_a_side_effect():
    t = flat(SKILL)
    assert "the same folding makes search case-insensitive, so T-002.1" in t
    assert "| \"While I'm there, I'll fix this too.\" |" in t


def test_failure_4_known_failing_read_as_a_fresh_defect():
    t = flat(SKILL)
    assert "The fix would be to compare lowercased text in `search_notes`; say if you want it." in t
    assert "route that separately to the builder" in t
    assert "`known-failing: E-nnn`" in t


def test_failure_5_verdict_by_paraphrase():
    t = flat(SKILL)
    assert "The test asserts exactly this" in t and "The test matches the PRD." in t
    assert "| \"The test obviously matches the AC; quoting it is ceremony.\" |" in t


def test_failure_6_coordinator_does_the_builders_work():
    t = flat(SKILL)
    assert "I went ahead and applied the fix myself." in t
    assert "| \"Routing a one-line fix is slower than making it.\" |" in t


def test_failure_7_second_guessing_the_testers_result():
    t = flat(SKILL)
    assert "The reported failure doesn't reproduce against the code" in t
    assert "| \"I'll re-run the code to check the tester's result.\" |" in t


def test_failure_8_no_built_or_verified_vocabulary():
    t = flat(SKILL)
    assert "mark FR-003 live" in t and "FR-003 can go `live (since 1.1.0)`" in t
    assert "`approved → built → verified`" in t
    assert "| \"Every test passed, so it's live.\" |" in t


def test_failure_9_status_move_as_a_version_change():
    t = flat(SKILL)
    assert "version 1.1.0 → 1.2.0" in t and "added a changelog row noting FR-003 built" in t
    assert "| \"Recording the build is a PRD change, so it gets a version.\" |" in t


def test_gap_builder_commits_with_refs():
    t = flat(SKILL)
    assert "Refs: <IDs>" in t and "--no-verify" in t
    assert "A commit with no `Refs:` trailer" in t


def test_pressure_pick_a_sensible_default_and_tester_test_is_wrong():
    t = flat(SKILL)
    assert "\"just pick a sensible default\"" in t
    assert "| \"The tester's test is wrong; fix it so the build goes green.\" |" in t


def test_pressure_just_mark_it_verified():
    t = flat(SKILL)
    assert "| \"Every test is green; just mark it verified.\" |" in t
    assert "the user's word is not a RESULTS line" in t


def test_pressure_caller_writes_it_here_because_it_is_tiny():
    t = flat(SKILL)
    assert "| \"It's tiny; a whole build is overkill, I'll write it here.\" |" in t
    r = flat(RUN)
    assert "A request to build anything beyond the approved IDs" in r
    assert "`status: Approved`" in r
