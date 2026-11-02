"""Pins from the 0.6 final review's fix wave (final-findings.md items 1-8 and the minors taken)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
SKILLS = ROOT / "skills"
RUN = SKILLS / "building-from-prds/running-a-build.md"
BUILD_SKILL = SKILLS / "building-from-prds/SKILL.md"
ERROR_RUN = SKILLS / "handling-errors/running-an-error.md"
FORMAT = ROOT / "references/prd-format.md"
SPEC = REPO / "docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md"
ACCEPTANCE = REPO / "docs/superpowers/plans/2026-11-01-prd-toolkit-0.6-acceptance.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a)]


# --- item 1 (Critical): a --fixes build removes the known-failing lines before step 7's trace ---

def _step(n: int, nxt: str) -> str:
    return between(flat(RUN), f"{n}. **", nxt)


def test_item1_deploy_gate_line_comes_off_right_after_the_unmark_commit():
    four = _step(4, "5. **Run.**")
    removal = four.split("git commit -m \"test(<area>): <T-ids> from the PRD\"", 1)[1]
    assert ("**`--fixes E-nnn` only: the deploy-gate lines.** Right after that commit, remove the "
            "`known-failing: E-nnn` line of each regression T-id whose test case is at a deploy-gate level") in removal
    assert 'git commit -m "docs(prd): <T-ids> no longer known-failing" -m "Refs: <IDs>, <E-nnn>"' in removal


def test_item1_build_gate_and_unit_lines_come_off_once_they_pass():
    five = _step(5, "6. **Reconcile**")
    assert ("**`--fixes E-nnn` only: the build-gate and unit lines.** Right after each step 5 check, remove the "
            "`known-failing: E-nnn` line of each build-gate or unit regression T-id that is `pass`") in five
    assert "(a build-gate T-id on the suite RESULTS, a unit T-id on the builder's UNIT lines)" in five
    assert "When step 5 is skipped, do this right after step 4's commits." in five
    assert 'git commit -m "docs(prd): <T-ids> no longer known-failing" -m "Refs: <IDs>, <E-nnn>"' in five
    assert "A build-gate or unit regression T-id that is not `pass` keeps its line" in five
    assert "stops the build at step 7" in five and "the un-mark is idempotent" in five


def test_item1_every_removal_precedes_step_7s_trace():
    r = flat(RUN)
    trace7 = r.index('7. **Full run.**')
    for s in ("**`--fixes E-nnn` only: the deploy-gate lines.**", "**`--fixes E-nnn` only: the build-gate and unit lines.**"):
        assert r.index(s) < trace7, s
    seven = _step(7, "8. **Close.**")
    assert "On a `--fixes` build the regression T-ids' `known-failing:` lines are already off (steps 4 and 5)" in seven


def test_item1_the_close_removes_no_line():
    close = flat(RUN).split("8. **Close.**", 1)[1].split("## Prompts", 1)[0]
    assert "**`--fixes E-nnn` only:** the close removes no `known-failing:` line" in close
    assert "removes each test case's `known-failing: E-nnn` line" not in close
    assert "the removals of steps 4 and 5" in close


def test_item1_callers_allowed_edits_name_steps_4_and_5():
    r = flat(RUN)
    assert ("One edit comes before the close: on a `--fixes` build, steps 4 and 5 remove that entry's "
            "`known-failing:` lines, each removal its own commit, before step 7's trace.") in r
    k = flat(BUILD_SKILL)
    assert ("on `--fixes E-nnn`, that entry's `known-failing:` lines before step 7's trace (a build-gate or unit "
            "regression T-id's once it is `pass`, a deploy-gate one's right after the tester's un-mark commit)") in k
    flags = between(k, "**The caller:**", "**All of these mean")
    assert "or at the close instead of before step 7's trace" in flags


def test_item1_no_text_says_the_line_comes_off_at_the_close():
    texts = [p for d in ("skills", "agents", "references") for p in (ROOT / d).rglob("*.md")] + [ROOT / "README.md"]
    stale = re.compile(r"(removed|came off|comes off|removes the line)[^.]{0,40}\b(clean|the) (`--fixes` )?close"
                       r"|close (also )?removes (each|the) [^.]{0,30}known-failing")
    for p in texts:
        hits = stale.findall(" ".join(p.read_text(encoding="utf-8").split()))
        assert not hits, (p.relative_to(ROOT), hits)


def test_item1_prd_format_error_loop_and_spec_agree():
    f = flat(FORMAT)
    assert ("A `/prd-build --fixes E-nnn` removes the line before its step 7 trace: once its T-id passes, or, at a "
            "deploy-gate level, once the tester's un-mark is committed") in f
    e = flat(ERROR_RUN)
    assert "removes their `known-failing:` lines before its full run" in e
    assert "(its `known-failing:` line came off once the tester's un-mark was committed)" in e
    rev = between(flat(SPEC), "> **Revisions.**", "## 1. Scope")
    assert "comes off in the `--fixes` build right after the tester's un-mark commit" in rev
    assert "before step 7's trace" in rev


# --- item 2: `check --ci` outside a git checkout is a tool error, not a pass ---

import os  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from datetime import date  # noqa: E402

import pytest  # noqa: E402
from conftest import PLUGINS_FILE, fired, lint  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from prdlint import deploy, errors, model, status  # noqa: E402

HOOKS = ROOT / "scripts/prd_hooks.py"
PRD_ERROR = ROOT / "scripts/prd_error.py"
GITHUB = ".github/workflows/prd-toolkit.yml"
TODAY = date(2026, 11, 3)


def _no_git_env(top: Path) -> dict:
    return {**os.environ, "GIT_CEILING_DIRECTORIES": str(top.parent), "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}


def _hooks(top: Path, *args):
    return subprocess.run([sys.executable, str(HOOKS), *args], cwd=top, capture_output=True, text=True, env=_no_git_env(top))


def test_item2_check_ci_without_git_exits_2_then_stale_after_git_init(prd):
    top = prd.parent.parent.parent
    (top / GITHUB).parent.mkdir(parents=True)
    (top / GITHUB).write_text("stale\n")
    r = _hooks(top, "check", "--ci", "docs/prd/orders")
    assert (r.returncode, r.stdout) == (2, "")
    assert r.stderr.strip() == f"prd_hooks: {prd.resolve().as_posix()} is not inside a git checkout"
    subprocess.run(["git", "init", "-q"], cwd=top, check=True)
    r = _hooks(top, "check", "--ci", "docs/prd/orders")
    assert r.returncode == 1 and r.stdout == f"stale: {GITHUB}: re-run prd_hooks.py ci --github --force\n"


def test_item2_status_ci_part_says_so_without_git(prd, monkeypatch):
    top = prd.parent.parent.parent
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(top.parent))
    items = [i.text for i in status.build_status(model.load(prd), top) if i.part == "CI"]
    assert items == [f"{prd.resolve().as_posix()} is not inside a git checkout"]
    subprocess.run(["git", "init", "-q"], cwd=top, check=True)
    assert [i.text for i in status.build_status(model.load(prd), top) if i.part == "CI"] == ["None."]


# --- item 3: a value that would open a code fence is refused ---

def _new(prd, **kw):
    a = dict(title="t", source="s", touches=["FR-001"], evidence=["ok"])
    a.update(kw)
    return errors.new(model.load(prd), a["title"], a["source"], a["touches"], a["evidence"], TODAY)


def _refused(fn, *a, **kw):
    with pytest.raises(deploy.Refused) as e:
        fn(*a, **kw)
    return e.value.reasons


@pytest.mark.parametrize("fence", ["```", "```python", "  ```", "~~~", " ~~~ text"])
def test_item3_new_refuses_evidence_that_opens_a_fence(prd, fence):
    before = (prd / "errors.md").read_bytes()
    assert _refused(_new, prd, evidence=["first", fence, "after"]) == [
        "Evidence: line 2 would open a code fence; drop it or put text before it"]
    assert (prd / "errors.md").read_bytes() == before


def test_item3_a_fence_inside_a_line_is_written(prd):
    assert _new(prd, evidence=["prints ``` then exits", "`x`"]) == "E-002"


def test_item3_one_line_values_that_start_a_fence_are_refused(prd):
    assert _refused(_new, prd, title="```python crash") == ["--title would open a code fence; drop it or put text before it"]
    _new(prd)
    assert _refused(errors.propose, model.load(prd), "E-002", "code bug", "~~~ d", None) == [
        "--diagnosis would open a code fence; drop it or put text before it"]
    errors.propose(model.load(prd), "E-002", "code bug", "d", None)
    assert _refused(errors.confirm, model.load(prd), "E-002", "``` yes", TODAY) == [
        "--reply would open a code fence; drop it or put text before it"]
    errors.confirm(model.load(prd), "E-002", "yes", TODAY)
    assert _refused(errors.resolve, model.load(prd), "E-002", t=None, level=None, version="", commit=None, run=None,
                    not_a_defect="```") == ["--not-a-defect would open a code fence; drop it or put text before it"]


def test_item3_cli_refuses_a_fenced_evidence_file_and_writes_nothing(prd, tmp_path):
    ev = tmp_path / "ev.txt"
    ev.write_text("Traceback:\n```\nboom\n")
    before = (prd / "errors.md").read_bytes()
    r = subprocess.run([sys.executable, str(PRD_ERROR), "new", str(prd), "--title", "t", "--source", "s",
                        "--evidence-file", str(ev)], capture_output=True, text=True, env=_no_git_env(prd.parent.parent.parent))
    assert (r.returncode, r.stdout) == (1, "")
    assert "refused: Evidence: line 2 would open a code fence; drop it or put text before it" in r.stderr
    assert (prd / "errors.md").read_bytes() == before


# --- item 4: Confirmed: is quoted material, and schema-refs skips errors.md ---

def _append_entry(prd, body: str):
    p = prd / "errors.md"
    p.write_text(p.read_text().rstrip("\n") + "\n\n### E-002 q\nDetected: 2026-11-03, user report\n" + body
                 + "Resolution: -\nRecurrence of: -\n")


@pytest.mark.parametrize("reply", ["yes TBD on the priority", "yes, it prints <name>"])
def test_item4_confirmed_reply_is_not_prose(prd, reply):
    _append_entry(prd, f'Classification: code bug\nConfirmed: 2026-11-03, "{reply}"\nDiagnosis: d\n')
    assert [f for f in lint(prd) if f.file == "errors.md"] == []


def test_item4_schema_refs_skips_errors_md(prd):
    _append_entry(prd, "Classification: code bug\nEvidence: `orders.order_kee` is empty\n"
                       "Diagnosis: the import writes `orders.order_kee`, not `orders.order_key`\n")
    assert "schema-refs" not in fired(lint(prd))
    (prd / "features/import.md").write_text((prd / "features/import.md").read_text().replace(
        "`orders.order_key` UNIQUE", "`orders.order_kee` UNIQUE"))
    assert "schema-refs" in fired(lint(prd))  # still fires in PRD prose


def test_item4_diagnosis_is_still_prose(prd):
    _append_entry(prd, 'Classification: code bug\nConfirmed: 2026-11-03, "yes"\nDiagnosis: prints <name>\n')
    assert "placeholder" in {f.rule for f in lint(prd) if f.file == "errors.md"}


def test_item4_cli_confirm_with_a_placeholder_like_reply_is_written(prd):
    env = _no_git_env(prd.parent.parent.parent)

    def run(*a):
        return subprocess.run([sys.executable, str(PRD_ERROR), *a], capture_output=True, text=True, env=env)

    assert run("new", str(prd), "--title", "t", "--source", "s", "--touches", "FR-001").returncode == 0
    assert run("propose", str(prd), "E-002", "--class", "code bug", "--diagnosis", "d").returncode == 0
    r = run("confirm", str(prd), "E-002", "--reply", "yes TBD on the priority, it prints <name>")
    assert r.returncode == 0, r.stderr


# --- item 8 (R23): Detected: and Recurrence of: are judged only on 0.6-loop (confirmed) entries ---

OLD = "Classification: code bug\nDiagnosis: d\n"


def test_item8_r23_old_entry_with_loose_lines_passes(prd):
    p = prd / "errors.md"
    p.write_text(p.read_text().rstrip("\n") + "\n\n### E-002 old\nDetected: 2026-10-01\n" + OLD
                 + "Resolution: -\nRecurrence of: E-001 (same cause)\n")
    assert "error-entries" not in fired(lint(prd))


def test_item8_r23_the_same_lines_on_a_confirmed_entry_are_findings(prd):
    p = prd / "errors.md"
    p.write_text(p.read_text().rstrip("\n") + "\n\n### E-002 new\nDetected: 2026-10-01\nClassification: code bug\n"
                 + 'Confirmed: 2026-10-02, "yes"\nDiagnosis: d\nResolution: -\nRecurrence of: E-001 (same cause)\n')
    got = {f.message for f in lint(prd) if f.rule == "error-entries"}
    assert got == {'E-002: Detected: must be "<YYYY-MM-DD>, <source>"', "E-002: Recurrence of: E-001 (same cause) is not an entry"}


# --- items 2-4: the README and the error procedure say what the scripts now do ---

README = ROOT / "README.md"


def test_items2_4_readme_and_procedure_name_the_new_refusals():
    r = flat(README)
    assert ("Outside a git checkout `check --ci` exits 2 (`prd_hooks: <path> is not inside a git checkout`), "
            "and `/prd-status`'s CI part says the same.") in r
    assert ("`new`, `propose`, `confirm` and `resolve`: a value that would open a code fence (an `Evidence:` line, "
            "or a title, diagnosis, reply or reason, whose first non-space characters are") in r
    assert "`refused: Evidence: line <n> would open a code fence; drop it or put text before it`" in r
    assert "Lint's prose rules skip `Evidence:` and `Confirmed:` lines, and `schema-refs` skips `errors.md`" in r
    e = flat(ERROR_RUN)
    assert "never a code fence (a line that starts with three backticks or tildes)" in e and "so `new` refuses one" in e


# --- item 5: one Refs rule across the skills ---

CHANGING = SKILLS / "changing-prds/SKILL.md"
AGENT = ROOT / "agents/prd-builder.md"


def test_item5_changing_prds_step5_cites_the_entry_and_hands_off_fixes():
    s5 = between(flat(CHANGING), "5. **Approval, then commit.**", "## Red Flags")
    assert ("a change made for an `errors.md` entry uses `Refs: <changed IDs>, E-nnn` on that commit instead") in s5
    assert ("hand off `/prd-build <area> <IDs> --fixes E-nnn` when the change was made for a confirmed entry "
            "whose route builds code") in s5
    assert "otherwise build with `/prd-build <area> <changed IDs>`" in s5


def test_item5_error_procedure_drops_the_builds_commits():
    s5 = between(flat(ERROR_RUN), "5. **Fix, by class.**", "| Class | Route |")
    assert "the build's commits" not in s5
    assert ("each `/prd-change`'s commits, its approval commit included, and the `--fixes` build's removal commits; "
            "the build's other commits cite its IDs, as every build commit does") in s5


# --- item 6: the builder is told a --fixes build is in scope ---

def test_item6_builder_prompt_carries_a_fixes_line():
    for path in (RUN, BUILD_SKILL):
        t = flat(path)
        assert "Fixes: E-nnn (regression T-ids: <T-ids>)" in t, path.name
    r = flat(RUN)
    assert "On a `--fixes` build the builder prompt adds `Fixes: E-nnn (regression T-ids: <T-ids>)`" in r
    assert "the builder un-marks a unit regression T-id itself" not in r
    assert "A unit regression T-id carries no marker" in r


def test_item6_rules_3_and_8_and_the_agent_make_the_fixes_entry_the_target():
    k = flat(BUILD_SKILL)
    rule3 = between(k, "3. **Only what the pack's ACs state.**", "4. **You never edit the PRD")
    rule8 = between(k, "8. **A failure you did not cause is not yours.**", "9. **A code-bug round")
    for rule in (rule3, rule8):
        assert "except the entry on your prompt's `Fixes:` line: its regression T-ids are your target" in rule
    a = flat(AGENT)
    assert "except the entry on the prompt's `Fixes:` line, whose regression T-ids are the build's target" in a
    assert "`Fixes:` line" in a.split("The prompt gives", 1)[1]


# --- item 7: the README's Handling errors section ---

def _readme_errors() -> str:
    t = README.read_text(encoding="utf-8")
    return " ".join(between(t, "\n## Handling errors\n", "\n## Publishing\n").split())


def test_item7_readme_handling_errors_is_accurate():
    s = _readme_errors()
    assert "(`code bug`, `spec gap`, `invalid requirement`, `environment` or `standard`)" in s
    assert "`prd gap`" not in s and "`test defect`" not in s
    assert "the commit-msg hook and `prd_error.py check` refuse a code commit that cites an unconfirmed one" in s
    assert "the commit hook and the trace refuse" not in s
    assert "a reproduction that cannot run stays in `Evidence:`" not in s
    assert "an error that does not reproduce gets a diagnosis that starts `not reproduced:`" in s


# --- item 8: the upgrade from 0.5 ---

WHICH_SCRIPT = [SKILLS / "building-from-prds/running-a-build.md", SKILLS / "building-from-prds/SKILL.md",
                SKILLS / "handling-errors/running-an-error.md", SKILLS / "deploying-from-prds/running-a-deploy.md",
                SKILLS / "changing-prds/SKILL.md", SKILLS / "adopting-prds/SKILL.md",
                ROOT / "commands/prd-status.md", ROOT / "commands/prd-context.md"]
OLD_COPY = ("When `.prd-toolkit/` exists but holds no `prd_error.py`, the vendored copy predates 0.6: stop, and tell "
            "the user to run `prd_hooks.py install docs/prd/<slug>` from the plugin (the README's form) and commit "
            "`.prd-toolkit/`.")


def test_item8_every_which_script_rule_stops_on_a_pre_06_copy():
    for path in WHICH_SCRIPT:
        t = flat(path)
        assert "**Which script.**" in t, path
        assert OLD_COPY in t, path


def test_item8_upgrade_note_names_the_working_routes():
    note = between(flat(README), "Upgrading from 0.5:", "- **0.5.0:**")
    assert "a tester-only round adds the marker and the tag" not in note
    assert ("An existing `known-failing` case needs a tagged citation: the trace's `known-failing-tags` reports it "
            "until `/prd-error E-nnn` takes its entry to the code-bug route, whose tester round marks the test a "
            "strict expected failure and tags its citation") in note
    assert ("An open 0.5 entry that carries a class now counts as `proposed`, so a code commit citing it is refused "
            "until `prd_error.py confirm` records your reply") in note
    assert "`error-entries` judges `Detected:` and `Recurrence of:` only on an entry that carries `Confirmed:`" in note


def test_item8_the_code_bug_route_takes_an_already_marked_case():
    s5 = between(flat(ERROR_RUN), "**A code bug.**", "6. **Close.**")
    assert ("When the regression T-id's case already carries `known-failing: <E-nnn>` and its block is `approved` "
            "(an entry from 0.5, or from adoption), the PRD already says it all: skip the patch, and the tester-only "
            "round below marks and tags its test.") in s5


# --- minors ---

DEPLOY_RUN = SKILLS / "deploying-from-prds/running-a-deploy.md"
PUBLISH_SKILL = SKILLS / "publishing-prds/SKILL.md"
PUBLISH_CMD = ROOT / "commands/prd-publish.md"


def test_minor_stop_entry_and_deploy_entry_use_the_procedures_forms():
    r = flat(RUN)
    assert ("prd_error.py new docs/prd/<slug> --title '<the stop in one line>' --source 'build <area> <IDs>' "
            "--touches <IDs> --evidence-file <SNAP>/stop-evidence.md; echo \"prd-error-exit=$?\"") in r
    d = flat(DEPLOY_RUN)
    assert ('--source "deploy run <run id>, failed step <N>"; echo "prd-error-exit=$?"') in d
    assert "Never write the entry by hand" in d  # restored pin (0.5)


def test_minor_deploy_names_prd_error_after_a_passing_regression_test():
    five = flat(DEPLOY_RUN).split("5. **Report.**", 1)[1]
    assert "prd_error.py list docs/prd/<slug> --open; echo \"prd-error-exit=$?\"" in five
    assert ("for each `confirmed` entry whose `Touches:` names a block the run's `tests` step passed, name "
            "`/prd-error E-nnn` as the next step: it resolves the entry from this run's log") in five


def test_minor_recover_then_rollback_restores_the_previous_install():
    d = flat(DEPLOY_RUN)
    assert ("A rollback after `recover` runs the step's `Rollback:` as written: it restores the previous install "
            "even when the killed step installed nothing, so say so when you ask") in d


def test_minor_readme_names_resolves_exit_2():
    s = _readme_errors()
    two = s.split("Exit 2 (usage error, nothing written)", 1)[1]
    assert "a fix without its T-id, level or commit (`a fix needs a T-id, its level and a commit`)" in two


def test_minor_spec_revisions_note_recover_without_a_log():
    rev = between(flat(SPEC), "> **Revisions.**", "## 1. Scope")
    assert "`recover` on a run with no log exits 2 (`no log for run <id>`)" in rev


def test_minor_r24_publish_goes_under_the_git_common_dir():
    s = flat(PUBLISH_SKILL)
    assert "git rev-parse --path-format=absolute --git-common-dir" in s
    assert "`<publish>` is `<git-common-dir>/prd-toolkit/publish`, outside the working tree" in s
    assert "`<publish>/<project>-prd-<version>.html`" in s
    assert "`<publish>/<project>-prd-<version>.summaries.json`" in s
    assert "the page's absolute path" in s
    assert "`./<project>-prd-<version>.html`" not in s and "in the repository root" not in s
    c = flat(PUBLISH_CMD)
    assert "`<git-common-dir>/prd-toolkit/publish/<project>-prd-<version>.html`" in c
    readme = flat(README)
    assert "(default `<git-common-dir>/prd-toolkit/publish/<project>-prd-<version>.html`" in readme


def test_minor_r24_render_creates_the_publish_directory(prd, tmp_path):
    out = tmp_path / "common/prd-toolkit/publish/orders-prd-1.0.0.html"
    r = subprocess.run([sys.executable, str(ROOT / "scripts/prd_publish.py"), "render", str(prd), "--out", str(out)],
                       capture_output=True, text=True, env=_no_git_env(prd.parent.parent.parent))
    assert r.returncode == 0, r.stderr
    assert out.is_file()


def test_minor_commit_msg_gate_checks_unconfirmed_entries_outside_the_boundary(prd):
    from prdlint import githook
    top = prd.parent.parent.parent
    subprocess.run(["git", "init", "-q"], cwd=top, check=True)
    (prd / "errors.md").write_text(
        "# Error ledger\n\n### E-002 x\nDetected: 2026-11-03, report\nClassification: code bug\nDiagnosis: d\nResolution: -\nRecurrence of: -\n")
    p = model.load(prd)
    vendored = [".prd-toolkit/prd_lint.py"]  # outside the PRD folder, outside the Boundary
    assert githook.commit_msg(p, top, "Bump\n\nRefs: E-002", vendored, merging=False) == [
        "E-002 is not confirmed; a commit that changes code may cite it only after prd_error.py confirm"]
    assert githook.commit_msg(p, top, "Bump", vendored, merging=False) == []  # no Refs: needed there
    assert githook.commit_msg(p, top, "Bump\n\nRefs: FR-099", vendored, merging=False) == []
