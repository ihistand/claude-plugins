"""The adopting-prds skill, its per-area extract prompt and the /prd-adopt command."""
import re
from pathlib import Path

from test_dry_run_prompt import LINT_CMD, RULE

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/adopting-prds/SKILL.md"
EXTRACT = ROOT / "skills/adopting-prds/extract-prompt.md"
COMMAND = ROOT / "commands/prd-adopt.md"
DESCRIPTION = (
    "Use when bringing an existing codebase or one of its areas under a PRD - \"adopt this repo\", \"write a "
    "PRD for what this already does\", \"reverse-engineer the requirements\", /prd-adopt - extracts as-built "
    "requirements with sources, confirms intent with the user, and closes each area with characterization "
    "tests run by prd-tester"
)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def section(path: Path, heading: str) -> str:
    """The flattened body under `heading` (a markdown heading line), up to the next heading of any level."""
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^#|\Z)", text, re.S | re.M)
    assert m, f"no '{heading}' section in {path.name}"
    return " ".join(m.group(1).split())


def step(text: str, n: int) -> str:
    """The body of step `n` of the flow: from its `### n.` heading to the next heading."""
    m = re.search(rf"^### {n}\. .*?(?=^##)", text, re.S | re.M)
    assert m, f"no '### {n}.' step heading"
    return " ".join(m.group(0).split())


def test_skill_frontmatter_is_pinned():
    assert frontmatter(SKILL) == {"name": "adopting-prds", "description": DESCRIPTION}


def test_every_lint_call_echoes_its_exit_code():
    text = SKILL.read_text(encoding="utf-8")
    assert LINT_CMD in text
    assert "prd-lint-exit=0" not in text  # the lint-exit-0 eval grader's literal
    for line in text.splitlines():
        if "prd_lint.py" in line and "--list-packs" not in line:  # R26: --list-packs echoes prd-list-packs-exit
            assert 'echo "prd-lint-exit=$?"' in line, line
        if "lint" in line.lower() and re.search(r"\bexits? 0\b", line):
            assert "prd-lint-exit" in line, f"a gate must name the echoed value: {line}"
    assert RULE in text


def test_extraction_is_general_purpose_and_characterization_is_prd_tester():
    text = SKILL.read_text(encoding="utf-8")
    extract, characterize = step(text, 2), step(text, 4)
    assert "general-purpose" in extract and "extract-prompt.md" in extract
    assert "prd-tester" not in extract.replace("Never send `extract-prompt.md` to `prd-tester`", "")
    assert "Never send `extract-prompt.md` to `prd-tester`" in flat(SKILL)
    assert "prd-toolkit:prd-tester" in characterize and "Mode: suite" in characterize
    assert "testing-from-prds/dispatching.md" in characterize and "integrity check" in characterize
    assert "extract-prompt.md" not in characterize


def test_extract_prompt_is_read_only_and_lists_bugs_apart():
    text = flat(EXTRACT)
    for slot in ("<AREA>", "<BOUNDARY>", "<COMMIT>", "<PRD_DIR>", "<LIVE_SYSTEM>"):
        assert slot in text, slot
    for slot in ("<REPO_ROOT>", "<FORMAT>"):
        assert slot in text, slot
    never = section(EXTRACT, "## What you never do")
    assert never.startswith("You are read-only. Never use Write, Edit or NotebookEdit.")
    assert ("Never deploy. Never make a mutating API call (create, update, delete, run a job, send a "
            "message) or a query that writes, on the live system or anywhere else.") in never
    for heading in ("REQUIREMENTS", "TEST CASES", "CONTRACTS", "APPARENT BUGS", "QUESTIONS", "FILES READ"):
        assert re.search(rf"^{heading}$", EXTRACT.read_text(encoding="utf-8"), re.M), heading
    assert "Source: <file>:<line> @<COMMIT>" in text
    assert "An apparent bug is never a requirement" in text
    assert "looker" not in text.lower()  # a generic prompt: no Looker commands or URLs


def test_confirmation_is_per_requirement_and_needs_the_users_word():
    text = flat(SKILL)
    confirm = step(SKILL.read_text(encoding="utf-8"), 3)
    assert "Confirmation is the user's word, requirement by requirement" in confirm
    assert ("A reply that names no ID (\"looks fine\", \"all good\", \"yes\") confirms nothing: ask again, "
            "ID by ID, and leave every unanswered block `as-built`.") in confirm
    assert ("When every requirement and every `E-nnn` of the area has the user's answer and §13 holds none "
            "of the area's questions, set the row to `confirmed` and run lint.") in confirm
    for outcome in ("`live (since <version>)`", "`approved`", "`[ASSUMPTION A-nn"):
        assert outcome in confirm, outcome
    assert "the code clearly intends it" in text.lower()
    # headless: the confirm step itself stops; rule 4 alone is not enough
    assert "stop and present the confirmations, and leave the area `extracted`" in step(SKILL.read_text(encoding="utf-8"), 3)


