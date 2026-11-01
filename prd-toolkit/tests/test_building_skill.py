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
                if f"<scripts>/{script}" in line:
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
    assert "the status follows **Stops**" in t and "/prd-change" in t
    assert "the builder may now read the failing test" in t
    assert "After a third failed round on one T-id the build stops and reports it to the user." in t
    assert "After three rounds on one T-id" not in t
    assert "A QUESTIONS line that is not a test dispute is a PRD gap and stops the build" in t


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


# --- fix round 1: review items, rulings R24-R29, scenario reruns ---

def test_r24_a_stop_after_the_merge_writes_built_before_it_none():
    t = flat(RUN)
    assert "statuses stay as they are" not in t
    assert ("Any stop after the builder's merge writes `built` for each block whose unit T-ids pass, "
            "never `verified`.") in t
    assert "A stop before the merge writes no status." in t
    for stop in ("a PRD gap", "a failing test that cites no T-id", "`prd-trace-exit=` other than `0`",
                 "the third failed round on a T-id"):
        assert stop in t.split("Any stop after the builder's merge", 1)[0].rsplit("**Stops.**", 1)[1], stop


def test_reconcile_record_quotes_the_tests_assertion():
    t = RUN.read_text(encoding="utf-8")
    assert 'test:      <path>:<line> "<the assertion, verbatim>"' in t
    assert "asserts <what it asserts>" not in t
    assert ("A classification without its quote does not count. The quote is all three, each verbatim: the "
            "`ac:` line, the `expect` entry and the test's assertion.") in flat(RUN)


def test_r26_no_worktree_fallback_stops_on_a_failed_check():
    t = flat(RUN)
    assert "there is no merge: its commits land on the build branch" in t
    assert "`git log --format=%B <base>..HEAD`" in t
    assert ("Without worktree isolation, a builder round that fails its state check stops the build and "
            "reports its commits to the user; never re-record `<base>` past them.") in t


def test_r27_rounds_are_counted_from_the_first_dispatch():
    t = flat(RUN)
    assert "Round 1 is a T-id's first builder dispatch (for a tester's T-id, its first `write`)." in t
    # final review minor 11: the repeated sentence is gone; test_final_review pins the one kept
    assert "After a third failed round on one T-id the build stops and reports it to the user." in t
    assert "every round's RECONCILE record or failure line" in t
    assert "a step 4 check failure counts as a round and is recorded by its finding lines" in t


def test_r25_test_disputes_are_reconciled_not_stopped():
    slot = '<T-id>: test dispute: "<assertion, verbatim>" vs "<ac:/expect quote, verbatim>"'
    assert slot in flat(SKILL) and slot in flat(RUN)
    t = flat(RUN)
    assert "the caller reconciles each test dispute by quote at step 6" in t
    assert "A QUESTIONS line that is not a test dispute is a PRD gap and stops the build" in t


def test_r28_caller_edits_the_prd_only_at_the_close():
    t = flat(RUN)
    assert ("The caller edits the PRD only at the close: a block's `Status:`, its §11 status and its "
            "`Source:`.") in t
    assert "A test case, a `known-failing:` marker, an AC or a contract change goes through `/prd-change`." in t
    assert "I didn't add a known-failing marker since this looks like a harness issue" in flat(SKILL)


def test_g1_description_triggers_on_a_failing_cited_test_and_go_green_requests():
    d = frontmatter(SKILL)["description"]
    assert "a test that cites a T-id of an approved requirement fails against the code" in d
    assert "fix the code or a tester's test so a build goes green" in d


def test_r29_never_merge_onto_the_default_branch():
    t = flat(RUN)
    assert "`prd-build/<area>-<IDs>`" in t
    assert "never merge onto the default branch" in t
    assert ("I merged straight onto `base` instead of asking about a feature branch, because you said not to "
            "ask questions.") in flat(SKILL)


def test_g3_snapshot_and_full_run_are_never_skipped():
    t = flat(RUN)
    for n in ("2", "7"):
        body = t.split(f"{n}. **", 1)[1].split(f"{int(n) + 1}. **", 1)[0]
        assert "Never skipped" in body, n
    s = flat(SKILL)
    assert "I did not take the before and after snapshots." in s
    assert "I did not run the full build-gate harness myself." in s
    assert '| "The agents already reported the results." |' in s


def test_minors_rounds_branches_trace_and_agent_skills():
    t = flat(RUN)
    assert "A builder round runs steps 4 and 5 again: the suite reruns." in t
    assert "A failed round's builder branch is kept and listed in the report; never delete one with `-D`." in t
    assert "`prd-trace-exit=1` after writing `verified` reverts those blocks to `built` and stops the build" in t
    assert "required" in flat(AGENT) and "Skills-registry row" in flat(AGENT)


