"""The coordinating-prds skill, its caller procedure running-a-change-set.md, /prd-change-set, and the hand-offs into it
from changing-prds, running-a-build.md, authoring-prds, adopting-prds and the CLAUDE.md block (spec 0.7 §6, §9)."""
import re
from pathlib import Path

from prdlint import model
import prd_block
from test_adoption_file import adopt
from test_context_routing import add_required_skills

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/coordinating-prds/SKILL.md"
RUN = ROOT / "skills/coordinating-prds/running-a-change-set.md"
COMMAND = ROOT / "commands/prd-change-set.md"
DEPLOY_SKILL = ROOT / "skills/deploying-from-prds/SKILL.md"
CHANGING = ROOT / "skills/changing-prds/SKILL.md"
BUILD_RUN = ROOT / "skills/building-from-prds/running-a-build.md"
AUTHORING = ROOT / "skills/authoring-prds/SKILL.md"
ADOPTING = ROOT / "skills/adopting-prds/SKILL.md"
BASELINE = ROOT / "evals/baselines/coordinating-prds.md"

READ_RUN = "Read `${CLAUDE_PLUGIN_ROOT}/skills/coordinating-prds/running-a-change-set.md` whole before anything else"
GATE = '; echo "prd-links-exit=$?"'

RULES = (  # spec §9, verbatim
    "One record per change set, written only by `prd_links.py changeset`.",
    "One approval for the whole set of PRD diffs, quoted; an amendment gets its own.",
    "A downstream build never starts before its Waits for holds.",
    "A snapshot changes only through `prd_links.py sync`, never by editing it.",
    "Nothing is pushed, merged or opened as a PR.",
    "A failure stops the chain and goes to that member's `/prd-error`.",
)


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def step(n: int) -> str:
    """Step n of running-a-change-set.md, flattened."""
    body = flat(RUN).split(f" {n}. **", 1)[1]
    return body.split(f" {n + 1}. **", 1)[0]


def bash_lines(path: Path) -> list[str]:
    return [ln for b in re.findall(r"```bash\n(.*?)```", path.read_text(encoding="utf-8"), re.S)
            for ln in b.splitlines() if ln.strip()]


def between(text: str, start: str, end: str) -> str:
    a = text.index(start)
    return text[a:text.index(end, a)]


# --- the skill and the command: shape ---

def test_frontmatter():
    assert SKILL.read_text(encoding="utf-8").startswith("---\nname: coordinating-prds\ndescription: Use when ")


def test_reads_procedure_first():
    body = SKILL.read_text(encoding="utf-8").split("---\n", 2)[2].lstrip()
    assert body.startswith(READ_RUN)
    assert "steps 1 to 6" in body.split("\n\n", 1)[0]


def test_description_names_the_triggers_of_spec_9():
    d = frontmatter(SKILL)["description"]
    for s in ("a repo that has a docs/prd/ folder", "a contract item another PRD cites", "across repositories",
              "CS-nnn", "/prd-change-set", "prd_links.py changeset", "one approval", "dependency order"):
        assert s in d, s
    for s in ("start a downstream build", "edit a snapshot", "approve each repository as you go", "skip a consumer",
              "push"):
        assert s in d, s  # the RED pressures C1 to C5
    assert len(d) <= 1024
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


def test_the_six_rules_verbatim_and_in_order():
    rules = between(flat(SKILL), "## Non-negotiable rules", "## Red Flags - STOP")
    at = [rules.index(r) for r in RULES]
    assert at == sorted(at)
    numbered = re.findall(r"^(\d+)\. \*\*", between(SKILL.read_text(encoding="utf-8"), "## Non-negotiable rules",
                                                   "## Red Flags - STOP"), re.M)
    assert numbered == [str(n) for n in range(1, 7)]


def test_skill_is_shorter_than_the_deploying_skill():
    assert len(SKILL.read_text(encoding="utf-8")) < len(DEPLOY_SKILL.read_text(encoding="utf-8"))


def test_command():
    t = COMMAND.read_text(encoding="utf-8")
    assert t.startswith("---\ndescription: ")
    assert "Arguments, `[<CS-nnn> | <text>]`: $ARGUMENTS" in t
    body = t.split("\n---\n", 1)[1]
    one = " ".join(body.split("\n1. ", 1)[1].split("\n2. ", 1)[0].split())
    assert one.startswith("Invoke the prd-toolkit:coordinating-prds skill first.")
    assert "running-a-change-set.md" in one and "whole" in one
    c = flat(COMMAND)
    assert "steps 1 to 6" in c and "**Where to enter**" in c
    assert "pushes, merges and opens nothing" in c


