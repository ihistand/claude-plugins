"""changing-prds calls prd_change.py for the bookkeeping, and /prd-change --review runs reviewing-a-change.md
(spec 0.8.1 §4 and §6)."""
import json
import re
from pathlib import Path

from prdlint import change

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/changing-prds/SKILL.md"
REVIEW = ROOT / "skills/changing-prds/reviewing-a-change.md"
COMMAND = ROOT / "commands/prd-change.md"
SPEC = ROOT.parent / "docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.1-design.md"
GATE = '; echo "prd-change-exit=$?"'


def flat(text: str) -> str:
    return " ".join(text.split())


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a + len(start))]


def step(n: int) -> str:
    t = flat(SKILL.read_text(encoding="utf-8"))
    heads = {0: "0. **Check the PRD", 1: "1. **Restate the change**", 2: "2. **Edit the PRD.**",
             3: "3. **Bump the version**", 4: "4. **Lint and dry run.**", 5: "5. **Approval, then commit.**"}
    return between(t, heads[n], heads[n + 1] if n < 5 else "## Red Flags")


def commands(text: str, script: str) -> list[str]:
    """Every backticked command that runs `script`, and every line of a bash block that does."""
    spans = re.findall(r"`(uv run --script [^`]*" + re.escape(script) + r"[^`]*)`", flat(text))
    blocks = [ln.strip() for b in re.findall(r"```bash\n(.*?)```", text, re.S) for ln in b.splitlines()
              if script in ln]
    return spans + blocks


# --- the skill: one Bash call per subcommand, with the exit gate ---

def test_skill_runs_each_prd_change_subcommand_as_its_own_gated_call():
    text = SKILL.read_text(encoding="utf-8")
    cmds = commands(text, "prd_change.py")
    for sub in ("ids next", "bump", "record", "approve"):
        mine = [c for c in cmds if f"prd_change.py {sub} " in c]
        assert mine, sub
        for c in mine:
            assert c.startswith("uv run --script <scripts>/prd_change.py "), c
            assert c.endswith(GATE), c
            assert "&&" not in c and "|" not in c.replace("prd-change-exit", ""), c
            assert "CLAUDE_PLUGIN_ROOT" not in c, c


def test_skill_states_the_exit_gate():
    t = flat(SKILL.read_text(encoding="utf-8"))
    assert "`prd-change-exit=`" in t
    gate = between(t, "The `prd-change-exit=` value", ".")
    for s in ("`0`", "`1`", "refused", "`2`", "usage"):
        assert s in gate, s


def test_skill_stops_on_a_vendored_copy_without_prd_change():
    t = flat(SKILL.read_text(encoding="utf-8"))
    assert "When `.prd-toolkit/` holds no `prd_change.py`, the vendored copy predates 0.8.1: stop" in t


def test_step_2_takes_each_new_id_from_ids_next():
    s = step(2)
    assert "prd_change.py ids next docs/prd/<slug> <kind>" in s
    for kind in ("`FR`", "`NFR`", "`UJ`", "`AC-<nnn>`", "`T-<nnn>`"):
        assert kind in s, kind
    assert "never count" in s


def test_step_3_runs_bump_then_record_and_the_model_decides_judgment():
    s = step(3)
    assert s.index("prd_change.py bump docs/prd/<slug> --base HEAD") < s.index("prd_change.py record docs/prd/<slug> --base HEAD")
    for needle in ("`needs judgment`", "Version rule", "`--bump`", "`patch`, `minor` or `major`",
                   "refused: the diff needs", "a needs-judgment bump must be decided first",
                   "replaces its own `pending` row", "never edit the version"):
        assert needle in s, needle


def test_step_4_writes_the_verdict_after_lint_and_dry_run():
    s = step(4)
    assert s.index("prd-lint-exit=") < s.index(".prd-review.json")
    assert "reviewing-a-change.md" in s and "`ready`" in s



def test_step_4_puts_an_error_entrys_refs_in_the_verdict():
    s = step(4)
    assert ("For a change made for an `errors.md` entry, add `\"refs\": \"<changed IDs>, E-nnn\"` to the verdict: the "
            "inbox's approval passes it to `approve` as `--refs`. Leave `refs` out for any other change.") in s
    assert s.index("`blockers` `[]`") < s.index('`\"refs\"')