# --- fix round 2 ---

def test_a_prd_gap_defers_to_stops_not_before_any_merge():
    assert "before any merge" not in flat(SKILL)
    assert "before any merge" not in flat(RUN)
    assert ("A PRD gap stops the build: `built` for the blocks an earlier round merged, otherwise no "
            "status (the caller's **Stops**).") in flat(SKILL)
    step4 = flat(RUN).split("4. **Check the state.**", 1)[1].split("5. **Run.**", 1)[0]
    assert ("is a PRD gap and stops the build, as **Stops** says: `built` if a merge happened, "
            "otherwise no status.") in step4


def test_b_stops_scopes_the_state_check():
    stops = flat(RUN).split("**Stops.**", 1)[1].split("1. **Preflight.**", 1)[0]
    assert "a failed state check," not in stops
    assert "on a failed tester state check (`dispatching.md` step 4)" in stops
    assert ("on a failed builder state check only without worktree isolation; with it, a failed builder "
            "check is a failed round (**Rounds**)") in stops
    assert "steps 2 and 4 are the snapshot and state check for the tester's rounds" in flat(SKILL)


def test_g3_the_failing_test_route_takes_the_snapshot():
    inp = flat(RUN).split("**Input:**", 1)[1].split("Both agents must be", 1)[0]
    assert "runs step 1, then step 2's snapshot before any dispatch" in inp
    assert "Never skipped, on this route too" in inp
    assert "then enters at step 6" in inp


def test_g4_a_build_finishes_in_one_turn():
    t = flat(RUN)
    assert ("**One turn.** A build runs to its close, or to a stop under **Stops**, in the same turn. Never "
            "end the turn with a next round announced: dispatch it.") in t
    assert "I'll re-dispatch with the same prompt" in flat(SKILL)


def test_minor4_trace_runs_before_the_close_commit():
    close = flat(RUN).split("8. **Close.**", 1)[1]
    assert "Run the trace before the close commit" in close
    assert "`prd-trace-exit=2` stops the build like `1`" in close
    assert "reverts those blocks to `built`" in close
    lines = RUN.read_text(encoding="utf-8").split("8. **Close.**", 1)[1].splitlines()
    trace = next(i for i, l in enumerate(lines) if "prd_trace.py" in l)
    commit = next(i for i, l in enumerate(lines) if l.strip().startswith("git commit"))
    assert trace < commit


def test_minor5_failed_round_rules_apply_with_isolation_only():
    step4 = flat(RUN).split("4. **Check the state.**", 1)[1].split("5. **Run.**", 1)[0]
    assert "With worktree isolation, a failed round merges nothing" in step4
    assert "Without worktree isolation, a failed builder check stops the build instead" in step4
    assert ("Without worktree isolation, `<base>` does not move on a UNIT-failure round: the range keeps the "
            "earlier commits, and the check covers them all.") in step4


