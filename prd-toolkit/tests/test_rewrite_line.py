"""The Rewrite: line and the caller's --stale step (spec section 15): pinned lines in each text."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/testing-from-prds/SKILL.md"
DISPATCHING = ROOT / "skills/testing-from-prds/dispatching.md"
AGENT = ROOT / "agents/prd-tester.md"
RUN = ROOT / "skills/building-from-prds/running-a-build.md"
ADOPT = ROOT / "skills/adopting-prds/SKILL.md"

TESTER_RULE = ("On `Rewrite: <T-id>`, rewrite that one test from the current test case and run it. Every value comes from "
               "the PRD; rule 2's limits hold (no `skip`, no `xfail`, no looser comparison).")
STALE_CALL = ('uv run --script <scripts>/prd_build_check.py docs/prd/<slug> --stale --tids <T-id>,<T-id>; '
              'echo "prd-build-check-exit=$?"')
RED_FLAG = "Editing a test to bring it up to date, or sending `Misread:` for a case you changed"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_dispatching_template_and_paragraph():
    t = flat(DISPATCHING)
    assert "Rewrite: <T-id> (suite only; one line per stale T-id)" in t
    assert ("A `Rewrite:` line lets the tester rewrite that one test from the case as it now stands. It carries no quote, "
            "and the state check allows changes to that test only.") in t


def test_tester_skill_and_agent_carry_the_rewrite_rule():
    for p in (SKILL, AGENT):
        assert TESTER_RULE in flat(p), p


def test_caller_runs_stale_as_its_own_call_before_the_suite_dispatch():
    for p in (RUN, ADOPT):
        t = flat(p)
        assert STALE_CALL in t, p
        assert "`prd-build-check-exit=1` prints one `stale <T-id> <test path>:" in t and "`Rewrite: <T-id>`" in t, p
        assert "`prd-build-check-exit=2` is a tool error, never \"nothing stale\": stop the dispatch" in t, p
    assert RUN.read_text().index(STALE_CALL.split(" --tids")[0]) < RUN.read_text().index("Save the tester's whole report")


def test_caller_red_flag_in_both_caller_files():
    for p in (RUN, ADOPT):
        assert RED_FLAG in flat(p) or RED_FLAG.lower() in flat(p).lower(), p
