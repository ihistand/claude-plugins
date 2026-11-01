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
    for s in ("**4, failed.**", "Rollback:", "prd_deploy.py rollback", "Classification: unclassified", "Go to step 3"):
        at = two.index(s, at)  # each after the one before
    assert "Rollback:" not in two.split("**4, failed.**", 1)[0]
    for s in ("Detected: <YYYY-MM-DD>, deploy <run id> step <N>", "Touches: -", "Diagnosis: see the deploy log <run id>",
              "no `Resolution:` line"):
        assert s in two, s


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


def test_platform_neutral():
    for path in (SKILL, RUN, COMMAND):
        t = path.read_text(encoding="utf-8").lower()
        for word in ("acuantia", "rotoplas", "gcloud", "bigquery", "looker", "ivan"):
            assert word not in t, (path.name, word)


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


def test_r19_errors_entry_is_appended_with_edit():
    two = step(2)
    assert "Add the entry with Edit, appended at the end of the file; never rewrite `errors.md` with Write." in two
    assert ("The template line ``No entries yet. Add `### E-001 <title>` when the first error is diagnosed.`` may "
            "go in the close that adds the first entry, and in no other.") in two