def test_minor6_prose_lines_are_wrapped():
    inside = False
    for n, line in enumerate(RUN.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside or line.lstrip().startswith("|"):
            continue
        assert len(line) <= 100, (n, len(line))


# --- fix round 3: the tester's suite runs after every builder round ---

def test_g5_suite_follows_every_builder_round_on_every_route():
    t = flat(RUN)
    assert ("On every route, after each builder round, step 5 runs: the snapshot (`dispatching.md` step 2) and "
            "then `prd-tester` `Mode: suite` on the build's non-unit build-gate T-ids.") in t
    assert ("Its RESULTS, checked with `prd_build_check.py --results`, are the only evidence for those T-ids. "
            "The caller's own harness run is step 7 and never replaces step 5.") in t
    inp = t.split("**Input:**", 1)[1].split("Both agents must be", 1)[0]
    assert "the first builder round it dispatches is followed by steps 4 and 5" in inp


def test_g5_verified_names_all_three_sources():
    close = flat(RUN).split("8. **Close.**", 1)[1]
    assert ("| `built → verified` | every unit T-id passes on the builder's UNIT lines, every non-unit "
            "build-gate T-id passes on the tester's suite RESULTS, every build-gate T-id passes in your step 7 "
            "run, and `prd-trace-exit=0` |") in close


def test_g5_red_flag_and_rationalization():
    s = flat(SKILL)
    assert "\"The tests pass when I run them, so the suite round isn't needed.\"" in s
    assert ("| \"I ran pytest myself and it's green.\" | Your run is step 7. RESULTS for a tester's T-id come "
            "only from the tester's suite round; without it the block stays `built`. |") in s


def test_g5_step5_states_the_snapshot_and_dispatch_once():
    step5 = flat(RUN).split("5. **Run.**", 1)[1].split("6. **Reconcile**", 1)[0]
    assert step5.count("the build's non-unit build-gate T-ids") == 1
    assert "Take step 2's snapshot again" not in step5 and "on the same T-ids" not in step5


def test_g5_no_tester_tids_skips_step5():
    t = flat(RUN)
    assert ("When the build has no non-unit build-gate T-ids, step 5 is skipped: there is nothing to dispatch, "
            "and the close's `verified` needs only the builder's UNIT lines, your step 7 run and "
            "`prd-trace-exit=0`.") in t
    step3 = t.split("3. **Dispatch both in one message**", 1)[1].split("4. **Check the state.**", 1)[0]
    # R28: the builder goes alone only when there is no non-unit T-id at all, build gate or deploy gate
    assert "With no non-unit T-ids, dispatch the builder alone: the tester has no `write`." in step3
    assert "With no non-unit build-gate T-ids, dispatch the builder alone" not in step3


THREE_SOURCES = ("every unit T-id passes on the builder's UNIT lines, every non-unit build-gate T-id on the "
                 "tester's suite RESULTS, every build-gate T-id in the caller's step 7 run, and `prd-trace-exit=0`")


def test_g5_skill_rows_use_the_three_source_rule():
    s = flat(SKILL)
    assert "when every build-gate T-id passes and `prd-trace-exit=0`" not in s
    assert "every build-gate T-id `pass` and `prd-trace-exit=0`" not in s
    assert s.count(THREE_SOURCES) == 2


# --- fix round 4: the caller reads running-a-build.md before anything else (G6) ---

READ_RUN = "Read of `${CLAUDE_PLUGIN_ROOT}/skills/building-from-prds/running-a-build.md`"


def test_g6_skill_opens_with_the_callers_read():
    text = SKILL.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1]
    first = " ".join(body.split("## Overview\n", 1)[1].lstrip("\n").split("\n\n", 1)[0].split())
    assert body.split("## Overview\n", 1)[0].strip() == "# Building from PRDs"  # the block is the body's first text
    assert first.startswith("If you are not running as the `prd-toolkit:prd-builder` agent, you are the caller.")
    for s in (f"Your next tool call is a {READ_RUN}, whole (no offset, no limit)",
              "follow it step by step",
              "Do not run a test, read the code or the PRD, or dispatch any agent before you have read it.",
              "The builder's rules below are not yours to follow"):
        assert s in first, s


def test_g6_caller_red_flag_quotes_the_skipped_procedure():
    caller = flat(SKILL).split("**The caller:**", 1)[1].split("## Common Rationalizations", 1)[0]
    assert "Dispatching `prd-toolkit:prd-builder` straight from the skill" in caller
    assert "\"Not done: the tester's suite round, the merge, and moving FR-003 …\"" in caller
    assert "running-a-build.md never read" in caller


def test_g6_command_reads_running_a_build_first():
    body = COMMAND.read_text(encoding="utf-8").split("\n---\n", 1)[1]
    steps = re.findall(r"^\d+\. ", body, re.M)
    assert steps[0] == "1. "
    one = " ".join(body.split("\n1. ", 1)[1].split("\n2. ", 1)[0].split())
    assert one.startswith(f"Before anything else, make a {READ_RUN}, whole (no offset, no limit).")
    flat_body = " ".join(body.split())
    assert flat_body.index(READ_RUN) < flat_body.index("Invoke the prd-toolkit:building-from-prds skill")


def test_g6_running_a_build_opens_with_the_checklist():
    text = RUN.read_text(encoding="utf-8")
    first = " ".join(text.split("# Running a build\n", 1)[1].lstrip("\n").split("\n\n", 1)[0].split())
    assert first == ("**Steps:** 1 Preflight, 2 Snapshot, 3 Dispatch, 4 Check the state, 5 Run (the tester's "
                     "suite), 6 Reconcile, 7 Full run, 8 Close. The build is not done until step 8's report or a "
                     "stop under **Stops**: run every step, in this turn.")


def test_r26_block_with_only_deploy_gate_tests_closes_verified():
    close = flat(RUN).split("8. **Close.**", 1)[1].split("Run `git rev-parse", 1)[0]
    for s in ["A block with no unit and no build-gate T-ids moves to `verified` at a clean close",
              "its deploy-gate tests run at `/prd-deploy`",
              "Never leave it `built`",
              "refuses a deploy while any block is `built`"]:
        assert s in close, s


def test_r26_never_built_is_scoped_to_a_clean_close():
    close = flat(RUN).split("8. **Close.**", 1)[1].split("Run `git rev-parse", 1)[0]
    assert "Never leave it `built` at a clean close" in close
    assert "On a stopped build it stays `built`, and the next clean build closes it `verified`" in close


# --- R28: the build's tester writes deploy-gate tests, and the build never runs them ---

def _step(t: str, n: int, title: str, nxt: str) -> str:
    return t.split(f"{n}. **{title}", 1)[1].split(nxt, 1)[0]