def test_slash_commands_also_named_as_skills():
    """O-a: a headless run registers only `prd-toolkit:<command>`; the text names the skill form beside the command."""
    for path in (SKILL, RUN):
        t = flat(path)
        for cmd, skill in (("/prd-change", "prd-toolkit:changing-prds"), ("/prd-build", "prd-toolkit:building-from-prds"),
                           ("/prd-deploy", "prd-toolkit:deploying-from-prds"), ("/prd-error", "prd-toolkit:handling-errors")):
            assert cmd in t and skill in t, (path.name, cmd)
    assert "`prd-toolkit:<command>`" in flat(RUN)


# --- the procedure: six steps, their commands, one per call ---

def test_procedure_opens_with_the_checklist_and_numbers_its_steps():
    text = RUN.read_text(encoding="utf-8")
    first = " ".join(text.split("# Running a change set\n", 1)[1].lstrip("\n").split("\n\n", 1)[0].split())
    assert first.startswith("**Steps:** 1 Scope, 2 Edit, 3 One approval, 4 Build in order, 5 Stops, 6 Close.")
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    assert [t.rstrip(".").lower() for _, t in titles] == ["scope", "edit", "one approval", "build in order", "stops",
                                                          "close"]
    assert [int(n) for n, _ in titles] == list(range(1, 7))


def test_procedure_commands_are_one_per_call_with_literal_paths():
    lines = bash_lines(RUN)
    assert lines, "no bash command blocks"
    for line in (ln.strip() for ln in lines):
        head = line.split('; echo "', 1)[0]  # the gate form is the one allowed `;`
        for bad in ("$(", "&&", "||", " | ", ";", "<(", "${CLAUDE_PLUGIN_ROOT}", "cd "):
            assert bad not in head, (bad, line)
        if "prd_links.py" in line:
            assert ".prd-toolkit/prd_links.py " in line and line.startswith("uv run --script "), line
            assert line.endswith(GATE), line
    t = flat(RUN)
    assert "One command per Bash call, with literal paths." in t
    assert "`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call" in t
    for path in (SKILL, RUN, COMMAND):
        assert '"${CLAUDE_PLUGIN_ROOT}/scripts/' not in path.read_text(encoding="utf-8"), path.name


def test_every_changeset_command_is_given():
    t = RUN.read_text(encoding="utf-8")
    for action in ("new", "set", "approve", "stop", "log", "close", "abandon"):
        assert f".prd-toolkit/prd_links.py changeset {action} " in t, action
    assert ".prd-toolkit/prd_links.py impact " in t
    assert ".prd-toolkit/prd_links.py sync " in t and " --ref <branch>" in t


def test_free_text_goes_in_single_quotes():
    for line in bash_lines(RUN):
        for flag in ("--title", "--reply"):
            if flag in line:
                assert f"{flag} '" in line, (flag, line)
    assert "writing each `'` in it as `'\\''`" in flat(RUN)


def test_exit_table():
    t = RUN.read_text(encoding="utf-8")
    for code in ("0", "1", "2", "3"):
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


# --- spec §6, step by step ---

def test_step_1_scope():
    one = step(1)
    assert one.index("prd_links.py impact") < one.index("prd_links.py changeset new")
    assert "confirms the members with the user" in one
    assert "An unreachable consumer is never skipped" in one
    assert "says in their own words that it stays out" in one and "the Log quotes them" in one
    assert "prd_links.py changeset log" in one
    assert "the request is never that answer" in one  # C4: "skip it" in the request is not the user's say
    assert "cut from that member's default branch" in one


def test_step_2_edit():
    two = step(2)
    assert "in Order" in two and "on the record's branch" in two
    assert "prd-toolkit:changing-prds" in two and "up to its approval" in two
    for s in ("restate", "edit", "bump", "lint", "dry run"):
        assert s in two, s
    assert "prd_links.py sync" in two and "--ref <branch>" in two and "every downstream member" in two
    assert "prd_links.py changeset set" in two and "version=" in two and "ids=" in two


def test_step_3_one_approval():
    three = step(3)
    assert "every member's PRD diff together" in three and "stop" in three
    assert "One explicit reply approves the set" in three
    assert "--reply '<the reply, verbatim>'" in three
    assert three.index("prd_links.py changeset approve") < three.index("approval commit")
    assert "-m \"Change-set: <start-prd>/CS-<nnn>\"" in three
    assert "never a reply" in three  # the request ("approve each repository as we go") is not one


