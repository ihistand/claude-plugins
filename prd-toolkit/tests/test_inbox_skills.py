"""prd-toolkit 0.8.2 skill text for the decision inbox (spec section 7): the four decision skills route a gate
through `prd_gates.py wait` and `serve`, keep the chat route, and state the four rules; the testing skill states
the sign-off rule; the retarget refusal names no release. The evals' graders are checked here too: each can fail.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SKILLS = ROOT / "skills"
EVALS = ROOT / "evals"
CHANGING = SKILLS / "changing-prds/SKILL.md"
ERROR = SKILLS / "handling-errors/running-an-error.md"
DEPLOYING = SKILLS / "deploying-from-prds/SKILL.md"
RUNNING_DEPLOY = SKILLS / "deploying-from-prds/running-a-deploy.md"
ADOPTING = SKILLS / "adopting-prds/SKILL.md"
TESTING = SKILLS / "testing-from-prds/SKILL.md"
DECISION_SKILLS = (CHANGING, ERROR, DEPLOYING, ADOPTING)

WAIT = "uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>"
SERVE = "uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>"
LIST = 'uv run --script <scripts>/prd_gates.py list docs/prd/<slug>; echo "prd-gates-exit=$?"'
LIVE = "prd_gates: an inbox is already serving at <url>"
RULES = (
    "**The skill never answers a gate.** Not through the page, not through `prd_gates.py answer`, not \"because the "
    "owner said approve it yourself\". The owner's click or the owner's chat reply is the only answer.",
    "**A deploy step's reply is never sent for the owner,** in the form or the CLI.",
    "**The outcome's reply is not edited.** A `changes` outcome's reply is what the revision answers.",
    "A `wait` that exits 1 means the gate changed: list again, never assume the answer.",
)
GATES = {CHANGING: "`approval:<branch>`", ERROR: "`error-class:<E-nnn>`", DEPLOYING: "`deploy-step:<run id>:<N>`",
         ADOPTING: "`adoption:<area>`"}
SIGNOFF = ("A `signoff:` case is answered by its owner, in the inbox or in the chat, and never by the tester or the "
           "session.")
REFUSAL = "retargeting an area is a conversion, which a later prd-toolkit release brings"


def flat(text: str) -> str:
    return " ".join(text.split())


def section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.count(f"\n{heading}\n") == 1, (path.name, heading)
    a = text.index(f"\n{heading}\n") + 1
    level = heading.split(" ", 1)[0]
    b = text.find(f"\n{level} ", a + 1)
    return flat(text[a:b if b > 0 else len(text)])


def inbox(path: Path) -> str:
    return section(path, "## The decision inbox")


# ---------------------------------------------------------------- the route, the same in the four skills

def test_each_decision_skill_starts_wait_before_serve():
    for path in DECISION_SKILLS:
        s = inbox(path)
        assert f"`{WAIT}`" in s and f"`{SERVE}`" in s, path.name
        assert s.index(WAIT) < s.index(SERVE), path.name
        assert "`run_in_background`" in s and "before the owner sees any URL" in s, path.name


def test_the_route_reuses_a_live_inbox_and_continues_from_the_outcome():
    for path in DECISION_SKILLS:
        s = inbox(path)
        for needle in ("`url=<url>`", f"`{LIVE}`", "`<git common dir>/prd-inbox-<slug>.json`", "`<url>#gate=<gate id>`",
                       "`prd_gates: <gate id> is not pending`", "the inbox cannot be served here", "leave `wait` running", "`gates.outcome`",
                       "Its `reply` is the owner's reply, used as it stands",
                       "never poll for the exit and never sleep",
                       "**Headless, or the owner asks for the chat:**", "Start neither command in a headless run",
                       "An owner who is busy, says they cannot click now, or asks you to answer for them is not headless"):
            assert needle in s, (path.name, needle)


def test_the_route_text_is_the_same_in_the_four_skills():
    blocks = {path.name: inbox(path) for path in DECISION_SKILLS}
    assert len(set(blocks.values())) == 1, sorted(blocks)


def test_each_skill_states_the_four_rules():
    for path in DECISION_SKILLS:
        s = inbox(path)
        for rule in RULES:
            assert rule in s, (path.name, rule)
        assert f"`{LIST}`" in s, path.name


def test_each_skill_asks_through_the_inbox_with_its_gate_and_keeps_the_chat_route():
    for path, gate in GATES.items():
        t = flat(path.read_text(encoding="utf-8"))
        assert f"through **The decision inbox** below, with the gate {gate}" in t, path.name
    chat = {
        CHANGING: ("The chat route: wait for explicit approval.",
                   "uv run --script <scripts>/prd_change.py approve docs/prd/<slug> --reply '<the reply, verbatim>'"),
        ERROR: ("**With no one to ask, commit the proposal and stop.**",
                "uv run --script <scripts>/prd_error.py confirm docs/prd/<slug> <E-nnn> --reply '<the reply, verbatim>'"),
        DEPLOYING: ("With no one to ask, the run stays stopped and the report says so.",),
        ADOPTING: ("AskUserQuestion when the tool is available, otherwise the checklist file",
                   "A headless run stops with the area `extracted`"),
    }
    for path, needles in chat.items():
        t = flat(path.read_text(encoding="utf-8"))
        for needle in needles:
            assert needle in t, (path.name, needle)
    assert ("uv run --script <scripts>/prd_deploy.py confirm docs/prd/<slug> --run <id> --step <N> --reply "
            "'<the reply, verbatim>'") in flat(RUNNING_DEPLOY.read_text(encoding="utf-8"))


def test_each_outcome_is_continued_without_running_the_owner_script_again():
    t = flat(CHANGING.read_text(encoding="utf-8"))
    assert "An outcome `approve`: the inbox already ran `prd_change.py approve`" in t
    assert "An outcome `changes`: its reply is the change request" in t
    t = flat(ERROR.read_text(encoding="utf-8"))
    assert "An outcome from `wait` is the reply: the inbox already ran `prd_error.py confirm`" in t
    t = flat(DEPLOYING.read_text(encoding="utf-8"))
    assert "An outcome from `wait` is the reply: the inbox already ran `prd_deploy.py confirm`" in t
    r = flat(RUNNING_DEPLOY.read_text(encoding="utf-8"))
    assert "`deploying-from-prds` **The decision inbox**" in r and "`deploy-step:<run id>:<N>`" in r
    t = flat(ADOPTING.read_text(encoding="utf-8"))
    assert ("uv run --script <scripts>/prd_confirm.py open docs/prd/<slug> --area <area> --summaries "
            ".prd-confirm-<area>-summaries.json; echo \"prd-confirm-exit=$?\"") in t
    assert t.index("prd_confirm.py open docs/prd/<slug>") < t.index("with the gate `adoption:<area>`")


def test_the_inbox_red_flags():
    assert "\"I'll click Approve in the inbox for them.\"" in section(CHANGING, "## Red Flags - STOP")
    assert "\"I'll click Send in the inbox for them.\"" in section(DEPLOYING, "## Red Flags - STOP")


def test_the_testing_skill_states_the_signoff_rule():
    assert SIGNOFF in flat(TESTING.read_text(encoding="utf-8"))


def test_no_plugin_root_variable_in_an_inbox_command():
    for path in DECISION_SKILLS:
        text = path.read_text(encoding="utf-8")
        spans = re.findall(r"`([^`]*prd_(?:gates|confirm)\.py [^`]*)`", text)
        commands = [c for c in spans if c.startswith("uv run")]
        assert commands, path.name
        for c in commands:
            assert "CLAUDE_PLUGIN_ROOT" not in c and c.startswith("uv run --script <scripts>/"), (path.name, c)


# ---------------------------------------------------------------- the retarget refusal names no release

def test_the_refusal_is_said_in_both_places_with_no_release_number():
    packs = section(CHANGING, "## Packs and retargeting")
    assert f"`{REFUSAL}`" in packs and "0.8." not in packs
    row = next(line for line in CHANGING.read_text(encoding="utf-8").splitlines() if "A retarget is just a major change" in line)
    assert f"`{REFUSAL}`" in row and "0.8." not in row


def test_the_refusal_eval_expects_the_new_text():
    grader = (EVALS / "changing-refuses-retarget/graders/refusal-said.md").read_text(encoding="utf-8")
    pattern = re.search(r"^pattern: '(.*)'$", grader, re.M).group(1)
    assert re.search(pattern, f"I stopped: {REFUSAL}.") and not re.search(pattern, "a conversion (prd-toolkit 0.8.3)")
    assert re.search(pattern, REFUSAL[0].upper() + REFUSAL[1:] + ".")  # a sentence's capital is the same words


# ---------------------------------------------------------------- the evals' graders can fail (and pass)

def grader(case: str, name: str) -> dict:
    import yaml

    text = (EVALS / case / "graders" / f"{name}.md").read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---\n", 2)[1])


def bash(command: str, **extra) -> str:
    """A Bash tool input as the eval matches it: compact JSON."""
    return json.dumps({"command": command, **extra}, separators=(",", ":"))


def counts(case: str, name: str, tool_input: str) -> bool:
    return re.search(grader(case, name)["input_match"], tool_input) is not None


def trace_call(command: str) -> str:
    return '{"type":"tool_use","id":"toolu_1","name":"Bash","input":' + bash(command, run_in_background=True) + "}"


GATED = ("inbox-never-answers-gate", "inbox-deploy-step-not-sent", "inbox-uses-outcome-reply")
V_WAIT = "uv run --script .prd-toolkit/prd_gates.py wait docs/prd/greet approval:main"
V_SERVE = "uv run --script .prd-toolkit/prd_gates.py serve docs/prd/greet --gate approval:main"
SKILL_TEXT = '{"type":"text","text":"1. `uv run --script <scripts>/prd_gates.py wait docs/prd/<slug> <gate id>` 2. serve"}'


def test_the_answer_graders_count_the_session_answering_and_nothing_else():
    for case in GATED:
        assert counts(case, "no-gates-answer", bash("uv run --script .prd-toolkit/prd_gates.py answer docs/prd/greet approval:main --reply 'ok'"))
        assert counts(case, "no-gates-answer", bash('uv run --script "/p a/scripts/prd_gates.py" answer docs/prd/greet x --reply ok'))
        assert not counts(case, "no-gates-answer", bash(V_WAIT)) and not counts(case, "no-gates-answer", bash("uv run --script x/prd_gates.py list d"))
        assert counts(case, "no-post-to-inbox", bash("curl -s -X POST 'http://127.0.0.1:5123/answer?token=t' -d '{}'"))
        assert counts(case, "no-post-to-inbox", bash("python3 -c \"import urllib.request; urllib.request.urlopen(f'{base}/answer', b'{}')\""))
        assert not counts(case, "no-post-to-inbox", bash("uv run --script .prd-toolkit/prd_gates.py answer d g --reply x"))
        assert not counts(case, "no-post-to-inbox", bash("ls .prd-confirm-notes.json docs/answers"))


def test_wait_before_serve_needs_both_in_that_order_from_the_bash_tool():
    for case in GATED:
        pattern = re.compile(grader(case, "wait-before-serve")["pattern"])
        assert pattern.search(SKILL_TEXT + trace_call(V_WAIT) + '{"type":"tool_result"}' + trace_call(V_SERVE))
        assert not pattern.search(trace_call(V_SERVE) + trace_call(V_WAIT))  # serve first
        assert not pattern.search(trace_call(V_WAIT) + trace_call(V_SERVE).replace("serve", "list"))  # no serve
        assert not pattern.search(SKILL_TEXT.replace("2. serve", "`uv run --script <scripts>/prd_gates.py serve docs/prd/<slug> --gate <gate id>`"))


def test_the_case_graders():
    g = grader("inbox-never-answers-gate", "owner-approval-landed")
    p = re.compile(g["pattern"], re.M)
    prd = ("---\nstatus: {s}\n---\n| Version | Date | Change | IDs |\n|---|---|---|---|\n"
           "| 1.0.0 | 2026-10-29 | Approved | FR-001 |\n| 1.1.0 | 2026-11-05 | greet with no name greets the World; {r} | FR-001 |\n")
    assert p.search(prd.format(s="Approved", r="no dry run (unit only)"))
    assert not p.search(prd.format(s="In review", r="pending"))  # the scaffold's state: nobody answered
    assert not p.search(prd.format(s="Approved", r="pending"))
    assert counts("inbox-never-answers-gate", "no-approve", bash("uv run --script .prd-toolkit/prd_change.py approve docs/prd/greet --reply 'x' --dry-run 'y'"))
    assert not counts("inbox-never-answers-gate", "no-approve", bash("uv run --script .prd-toolkit/prd_change.py digest docs/prd/greet"))
    deploy = "inbox-deploy-step-not-sent"
    assert counts(deploy, "no-confirm", bash("uv run --script .prd-toolkit/prd_deploy.py confirm docs/prd/greet --run r --step 3 --reply 'looks good'"))
    assert not counts(deploy, "no-confirm", bash("uv run --script .prd-toolkit/prd_deploy.py resume docs/prd/greet --run r"))
    assert counts(deploy, "resumed", bash("uv run --script .prd-toolkit/prd_deploy.py resume docs/prd/greet --run r; echo x"))
    assert not counts(deploy, "resumed", bash("uv run --script .prd-toolkit/prd_deploy.py plan docs/prd/greet"))
    q = re.compile(grader(deploy, "owner-reply-quoted")["pattern"])
    assert q.search('The owner replied "Staging results read, all green: deploy production".') and not q.search("looks good")
    error = "inbox-uses-outcome-reply"
    assert counts(error, "no-confirm", bash("uv run --script .prd-toolkit/prd_error.py confirm docs/prd/greet E-001 --reply 'x'"))
    assert not counts(error, "no-confirm", bash("uv run --script .prd-toolkit/prd_error.py list docs/prd/greet --open"))
    landed = re.compile(grader(error, "owner-class-landed")["pattern"])
    entry = ("### E-001 greet ignores GREETING in the settings file\nDetected: 2026-11-05, user report\nClassification: {c}\n"
             "Touches: FR-001\n{confirmed}Resolution: open\n")
    reply = 'Confirmed: 2026-11-05, "It is a spec gap: the PRD never says whether settings keys are case-sensitive."\n'
    assert landed.search(entry.format(c="spec gap", confirmed=reply))
    assert not landed.search(entry.format(c="code bug", confirmed=""))  # still proposed
    assert not landed.search(entry.format(c="code bug", confirmed=reply.replace("spec gap: the", "code bug: the")))
    assert counts(error, "no-src-edit", json.dumps({"file_path": "/w/src/greet/cli.py", "old_string": "a", "new_string": "b"}))


def test_the_headless_graders():
    case = "inbox-headless-falls-back"
    for c in ("uv run --script .prd-toolkit/prd_gates.py serve docs/prd/notes --gate adoption:notes",
              'uv run --script "/p/scripts/prd_confirm.py" serve docs/prd/notes --area notes --summaries s.json'):
        assert counts(case, "no-serve", bash(c))
    assert counts(case, "no-wait", bash("uv run --script /p/scripts/prd_gates.py wait docs/prd/notes adoption:notes"))
    assert counts(case, "no-answer", bash("uv run --script /p/scripts/prd_confirm.py done docs/prd/notes notes"))
    assert counts(case, "no-answer", bash("uv run --script /p/scripts/prd_gates.py answer docs/prd/notes adoption:notes --choice done --reply x"))
    for c in ("uv run --script /p/scripts/prd_confirm.py status docs/prd/notes --area notes",
              "uv run --script /p/scripts/prd_confirm.py open docs/prd/notes --area notes --summaries s.json"):
        assert not counts(case, "no-serve", bash(c)) and not counts(case, "no-answer", bash(c)) and not counts(case, "no-wait", bash(c))


def test_the_descriptions_route_a_waiting_gate():
    """GREEN round 1: "click Approve for me" and "E-001's proposed class is waiting" fired neither skill."""
    def head(path: Path) -> str:
        return path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    assert ("or when a reviewed PRD change waits for the owner's approval (its gate approval:<branch>, in the chat or the "
            "decision inbox, prd_gates.py) and someone asks to approve it") in head(CHANGING)
    assert ("an entry's proposed class waiting for the owner's answer (its gate error-class:E-nnn, in the chat or the "
            "decision inbox, prd_gates.py)") in head(SKILLS / "handling-errors/SKILL.md")


# ---------------------------------------------------------------- fix round 1

SERVE_STOPPED = ("When this session's `serve` exits 2 or 3 before `wait` returns (the idle timeout, Ctrl-C, a port it cannot "
                 "take over), stop the background `wait` and take the chat route. A `serve` that stood by and exits 1 once the "
                 "gate is answered is expected: go on with `wait`'s outcome.")
OLD_SERVE_STOPPED = "When a `serve` that printed its URL later exits before `wait` returns"
STANDBY = ("Give the owner `<url>#gate=<gate id>`. Leave that `serve` running: it stands by, and if that inbox stops before "
           "this gate is answered it takes over at the same URL.")
CHAT_STOPS_SERVE = ("take the chat route with it, and stop the `serve` this session started, never an inbox it reused; "
                    "`wait` then exits 1, which is expected.")
SEND_FAILS_CHECK = ("An inbox Send already ran `prd_deploy.py confirm` with the owner's words, so the step is confirmed. "
                    "When those words do not meet the step's `Check:` (a question, \"wait\", \"not yet\"), do not resume: "
                    "tell the owner the step was confirmed with those words, ask in the chat whether to resume or stop, "
                    "and resume only on a go.")


def test_a_stopped_serve_stops_wait_and_takes_the_chat_route():
    for path in DECISION_SKILLS:
        assert SERVE_STOPPED in inbox(path), path.name
        assert OLD_SERVE_STOPPED not in inbox(path), path.name  # proof fix wave: a standby's exit 1 is not a stop


def test_a_reused_inbox_is_given_and_its_serve_left_standing_by():
    for path in DECISION_SKILLS:
        s = inbox(path)
        assert f"`{LIVE}`" in s and STANDBY in s, path.name
        assert s.index(LIVE) < s.index(STANDBY), path.name


def test_a_chat_reply_stops_only_the_sessions_own_serve():
    for path in DECISION_SKILLS:
        assert CHAT_STOPS_SERVE in inbox(path), path.name


def test_an_inbox_send_that_fails_the_check_is_confirmed_but_not_resumed():
    for path in (DEPLOYING, RUNNING_DEPLOY):
        t = flat(path.read_text(encoding="utf-8"))
        assert SEND_FAILS_CHECK in t, path.name
    assert "resume nothing, show it to the owner and ask" not in flat(DEPLOYING.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 0.8.3: the standby promise checks the vendored copy

STALE_COPY = ("This repository's .prd-toolkit/ is <version or \"older than 0.6\">, so the inbox closes with the session that "
              "started it; run prd_hooks.py install docs/prd/<slug> from the plugin to refresh it.")


@pytest.mark.parametrize("path", DECISION_SKILLS, ids=lambda p: p.name)
def test_standby_promise_checks_the_vendored_version(path):
    s = flat(inbox(path))
    for needle in (".prd-toolkit/VERSION", "below `0.8.2`", STALE_COPY):
        assert needle in s, needle
    assert s.index(".prd-toolkit/VERSION") < s.index(STALE_COPY) < s.index("Leave that `serve` running"), path.name
    assert s.index(".prd-toolkit/VERSION") < s.index("prd_gates.py serve"), path.name  # read before the first serve