def test_step_5_says_the_inbox_approval_carries_the_verdicts_refs():
    s = step(5)
    assert ("An outcome `approve`: the inbox already ran `prd_change.py approve` with the owner's reply, step 4's record "
            "and the verdict's `refs` (step 4 sets it for a change made for an `errors.md` entry: "
            "`'<changed IDs>, E-nnn'`), and made the approval commit.") in s


def test_step_5_approves_through_the_script_with_the_reply_verbatim():
    s = step(5)
    approve = next(c for c in commands(SKILL.read_text(encoding="utf-8"), "prd_change.py") if " approve " in c)
    assert "--reply '<the reply, verbatim>'" in approve and "--dry-run '<the dry-run record>'" in approve
    assert "`'\\''`" in s
    assert "`--refs" in s and "E-nnn" in s
    assert "Change-set:" in s


def test_version_rule_table_equals_bump_rules():
    text = SKILL.read_text(encoding="utf-8")
    rule = between(text, "## Version rule", "## ID rules")
    head = "| Item | Level |\n|---|---|\n"
    assert head in rule
    rows = rule.split(head, 1)[1].split("\n\n", 1)[0].strip().splitlines()
    cells = [tuple(c.strip() for c in r.strip().strip("|").split("|")) for r in rows]
    assert cells == [(item, level) for item, level in change.BUMP_RULES]


def test_skill_no_longer_says_bump_ignores_block_status():
    text = flat(SKILL.read_text(encoding="utf-8"))
    sentence = text.split("It ignores", 1)[1].split(". The highest level wins", 1)[0]
    assert "block `Status:`" not in sentence and "`Source:` lines" in sentence


def test_skill_points_at_review_mode():
    t = flat(SKILL.read_text(encoding="utf-8"))
    assert "/prd-change --review <dir>" in t and "reviewing-a-change.md" in t


def test_id_rules_name_ids_next_and_uj():
    t = flat(between(SKILL.read_text(encoding="utf-8"), "## ID rules", "## The five steps"))
    assert "`ids next`" in t and "UJ" in t and "two digits" in t


# --- review mode ---

def review_rule_1() -> str:
    paragraphs = REVIEW.read_text(encoding="utf-8").split("\n\n")
    assert paragraphs[0].startswith("# "), paragraphs[0]
    return flat(paragraphs[1])


def test_review_first_rule_is_edit_nothing():
    r1 = review_rule_1()
    assert r1.startswith("**Rule 1: edit nothing.**"), r1
    for s in ("no Write", "no Edit", "no Bash that writes", "outside the dry-run directory", "`.prd-review.json`"):
        assert s in r1, s


def test_review_refuses_an_edit_asked_for_during_the_review():
    t = flat(REVIEW.read_text(encoding="utf-8"))
    assert "just fix the AC while you review it" in t
    assert "not edited" in t


def test_review_runs_digest_head_and_impact():
    text = REVIEW.read_text(encoding="utf-8")
    t = flat(text)
    assert commands(text, "prd_change.py digest") and all(c.endswith(GATE) for c in commands(text, "prd_change.py digest"))
    assert "`git rev-parse HEAD`" in t
    impact = commands(text, "prd_links.py impact")
    assert impact and all(c.endswith('; echo "prd-links-exit=$?"') for c in impact)
    assert "When `links.md` has Consumers" in t
    bump = commands(text, "prd_change.py bump")
    assert bump and all(c.endswith(GATE) for c in bump)
    assert not commands(text, "prd_change.py record") and not commands(text, "prd_change.py approve")


def _verdict(text: str) -> dict:
    block = next(b for b in re.findall(r"```json\n(.*?)```", text, re.S) if '"kind": "review"' in b)
    return json.loads(block)


def test_review_verdict_keys_equal_the_spec():
    spec = SPEC.read_text(encoding="utf-8")
    want = _verdict(spec[spec.index("## 6. Review mode"):spec.index("## 7.")])
    got = _verdict(REVIEW.read_text(encoding="utf-8"))
    got.pop("base")  # 0.8.3's optional key, which the 0.7 spec predates
    assert list(got) == list(want)
    for key in ("impact", "bump", "dry_run"):
        assert list(got[key]) == list(want[key]), key
    assert got["interface"] == 1 and got["kind"] == "review"