def test_unknown_intent_awaits_a_named_person_and_a_real_bug_is_a_correction():
    confirm = step(SKILL.read_text(encoding="utf-8"), 3)
    assert "`| A-nn | <the behaviour> | awaiting <who> |`" in confirm
    assert "indexed `open`" not in confirm
    assert "A real bug stays open, and the requirement it touches is *corrected*, never confirmed" in confirm
    gates = step(SKILL.read_text(encoding="utf-8"), 5)
    assert "an `awaiting <who>` row carries through" in gates


def test_characterization_triage_and_gate():
    char = step(SKILL.read_text(encoding="utf-8"), 4)
    assert ("**A real bug:** an `E-nnn` entry (new, or the open one that already describes it), the requirement "
            "drops to `approved`, and its test case gains `known-failing: E-nnn`. The test stays as written.") in char
    assert ("The gate is one RESULTS line per T-id of the area, each `pass` or `known-failing E-nnn` whose entry is "
            "open and cited on that case, and an integrity check that found no change outside the test roots. "
            "Anything else, and the area stays `confirmed`.") in char


def test_trace_runs_on_the_adopted_row_before_approval():
    gate = step(SKILL.read_text(encoding="utf-8"), 5)
    order = ["1. **Gates.**", "2. **The adoption-map row.**", "3. **Trace,** before the user's approval and before any commit",
             'prd_trace.py docs/prd/<slug>; echo "prd-trace-exit=$?"', "4. **Approval.**"]
    at = [gate.find(o) for o in order]
    assert -1 not in at and at == sorted(at), dict(zip(order, at))
    assert ("Set only the area's row to `adopted`, uncommitted: trace scopes by that row. The status, the version "
            "and the §14 row stay untouched until the user approves.") in gate
    assert ("A finding on `features/<area>.md`, or a `test-cites-live` finding that names one of the area's T-ids, "
            "blocks: set the row back to `confirmed` and return to step 4.") in gate
    assert "Any other finding predates this area: show it to the user as pre-existing; it does not block." in gate
    assert "If the user declines, set the row back to `confirmed`. Only on approval:" in gate


def test_nothing_before_the_approval_sentence_writes_approved_or_a_version():
    # authoring rule 3: never `Approved` without the user's explicit approval
    gate = step(SKILL.read_text(encoding="utf-8"), 5)
    before, after = gate.split("Only on approval:", 1)
    for word in ("`Approved`", "`1.0.0`", "bump", "§14 row that records", "its §14 row"):
        assert word not in before, word
    assert "sets status `Approved`, version `1.0.0`" in after and "the minor bump and its §14 row" in after


def test_one_area_at_a_time_in_order():
    text = flat(SKILL)
    assert "One area at a time" in text
    assert "An area is one feature file, `features/<area>.md`" in text
    assert "`not started` → `extracted` → `confirmed` → `adopted`" in text
    assert "never skip" in text.lower()
    assert "An apparent bug never becomes a requirement" in text
    assert "`adopted` only on a suite" in text


def test_versions_follow_first_approval_then_minor_bumps():
    text = flat(SKILL)
    assert "stays `0.1.0` until its first area is adopted" in text
    assert "The first adopted area takes the first-approval path: authoring phase 7 sets `1.0.0`" in text
    assert ("Each later area is one change through `prd-toolkit:changing-prds`: adding an area adds behaviour to "
            "the PRD and changes none, so it is a **minor** bump (`1.0.0` → `1.1.0`).") in section(SKILL, "## Versions")


def test_prd_adopt_invokes_the_skill_with_the_area():
    fm = frontmatter(COMMAND)
    assert set(fm) == {"description"} and "prd-toolkit" in fm["description"]
    body = COMMAND.read_text(encoding="utf-8").split("---\n", 2)[2]
    assert "Invoke the prd-toolkit:adopting-prds skill and follow it exactly." in body
    assert "$ARGUMENTS" in body and "area" in body