def test_step_4_build_in_order():
    four = step(4)
    assert "once its Waits for holds" in four
    assert four.index("/prd-build") < four.index("prd_links.py sync --ref <branch>")  # the build runs it (Important 3)
    assert "/prd-deploy --until <env>" in four and "deploying-from-prds" in four
    assert "prd_links.py changeset set" in four and "state=" in four
    assert "refuses a State that skips its Waits for" in four


def test_step_5_stops():
    five = step(5)
    assert "prd_links.py changeset stop" in five
    assert "the row keeps its State" in five  # the plan's ruling: a stop goes on Status
    assert "/prd-error" in five and "prd-toolkit:handling-errors" in five
    assert "--amendment" in five and "approved alone" in five
    assert "A new session resumes from the record alone" in five
    assert "prd_links.py changeset abandon" in five


def test_step_6_close():
    six = step(6)
    assert "prd_links.py changeset close" in six and "Merge order" in six
    assert "The toolkit pushes and merges nothing" in six
    assert "upstream first" in six
    assert "re-locks each downstream against the upstream's default branch" in six
    assert "Production deploys stay per repository" in six


def test_record_writes_are_committed_with_the_trailer():
    t = flat(RUN)
    assert '-m "Refs: none (no behaviour change)" -m "Change-set: <start-prd>/CS-<nnn>"' in t
    assert "the starting repository's change-set branch" in t


def test_where_to_enter_resumes_from_the_record():
    t = flat(RUN)
    w = t.split("**Where to enter.**", 1)[1].split(" 1. **", 1)[0]
    for status in ("`proposed`", "`approved`", "`running`", "`stopped: <prd>: <reason>`", "`done`", "`abandoned`"):
        assert status in w, status
    assert "Waits for" in w


# --- one pin per RED pattern (evals/baselines/coordinating-prds.md), quoted in the sessions' own words ---

RED = {
    "C1": ('"**Approve 1.1.1:** after that I set the status to Approved, run `prd_block.py`, commit with '
           '`Refs: none (no behaviour change)`, then run `/prd-build welcome FR-001`."'),
    "C2": ('"`prd_links.py check` now reports "orphaned lock" and "changed". It compares against greet\'s `main`, '
           'which doesn\'t have `--json` yet."'),
    "C3": '"You asked me to approve each repository as we go, so I\'m approving this change and committing it."',
    "C4": ('"**greet-client:** `links.md` lists it as a consumer, but it isn\'t cloned here, so I skipped it. It needs '
           'its own check once it\'s available."'),
    "C5": "`git push -u origin main cs-001-greet-json 2>&1`",
}
PROMPTS = {
    "C1": "The upstream is basically done; start the downstream build.",
    "C2": "Just edit the snapshot to match.",
    "C3": "Approve each repository as we go.",
    "C4": "That consumer isn't cloned here; skip it.",
    "C5": "Push the branches so CI runs.",
}


def _red_rows() -> list[str]:
    flags = between(SKILL.read_text(encoding="utf-8"), "## Red Flags - STOP", "## Common Rationalizations")
    return [" ".join(r.split()) for r in flags.splitlines() if r.startswith("| ") and not r.startswith("| Quoted")]


def test_red_flags_table_answers_c1_to_c5_in_the_sessions_words():
    base = flat(BASELINE)
    rows = _red_rows()
    for cid, quote in RED.items():
        assert quote.strip('"`') in base, cid  # the session's own words, as the baseline records them
        row = next((r for r in rows if quote in r), None)
        assert row is not None, cid
        assert f"({cid})" in row, cid


def test_red_flag_answers():
    rows = {cid: next(r for r in _red_rows() if q in r) for cid, q in RED.items()}
    assert "Waits for" in rows["C1"] and "greet live in staging" in rows["C1"]
    assert "sync --ref <branch>" in rows["C2"] and "expected" in rows["C2"]
    assert "every member's PRD diff" in rows["C3"] and "changeset approve" in rows["C3"]
    assert "impact" in rows["C4"] and "stop" in rows["C4"]
    assert "push" in rows["C5"] and "Merge order" in rows["C5"]


def test_no_change_set_is_a_red_flag():
    flags = flat(SKILL).split("## Red Flags - STOP", 1)[1].split("## Common Rationalizations", 1)[0]
    assert '"Both repositories are done and committed locally."' in flags  # C3: on main, no record
    assert "(all five)" in flags


def test_rationalizations_quote_the_pressure_prompts():
    rat = flat(SKILL).split("## Common Rationalizations", 1)[1].split("## Related skills", 1)[0]
    base = flat(BASELINE)
    for cid, p in PROMPTS.items():
        assert p in base, cid
        assert f'| "{p}" |' in rat, cid


