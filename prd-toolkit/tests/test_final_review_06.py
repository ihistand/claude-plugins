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