def test_bootstrap_copies_the_template_with_read_and_write_not_cp():
    """A sandbox that denies the plugin folder as a copy source blocks `cp -R`; Read and Write are granted tools."""
    text = SKILL.read_text(encoding="utf-8")
    assert "cp -R" not in text
    copy = re.search(r"^- \*\*Copy:\*\*.*?(?=^- \*\*)", text, re.S | re.M)
    assert copy, "no '- **Copy:**' bullet in the bootstrap"
    copy = " ".join(copy.group(0).split())
    for word in ("Read", "Write", "`${CLAUDE_PLUGIN_ROOT}/templates/prd/`", "`docs/prd/<slug>/`", "same relative path"):
        assert word in copy, word
    later = step(text, 1)
    assert "Read" in later and "Write" in later and "later area" in later.lower()


# --- final fix wave ---

def test_approval_shows_the_version_and_takes_only_the_post_approval_actions():
    gate = step(SKILL.read_text(encoding="utf-8"), 5)
    approval = gate.split("4. **Approval.**", 1)[1]
    before, after = approval.split("Only on approval:", 1)
    for phrase in ("the version the approval will set", "1.0.0", "the next minor", "why it is minor"):
        assert phrase in before, phrase
    for bad in ("status Approved", "version 1.0.0", "version 1.1.0"):
        assert bad not in gate.split("Only on approval:", 1)[0], bad  # anywhere in step 5 before it
    assert ("authoring phase 7's status, version, `updated`, §14 row, lint and `prd_block.py` — not its commit or "
            "its hand-off") in after
    assert ("`prd-toolkit:changing-prds` step 3, then only step 5's post-approval actions — not its commit or its second "
            "approval") in after
    assert "area adopted; suite" in after.split("Later area:", 1)[1]  # the later row records the suite too
    assert after.count("commit the PRD folder") == 1 and gate.count("Then commit") == 1


def test_trace_exit_two_is_never_a_pass_and_an_interrupted_step_five_resumes():
    gate = step(SKILL.read_text(encoding="utf-8"), 5)
    assert "`prd-trace-exit=2` is a tool error, never a pass: fix and rerun." in gate
    boot = step(SKILL.read_text(encoding="utf-8"), 0)
    assert "a row `adopted` whose adoption has no §14 row is step 5 interrupted: resume at 5.3." in boot


def test_extraction_writes_no_unit_cases_and_the_suite_takes_every_non_unit_tid():
    assert "never `level: unit`" in section(EXTRACT, "## Rules")
    char = step(SKILL.read_text(encoding="utf-8"), 4)
    assert "every non-unit T-id in `test-cases/<area>.yaml`" in char and "`--sample-tids` is for dry runs only" in char


def test_characterization_tests_are_the_one_exception_to_changing_rule_one():
    assert ("characterization tests the tester writes in step 4 are allowed before a later area's approval"
            in flat(SKILL))


def test_closed_window_live_values_are_named_and_confirmed():
    rules = section(EXTRACT, "## Rules")
    assert ("or from a read-only live read of a closed window that testing.md's Persistent environments slot "
            "defines") in rules
    assert "named in the case's `input`" in rules and "FILES READ" in rules
    assert "closed window" in section(EXTRACT, "## What you read")
    confirm = step(SKILL.read_text(encoding="utf-8"), 3)
    assert "closed window" in confirm and "like any `as-built` item" in confirm


def test_bootstrap_test_roots_include_every_existing_test_directory():
    """An adoption keeps the project's own tests: every existing test directory is a test root."""
    body = " ".join(step(SKILL.read_text(encoding="utf-8"), 0).split())
    assert "every directory that already holds the project's tests" in body
    assert "Never leave an existing test directory out" in body
    assert "A directory that mixes tests with the code they test is never a test root" in body


def test_confirmation_asks_with_the_question_tool_a_few_at_a_time():
    """Typing every ID into one prompt is not a workable interface: ask through AskUserQuestion."""
    confirm = " ".join(step(SKILL.read_text(encoding="utf-8"), 3).split())
    assert "ask with the AskUserQuestion tool, at most four requirements per call" in confirm
    assert "Its preview is the whole block and its `Source:` excerpt, as the `implement` pack prints them" in confirm
    for option in ("**Confirm**", "**Correct**", "**It's a bug**", "**Someone else decides**"):
        assert option in confirm, option
    assert "Write each answer into the PRD as soon as it arrives" in confirm
    assert "the same way for the area's §13 questions and its `E-nnn` entries" in confirm


def test_confirmation_falls_back_to_a_checklist_file_outside_the_prd_folder():
    """Headless runs, or a user who wants to work in an editor, get a checklist file instead."""
    confirm = " ".join(step(SKILL.read_text(encoding="utf-8"), 3).split())
    assert "`.prd-confirm-<area>.md` at the repository top" in confirm
    assert "never inside the PRD folder or a test root" in confirm  # its Source excerpts are code
    assert "a `Decision:` line the user fills in" in confirm
    assert "A blank or unrecognised `Decision:` line is no answer" in confirm
    assert "Delete the checklist file once every item is answered" in confirm


