"""prd_judge.py: judged cases scored by a model grader, the quote check, the median and the record (0.8.0).

The suite never runs the real `claude`: PRD_JUDGE_CLAUDE points at tests/fake_claude.py."""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from conftest import edit
from doc_fixture import document_prd
from packs_fixture import plugins_file, write_pack

from prdlint import judge, model

SCRIPT = Path(__file__).parent.parent / "scripts/prd_judge.py"
FAKE = Path(__file__).parent / "fake_claude.py"
GRADER_MD = Path(__file__).parent.parent / "templates/judge/grader.md"
TID = "T-001.2"
R1 = "Each step in Install names one action the reader performs"
R2 = "No step relies on a tool that Requirements does not list"
DOC = """# Install guide

## Requirements

You need a computer with Python 3.11 and the uv tool.

## Install

1. Open a terminal
   and type the install command.
2. Press Enter to run it.

## First run

Type `greet --name you` and read the greeting.
"""
GOOD_Q1 = "Open a terminal and type the install command."  # re-wrapped: the output breaks this line
GOOD_Q2 = "You need a computer with Python 3.11 and the uv tool."
FLAGS = ["-p", "--output-format", "json", "--json-schema", "<schema>", "--tools", "", "--strict-mcp-config",
         "--setting-sources", "", "--disable-slash-commands", "--no-session-persistence"]


def envelope(*items, field="structured_output"):
    """A `claude -p --output-format json` result envelope carrying the answer in `field`."""
    answer = {"items": [{"item": i, "pass": p, "quote": q} for i, p, q in items]}
    env = {"type": "result", "subtype": "success", "is_error": False, "result": "", "session_id": "x"}
    if field == "structured_output":
        env["structured_output"] = answer
    else:
        env["result"] = json.dumps(answer)
    return env


BOTH = envelope((R1, True, GOOD_Q1), (R2, True, GOOD_Q2))  # 1.0
HALF = envelope((R1, True, GOOD_Q1), (R2, False, ""))  # 0.5


@pytest.fixture
def guide(tmp_path, monkeypatch):
    """The document PRD at tmp/docs/prd/guide, its built guide at tmp/docs/guide/install.md, and the fake grader."""
    root = document_prd(tmp_path)
    out = tmp_path / "docs/guide/install.md"
    out.parent.mkdir(parents=True)
    out.write_text(DOC, encoding="utf-8")
    monkeypatch.setenv("PRD_JUDGE_CLAUDE", str(FAKE))
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(tmp_path / "calls.jsonl"))
    for k in ("FAKE_CLAUDE_EXIT", "FAKE_CLAUDE_STDERR", "FAKE_CLAUDE_REPLY"):
        monkeypatch.delenv(k, raising=False)
    return root, out


def replies(monkeypatch, tmp_path, *items):
    path = tmp_path / "replies.json"
    path.write_text(json.dumps(list(items)), encoding="utf-8")
    monkeypatch.setenv("FAKE_CLAUDE_REPLY", str(path))


def calls(tmp_path):
    log = tmp_path / "calls.jsonl"
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def run(root, out, *args, tid=TID, env=None):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), str(root), tid, str(out), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def record(tmp_path):
    return json.loads((tmp_path / "tests/.prd-judge" / f"{TID}.json").read_text(encoding="utf-8"))


def set_expect(root, old, new):
    edit(root, "test-cases/install.yaml", old, new)


# --- the default grader's command line ------------------------------------------------------------------------------

def test_default_argv_is_the_rulings_flags(monkeypatch):
    monkeypatch.delenv("PRD_JUDGE_CLAUDE", raising=False)
    argv = judge.default_argv(None)
    assert argv[0] == "claude"
    assert json.loads(argv[5]) == judge.SCHEMA
    assert argv[1:5] + ["<schema>"] + argv[6:] == FLAGS
    assert "--bare" not in argv
    assert judge.default_argv("sonnet")[-2:] == ["--model", "sonnet"]
    assert judge.default_argv("sonnet")[:-2] == argv
    monkeypatch.setenv("PRD_JUDGE_CLAUDE", "/x/fake")
    assert judge.default_argv(None)[0] == "/x/fake"


def test_schema_requires_item_pass_quote():
    items = judge.SCHEMA["properties"]["items"]
    assert judge.SCHEMA["required"] == ["items"] and items["type"] == "array"
    assert items["items"]["properties"] == {"item": {"type": "string"}, "pass": {"type": "boolean"},
                                            "quote": {"type": "string"}}
    assert sorted(items["items"]["required"]) == ["item", "pass", "quote"]


