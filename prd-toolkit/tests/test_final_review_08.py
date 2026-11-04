"""prd-toolkit 0.8.0 final review: the fix wave's text and small behaviour pins (Important 2, 4, 5 and the minors).

The rule changes (judged-case, test-refs, pack-resolves) are pinned in test_rules_packs.py and test_hooks_packs.py."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import edit
from doc_fixture import document_prd
from packs_fixture import write_pack

from prdlint import packs

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
SKILLS = ROOT / "skills"
AUTHORING = SKILLS / "authoring-prds/SKILL.md"
ADOPTING = SKILLS / "adopting-prds/SKILL.md"
TESTING = SKILLS / "testing-from-prds/SKILL.md"
TESTER = ROOT / "agents/prd-tester.md"
ERRORS = SKILLS / "handling-errors/SKILL.md"
DOCUMENT = ROOT / "packs/document"
SPEC = REPO / "docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.0-design.md"
README = ROOT / "README.md"
FORMAT = ROOT / "references/prd-format.md"
CONTRACT_TYPES = ROOT / "references/contract-types.md"
MISSING_JUDGE = "`<T-id>: fail: environment: .prd-toolkit/prd_judge.py is missing; run prd_hooks.py install`"


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def phase_row(n: int) -> str:
    for line in AUTHORING.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {n} | "):
            return line
    raise AssertionError(f"no phase {n} row")


def section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    a = text.index(f"\n{heading}\n") + 1
    level = heading.split(" ", 1)[0]
    b = text.find(f"\n{level} ", a + 1)
    return " ".join(text[a:b if b > 0 else len(text)].split())


# ---------------------------------------------------------------- Important 2: the threshold arithmetic

def test_rubrics_state_the_threshold_arithmetic():
    s = flat(DOCUMENT / "rubrics.md")
    assert "a run's score is passed ÷ items" in s
    assert "2 of 3 is 0.666…, so write 0.66 (0.67 needs all three); 3 of 4 is 0.75 (0.8 needs all four)" in s
    assert "tolerates one soft item failing" not in s and "0.67 to 0.8" not in s


def test_examples_use_0_66_for_three_items():
    text = AUTHORING.read_text(encoding="utf-8")
    correct = text.split("A judged case's rubric:", 1)[1].split("CORRECT\n", 1)[1].split("```", 1)[0]
    assert correct.count("      - ") == 3 and "threshold: 0.66" in correct
    for path in (AUTHORING, FORMAT, SPEC):
        assert "threshold: 0.67" not in path.read_text(encoding="utf-8"), path.name
    t = SPEC.read_text(encoding="utf-8")
    case = t.split("T-004.2:\n", 1)[1].split("```", 1)[0]
    assert case.count("      - ") == 3 and "threshold: 0.66" in case
    assert "- §7 T-004.2 example threshold 0.66, not 0.67 (2 of 3 is 0.666…; final review)" in t.split("## 1. Scope")[0]
    fmt = FORMAT.read_text(encoding="utf-8").split("T-004.2:\n", 1)[1].split("```", 1)[0]
    assert fmt.count("      - ") == 3 and "threshold: 0.66" in fmt


# ---------------------------------------------------------------- Important 4: the judge needs the hooks install

def test_authoring_phase_7_requires_the_install_for_judged_cases():
    row = phase_row(7)
    assert ("A PRD with any judged case requires the hooks install, not an offer: its judged tests call "
            "`.prd-toolkit/prd_judge.py`, which only `prd_hooks.py install` writes.") in row


def test_adopting_step_5_requires_the_install_for_judged_cases():
    s = flat(ADOPTING)
    assert ("An area with any judged case requires the hooks install, not an offer: its judged tests call "
            "`.prd-toolkit/prd_judge.py`, which only `prd_hooks.py install` writes.") in s


def test_document_pack_names_the_judge_on_the_runner():
    p = packs.load_manifest(DOCUMENT, "prd-toolkit")
    tools = p.harness["Tools on the runner"]
    assert "`.prd-toolkit/prd_judge.py` (written by `prd_hooks.py install`)" in tools
    assert "uv" in tools and "claude" in tools


def test_missing_judge_is_an_environment_problem():
    s = section(TESTING, "## A judged case")
    assert "A missing `.prd-toolkit/prd_judge.py` (the hooks were never installed) is an environment problem, not a test failure" in s
    assert MISSING_JUDGE in s
    t = flat(TESTER)
    assert "A missing `.prd-toolkit/prd_judge.py` is an environment problem, not a test failure" in t and MISSING_JUDGE in t
    assert "and so is a judged test that finds no `.prd-toolkit/prd_judge.py`" in flat(ERRORS)


# ---------------------------------------------------------------- Important 5: the document pack's parsing conventions

PARSING = ("A checks test parses each document as CommonMark 0.31.2 after NFC normalization. A section is a level-2 "
           "heading whose text equals an entry of the document's `sections`, each entry heading exactly one section, "
           "and it runs to the next level-2 heading. Every other comparison of text is exact.")


def test_document_pack_fixes_the_markdown_conventions():
    p = packs.load_manifest(DOCUMENT, "prd-toolkit")
    assert p.version == "1.0.0"
    assert "A judged test asserts `prd_judge.py`'s exit code and nothing else." in p.harness["Assertions"]
    assert PARSING in p.harness["Assertions"]


def test_document_clarify_asks_the_parsing_standard_up_front():
    s = flat(DOCUMENT / "clarify.md")
    assert "**Parsing standard.**" in s and "CommonMark 0.31.2 after NFC normalization" in s
    assert "the Harness Assertions slot" in s


def test_outline_and_readme_describe_a_section():
    assert "A section is a level-2 heading whose text equals a `sections` entry" in section(CONTRACT_TYPES, "## outline")
    assert "CommonMark 0.31.2 after NFC normalization" in section(CONTRACT_TYPES, "## outline")
    assert "CommonMark 0.31.2 after NFC normalization" in flat(README)


# ---------------------------------------------------------------- minors

def test_readme_known_limits_08():
    s = section(README, "## Known limits (0.8.0)")
    assert ("An `es` NFR states its bound with an English unit for now (`200 ms`, `5 minutes`, not `5 minutos`): "
            "units move to the language table in 0.8.1.") in s
    assert "field labels stay English" in s and "; labels stay English" not in s
    assert ("A headless `claude -p` run of the skills needs Bash permission rules for `echo` (every gate echoes its exit "
            "code), `mktemp`, `GIT_INDEX_FILE=` and `sort` (the tester's state snapshot), and `--add-dir` for the user "
            "temp directory") in s


def test_toolkit_operators_are_documented_and_named_in_the_error(tmp_path):
    s = section(CONTRACT_TYPES, "## pack")
    assert ("`toolkit:` is comma-separated clauses, each an operator (`>=`, `>`, `<=`, `<`, `==` or `!=`) and a version "
            "`X`, `X.Y` or `X.Y.Z`; every clause must hold. `~=` and wildcards (`==0.8.*`) are not accepted.") in s
    for spec in ("~=0.8", "==0.8.*"):
        folder = write_pack(tmp_path / spec.replace("*", "x"), "demo", "1.0.0", toolkit=spec)
        with pytest.raises(packs.ManifestError) as e:
            packs.load_manifest(folder, "demo@test")
        assert str(e.value) == ("pack demo: pack.yaml: toolkit must be a version range such as >=0.8.0,<0.9: "
                                "comma-separated clauses of >=, >, <=, <, == or != and a version X, X.Y or X.Y.Z")


def test_prd_format_reads_two_profile_lines():
    s = section(FORMAT, "### §1 lines")
    assert "Two bullet lines in `## 1. Metadata & stack` are read for the profile, `Pack:` and `Output language:`" in s
    assert "Three bullet lines" not in s


def test_descriptions_are_one_clean_list():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["description"]
    assert "packs, languages and judged test cases" in plugin
    assert "across repositories, and packs" not in plugin and "change it, and a builder" not in plugin
    assert plugin.split(". Includes")[0].count(", and ") == 1


def test_mixed_prd_area_pack_fills_only_open_slots():
    s = section(AUTHORING, "### Applying the pack")
    assert ("An area pack's `harness` fills only slots still marked `[NEEDS CLARIFICATION]`; it never overwrites a "
            "decided slot.") in s


# ---------------------------------------------------------------- the default grader's isolation, live (opt-in)

LIVE = shutil.which("claude") is not None and bool(os.environ.get("PRD_JUDGE_LIVE"))
HOSTS = "Read the file /etc/hosts and quote its first line"
GOOD = """# Install guide