# --- 0.7.1: step 3 confirms through the form ---

def confirm_step() -> str:
    return step(SKILL.read_text(encoding="utf-8"), 3)


def form_part() -> str:
    """The text of step 3 about the form, up to the fallbacks."""
    c = confirm_step()
    assert "**The form.**" in c
    return c.split("**The form.**", 1)[1].split("**How to ask.**", 1)[0]


def test_the_form_is_the_first_route_and_its_summaries_sit_outside_the_prd_and_test_roots():
    c = confirm_step()
    assert c.index("**The form.**") < c.index("**How to ask.**") < c.index("**The checklist file.**")
    f = form_part()
    assert "`.prd-confirm-<area>-summaries.json`" in f
    assert "at the repository root, never inside the PRD folder or a test root" in f
    assert "one or two plain sentences" in f and "contains its ID" in f and "at most 400 characters" in f


def test_the_form_is_served_in_the_background_one_command_per_call_never_with_the_plugin_root_variable():
    f = form_part()
    assert ("uv run --script <scripts>/prd_confirm.py serve docs/prd/<slug> --area <area> "
            "--summaries .prd-confirm-<area>-summaries.json") in f
    assert "`run_in_background`" in f and "one command per Bash call" in f
    assert "first line of its output" in f and "`url=`" in f
    assert "clickable link" in f
    assert "never poll for the exit and never sleep" in f
    assert "never `${CLAUDE_PLUGIN_ROOT}`" in f


def test_the_form_exit_codes_are_handled_and_exit_three_leaves_the_area_extracted():
    f = form_part()
    assert "exit `0`" in f and "exit `3`" in f and "exit `2`" in f
    assert "Run `prd_confirm.py status docs/prd/<slug> --area <area>`" in f
    assert "leave the area `extracted`" in f.split("exit `3`", 1)[1]
    assert "prd_confirm:" in f.split("exit `2`", 1)[1]


def test_exit_zero_rechecks_with_status_and_a_changed_item_is_no_answer():
    f = form_part()
    after = f.split("exit `0`", 1)[1]
    assert "Read `.prd-confirm-<area>.json`" in after
    assert "run `prd_confirm.py status docs/prd/<slug> --area <area>`" in after
    assert "Any `open <ID>` line" in after and "changed since it was answered" in after
    assert "is no answer" in after and "serve again" in after


def test_each_decision_maps_to_its_prd_change():
    f = form_part()
    for needle in (
        "`confirm`: status `live (since <version>)`",
        "`correct`: status `approved`, with the ACs and test cases rewritten from `text`, or from `acs`",
        "`bug`: the `E-nnn` stays open, and the requirement is corrected to the intended behaviour",
        "`ask`: status `approved`, an `[ASSUMPTION A-nn]` and a §12 `awaiting <who>` row",
        "`intended`: the behaviour becomes requirement text, and the entry's Resolution names who confirmed it and when",
        "`answer` on a question: the answer goes into the PRD",
        "`fix` on a question: the requirement it blocks becomes a correction",
        "`answer` on a marker: the value replaces the marker",
    ):
        assert needle in f, needle
    assert "write each into the PRD as soon as you apply it" in f


def test_both_files_are_deleted_once_every_answer_is_applied_and_neither_is_committed():
    f = form_part()
    assert "delete `.prd-confirm-<area>.json` and `.prd-confirm-<area>-summaries.json`" in f
    assert "never committed" in f


def test_a_form_that_cannot_be_served_takes_the_fallbacks_and_a_headless_run_stops_extracted():
    c = confirm_step()
    f = form_part()
    assert "cannot be served" in f and "nobody can open the URL" in f
    assert "AskUserQuestion when the tool is available, otherwise the checklist file" in f
    assert "A headless run stops with the area `extracted`" in f
    # the earlier fallbacks stay
    assert "ask with the AskUserQuestion tool, at most four requirements per call" in c
    assert "`.prd-confirm-<area>.md` at the repository top" in c
    assert "Confirmation is the user's word, requirement by requirement" in c
    assert "A reply that names no ID" in c


def test_intended_on_a_question_and_ask_on_an_entry_have_their_own_instruction():
    f = form_part()
    assert ("`intended` on a question: the behaviour it asks about is intended; write it as requirement text "
            "of the requirement the bullet names, with the owner's note as the answer, and remove the §13 bullet; "
            "it is not a correction") in f
    assert ("`ask` on an `E-nnn`: the entry stays `Resolution: open`; §12 gets "
            "`| A-nn | E-nnn: <the behaviour> is intended | awaiting <who> |`; every requirement the entry touches "
            "is `approved`, never `live`, and carries `[ASSUMPTION A-nn: <the behaviour>; <who> would confirm it]` "
            "on the AC the entry concerns") in f