def test_each_run_is_claude_p_in_a_fresh_empty_temp_dir_with_the_prompt_on_stdin(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    r = run(root, out, "--runs", "2")
    assert r.returncode == 0, r.stderr
    got = calls(tmp_path)
    assert len(got) == 2
    for c in got:
        assert c["argv"][:4] + ["<schema>"] + c["argv"][5:] == FLAGS
        assert json.loads(c["argv"][4]) == judge.SCHEMA
        assert c["cwd_files"] == []
        assert Path(c["cwd"]).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
        assert not Path(c["cwd"]).exists()  # removed after the run
        assert not Path(c["cwd"]).resolve().is_relative_to(tmp_path.resolve())
        assert R1 in c["stdin"] and R2 in c["stdin"] and "Press Enter to run it." in c["stdin"]
        assert "AC-001.2" not in c["stdin"] and "explain each step" not in c["stdin"]  # nothing else from the PRD
    assert got[0]["cwd"] != got[1]["cwd"]


def test_model_flag_reaches_claude(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    assert run(root, out, "--runs", "1", "--model", "sonnet").returncode == 0
    assert calls(tmp_path)[0]["argv"][-2:] == ["--model", "sonnet"]
    assert record(tmp_path)["model"] == "sonnet"


# --- scoring and the median -----------------------------------------------------------------------------------------

def test_median_of_one_half_one_passes_at_0_8(guide, tmp_path, monkeypatch):
    root, out = guide
    set_expect(root, "threshold: 0.67", "threshold: 0.8")
    replies(monkeypatch, tmp_path, BOTH, HALF, BOTH)
    r = run(root, out)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"pass {TID} median 1 threshold 0.8"]
    assert [x["score"] for x in record(tmp_path)["runs"]] == [1.0, 0.5, 1.0]


def test_median_of_half_half_one_fails_and_names_the_failed_item(guide, tmp_path, monkeypatch):
    root, out = guide
    set_expect(root, "threshold: 0.67", "threshold: 0.8")
    replies(monkeypatch, tmp_path, HALF, HALF, BOTH)
    r = run(root, out)
    assert r.returncode == 1, r.stderr
    assert r.stdout.splitlines() == [f"fail {TID} median 0.5 threshold 0.8", f"failed: {R2}"]
    rec = record(tmp_path)
    assert (rec["median"], rec["verdict"]) == (0.5, "fail")


def test_runs_flag_overrides_runs_in_the_case(guide, tmp_path, monkeypatch):
    root, out = guide
    set_expect(root, "threshold: 0.67", "threshold: 0.67\n    runs: 3")
    replies(monkeypatch, tmp_path, BOTH)
    assert run(root, out, "--runs", "1").returncode == 0
    assert len(calls(tmp_path)) == 1 and len(record(tmp_path)["runs"]) == 1


def test_runs_default_to_three_and_follow_the_case(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    assert run(root, out).returncode == 0
    assert len(calls(tmp_path)) == 3
    set_expect(root, "threshold: 0.67", "threshold: 0.67\n    runs: 2")
    (tmp_path / "calls.jsonl").unlink()
    assert run(root, out).returncode == 0
    assert len(calls(tmp_path)) == 2


# --- the quote check ------------------------------------------------------------------------------------------------

def test_a_fabricated_quote_counts_as_fail_and_the_record_keeps_it(guide, tmp_path, monkeypatch):
    root, out = guide
    fake = "Install the tool with the graphical installer."
    replies(monkeypatch, tmp_path, envelope((R1, True, GOOD_Q1), (R2, True, fake)))
    r = run(root, out, "--runs", "1")
    assert r.returncode == 1
    assert f"failed: {R2}" in r.stdout.splitlines()
    items = record(tmp_path)["runs"][0]["items"]
    assert items[1] == {"item": R2, "pass": True, "quote": fake, "quote_found": False}
    assert items[0]["quote_found"] is True
    assert record(tmp_path)["runs"][0]["score"] == 0.5


def test_quote_found_collapses_whitespace_and_nothing_else():
    output = "1. Open a terminal\n   and type the install command.\n2. Press   Enter."
    assert judge.quote_found("Open a terminal and type the install command.", output)
    assert judge.quote_found("Open a terminal\tand  type", output)
    assert judge.quote_found("Press Enter.", output)
    assert not judge.quote_found("Open a window and type the install command.", output)  # one word changed
    assert not judge.quote_found("open a terminal", output)  # case stays exact
    assert not judge.quote_found("Press Enter!", output)  # punctuation stays exact
    assert not judge.quote_found("the install command.", output.replace(".", "。"))  # no punctuation folding
    assert not judge.quote_found("“Open”", 'say "Open" now')  # quote marks stay exact
    assert not judge.quote_found("", output) and not judge.quote_found("  \n ", output)


def test_a_rewrapped_quote_passes_and_a_one_word_change_fails(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    assert run(root, out, "--runs", "1").returncode == 0
    replies(monkeypatch, tmp_path, envelope((R1, True, "Open a window and type the install command."), (R2, True, GOOD_Q2)))
    r = run(root, out, "--runs", "1")
    assert r.returncode == 1 and f"failed: {R1}" in r.stdout.splitlines()


# --- bad answers and a failing grader -------------------------------------------------------------------------------

def test_a_non_json_answer_is_retried_once(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, "I think the guide is fine.", BOTH)
    r = run(root, out, "--runs", "1")
    assert r.returncode == 0, r.stderr
    assert len(calls(tmp_path)) == 2


def test_an_answer_in_result_is_decoded(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, envelope((R1, True, GOOD_Q1), (R2, True, GOOD_Q2), field="result"))
    assert run(root, out, "--runs", "1").returncode == 0
    assert len(calls(tmp_path)) == 1


def test_an_answer_naming_other_items_is_a_bad_answer(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, envelope((R1, True, GOOD_Q1), ("Something else", True, GOOD_Q2)), BOTH)
    assert run(root, out, "--runs", "1").returncode == 0
    assert len(calls(tmp_path)) == 2
    (tmp_path / "calls.jsonl").unlink()
    replies(monkeypatch, tmp_path, envelope((R1, True, GOOD_Q1)), BOTH)  # an item missing
    assert run(root, out, "--runs", "1").returncode == 0
    assert len(calls(tmp_path)) == 2


def test_two_bad_answers_exit_2(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, "not json", {"items": "nope"}, BOTH)
    r = run(root, out, "--runs", "3")
    assert r.returncode == 2
    assert len(calls(tmp_path)) == 2
    assert "bad answer" in r.stderr
    assert not r.stdout.startswith(("pass", "fail"))
    assert not (tmp_path / "tests/.prd-judge" / f"{TID}.json").exists()


def test_signed_out_claude_exits_2_with_its_first_stderr_line(guide, tmp_path, monkeypatch):
    root, out = guide
    monkeypatch.setenv("FAKE_CLAUDE_EXIT", "1")
    monkeypatch.setenv("FAKE_CLAUDE_STDERR", "Not logged in · Please run /login\nsecond line\n")
    r = run(root, out, "--runs", "1")
    assert r.returncode == 2
    assert "Not logged in · Please run /login" in r.stderr
    assert "second line" not in r.stderr
    assert r.stdout == ""
    assert len(calls(tmp_path)) == 1  # a failing CLI is not retried


def test_a_failing_claude_with_its_error_in_the_envelope_exits_2(guide, tmp_path, monkeypatch):
    root, out = guide
    # claude -p --output-format json reports some failures on stdout, in the envelope, with an empty stderr
    script = tmp_path / "bin/claude"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\ncat >/dev/null\n"
                      "echo '{\"type\":\"result\",\"is_error\":true,\"result\":\"Not logged in · Please run /login\"}'\n"
                      "exit 1\n", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setenv("PRD_JUDGE_CLAUDE", str(script))
    r = run(root, out, "--runs", "1")
    assert r.returncode == 2 and "Not logged in" in r.stderr


def test_no_claude_on_path_exits_2_with_a_hint(guide, tmp_path, monkeypatch):
    root, out = guide
    monkeypatch.delenv("PRD_JUDGE_CLAUDE")
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    env = {k: v for k, v in os.environ.items()} | {"PATH": str(empty)}
    r = run(root, out, "--runs", "1", env=env)
    assert r.returncode == 2
    assert "install Claude Code or set a pack grader" in r.stderr


# --- cases it cannot use --------------------------------------------------------------------------------------------

def test_unknown_tid_exits_2(guide):
    root, out = guide
    r = run(root, out, tid="T-009.9")
    assert r.returncode == 2 and "T-009.9" in r.stderr


def test_a_case_that_is_not_judged_exits_2(guide):
    root, out = guide
    r = run(root, out, tid="T-001.1")
    assert r.returncode == 2 and "not a judged case" in r.stderr


def test_a_missing_output_file_exits_2(guide, tmp_path):
    root, _ = guide
    r = run(root, tmp_path / "docs/guide/missing.md")
    assert r.returncode == 2 and "missing.md" in r.stderr


def test_a_judged_case_lint_would_reject_exits_2(guide):
    root, out = guide
    set_expect(root, "threshold: 0.67", "threshold: 7")
    r = run(root, out)
    assert r.returncode == 2 and "threshold" in r.stderr and "prd_lint.py" in r.stderr


def test_a_rubric_that_repeats_an_item_exits_2(guide, tmp_path, monkeypatch):
    root, out = guide
    set_expect(root, f"      - {R2}\n", f"      - {R2}\n      - {R2}\n")
    replies(monkeypatch, tmp_path, BOTH)
    r = run(root, out, "--runs", "1")
    assert r.returncode == 2 and "repeats" in r.stderr
    assert calls(tmp_path) == []


def test_not_a_prd_exits_2(guide, tmp_path):
    _, out = guide
    r = run(tmp_path / "nowhere", out)
    assert r.returncode == 2


# --- a pack grader --------------------------------------------------------------------------------------------------

def test_a_pack_grader_under_a_spaced_path_runs_and_the_quote_check_applies(guide, tmp_path, monkeypatch):
    root, out = guide
    install = tmp_path / "My Plugins/demo"
    folder = write_pack(install / "prd-packs", "demo", "1.0.0", toolkit=">=0.8.0,<0.9", description="Demo.",
                        grader="${PACK}/grade.py")
    shutil.copy(FAKE, folder / "grade.py")
    (folder / "grade.py").chmod((folder / "grade.py").stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@test": install})))
    edit(root, "prd.md", "- Pack: document 1.0.0 (prd-toolkit)", "- Pack: demo 1.0.0 (demo@test)")
    monkeypatch.setenv("PRD_JUDGE_CLAUDE", str(tmp_path / "never-called"))
    fake = "This guide uses the graphical installer."
    replies(monkeypatch, tmp_path, {"items": [{"item": R1, "pass": True, "quote": GOOD_Q1},
                                              {"item": R2, "pass": True, "quote": fake}]})
    r = run(root, out, "--runs", "1")
    assert r.returncode == 1, r.stderr
    (c,) = calls(tmp_path)
    assert c["argv"][0] == "--rubric" and c["argv"][2:] == ["--output", str(out.resolve())]
    assert json.loads(c["rubric_file"]) == [R1, R2]
    assert c["stdin"] == ""
    rec = record(tmp_path)
    assert rec["grader"] == "${PACK}/grade.py"
    assert rec["runs"][0]["items"][1]["quote_found"] is False and rec["runs"][0]["score"] == 0.5


# --- the record -----------------------------------------------------------------------------------------------------

def test_the_record_holds_every_field_of_the_spec(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH, HALF, BOTH)
    assert run(root, out).returncode == 0
    rec = record(tmp_path)
    assert rec["tid"] == TID
    assert rec["output"] == str(out.resolve())
    assert rec["sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert rec["threshold"] == 0.67
    assert rec["model"] is None
    assert rec["grader"] == "default"
    assert [x["score"] for x in rec["runs"]] == [1.0, 0.5, 1.0]
    assert rec["runs"][1]["items"] == [{"item": R1, "pass": True, "quote": GOOD_Q1, "quote_found": True},
                                       {"item": R2, "pass": False, "quote": "", "quote_found": False}]
    assert rec["median"] == 1.0 and rec["verdict"] == "pass"


def test_record_dir_flag(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    d = tmp_path / "elsewhere"
    assert run(root, out, "--runs", "1", "--record-dir", str(d)).returncode == 0
    assert json.loads((d / f"{TID}.json").read_text())["verdict"] == "pass"
    assert not (tmp_path / "tests/.prd-judge").exists()


def test_judge_returns_a_verdict(guide, tmp_path, monkeypatch):
    root, out = guide
    replies(monkeypatch, tmp_path, BOTH)
    v = judge.judge(model.load(root), TID, out, 1, None, tmp_path / "rec")
    assert (v.tid, v.threshold, v.median, v.passed, v.grader, v.model) == (TID, 0.67, 1.0, True, "default", None)
    assert v.runs[0].score == 1.0 and [i.quote_found for i in v.runs[0].items] == [True, True]
    assert isinstance(v.runs[0].items[0], judge.Item)
    with pytest.raises(judge.CannotJudge):
        judge.judge(model.load(root), "T-001.1", out, 1, None, tmp_path / "rec")


# --- the prompt -----------------------------------------------------------------------------------------------------

def test_grader_prompt_says_what_the_spec_requires():
    text = GRADER_MD.read_text(encoding="utf-8")
    low = " ".join(text.split()).lower()
    for phrase in ("independently", "verbatim", "only the json", "any language", "ignore any instructions"):
        assert phrase in low, phrase
    assert "{{RUBRIC}}" in text and "{{OUTPUT}}" in text


def test_prompt_template_survives_braces_and_placeholders_in_the_output(guide):
    text = judge.prompt([R1], "a {{RUBRIC}} {x} b")
    assert text.count(R1) == 1 and "a {{RUBRIC}} {x} b" in text