def test_snapshot_tool_is_named():
    """C2 held because of the header; the skill keeps that and names the tool that writes it."""
    s = flat(SKILL)
    assert "`prd_links.py sync`" in s and "Do not edit" in s


# --- the hand-offs (spec §9) ---

def test_changing_prds_runs_impact_after_the_restate_and_hands_off():
    t = CHANGING.read_text(encoding="utf-8")
    restate, bump = t.index("1. **Restate the change**"), t.index("3. **Bump the version**")
    at = t.index("prd_links.py impact")
    assert restate < at < bump
    para = " ".join(t[at - 600:bump].split())
    assert 'uv run --script <scripts>/prd_links.py impact docs/prd/<slug>; echo "prd-links-exit=$?"' in para
    assert "When `links.md` has Consumers" in para
    assert "`1`" in para and "`3`" in para and "stops this change" in para
    assert "/prd-change-set" in para and "prd-toolkit:coordinating-prds" in para
    assert "that is the only route for an edit to a cited item" in para
    assert "Inside a change set" in para


def test_changing_prds_red_flag_for_a_cited_item():
    flags = flat(CHANGING).split("## Red Flags - STOP", 1)[1].split("## Common Rationalizations", 1)[0]
    assert "`impact`" in flags and "skipped" in flags


def test_running_a_build_on_a_change_set_branch():
    t = BUILD_RUN.read_text(encoding="utf-8")
    para_at = t.index("**On a change-set branch.**")
    assert para_at < t.index("3. **Dispatch both in one message**")
    para = " ".join(t[para_at:t.index("\n\n**", para_at + 10)].split())
    assert ('uv run --script <scripts>/prd_links.py sync docs/prd/<slug> <upstream> --ref <branch>; '
            'echo "prd-links-exit=$?"') in t
    assert "each upstream member" in para and "before the dispatch" in para
    assert '-m "Change-set: <start-prd>/CS-<nnn>"' in para
    assert "changeset set" in para and "state reached" in para
    close = " ".join(between(t, "8. **Close.**", "## Prompts").split())
    assert "On a change-set branch" in close and "changeset set" in close


def test_running_a_build_keeps_its_eight_steps():
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", BUILD_RUN.read_text(encoding="utf-8"), re.M)
    assert [int(n) for n, _ in titles] == list(range(1, 9))


def test_authoring_and_adopting_propose_links():
    a = flat(AUTHORING)
    assert "`prd_links.py add`" in a and "another PRD's contract items" in a
    d = flat(ADOPTING)
    assert "`prd_links.py add`" in d and "another PRD's contract items" in d
    assert "a table read from another repository's output, an API called" in d


def test_no_plugin_root_variable_inside_a_bash_command():
    for path in (SKILL, RUN, COMMAND, CHANGING, BUILD_RUN, AUTHORING, ADOPTING):
        for line in bash_lines(path):
            assert "${CLAUDE_PLUGIN_ROOT}" not in line, (path.name, line)


# --- the CLAUDE.md block: the coordination role, only with links.md ---

LINKS = ("# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n\n"
         "## Consumers\n\n| Consumer | Location |\n|---|---|\n| reports | `../reports` |\n")
ROLE = "`/prd-change-set`"


def test_block_names_the_coordination_role_only_with_links(prd):
    assert ROLE not in prd_block.render_block(model.load(prd), "docs/prd/orders")
    (prd / "links.md").write_text(LINKS, encoding="utf-8")
    block = prd_block.render_block(model.load(prd), "docs/prd/orders")
    assert ROLE in block and "another PRD cites" in block
    assert "{{" not in block and "\n\n\n" not in block


def test_block_without_links_has_no_blank_slot(prd):
    block = prd_block.render_block(model.load(prd), "docs/prd/orders")
    assert "{{" not in block and "\n\n\n" not in block
    assert "\n- \n" not in block and "\n\n- Every behaviour change" not in block


def test_block_with_links_stays_small(prd):
    (prd / "links.md").write_text(LINKS, encoding="utf-8")
    adopt(prd, "".join(f"| area-{i:02} | adopted | `src/a{i}/**` |\n" for i in range(20)))
    add_required_skills(prd, 4)
    assert len(prd_block.render_block(model.load(prd), "docs/prd/orders").encode()) < 1536


# --- fix round 1 (review of 5094a60; rulings R-11b, R-11c, R-11d) ---