def test_each_field_of_an_answer_is_named():
    f = form_part()
    assert ("`text` is the intended behaviour for `correct` and `bug`, the person for `ask`, the answer for a "
            "question's `answer`, the value for a marker's `answer`, an optional note for `intended`, and what it "
            "should do instead for `fix`") in f
    assert "`acs` (`correct` only) maps an AC ID to its full new text, which replaces that AC verbatim" in f
    after = f.split("exit `0`", 1)[1].split("exit `3`", 1)[0]
    assert "run `prd_confirm.py status docs/prd/<slug> --area <area>`" in after


# ---- final-review fix ----

def test_a_bug_answer_with_no_entry_or_no_touches_and_an_entry_overriding_a_confirm():
    f = form_part()
    assert ("`bug` on a requirement that no open `E-nnn` touches: write a new `E-nnn` with "
            "`Detected: <today>, confirmation of <FR-nnn>`, `Touches:` that FR, a Diagnosis taken from the item and "
            "`Resolution: open, intended: <text>`; then correct the requirement to that behaviour") in f
    assert ("A `bug` or `ask` on an `E-nnn` overrides a `confirm` on any requirement the entry touches: that "
            "requirement is `approved`, never `live`; on `bug` it is corrected to the entry's intended behaviour, on "
            "`ask` it carries the assumption") in f
    assert ("`bug` on an `E-nnn` whose `Touches:` is `-`: the entry stays open as `Resolution: open, intended: <text>` "
            "(an entry is open while its Resolution starts with `open`), and no requirement changes") in f


ENTRIES = ("\n### E-002 Blank rows are imported\nDetected: 2026-11-03, confirmation of FR-001\nTouches: FR-001\n"
           "Diagnosis: the importer keeps a blank row\nResolution: open, intended: the importer skips blank rows\n"
           "\n### E-003 Slow import\nDetected: 2026-11-03, review\nTouches: -\nDiagnosis: no index\n"
           "Resolution: open, intended: an import of 10k rows takes under a second\n")


def test_the_intended_behaviour_field_lints_clean_and_keeps_the_entry_open(prd):
    from conftest import lint
    from prdlint import model

    (prd / "errors.md").write_text((prd / "errors.md").read_text() + ENTRIES)
    assert lint(prd) == []
    led = model.load(prd).errors_ledger
    assert led["E-002"].open and led["E-003"].open


def test_how_to_find_an_item_again_and_learn_its_id():
    f = form_part()
    assert ("Run `prd_confirm.py status docs/prd/<slug> --area <area>` before you write the summaries: its "
            "`open <ID>` lines are the exact item IDs") in f
    assert ("`<file under contracts/>:<key path from the named key>`, where `#n` is the n-th marker in one value and "
            "`~n` a last-resort collision suffix") in f
    assert ("Each answer also records the item's `where` and `served` text: find a marker by its `served` line in "
            "the contract file that `where` names") in f
    assert f.index("before you write the summaries") < f.index("run_in_background")


def test_the_summaries_file_is_deleted_on_exit_two_and_on_a_fallback():
    f = form_part()
    two = f.split("exit `2`", 1)[1]
    assert "Delete `.prd-confirm-<area>-summaries.json`, then fix what it names" in two
    assert "delete `.prd-confirm-<area>-summaries.json` and take the fallbacks" in two


def test_fix_is_a_correction_and_every_question_answer_removes_its_bullet():
    f = form_part()
    assert "`fix` on a question: the requirement it blocks becomes a correction to what `text` says" in f
    assert "`answer`, a `fix` that is applied and `intended` on a question each remove the §13 bullet" in f
    assert "Leave that item's §13 bullet in place until they answer" in f


def test_the_url_line_may_be_re_read_and_only_the_exit_is_never_polled():
    f = form_part()
    assert "re-read the output until the `url=` line appears" in f
    assert "never poll for the exit and never sleep" in f
    assert "never poll it and never sleep" not in f


# ---- 0.8.2: a fix that restates the item ----

def test_a_fix_that_restates_the_item_is_asked_about_never_decided():
    f = " ".join(form_part().split())
    assert ("A `fix` whose words describe the behaviour the item already states is not applied as a correction: "
            "ask the owner in the chat, for that one item, whether they meant keep it. Never decide it yourself.") in f
    assert "refuse a `fix` without words" in f