def test_r28_split_gives_the_tester_every_non_unit_tid():
    step1 = _step(flat(RUN), 1, "Preflight.**", "2. **Snapshot**")
    assert "Deploy-gate T-ids are not run in 0.4." not in step1
    for s in ["**unit** (level `unit`) for the builder, and **non-unit** (every other level, build gate and "
              "deploy gate alike) for the tester's `write`",
              "The tester writes a test for every non-unit T-id and never runs a deploy-gate one.",
              "Of those, only the **build-gate non-unit** T-ids (a level whose `Gate` is `build`) run in the "
              "build: step 5's suite and its `--results` list, step 7 and the close's `verified` take them "
              "and never a deploy-gate T-id, which runs at `/prd-deploy`."]:
        assert s in step1, s


def test_r28_step3_dispatches_the_tester_with_every_non_unit_tid():
    step3 = _step(flat(RUN), 3, "Dispatch both in one message**", "4. **Check the state.**")
    assert ("`prd-toolkit:prd-tester`, with the tester prompt (below) as `Mode: write` and every non-unit "
            "T-id, build gate and deploy gate, each with its test-case file.") in step3
    assert ("When every non-unit T-id is deploy-gate, dispatch the tester all the same: it writes their "
            "tests, and step 5 is skipped.") in step3


def test_r28_tester_files_citing_deploy_gate_tids_are_the_testers():
    step4 = _step(flat(RUN), 4, "Check the state.**", "5. **Run.**")
    assert ("A test that cites a deploy-gate T-id is the tester's like any other non-unit test: "
            "`prd_build_check.py --diff` fails a builder round that edits it, and the commit below takes it "
            "with the rest.") in step4


def test_r28_suite_results_and_close_stay_build_gate():
    t = flat(RUN)
    step5 = _step(t, 5, "Run.**", "6. **Reconcile**")
    assert ("A deploy-gate T-id is never in the suite or its `--tids` list, though the tester wrote its test "
            "in step 3: it runs at `/prd-deploy`.") in step5
    step7 = _step(t, 7, "Full run.**", "8. **Close.**")
    assert "Run every Levels harness command whose `Gate` is `build`" in step7
    close = t.split("8. **Close.**", 1)[1]
    assert "every non-unit build-gate T-id passes on the tester's suite RESULTS" in close


def test_r28_tester_only_round_for_verified_blocks():
    t = flat(RUN)
    inp = t.split("**Input:**", 1)[1].split("Both agents must be", 1)[0]
    assert "or at `verified` for a tester-only round (below)" in inp
    para = t.split("**A tester-only round.**", 1)[1].split("1. **Preflight.**", 1)[0]
    for s in ["A block already `verified` whose deploy-gate T-ids no test cites",
              "`<ID>: <T-id> (deploy gate) has no citing test; it cannot go live`",
              "`/prd-build <area> <IDs>`",
              "no builder and no status change",
              "the T-ids of the pre-flight's `refused:` lines",
              r"Grep the anchored pattern `@prd\s+<T-id>\b`",
              "Dispatch `prd-toolkit:prd-tester` alone, `Mode: write`, with those T-ids only",
              "step 4's tester bullet",
              '`git commit -m "test(<area>): <T-ids> from the PRD" -m "Refs: <IDs>"`',
              "That dispatch replaces step 3, and steps 5 to 8 are skipped",
              "the block stays `verified`",
              "its `Status:`, `Source:` and §11 row are untouched"]:
        assert s in para, s


# --- final review: harness overlap (finding 3) and the tester-only search (finding 6) ---

def test_step7_deploy_gate_failure_is_a_harness_overlap():
    seven = flat(RUN).split("7. **Full run.**", 1)[1].split("8. **Close.**", 1)[0]
    assert ("A failure here of a test that cites a deploy-gate T-id is a harness overlap: a build-gate "
            "command collected a deploy-gate test.") in seven
    assert "It stops the build with a report: never reconcile it, and never change code for it." in seven
    stops = flat(RUN).split("**Stops.**", 1)[1].split("Any stop after the builder's merge", 1)[0]
    assert "a harness overlap in step 7" in stops


def test_tester_only_round_finds_missing_tids_exactly():
    para = flat(RUN).split("**A tester-only round.**", 1)[1].split("1. **Preflight.**", 1)[0]
    assert "Grep `@prd <T-id>` with" not in para
    assert ("When the round comes from a refusal, the missing T-ids are the T-ids of the pre-flight's "
            "`refused:` lines") in para
    assert r"Grep the anchored pattern `@prd\s+<T-id>\b` (dots escaped: `@prd\s+T-004\.1\b`)" in para
    assert "When none is missing, report that and commit nothing." in para