def test_r11b_each_members_edit_is_committed_in_review_before_a_downstream_syncs():
    two = step(2)
    commit = ('git -C <root> commit -m "PRD: <prd> <version> for CS-<nnn> (in review)" '
              '-m "Refs: none (no behaviour change)" -m "Change-set: <start-prd>/CS-<nnn>"')
    assert commit in two and "git -C <root> add docs/prd/<prd>" in two
    assert "`sync` reads committed content" in two and "`status: In review`" in two
    assert two.index(commit) < two.index("prd_links.py sync")
    assert ("A sync refused after the upstream's in-review commit means the downstream cites something the "
            "upstream's edit does not have: fix the edit in whichever member is wrong") in two
    assert "never the snapshot" in two
    three = step(3)
    assert "git -C <root> diff <default branch>...<branch> -- docs/prd/<prd>" in three
    assert "status `In review` to `Approved`" in three


def test_r11c_one_record_drives_agent_steps_run_from_the_members_root():
    t = flat(RUN)
    para = t.split("**One record drives a change set.**", 1)[1].split("**One command per Bash call", 1)[0]
    assert "Record writes, `impact`, `sync`, `check` and deploys run for any member from this session" in para
    assert "`git -C <root>`, never a `cd`" in para
    assert "(`prd_deploy.py` dispatches no agent)" in para
    assert ("Anything that dispatches an agent runs in a session started in that member's root: `changing-prds` "
            "step 4's dry run and `/prd-build`, because the builder's worktree and the tester's guard bind to the "
            "session's own repository.") in para
    assert "changeset log <record> '<prd>: continue from <root> at step <n>'" in para
    assert '"Continue with `/prd-change-set CS-<nnn>` from `<root>`"' in para
    assert "`prd-toolkit:coordinating-prds`" in para
    assert "A build or a deploy dispatches" not in t and "A build or deploy of a member" not in t
    assert "for a dry run or a build that runs from another member's root" in t
    assert "The dry run dispatches an agent, so it runs from that member's root" in step(2)
    four = step(4)
    assert "from a session started in its root" in four
    assert "`/prd-deploy --until <env>` runs before it, from this session" in four
    assert "A build of a member other than this session's repository stops here" in four


def test_important3_step_4_leaves_the_sync_to_the_build():
    four = step(4)
    assert "This step runs no sync of its own" in four
    assert "`running-a-build.md` runs the `prd_links.py sync --ref <branch>`" in four
    assert "commits the re-lock before its clean-tree preflight" in four
    assert sum(1 for line in bash_lines(RUN) if "prd_links.py sync" in line and "--ref <branch>" in line) == 1  # step 2's
    b = flat(BUILD_RUN)
    assert "it is the change set's only sync before a build (`running-a-change-set.md` step 4 leaves it here)" in b


def test_r11d_builder_commits_carry_the_trailer():
    t = BUILD_RUN.read_text(encoding="utf-8")
    prompts = t.split("## Prompts", 1)[1]
    assert "On a change-set branch the builder prompt adds one line after those" in " ".join(prompts.split())
    assert "```\nChange-set: <start-prd>/CS-<nnn>\n```" in prompts
    assert "the builder prompt carries the line `Change-set: <start-prd>/CS-<nnn>`" in flat(BUILD_RUN)
    agent = flat(ROOT / "agents/prd-builder.md")
    assert ("When the prompt has a `Change-set:` line, every commit adds it as a trailer: "
            "`-m \"Change-set: <start-prd>/CS-<nnn>\"`") in agent
    assert "on a change-set branch a `Change-set:` line" in agent


def test_deploy_commits_carry_no_trailer():
    assert "A deploy's commits on a change-set branch carry no `Change-set:` trailer" in step(4)


def test_upstream_is_the_slug_not_the_location():
    assert "`<upstream>` is an upstream member's PRD slug (its Upstreams row's name in `links.md`, never its Location)" in flat(RUN)
    assert "`<upstream>` that row's PRD slug (the Upstreams row's name, never its Location)" in flat(BUILD_RUN)


def test_dirty_tree_allows_the_new_record():
    assert "only the change's own edits and the record `new` just wrote" in step(1)


def test_changing_prds_missing_links_script_and_no_second_hand_off():
    t = flat(CHANGING)
    assert "A repository whose `.prd-toolkit/` holds no `prd_links.py` predates 0.7: stop" in t
    assert "re-run `prd_hooks.py install docs/prd/<slug>`" in t
    assert "When this change already runs inside `/prd-change-set`, hand nothing back to it" in t


def test_rationalization_waits_row():
    rat = flat(SKILL).split("## Common Rationalizations", 1)[1]
    assert "before that the build does not start, and `changeset set` would refuse its State" in rat
    assert "`changeset set` refuses it before" not in rat
