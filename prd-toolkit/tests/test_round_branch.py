"""Every builder round on a round branch the caller cuts, and a `verified` with no build-gate test (spec section 17,
fixes 6 and 7): pinned lines in running-a-build.md, the building-from-prds skill and the prd-builder agent."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/building-from-prds/SKILL.md"
RUN = ROOT / "skills/building-from-prds/running-a-build.md"
AGENT = ROOT / "agents/prd-builder.md"

NO_ISOLATION = ("Never dispatch the builder with `isolation: worktree`: it cuts from the main checkout's HEAD, not from "
                "the build branch.")
FIRST_CHECK = ("Run `git merge-base --is-ancestor <Base> HEAD` and `git branch --show-current`, each its own Bash call; "
               "if the first fails or the second is not the `Branch:` line, change nothing and report "
               "`QUESTIONS: worktree is not on the build branch`.")
PROMPT_LINES = "Scripts: <scripts directory, as an absolute path>\nBase: <sha>\nBranch: prd-round/<area>-<n>\n"
CLOSE_LINE = "<ID>: verified with no build-gate test; its proof is the deploy gate at /prd-deploy"
RED_FLAG = "Dispatching the builder with `isolation: worktree`, or letting it commit on the build branch"
DIFF_CALL = ("uv run --script <scripts>/prd_build_check.py docs/prd/<slug> --diff <base>..prd-round/<area>-<n> "
             "--sources <SNAP>/sources-<n>.txt; "
             'echo "prd-build-check-exit=$?"')


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def step(n: int) -> str:
    return flat(RUN).split(f"{n}. **", 1)[1].split(f"{n + 1}. **", 1)[0]


def test_step3_runs_the_round_in_order():
    s3 = step(3)
    order = ["git status --porcelain --untracked-files=all", "git switch -c prd-round/<area>-<n>",
             "`prd-toolkit:prd-builder` with no `isolation`", "git switch <build branch>", DIFF_CALL,
             "git merge --ff-only prd-round/<area>-<n>", "git branch -d prd-round/<area>-<n>"]
    at = [s3.find(s) for s in order]
    assert -1 not in at, [s for s, i in zip(order, at) if i == -1]
    assert at == sorted(at), at


def test_step3_names_the_round_branch_and_its_number():
    s3 = step(3)
    assert "`<n>` is the round number counted from 1 for the build (a `--fixes` build too)" in s3
    assert ("An existing branch of that name takes the next free `<n>`: run `git branch --list 'prd-round/<area>-*'`, its "
            "own call, and take one more than the highest `<n>` it lists.") in s3
    assert ("A tester round (a test-misread round or a tester-only round) cuts no round branch and does not advance "
            "`<n>`.") in s3


def test_step3_never_dispatches_with_isolation():
    assert NO_ISOLATION in step(3)
    assert flat(RUN).count("isolation: worktree") == 1  # only in the sentence that forbids it


def test_no_isolation_branch_is_left_in_running_a_build():
    t = flat(RUN).lower()
    assert "without worktree isolation" not in t
    assert "with worktree isolation" not in t
    assert "offers no worktree isolation" not in t
    assert "<builder branch>" not in flat(RUN)


def test_a_failed_round_merges_nothing_and_keeps_its_branch():
    t = flat(RUN)
    assert ("A failed round (a failed check, a UNIT failure, a stop) merges nothing. Its branch is kept and named in "
            "the report, and the next round cuts a new branch from the unchanged build branch.") in t
    assert "never delete one with `-D`" in t


def test_the_tester_write_follows_the_merged_round():
    s3 = step(3)
    assert "Dispatch both in one message" not in flat(RUN)
    assert "The tester's `write` dispatch follows the merged round, never in the same message as the builder" in s3


def test_the_prompt_lines_in_both_files():
    for p in (RUN, SKILL):
        assert PROMPT_LINES in p.read_text(encoding="utf-8"), p
    assert "`Base:` and `Branch:`" in flat(AGENT)


def test_the_builders_first_check_comes_before_rule_1():
    for p in (SKILL, AGENT):
        assert FIRST_CHECK in flat(p), p
    s = flat(SKILL)
    assert s.index(FIRST_CHECK) < s.index("1. **The pack first.**")
    a = flat(AGENT)
    assert a.index(FIRST_CHECK) < a.index("Run the implement pack first")


def test_the_agent_names_no_worktree_of_its_own():
    a = AGENT.read_text(encoding="utf-8")
    assert "isolation worktree" not in a and "own worktree" not in a
    assert "round branch" in a


def test_the_close_names_a_verified_block_with_no_build_gate_test():
    close = flat(RUN).split("8. **Close.**", 1)[1].split("## Prompts", 1)[0]
    assert f"`{CLOSE_LINE}`" in close
    assert "each block whose IDs have no unit and no build-gate T-id" in close


def test_the_caller_red_flag():
    caller = flat(SKILL).split("**The caller:**", 1)[1]
    assert RED_FLAG in caller


def test_the_builder_question_is_not_a_prd_gap():
    s4 = step(4)
    assert re.search(r"`QUESTIONS: worktree is not on the build branch` is not a PRD gap", s4)


# --- fix round 1 ---

def test_the_cut_is_checked_before_each_dispatch():
    s3 = step(3)
    cut = s3.index("git switch -c prd-round/<area>-<n>")
    dispatch = s3.index("`prd-toolkit:prd-builder` with no `isolation`")
    check = s3.find("`git branch --show-current` and `git rev-parse HEAD`", cut)
    assert cut < check < dispatch
    between = s3[cut:dispatch]
    assert "must print the new round branch" in between and "the `<base>` its prompt carries as `Base:`" in between
    assert "On a mismatch, the build stops and reports both values." in between
    assert "before the next one, run" not in step(4)


def test_a_refused_switch_back_stops_as_a_dirty_tree():
    s3 = step(3)
    back = s3.index("git switch <build branch>")
    diff = s3.index(DIFF_CALL)
    rule = s3[back:diff]
    assert "If it refuses, the round fails and the build stops as a dirty tree" in rule
    assert "git status --porcelain --untracked-files=all" in rule
    assert "Never `--force`, and never discard the edit." in rule


def test_no_double_bullet():
    assert "- - **" not in RUN.read_text(encoding="utf-8")