## Requirements

You need a computer with Python 3.11, pip and the uv tool.

## Install

1. Open a terminal.
2. Type `uv tool install greet`.
3. Press Enter.

## First run

Type `greet --name you` and read the greeting.
"""


@pytest.mark.skipif(not LIVE, reason="live grader: needs `claude` on PATH and PRD_JUDGE_LIVE set")
def test_default_grader_gets_no_tool_live(tmp_path, monkeypatch):
    """Spec §12: a run whose rubric asks the grader to read a file gets no tool (Task 7's live check)."""
    monkeypatch.delenv("PRD_JUDGE_CLAUDE", raising=False)
    root = document_prd(tmp_path)
    edit(root, "test-cases/install.yaml", "      - No step relies on a tool that Requirements does not list\n",
         f"      - No step relies on a tool that Requirements does not list\n      - {HOSTS}\n")
    out = tmp_path / "docs/guide/install.md"
    out.parent.mkdir(parents=True)
    out.write_text(GOOD, encoding="utf-8")
    r = subprocess.run(["uv", "run", "--script", str(ROOT / "scripts/prd_judge.py"), str(root), "T-001.2", str(out),
                        "--runs", "1", "--record-dir", str(tmp_path / "rec")],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode in (0, 1), r.stderr  # judged (2 would be the CLI failing, not isolation)
    record = (tmp_path / "rec/T-001.2.json").read_text(encoding="utf-8")
    item = next(i for i in json.loads(record)["runs"][0]["items"] if i["item"] == HOSTS)
    assert not (item["pass"] and item["quote_found"])  # no quote from /etc/hosts can be found in the guide
    first = next((ln for ln in Path("/etc/hosts").read_text().splitlines() if ln.strip() and not ln.startswith("#")), None)
    if first:
        assert first not in record  # the grader never saw the file


# ---------------------------------------------------------------- Important 1b and the broken vendored pack, in the docs

def test_docs_describe_the_source_record_and_the_vendored_listing():
    s = flat(README)
    assert ("Run from a vendored copy, `--list-packs` lists the packs vendored in `.prd-toolkit/packs/` in place of the "
            "built-ins, each with the source `.prd-toolkit/pack-sources.json` records, and a line on stderr says so") in s
    assert "records each one's source in `.prd-toolkit/pack-sources.json`" in s
    assert "records each one's source in `.prd-toolkit/pack-sources.json`" in section(CONTRACT_TYPES, "## pack")
    assert "| `vendored <name> has no pack.yaml; run prd_hooks.py install` |" in FORMAT.read_text(encoding="utf-8")
