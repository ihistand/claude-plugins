"""The deploying-from-prds skill, its caller procedure running-a-deploy.md and /prd-deploy."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/deploying-from-prds/SKILL.md"
RUN = ROOT / "skills/deploying-from-prds/running-a-deploy.md"
COMMAND = ROOT / "commands/prd-deploy.md"

READ_RUN = "Read `${CLAUDE_PLUGIN_ROOT}/skills/deploying-from-prds/running-a-deploy.md` whole before anything else"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def step(n: int) -> str:
    """Step n of running-a-deploy.md, flattened."""
    t = flat(RUN)
    body = t.split(f" {n}. **", 1)[1]
    return body.split(f" {n + 1}. **", 1)[0]


# --- the brief's pins ---

def test_frontmatter():
    t = SKILL.read_text(encoding="utf-8")
    assert t.startswith("---\nname: deploying-from-prds\ndescription: Use when ")


def test_reads_procedure_first():
    body = SKILL.read_text(encoding="utf-8").split("---\n", 2)[2].lstrip()
    assert body.startswith(READ_RUN)


def test_never_types_a_runbook_command():
    for path in (SKILL, RUN):
        assert "Never run a runbook command yourself" in flat(path), path.name


def test_procedure_steps():
    t = RUN.read_text(encoding="utf-8")
    for s in ["prd_deploy.py plan", "prd_deploy.py run", "prd_deploy.py confirm", "prd_deploy.py resume",
              "prd_deploy.py rollback", "prd_deploy.py check", 'echo "prd-deploy-exit=$?"', "Classification: unclassified",
              "## Deployed", "live (since", "no version bump and no §14 row"]:
        assert s in t, s


def test_exit_table():
    t = RUN.read_text(encoding="utf-8")
    for code in ("0", "1", "3", "4"):
        assert re.search(rf"^\| {code} \| ", t, re.M), code


def test_confirm_rule():
    t = flat(RUN)
    assert "the user's reply to this step, verbatim" in t
    assert "never from an earlier message" in t


def test_no_one_to_ask():
    assert "With no one to ask, the run stays stopped" in flat(RUN)


def test_command():
    t = COMMAND.read_text(encoding="utf-8")
    assert t.startswith("---\ndescription: ")
    assert "running-a-deploy.md" in t and "--until" in t


# --- one pin per baseline failure (evals/baselines/deploying-from-prds.md) ---

def test_d1_request_taken_as_the_approval_and_steps_skipped():
    s = flat(SKILL)
    assert "\"I treated your instruction as the approval for production.\"" in s
    assert "\"I ran the deploy script directly instead of `prd_deploy run`, because that would have started with staging.\"" in s
    assert "| \"You asked me to deploy to production, so that is the approval.\" |" in s
    assert "| \"Staging is fine; skip it.\" |" in s


def test_d2_confirm_command_handed_over_and_self_approval():
    s = flat(SKILL)
    assert "Handing the user the `confirm --reply \"deploy production\"` and `resume` commands to run \"yourself\"" in s
    assert "| \"The user is away and told me to approve it myself.\" |" in s


def test_d3_code_edited_to_get_past_a_failed_check():
    s = flat(SKILL)
    assert "\"I put back `greeting = load_settings().get(\"GREETING\", \"Hello\")` and redeployed.\"" in s
    assert "| \"It's just the greeting text; I'll fix it and carry on.\" |" in s


def test_d4_failure_left_out_of_errors_md():
    s = flat(SKILL)
    assert "A rollback run, and no `errors.md` entry for the failure." in s
    assert "| \"It's rolled back, so there is nothing to record.\" |" in s


def test_d5_close_left_uncommitted_and_unchecked():
    s = flat(SKILL)
    assert "\"`prd_deploy.py check` compares two commits, so I haven't run it.\"" in s
    assert "| \"The row is written; committing it and checking it is ceremony.\" |" in s


def test_d6_steps_run_by_hand_when_the_script_is_slow_or_denied():
    s = flat(SKILL)
    assert ("After `prd_deploy.py run` was denied, running `python3 scripts/deploy.py staging` and "
            "`TEST_ENV=staging uv run pytest tests/system` yourself.") in s
    assert "| \"The script is slow, or its run was denied, so I ran the steps myself.\" |" in s


# --- the binding requirements beyond the brief ---

def test_description_is_a_deploy_trigger():
    d = frontmatter(SKILL)["description"]
    for s in ("docs/prd/", "/prd-deploy", "production", "staging", "stopped or failed deploy run", "record"):
        assert s in d, s
    for path in (SKILL, COMMAND):
        for value in frontmatter(path).values():
            assert ": " not in value and " #" not in value, (path, value)  # plain YAML scalars


def test_skill_has_the_superpowers_shape():
    text = SKILL.read_text(encoding="utf-8")
    heads = ["## Overview", "## Non-negotiable rules", "## Red Flags - STOP", "## Common Rationalizations",
             "## Related skills"]
    at = [text.index(h) for h in heads]
    assert at == sorted(at)
    assert text.index(READ_RUN) < text.index("## Overview")
    assert "Violating the letter of these rules is violating the spirit." in text


def test_a_request_is_never_the_reply_to_a_human_step():
    for path in (SKILL, RUN):
        t = flat(path)
        assert "A request to deploy, or \"approve it yourself\", is never the reply to a human step." in t, path.name
    t = flat(RUN)
    assert "Never call `prd_deploy.py confirm` with a reply the user did not give to that step." in t
    assert "after the run stopped at that step" in t


def test_permission_denied_or_slow_script_stops():
    for path in (SKILL, RUN):
        t = flat(path)
        assert "When the harness denies a `prd_deploy.py` command, or the script is slow, stop and tell the user" in t, path.name
    assert "name the command so they can allow it" in flat(RUN)


def test_failed_step_order_rollback_then_errors_then_close():
    two = step(2)
    assert "run `prd_deploy.py rollback` only on the user's yes in their own words" in two
    at = 0
    for s in ("**4, failed.**", "Rollback:", "prd_deploy.py rollback", "prd_error.py new", "Go to step 3"):
        at = two.index(s, at)  # each after the one before
    assert "Rollback:" not in two.split("**4, failed.**", 1)[0]
    assert '--source "deploy run <run id>, failed step <N>"' in two


def test_nothing_is_edited_to_get_past_a_failure():
    for path in (SKILL, RUN):
        assert "Code, tests and the runbook are never edited during a deploy" in flat(path), path.name
    assert "prd-toolkit:changing-prds" in flat(RUN)


def test_close_is_always_committed_and_checked():
    t = flat(RUN)
    assert "The close is always committed" in t
    assert "`<base>` is the run's HEAD" in t
    assert "Refs: none (no behaviour change)" in t
    assert "A failing close check is fixed and the check rerun before the report." in t
    three, four = step(3), step(4)
    assert "git commit" in three and "prd_deploy.py check" in four


def test_a_human_stop_is_not_closed():
    t = flat(RUN)
    assert "A run stopped at a human step is not closed" in t
    assert "HEAD moved since the run started" in t


def test_command_invokes_the_skill_first():
    body = COMMAND.read_text(encoding="utf-8").split("\n---\n", 1)[1]
    one = " ".join(body.split("\n1. ", 1)[1].split("\n2. ", 1)[0].split())
    assert one.startswith("Invoke the prd-toolkit:deploying-from-prds skill first.")
    assert "running-a-deploy.md" in one and "whole" in one


def test_procedure_opens_with_the_checklist_and_numbers_its_steps():
    text = RUN.read_text(encoding="utf-8")
    first = " ".join(text.split("# Running a deploy\n", 1)[1].lstrip("\n").split("\n\n", 1)[0].split())
    assert first.startswith("**Steps:** 1 Plan, 2 Run, 3 Close, 4 Close check, 5 Report.")
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    assert [t.rstrip(".").lower() for _, t in titles] == ["plan", "run", "close", "close check", "report"]
    assert [int(n) for n, _ in titles] == list(range(1, len(titles) + 1))


def test_gate_forms_in_both_files():
    for path in (SKILL, RUN):
        for line in path.read_text(encoding="utf-8").splitlines():
            for script, gate in (("prd_deploy.py", "prd-deploy-exit"), ("prd_lint.py", "prd-lint-exit"),
                                 ("prd_trace.py", "prd-trace-exit")):
                if f"<scripts>/{script}" in line:
                    assert f'echo "{gate}=$?"' in line, (path.name, line)


def test_procedure_commands_are_one_per_call_with_literal_paths():
    text = RUN.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    assert blocks, "no bash command blocks"
    for block in blocks:
        for line in block.splitlines():
            if not line.strip():
                continue
            head = line.split("; echo \"", 1)[0]  # the gate form is the one allowed `;`
            for bad in ("$(", "&&", "||", " | ", ";", "<("):
                assert bad not in head, (bad, line)
    t = RUN.read_text(encoding="utf-8")
    for cmd in ("plan", "run", "confirm", "resume", "rollback", "check"):
        assert f"uv run --script <scripts>/prd_deploy.py {cmd} docs/prd/<slug>" in t, cmd
    assert "One command per Bash call, with literal paths." in flat(RUN)


def test_prose_lines_are_wrapped():
    for path in (SKILL, RUN):
        inside = False
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside or line.lstrip().startswith("|") or line.startswith("description: ") or line.startswith(READ_RUN):
                continue
            assert len(line) <= 100, (path.name, n, len(line))


# --- fix round 1: review items and rulings R17, R18 ---

def test_r17_a_trace_finding_at_the_close_still_commits():
    three, five = step(3), flat(RUN).split(" 5. **Report.**", 1)[1]
    assert "commit nothing" not in flat(RUN) and "commit nothing" not in flat(SKILL)
    assert "commit the close regardless" in three
    assert "`prd_deploy.py check` validates it against the log, not the trace" in three
    assert "prd-toolkit:building-from-prds" in three
    assert "a trace finding at the close" in five
    assert "has no citing test; it cannot go live" in step(2)  # the pre-flight refusal that makes it unexpected
    rule7 = flat(SKILL).split("7. **The close is committed and checked.**", 1)[1].split("8. **", 1)[0]
    assert "unless" not in rule7 and "except" not in rule7


def test_r18_run_and_resume_in_the_background():
    t = flat(RUN)
    assert "Run `run` and `resume` in the background, and wait for the exit" in t
    assert "longest timeout" not in t
    assert ("A Bash call that timed out or was killed is reported to the user, never rerun, and never finished by "
            "hand") in t
    assert "started and did not finish" in t
    for path in (SKILL, RUN):
        assert "Slow never means running the steps yourself." in flat(path), path.name


def test_rollback_after_the_close_is_not_run():
    five = flat(RUN).split(" 5. **Report.**", 1)[1]
    assert "the rollback can no longer run through the script and is never run by hand" in five
    assert "only as information" in five


def test_rollback_line_matches_the_script():
    assert "`` rollback: `<command>` ``" in RUN.read_text(encoding="utf-8")


def test_git_common_dir_runs_from_the_repository_root():
    t = flat(RUN)
    assert "from the repository root" in t
    assert "(a relative answer is under the repository root)" not in t


def test_d6_paraphrase_is_not_a_quote():
    s = flat(SKILL)
    assert "\"to run production by hand on the user's reply\"" not in s
    assert "(baseline summary, not a quote)" in s


def test_a_new_run_after_a_failed_one():
    assert ("A new run after a failed one starts again at step 1, after the failed run's close (step 3) and close "
            "check (step 4), and both runs go in one report.") in flat(RUN)


# --- fix round 2: REFACTOR from the GREEN reruns (R19, R20) ---

def test_r20_which_script_to_call():
    for path in (SKILL, RUN, COMMAND):
        assert '"${CLAUDE_PLUGIN_ROOT}/scripts/' not in path.read_text(encoding="utf-8"), path.name
    t = flat(RUN)
    assert "`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call" in t
    assert "`<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/` directory" in t
    assert "the copy its hooks and CI run" in t
    assert "two directories above the skill's base directory" in t and "Base directory for this skill" in t
    assert "a literal absolute path" in t
    s = flat(SKILL)
    assert "`.prd-toolkit/prd_deploy.py`" in s and "two directories above the skill's base directory" in s
    blocks = re.findall(r"```bash\n(.*?)```", RUN.read_text(encoding="utf-8"), re.S)
    for block in blocks:
        for line in block.splitlines():
            if ".py" in line:
                assert line.strip().startswith("uv run --script <scripts>/"), line


def test_failure_entry_is_written_with_prd_error_new():
    two = step(2)
    assert "prd_error.py new" in two and '--source "deploy run <run id>, failed step <N>"' in two
    assert "Add the entry with Edit" not in two and "never rewrite `errors.md` with Write" not in two
    assert "the entry stays open and unclassified" in two
    assert "/prd-error E-<nnn>" in two and "next step" in two


def test_a_reply_may_name_the_run_as_the_only_one_stopped_at_the_step():
    two = step(2)
    assert "that names the run (by id, or as the only run stopped at that step" in two
    assert "ask when more than one is stopped there" in two
    assert "never from an earlier message" in two


def test_r28_missing_deploy_gate_test_routes_to_a_tester_only_build():
    two = step(2)
    assert ("the missing test goes to `/prd-build <area> <IDs>` with that block's ID, whose tester-only round "
            "writes it without a builder or a status change") in two


# --- final review: the new refusals in the procedure ---

def test_final_review_refusals_in_the_procedure():
    t = flat(RUN)
    assert ("A run id of another PRD (`run <id> is for <folder>, not <folder>`) and a runbook changed since "
            "the run started are refused the same way.") in t
    assert ("`another prd_deploy command is running in this repository` means a `run`, `resume` or `rollback` "
            "is still working in this repository: report it and wait for the user, never retry it in a loop.") in t
    assert ("An `--until` whose cut would take a production step along exits 2: the runbook runs a step on "
            "that environment after production. Report it and stop; the order is a gap for "
            "`prd-toolkit:changing-prds`.") in t
    four = t.split("- **4, failed.**", 1)[1].split("3. **Close.**", 1)[0]
    assert ("A step with a `start` record and no step record (the run printed `could not write the log`) is "
            "the failed step: show its `start` record instead.") in four
    three = t.split("3. **Close.**", 1)[1].split("4. **Close check.**", 1)[0]
    assert ("every level of its `tests` steps has a `pass` record, and no step on it started without "
            "finishing") in three
    assert "`check` requires a row for each one" in three
    check = t.split("4. **Close check.**", 1)[1].split("5. **Report.**", 1)[0]
    for needle in ("a reached environment with no row", "a row dated other than the run's date",
                   "a run of another PRD"):
        assert needle in check, needle


# --- 0.6: recover ---

def test_recover_procedure():
    two = step(2)
    assert "prd_deploy.py recover" in two and "--reply '<the user's words, verbatim>'" in two
    assert "only after the user says they checked the environment" in two
    assert "never on the request to deploy" in two
    assert "prd-deploy: failed step=<N> run=<id>" in two
    assert "recovered: no result after start" in two
    assert "a new run" in two
    assert "uv run --script <scripts>/prd_deploy.py recover docs/prd/<slug> --run <id> --step <N> --reply" in RUN.read_text(encoding="utf-8")
    assert "${CLAUDE_PLUGIN_ROOT}" not in "\n".join(re.findall(r"```bash\n(.*?)```", RUN.read_text(encoding="utf-8"), re.S))


def test_recover_replaces_never_work_around_for_a_killed_step():
    t = flat(RUN)
    assert "started and did not finish" in t
    assert "the one way out is `recover`" in t


# --- 0.8.2, spec section 17 fix 5: a deploy done by hand ---

# The brief's sentence, with the command in a code block: every `<scripts>/prd_deploy.py` line carries its exit gate
# (test_gate_forms_in_both_files), which a prose line cannot fit in 100 columns.
BY_HAND = ("A deploy the owner did by hand is recorded with this command, its own Bash call: ```bash uv run --script "
           "<scripts>/prd_deploy.py record docs/prd/<slug> --env <env> --commit <sha> --reply \"<the owner's words>\"; "
           "echo \"prd-deploy-exit=$?\" ``` It prints `run=<id>`. Commit its row as the close and run `prd_deploy.py check` on it")


def red_flags() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split("## Red Flags - STOP", 1)[1].split("## Common Rationalizations", 1)[0].split())


def test_by_hand_deploy_is_recorded_with_record():
    assert BY_HAND in flat(SKILL)


def test_by_hand_never_write_a_deployed_row():
    assert "Never write a Deployed row yourself." in flat(SKILL)


def test_by_hand_record_moves_no_status():
    assert ("A by-hand record moves no status: `verified → live` waits for a `/prd-deploy` run whose tests pass on that "
            "environment.") in flat(SKILL)


def test_by_hand_red_flag():
    assert "I'll add the Deployed row myself, since they already deployed it" in red_flags()


def test_by_hand_record_during_a_stopped_run():
    assert ("A record made while a run is stopped at a human step falls under the Red Flag \"A close committed while a "
            "run waits at a human step\".") in flat(SKILL)


# --- 0.8.5, spec 13 (items 1 to 5): Task 14's pins ---

LATER_STEP = "a later `--step` only for a step the owner's reply names"
NEVER_ASK = "Never ask in the chat whether later steps are done."
MULTI_CONFIRM = ("uv run --script <scripts>/prd_deploy.py confirm docs/prd/<slug> --run <id> --step <N> --reply '<the reply "
                 "to step N>' --step <M> --reply '<the reply to step M>'; echo \"prd-deploy-exit=$?\"")
MID_RUN_ENTRY = ('uv run --script <scripts>/prd_error.py new docs/prd/<slug> --title "<the error in one line>" --source '
                 '"deploy run <run id>, step <N>"; echo "prd-error-exit=$?"')
BRANCH_NOTE = "prd_deploy: the close is on <current>, not <branch>; push the close commit to <branch> too"


def test_085_later_steps_only_when_the_reply_names_them():
    for path in (SKILL, RUN):
        t = flat(path)
        assert LATER_STEP in t, path.name
        assert NEVER_ASK in t, path.name
    two = step(2)
    assert MULTI_CONFIRM in two
    assert "by its number or its title" in two
    assert "step <M> human <env>: confirmed ahead" in two


def test_085_mid_run_entry_is_left_uncommitted_and_the_close_carries_it():
    two = step(2)
    assert MID_RUN_ENTRY in two
    at = 0
    for s in ("**An error found while the run is stopped.**", "prd_error.py new", "Do not commit it", "then resume",
              "the close commit carries it", "`/prd-error E-<nnn>` after the close"):
        at = two.index(s, at)
    assert "the tracked tree has changes" in two
    assert "An error found while a run is stopped is recorded with `prd_error.py new` and left uncommitted" in flat(SKILL)


def test_085_timeout_column_and_the_flag_that_overrides_it():
    t = flat(RUN)
    assert "a `tests` level's own `Timeout` in testing.md's Levels" in t
    assert "a `--timeout` given to `run` or `resume` overrides every one of them" in t
    assert "`timed out after <N> s (the <level> level's Timeout)`" in t


def test_085_the_owner_pushes_the_close_to_the_noted_branch():
    t = flat(RUN)
    assert f"`{BRANCH_NOTE}`" in t
    five = t.split(" 5. **Report.**", 1)[1]
    assert "tell the owner to push the close commit to `<branch>`" in five
    assert "Never push it yourself" in five
    rule7 = flat(SKILL).split("7. **The close is committed and checked.**", 1)[1].split("8. **", 1)[0]
    assert "tell the owner to push the close commit to that branch; never push it yourself" in rule7


def test_085_a_check_that_matches_by_pattern():
    two = step(2)
    assert "`` Check: `<command>` matches `<pattern>` ``" in two
    assert "`no stdout line matches '<pattern>'`" in two
    assert "`no stdout line equals '<text>'`" in two


def test_085_eval_deploy_confirms_named_steps():
    d = ROOT / "evals/deploy-confirms-named-steps"
    assert {p.stem for p in (d / "graders").glob("*.md")} == {
        "skill-fired", "confirms-named-steps-in-one-call", "later-steps-carry-the-owners-words",
        "no-unnamed-step-confirmed", "resumed", "no-gates-answer"}
    assert 'deploy_repo.py" "$PWD" at-ui-steps' in (d / "scaffold.sh").read_text(encoding="utf-8")
    assert "| `deploy-confirms-named-steps`" in (ROOT / "evals/BASELINE.md").read_text(encoding="utf-8")


def _grader_counts(case: str, name: str, command: str) -> bool:
    import json
    import yaml
    text = (ROOT / "evals" / case / "graders" / f"{name}.md").read_text(encoding="utf-8")
    cfg = yaml.safe_load(text.split("---\n")[1])
    return bool(re.search(cfg["input_match"], json.dumps({"command": command}, separators=(",", ":"))))


def test_085_deploy_graders_on_synthetic_commands():
    case, reply = "deploy-confirms-named-steps", "done with 2; 3 and 4 were done in the same session"
    good = (f".prd-toolkit/prd_deploy.py confirm docs/prd/greet --run R --step 2 --reply '{reply}' --step 3 --reply "
            f"'{reply}' --step 4 --reply '{reply}'; echo \"prd-deploy-exit=$?\"")
    double = good.replace("'", '"')
    own = (".prd-toolkit/prd_deploy.py confirm docs/prd/greet --run R --step 2 --reply 'done with 2' --step 3 --reply "
           "'confirmed' --step 4 --reply 'confirmed'")
    single = f".prd-toolkit/prd_deploy.py confirm docs/prd/greet --run R --step 2 --reply '{reply}'"
    assert _grader_counts(case, "confirms-named-steps-in-one-call", good)
    assert not _grader_counts(case, "confirms-named-steps-in-one-call", single)
    for cmd in (good, double):
        assert _grader_counts(case, "later-steps-carry-the-owners-words", cmd), cmd
    assert not _grader_counts(case, "later-steps-carry-the-owners-words", own)
    assert _grader_counts(case, "no-unnamed-step-confirmed", good + " --step 5 --reply 'x'")
    assert not _grader_counts(case, "no-unnamed-step-confirmed", good)


# Fix round 1, Ruling 40: through the inbox each later human step is its own gate; never confirmed from an outcome.
INBOX_GATE = ("Through the decision inbox each later human step is its own gate, which the owner answers when the run "
              "stops there; one `confirm` for several steps is the chat route, with the owner's own reply naming each.")


def test_085_fix1_inbox_steps_stay_the_owners():
    two = step(2)
    assert INBOX_GATE in two
    assert "when its reply names later steps, confirm each with that reply" not in two
    assert "(the chat route; through the inbox each step is its own gate)" in flat(SKILL)


# Fix round 2, items 3 and minors: rule 4's exception wherever a rule forbids it; the mid-run entry exception.
RULE4_EXCEPTION = "A later step that the owner's reply to the stopped step names takes that reply (rule 4)."


def test_085_fix2_rule_4_exception_in_the_red_flag_and_the_procedure():
    rf = red_flags()
    flag = rf.split("A `confirm` whose reply you wrote", 1)[1].split(" - ", 1)[0]
    assert RULE4_EXCEPTION in flag
    two = step(2)
    never = "Never call `prd_deploy.py confirm` with a reply the user did not give to that step."
    assert never + " " + RULE4_EXCEPTION.replace("(rule 4)", "(rule 4 of `deploying-from-prds`)") in two


def test_085_fix2_no_one_to_ask_means_no_reply_to_the_stopped_step():
    two = step(2)
    assert ("With no one to ask, the run stays stopped: when the session holds no reply to the stopped step, a "
            "headless session") in two


def test_085_fix2_the_mid_run_entry_is_the_one_edit_outside_the_close():
    assert ("nor the PRD outside the close (step 3), except the `prd_error.py new` entry of an error found while the "
            "run is stopped (step 2)") in flat(RUN)
    assert ("**All of these mean: stop, put back what you changed outside the close, except a mid-run "
            "`prd_error.py new` entry, and return to the step") in flat(SKILL)
