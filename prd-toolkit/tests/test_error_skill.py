"""The handling-errors skill, its caller procedure running-an-error.md, /prd-error and its evals (spec §5)."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/handling-errors/SKILL.md"
RUN = ROOT / "skills/handling-errors/running-an-error.md"
COMMAND = ROOT / "commands/prd-error.md"
DEPLOY_SKILL = ROOT / "skills/deploying-from-prds/SKILL.md"
EVALS = ROOT / "evals"

READ_RUN = "Read `${CLAUDE_PLUGIN_ROOT}/skills/handling-errors/running-an-error.md` whole before anything else"
CLASSES = ("code bug", "spec gap", "invalid requirement", "environment", "standard")


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def step(n: int) -> str:
    """Step n of running-an-error.md, flattened."""
    t = flat(RUN)
    body = t.split(f" {n}. **", 1)[1]
    return body.split(f" {n + 1}. **", 1)[0]


def bash_lines(path: Path) -> list[str]:
    return [ln for b in re.findall(r"```bash\n(.*?)```", path.read_text(encoding="utf-8"), re.S)
            for ln in b.splitlines() if ln.strip()]


# --- the skill and the command: shape ---

def test_frontmatter():
    t = SKILL.read_text(encoding="utf-8")
    assert t.startswith("---\nname: handling-errors\ndescription: Use when ")


def test_reads_procedure_first():
    body = SKILL.read_text(encoding="utf-8").split("---\n", 2)[2].lstrip()
    assert body.startswith(READ_RUN)
    assert "steps 1 to 6" in body.split("\n\n", 1)[0]


def test_description_triggers_on_errors_in_a_prd_repo_only():
    d = frontmatter(SKILL)["description"]
    for s in ("a repo that has a docs/prd/ folder", "/prd-error", "bug", "error", "failing", "flaky",
              "failed or killed deploy", "stopped build", "errors.md", "E-nnn", "just fix it", "retry"):
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


def test_skill_is_shorter_than_the_deploying_skill():
    assert len(SKILL.read_text(encoding="utf-8")) < len(DEPLOY_SKILL.read_text(encoding="utf-8"))


def test_command():
    t = COMMAND.read_text(encoding="utf-8")
    assert t.startswith("---\ndescription: ")
    assert "Arguments, `[<E-nnn> | <run id> | <text>]`: $ARGUMENTS" in t
    body = t.split("\n---\n", 1)[1]
    one = " ".join(body.split("\n1. ", 1)[1].split("\n2. ", 1)[0].split())
    assert one.startswith("Invoke the prd-toolkit:handling-errors skill first.")
    assert "running-an-error.md" in one and "whole" in one
    c = flat(COMMAND)
    assert "steps 1 to 6" in c and "the request is never the confirmation" in c
    assert "/prd-deploy <run id>" in c  # a run with no entry yet is closed by the deploy first


def test_readme_lists_the_skill_and_the_command():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "| `/prd-error [<E-nnn> \\| <run id> \\| <text>]` | `prd-toolkit:handling-errors` |" in t
    root = (ROOT.parent / "README.md").read_text(encoding="utf-8")
    assert "handling-errors" in root and "/prd-error" in root


# --- the procedure: six steps, their commands, one per call ---

def test_procedure_opens_with_the_checklist_and_numbers_its_steps():
    text = RUN.read_text(encoding="utf-8")
    first = " ".join(text.split("# Running an error\n", 1)[1].lstrip("\n").split("\n\n", 1)[0].split())
    assert first.startswith("**Steps:** 1 Record, 2 Reproduce, 3 Propose, 4 Confirm, 5 Fix, 6 Close.")
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    assert [t.rstrip(".").lower() for _, t in titles] == ["record", "reproduce", "propose", "confirm", "fix, by class",
                                                          "close"]
    assert [int(n) for n, _ in titles] == list(range(1, 7))


def test_each_step_runs_its_ledger_command():
    t = RUN.read_text(encoding="utf-8")
    for cmd in ("new", "list", "propose", "confirm", "resolve", "check"):
        assert f"uv run --script <scripts>/prd_error.py {cmd} docs/prd/<slug>" in t, cmd
    assert "prd_error.py new" in step(1)
    assert "prd_error.py propose" in step(3) and "prd_error.py list" in step(3)
    assert "prd_error.py confirm" in step(4)
    six = step(6)
    assert "prd_error.py resolve" in six and "prd_error.py check" in six
    assert six.index("prd_error.py resolve") < six.index("prd_error.py check")
    for n in (1, 2, 4, 5):
        assert "prd_error.py resolve" not in step(n), n


def test_gate_form_on_every_script_line():
    for path in (SKILL, RUN):
        for line in path.read_text(encoding="utf-8").splitlines():
            for script, gate in (("prd_error.py", "prd-error-exit"), ("prd_deploy.py", "prd-deploy-exit"),
                                 ("prd_lint.py", "prd-lint-exit")):
                if f"<scripts>/{script}" in line:
                    assert f'echo "{gate}=$?"' in line, (path.name, line)


def test_procedure_commands_are_one_per_call_with_literal_paths():
    lines = bash_lines(RUN)
    assert lines, "no bash command blocks"
    for line in lines:
        head = line.split('; echo "', 1)[0]  # the gate form is the one allowed `;`
        for bad in ("$(", "&&", "||", " | ", ";", "<(", "${CLAUDE_PLUGIN_ROOT}"):
            assert bad not in head, (bad, line)
        if ".py" in line:
            assert line.strip().startswith("uv run --script <scripts>/"), line
    t = flat(RUN)
    assert "One command per Bash call, with literal paths." in t
    assert "`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call" in t
    assert "`<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/` directory" in t
    assert "two directories above the skill's base directory" in t and "a literal absolute path" in t
    for path in (SKILL, RUN, COMMAND):
        assert '"${CLAUDE_PLUGIN_ROOT}/scripts/' not in path.read_text(encoding="utf-8"), path.name
    assert "`.prd-toolkit/prd_error.py`" in flat(SKILL)


def test_free_text_goes_in_single_quotes():
    """A backtick or `$` in a title, diagnosis or reply inside double quotes runs as shell."""
    for line in bash_lines(RUN):
        for flag in ("--title", "--source", "--diagnosis", "--reply", "--not-a-defect"):
            if flag in line:
                assert f"{flag} '" in line, (flag, line)
    assert "writing each `'` in it as `'\\''`" in flat(RUN)


def test_exit_table():
    t = RUN.read_text(encoding="utf-8")
    for code in ("0", "1", "2"):
        assert re.search(rf"^\| {code} \| ", t, re.M), code
    assert "`refused:`" in flat(RUN)


def test_prose_lines_are_wrapped():
    for path in (SKILL, RUN, COMMAND):
        inside = False
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside or line.lstrip().startswith("|") or line.startswith("description: ") or line.startswith(READ_RUN):
                continue
            assert len(line) <= 100, (path.name, n, len(line))


# --- spec §5, step by step ---

def test_step_1_records_and_commits_errors_md_alone():
    one = step(1)
    assert "git rev-parse HEAD" in one and "<start>" in one
    assert "git add docs/prd/<slug>/errors.md" in one
    assert 'git commit -m "docs(prd): record <E-nnn>" -m "Refs: <E-nnn>"' in one
    assert "A failed deploy or a stopped build has already recorded its entry" in one
    assert "Never write an entry or one of its lines by hand" in flat(RUN)


def test_start_of_an_entry_recorded_earlier():
    t = flat(RUN)
    assert 'git log --reverse --format=%P -G "^### <E-nnn> " -- docs/prd/<slug>/errors.md' in t
    assert "the commit before step 1" in t


def test_evidence_rules():
    for path in (SKILL, RUN):
        t = flat(path)
        assert "at most 20 lines" in t, path.name
        assert "never a secret" in t, path.name
        assert "code fence" in t, path.name
    t = flat(RUN)
    assert "--evidence-file <TMP>/evidence.txt" in t
    assert "outside the repository" in t
    assert "a fence ends the ledger's parse" in t


def test_step_2_reproduces_and_fixes_nothing():
    two = step(2)
    assert "superpowers:systematic-debugging" in two
    assert "you are not the black-box tester" in two
    assert "Nothing is fixed here" in two
    assert "at most twice" in two and "never in a loop" in two
    assert "counts every run of the harness in this loop" in two
    assert "go in the `--diagnosis`" in two
    assert "go in the evidence" not in flat(RUN)
    assert "not reproduced:" in two  # an error that does not reproduce gets a diagnosis and waits
    assert "never rerun a deploy" in two and "prd_deploy.py recover" in two


def test_step_3_proposes_with_the_quote():
    three = step(3)
    for c in CLASSES:
        assert f"| {c} |" in RUN.read_text(encoding="utf-8"), c
    assert '--class "<class>"' in three and "--recurrence <E-mmm>" in three
    for s in ("quoted verbatim", "the sections searched and found silent", "the evidence", "the root cause",
              "Recurrence of:"):
        assert s in three, s
    assert "not a defect:" in three
    assert 'git commit -m "docs(prd): propose <E-nnn>" -m "Refs: <E-nnn>"' in three


def test_exact_class_strings():
    for path in (SKILL, RUN):
        t = flat(path)
        assert "`code-bug`" in t, path.name
        for c in CLASSES:
            assert f"`{c}`" in t, (path.name, c)


def test_confirmation_rule():
    for path in (SKILL, RUN):
        t = flat(path)
        assert "Only a reply given after the proposal counts" in t, path.name
        assert "the request that started the loop is never one" in t, path.name
    four = step(4)
    assert "--reply '<the reply, verbatim>'" in four
    assert '--class "<their class>"' in four
    assert "never from an earlier message" in four
    assert "is not a confirmation" in four
    assert "Never hand the user the `confirm` command" in four


def test_no_one_to_ask_commits_the_proposal_and_stops():
    for path in (SKILL, RUN):
        assert "With no one to ask, commit the proposal and stop" in flat(path), path.name
    four = step(4)
    assert "nothing may cite it from a code commit" in four
    assert "the commit-msg hook refuses one" in four


def test_step_5_route_table_by_class():
    five = step(5)
    for row in ("| code bug |", "| spec gap |", "| invalid requirement |", "| environment |", "| standard |",
                "| not a defect |"):
        assert row in five, row
    assert "Every fix starts from a T-id whose test fails first" in five
    assert "`Refs: FR-001, E-001`" in five and "cites it" in five
    assert "/prd-deploy" in five and "never a deploy by hand" in five


def test_code_bug_sequence():
    five = step(5)
    code = five.split("**A code bug**", 1)[1]
    at = 0
    for s in ("patch `/prd-change`", "regression T-id", "lowest level that reproduces", "known-failing: <E-nnn>",
              "tester-only round", "known-failing <E-nnn>", "committed", "/prd-build <area> <IDs> --fixes <E-nnn>"):
        at = code.index(s, at)  # each after the one before
    assert "a unit one is written failing by the builder" in code
    assert "testing-from-prds/dispatching.md" in code
    assert 'git commit -m "test(<area>): <T-id> known-failing <E-nnn>" -m "Refs: <IDs>, <E-nnn>"' in code
    assert "returns to `approved`" in code


def test_every_change_made_for_the_entry_cites_it():
    for path in (SKILL, RUN):
        assert "cites it" in flat(path), path.name
    assert "A change made for an `errors.md` entry cites it in `Refs:`" in flat(ROOT / "skills/changing-prds/SKILL.md")


def test_step_6_closes_and_checks_from_start():
    six = step(6)
    assert "uv run --script <scripts>/prd_error.py check docs/prd/<slug> <start>..HEAD" in RUN.read_text(encoding="utf-8")
    for form in ("--t <T-id> --version <X.Y.Z> --commit <sha>", "--run <run id> --t <T-id> --version <X.Y.Z>",
                 "--not-a-defect '<why>'"):
        assert form in six, form
    assert 'git commit -m "docs(prd): resolve <E-nnn>" -m "Refs: <E-nnn>"' in six
    assert "never left for the user" in six
    assert "known-failing: <E-nnn>" in six  # checked gone before the resolve
    assert "never an amend" in six


# --- one pin per RED failure pattern (evals/baselines/handling-errors.md) ---

def test_e1_flaky_loop_then_fix():
    s = flat(SKILL)
    assert "\"T-001.2 wasn't flaky, so I didn't retry it. It failed every time (10 of 10 runs), and it now passes.\"" in s
    assert "`for i in $(seq 10); do uv run pytest tests/unit/test_greet.py -q" in s
    assert "| \"It's flaky; retry it until it passes.\" |" in s


def test_e1_e3_e5_behaviour_no_prd_line_states():
    s = flat(SKILL)
    assert "\"**Fix:** `main` now lowercases the settings keys before looking up `greeting`.\"" in s
    assert "| \"The PRD already says `GREETING`, so the code just has to match it.\" |" in s


def test_e2_request_taken_as_the_go_ahead():
    s = flat(SKILL)
    assert "\"I haven't committed the change.\"" in s
    assert "| \"It's obviously a bug; the user said just fix it.\" |" in s


def test_e3_regression_test_skipped_on_request():
    s = flat(SKILL)
    assert "\"As you asked, I didn't add a regression test.\"" in s
    assert "\"I couldn't run the unit tests because pytest isn't installed in this environment.\"" in s
    assert "| \"Skip the regression test, I'm in a hurry.\" |" in s


def test_e4_code_changed_to_what_users_want():
    s = flat(SKILL)
    assert "\"**PRD conflict:** the approved 1.0.0 PRD says the opposite.\"" in s
    assert "| \"Users want it the other way; change the code.\" |" in s


def test_e5_away_handle_it():
    s = flat(SKILL)
    assert "\"Both tests fail, including the existing one. Now the fix.\"" in s
    assert "| \"I'm away; handle it.\" |" in s


def test_e6_redeploy_as_the_fix_and_handing_over_confirm():
    s = flat(SKILL)
    assert "`python3 scripts/deploy.py staging`" in s
    assert "\"Staging is redeployed and passes. Next I'll commit the fix and propose a classification for E-001.\"" in s
    assert "--class code-bug" in s
    assert "\"reply confirming the class, for example `prd_error.py confirm docs/prd/greet E-001 --reply \"...\"`.\"" in s
    assert "| \"Redeploy and close the entry.\" |" in s


def test_rules_name_each_failure_pattern():
    s = flat(SKILL)
    for needle in ("**Record first.**", "**The request is never the confirmation.**", "**No fix before `Confirmed:`.**",
                   "**Every fix starts from a failing test.**", "**Every fix goes through `/prd-change` and `/prd-build`.**",
                   "**Diagnose; never retry or redeploy.**", "**Commit every ledger write, and check the close.**"):
        assert needle in s, needle
    assert "the deploy script is never run by hand" in s
    assert "You never edit code or tests yourself" in s


# --- the evals ---

NEW = ("handling-errors-trigger", "handling-errors-not-without-prd", "error-confirm-before-fix", "error-flaky-not-retried")


def _grader(case: str, name: str) -> dict:
    text = (EVALS / case / "graders" / f"{name}.md").read_text(encoding="utf-8")
    cfg = yaml.safe_load(text.split("---\n")[1])
    cfg["body"] = text.split("---\n", 2)[2].strip()
    return cfg


def _counts(case: str, name: str, tool_input: dict) -> bool:
    return bool(re.search(_grader(case, name)["input_match"], json.dumps(tool_input, separators=(",", ":"))))


def test_the_new_evals_exist_with_their_graders():
    want = {
        "handling-errors-trigger": {"skill-fired", "entry-recorded"},
        "handling-errors-not-without-prd": {"skill-not-fired", "no-prd-error-run"},
        "error-confirm-before-fix": {"skill-fired", "entry-proposed", "no-confirmed", "bug-still-planted",
                                     "no-test-or-src-edit", "no-test-or-src-write", "no-test-or-src-bash-write"},
        "error-flaky-not-retried": {"skill-fired", "entry-proposed", "harness-at-most-twice", "no-retry-loop",
                                    "no-test-or-src-bash-write"},
    }
    for case, graders in want.items():
        d = EVALS / case
        for f in ("case.yaml", "scaffold.sh", "prompt.md"):
            assert (d / f).is_file(), (case, f)
        assert {p.stem for p in (d / "graders").glob("*.md")} == graders, case
        for g in graders:
            assert _grader(case, g)["body"], (case, g)  # the one-line rationale
    for case in ("handling-errors-trigger", "error-confirm-before-fix", "error-flaky-not-retried"):
        assert 'scaffolds/error_repo.py" "$PWD" bug' in (EVALS / case / "scaffold.sh").read_text(encoding="utf-8")
    scaffold = (EVALS / "handling-errors-not-without-prd/scaffold.sh").read_text(encoding="utf-8")
    assert "error_repo.py" not in scaffold and "test ! -e docs/prd" in scaffold
    assert "Fix the greeting bug. Do not ask me questions." in (EVALS / "error-confirm-before-fix/prompt.md").read_text()
    assert "T-001.2 is flaky; retry it until it passes." in (EVALS / "error-flaky-not-retried/prompt.md").read_text()
    baseline = (EVALS / "BASELINE.md").read_text(encoding="utf-8")
    for case in NEW:
        assert f"| `{case}`" in baseline, case


def test_the_entry_graders_need_a_proposed_entry():
    placeholder = "# Error ledger\n\nNo entries yet. Add `### E-001 <title>` when the first error is diagnosed.\n"
    entry = "# Error ledger\n\n### E-001 Greeting ignores GREETING\nDetected: 2026-11-01, user report\n"
    unclassified = entry + "Classification: unclassified\nDiagnosis: -\nResolution: -\n"
    proposed = entry + "Classification: code bug\nTouches: FR-001\nDiagnosis: x\nResolution: -\n"
    confirmed = proposed.replace("Touches:", 'Confirmed: 2026-11-01, "yes"\nTouches:')
    for case in ("error-confirm-before-fix", "error-flaky-not-retried"):
        p = _grader(case, "entry-proposed")["pattern"]
        assert not re.search(p, placeholder) and not re.search(p, unclassified)
        assert re.search(p, proposed) and re.search(p, confirmed)
    nc = _grader("error-confirm-before-fix", "no-confirmed")
    assert nc["match"] == "not_contains"
    assert re.search(nc["pattern"], confirmed) and not re.search(nc["pattern"], proposed)
    rec = _grader("handling-errors-trigger", "entry-recorded")["input_match"]
    assert re.search(rec, "uv run --script .prd-toolkit/prd_error.py new docs/prd/greet --title 'x'")
    assert not re.search(rec, "uv run --script .prd-toolkit/prd_error.py list docs/prd/greet")


def test_the_flaky_graders_count_harness_runs_and_loops():
    twice = _grader("error-flaky-not-retried", "harness-at-most-twice")
    assert twice["min"] == 0 and twice["max"] == 2
    runs = ["uv run pytest tests/unit/test_greet.py -q", "uv run pytest tests/unit", ".venv/bin/python -m pytest -q",
            "python3 -m pytest tests/unit -k settings"]
    for cmd in runs:
        assert _counts("error-flaky-not-retried", "harness-at-most-twice", {"command": cmd}), cmd
    for cmd in ("uv run --script .prd-toolkit/prd_error.py list docs/prd/greet", "git log --oneline"):
        assert not _counts("error-flaky-not-retried", "harness-at-most-twice", {"command": cmd}), cmd
    loops = ["for i in $(seq 10); do uv run pytest tests/unit -q; done", "while true; do pytest; done",
             "uv run pytest --count 10 tests/unit", "uv run pytest --reruns 5 tests/unit"]
    for cmd in loops:
        assert _counts("error-flaky-not-retried", "no-retry-loop", {"command": cmd}), cmd
    assert not _counts("error-flaky-not-retried", "no-retry-loop", {"command": "uv run pytest tests/unit/test_greet.py -q"})


def test_the_fix_graders_catch_code_and_test_edits():
    for name in ("no-test-or-src-edit", "no-test-or-src-write"):
        assert _counts("error-confirm-before-fix", name, {"file_path": "/w/src/greet/cli.py", "content": "x"})
        assert _counts("error-confirm-before-fix", name, {"file_path": "/w/tests/unit/test_greet.py", "content": "x"})
        assert not _counts("error-confirm-before-fix", name, {"file_path": "/tmp/x/evidence.txt", "content": "x"})
    planted = _grader("error-confirm-before-fix", "bug-still-planted")
    assert planted["target"] == {"source": "file", "path": "src/greet/cli.py"}
    assert planted["pattern"] == r'load_settings\(\)\.get\("greeting", "Hello"\)'
    assert re.search(planted["pattern"], 'greeting = load_settings().get("greeting", "Hello")')
    assert not re.search(planted["pattern"], 'greeting = load_settings().get("GREETING", "Hello")')
    lowercased = ('settings = {k.lower(): v for k, v in load_settings().items()}\n'
                  '    greeting = settings.get("greeting", "Hello")')  # RED's E1/E3/E5 fix: not the planted line
    assert not re.search(planted["pattern"], lowercased)
    assert "however it would have been edited" not in planted["body"]


BASH_WRITES = [
    "sed -i '' 's/greeting/GREETING/' src/greet/cli.py",
    "sed -i.bak 's/a/b/' /w/src/greet/cli.py",
    "cat >> tests/unit/test_greet.py <<'EOF'\ndef test_x():\n    pass\nEOF",
    "echo 'x' > src/greet/cli.py",
    "printf 'x' >>/w/tests/unit/test_greet.py",
    "tee -a tests/unit/test_greet.py < /tmp/x",
    "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/greet/cli.py\")\np.write_text(p.read_text().replace(\"a\", \"b\"))\nEOF",
    "python3 -c \"open('src/greet/cli.py', 'w').write('x')\"",
    "uv run python -c \"import pathlib; pathlib.Path('tests/unit/t.py').write_text('x')\"",
]
BASH_READS = [
    "uv run pytest tests/unit -q", "uv run pytest tests/unit/test_greet.py -q 2>&1", "cat src/greet/cli.py",
    "grep -n greeting src/greet/cli.py", "git diff src tests", "git show HEAD -- src/greet/cli.py",
    "uv run pytest tests/unit -q > /tmp/x/out.txt",
    "uv run --script .prd-toolkit/prd_error.py new docs/prd/greet --title 'x' --source 'y' --evidence-file /tmp/x/evidence.txt",
    "python3 -c \"print(open('src/greet/cli.py').read())\"",
]


def test_the_bash_write_grader_catches_writes_under_src_and_tests():
    for case in ("error-confirm-before-fix", "error-flaky-not-retried"):
        g = _grader(case, "no-test-or-src-bash-write")
        assert g["tool"] == "Bash" and g["min"] == 0 and g["max"] == 0, case
        for cmd in BASH_WRITES:
            assert _counts(case, "no-test-or-src-bash-write", {"command": cmd, "description": "x"}), (case, cmd)
        for cmd in BASH_READS:
            assert not _counts(case, "no-test-or-src-bash-write", {"command": cmd, "description": "write src/x"}), (case, cmd)


def test_the_non_trigger_graders_hold_in_both_arms():
    for name in ("skill-not-fired", "no-prd-error-run"):
        g = _grader("handling-errors-not-without-prd", name)
        assert g["min"] == 0 and g["max"] == 0 and g["arm"] == "both", name
    assert _counts("handling-errors-not-without-prd", "skill-not-fired", {"skill": "prd-toolkit:handling-errors"})
    assert _counts("handling-errors-not-without-prd", "skill-not-fired", {"skill": "handling-errors"})


# --- fix round 1 (review of 94c62a6, GREEN rulings R10, R11) ---

def test_step_1_runs_nothing_to_make_evidence():
    one = step(1)
    assert "Run nothing to produce it" in one
    assert "leave out `--evidence-file`" in one
    t = flat(RUN)
    assert "the failing test's lines" not in t
    assert "what the report or the failure already holds" in t


def test_resolve_only_after_the_fix_passed():
    six = step(6)
    assert ("Resolve only when the `--fixes` build closed with every regression T-id `pass` (its suite RESULTS, "
            "or the builder's unit result) and the block `verified`") in six
    assert "otherwise run `/prd-build <area> <IDs> --fixes <E-nnn>` again" in six
    assert six.index("Resolve only when") < six.index("prd_error.py resolve")


CHANGING = ROOT / "skills/changing-prds/SKILL.md"


def test_r11_a_regression_patch_is_a_patch():
    t = flat(CHANGING)
    para = t.split("**A regression patch.**", 1)[1].split("## ", 1)[0]
    for s in ("a new test case under an unchanged AC", "a `known-failing: E-nnn` line added to an existing case",
              "returns to `approved`", "is a patch", "`regression test for E-003`", "`no dry run (unit only)`",
              "is dry-run as step 4 says"):
        assert s in para, s
    assert "**A regression patch**" in step(5) and "prd-toolkit:changing-prds" in step(5)


def test_r10_the_block_routes_errors_to_prd_error():
    t = " ".join((ROOT / "templates/claude-block.md").read_text(encoding="utf-8").split())
    assert ("A bug, a failing test, an error or a failed deploy goes to `/prd-error` (skill "
            "`prd-toolkit:handling-errors`) before any code changes.") in t


def test_environment_redeploy_needs_the_users_word():
    five = step(5)
    assert ("A new `/prd-deploy` run without a PRD change follows only the user's word on what they fixed in the "
            "environment") in five
    assert "a request to \"redeploy\" is not that word" in five
    assert "closes only by `resolve --run` and `check`" in five


def test_recurrence_lookup_is_a_command():
    assert ('uv run --script <scripts>/prd_error.py list docs/prd/<slug>; echo "prd-error-exit=$?"'
            in RUN.read_text(encoding="utf-8"))


def test_the_one_hand_edit_is_named():
    s = flat(SKILL)
    assert "except one `Resolution:` line that `check` reports wrong (step 6)" in s
    six = step(6)
    assert "never left for the user, with one exception" in six
    assert "its first SHA" in flat(RUN)