def test_review_states_ready_and_the_client_order():
    t = flat(REVIEW.read_text(encoding="utf-8"))
    for s in ("`ready` is `false`", "lint", "impact", "judgment", "open question", "`blockers`"):
        assert s in t, s
    order = between(t, "The order a client runs", ".")
    assert order.index("bump") < order.index("review") < order.index("record") < order.index("lint")


def test_command_routes_review_to_review_mode():
    t = flat(COMMAND.read_text(encoding="utf-8"))
    assert COMMAND.read_text(encoding="utf-8").startswith("---\ndescription: ")
    assert "`--review <dir>`" in t and "skills/changing-prds/reviewing-a-change.md" in t
    assert "Invoke the prd-toolkit:changing-prds skill and follow it exactly" in t


# --- fix round 1 (R16 to R18 and the minors) ---

RUN_SET = ROOT / "skills/coordinating-prds/running-a-change-set.md"


def red_flags(path: Path) -> str:
    return flat(between(path.read_text(encoding="utf-8"), "## Red Flags", "## Common Rationalizations"))


def test_r16_the_block_status_is_edited_and_record_writes_section_11():
    s = step(2)
    assert "in the block's `Status:` line; `record` (step 3) writes the §11 index from it" in s
    assert "in the block and the index" not in s
    t = flat(SKILL.read_text(encoding="utf-8"))
    regression = between(t, "**A regression patch.**", "**A test case or contract corrected")
    corrected = between(t, "**A test case or contract corrected", "## ID rules")
    for para in (regression, corrected):
        assert "returns to `approved` (its `Status:` line; `record` writes its §11 row)" in para, para
    assert "every §11 row's status from its block's `Status:` line" in step(3)


def test_r17_the_ids_cell_names_each_requirement():
    s = step(3)
    assert "and the requirement each AC and T-id belongs to" in s
    assert "When it leaves out a UJ, FR, NFR, AC or T-id step 1 listed" in s


def test_r18_no_verdict_inside_a_change_set():
    s = step(4)
    assert "Inside a change set (step 2), write no `.prd-review.json`" in s
    assert "the change set's one approval" in s
    assert "`.prd-review.json` written inside a change set" in red_flags(SKILL)
    three = flat(between(RUN_SET.read_text(encoding="utf-8"), "3. **One approval.**", "4. **Build in order.**"))
    assert "replaces the row's trailing `; pending` with that member's dry-run record" in three
    assert "`changing-prds` step 4" in three


def test_red_flag_for_a_loop_function_or_variable():
    assert "A loop, a shell function or a variable in a `prd_change.py` call" in red_flags(SKILL)


def test_change_text_is_one_line_without_a_pipe_up_front():
    t = flat(between(SKILL.read_text(encoding="utf-8"), "The bookkeeping, `prd_change.py`", "## The gap rule"))
    assert "`record --change` takes one line with no `|`" in t


def test_review_red_flag_allows_the_verdict_redirect_and_step_7_reads_level():
    assert "a `>` to any path but the verdict" in red_flags(REVIEW)
    seven = flat(between(REVIEW.read_text(encoding="utf-8"), "7. **Dry run**", "8. **Write the verdict**"))
    assert "whose test case's `level:` is not `unit`" in seven
    assert "whose level is not `unit`" not in seven


def test_own_call_means_nothing_else_in_it():
    t = flat(between(SKILL.read_text(encoding="utf-8"), "The bookkeeping, `prd_change.py`", "## The gap rule"))
    assert "Its own call holds that command and that echo and nothing else" in t
    for s in ("no `cd`", "no state check or cleanup folded in", "no loop, no shell function and no variable"):
        assert s in t, s


# --- final review: three wording fixes ---

def test_the_variable_rule_is_about_the_path():
    t = flat(between(SKILL.read_text(encoding="utf-8"), "The bookkeeping, `prd_change.py`", "## The gap rule"))
    assert "no loop, no shell function and no variable in the path; the script path is typed out" in t


def test_the_hand_edit_red_flag_carries_the_change_set_carve_out():
    flags = red_flags(SKILL)
    assert ("A `version:`, `updated:`, §14 row or §11 row typed by hand, or an edit to a row `record` wrote "
            "(inside a change set, the dry-run record in place of its `pending` is the one hand edit step 5 allows)") in flags
    assert "(the one hand edit of a row `record` wrote)" in step(5)


def test_the_change_set_deletes_any_stale_verdict():
    s = step(5)
    assert "delete any stale `.prd-review.json`" in s
    assert "delete `.prd-review.json`" not in s
