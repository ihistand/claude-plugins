"""Pins for the 0.8.2 release text: versions, the README's inbox part, known limits and changelog, and the three wording fixes."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
FORMAT = (ROOT / "references/prd-format.md").read_text(encoding="utf-8")
CHANGE_SET = (ROOT / "skills/coordinating-prds/running-a-change-set.md").read_text(encoding="utf-8")
TESTER = (ROOT / "agents/prd-tester.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def entry() -> str:
    c = section(README, "Changelog")
    return flat(c[c.index("- **0.8.2:**"):c.index("- **0.8.1:**")])


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.8.2"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.8.2"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert "version: '0.8.2'" in block
    assert "{ label: 'Design spec (0.8.2)', url: 'https://github.com/ihistand/claude-plugins/blob/main/" + SPEC_REL + "' }" in block
    assert "Version 0.8.2." in README
    assert f"(../{SPEC_REL})" in README


def test_readme_commands_and_exit_codes():
    s = flat(section(README, "Decision inbox"))
    for needle in ("prd_gates.py serve", "--gate", "--port", "--no-open", "--idle-minutes", "url=http://127.0.0.1:",
                   "prd_gates.py wait", "--worktree", "--timeout", "gates.outcome",
                   "`serve` exits 3 when stopped (Ctrl-C, SIGTERM or the idle time), 1 when refused", "2 when it cannot start",
                   "`wait` exits 0 when answered, 1 when the gate is not pending, 3 on timeout",
                   "prd_build_check.py --stale", "--tids", "`--stale` exits 0 when nothing is stale, 1 when any is, 2 on a usage or tool error",
                   "`Rewrite: <T-id>`",
                   "prd_deploy.py record", "--env", "--commit", "--reply", "`record` exits 0, 1 when refused",
                   "moves no status",
                   "`prd-inbox-<slug>.json`", "`prd-gates-log.jsonl`", "`prd-gates-answering/`", "older than 15 minutes",
                   "a dead pid", "`.prd-toolkit/gates/inbox.html`", "` (form)`", "an inbox is already serving at"):
        assert needle in s, needle
    assert README.index("## Decision inbox") < README.index("## Known limits (0.8.2)")


def test_readme_known_limits():
    k = flat(section(README, "Known limits (0.8.2)"))
    for needle in ("cannot prove a person clicked", "Signing as", "up to 5 seconds", "grows without bound",
                   "cannot start the inbox: …", "ask in the chat", "longer than 15 minutes", "`wait` exit 1",
                   "lists the gates again"):
        assert needle in k, needle
    assert README.index("## Known limits (0.8.2)") < README.index("## Known limits (0.8.1)")


def test_changelog_entry():
    c = section(README, "Changelog")
    assert c.index("- **0.8.2:**") < c.index("- **0.8.1:**")
    e = entry()
    for needle in (
        "prd_gates.py serve", "prd_gates.py wait", "`by`", "(form)", "`.prd-toolkit/gates/inbox.html`",
        "`/ping`", "Keep it as it is", "Change it…", "Answer in my own words",      # section 13
        "`--touches -`", "`Touches: -`", "E-012 follows E-010",
        "`<id>.output`", "`.prd-toolkit/packs/`",                                  # section 14
        "`prd_build_check.py --stale`", "`Rewrite:`",                              # section 15
        "`symptom:`", "names no symptom",                                          # section 16
        "`prd_deploy.py record`", "`prd_block.py`", "round branch", "`--tb=short`",  # section 17
        "verified with no build-gate test", "`prd-round/<area>-<n>`",
        "retargeting an area is a conversion, which a later prd-toolkit release brings",
        "the 0.8.1 interface", "approval gate", "`done`", "`prd_confirm.py open`",
    ):
        assert needle in e, needle
    assert "re-run `prd_hooks.py install`" in e and "Re-run `prd_block.py`" in e


def test_format_deployed_names_record():
    i = FORMAT.index("`## Deployed` is the PRD's record")
    a = flat(FORMAT[i:FORMAT.index("**Migration from 0.4.**", i)])
    for needle in ("`prd_deploy.py record <prd dir>", "deploy the owner did by hand", "moves no status", "never writes that row directly"):
        assert needle in a, needle


def test_change_set_names_the_round_branch():
    t = flat(CHANGE_SET)
    assert "builder's worktree" not in t
    assert "`prd-round/<area>-<n>` branch" in t and "in the session's own worktree" in t


def test_tester_description_matches_the_round_branch_build():
    d = TESTER.split("\n", 4)[2]
    assert d.startswith("description:")
    assert "built elsewhere" not in d
    assert "while the builder's round runs on its own branch" in d


def test_the_changelog_links_the_spec_its_sections_name():
    e = entry()
    assert "(section 13)" in e
    assert f"[design spec](../{SPEC_REL})" in e
    assert e.index(f"[design spec](../{SPEC_REL})") < e.index("(section 13)")


def test_wait_says_exit_0_always_names_the_choice():
    row = flat(next(line for line in README.splitlines() if line.startswith("| `prd_gates.py wait` |")))
    assert "at exit 0 `choice` is the answer's, `confirm` for a deploy step" in row


def test_the_tester_rewrite_scaffold_header_says_what_it_builds():
    header = (ROOT / "evals/tester-rewrite-only-that-test/scaffold.sh").read_text(encoding="utf-8").splitlines()[1]
    assert "one note stored first" in header and "corrects T-001.1's expected id from 1 to 2" in header
    assert "corrects T-001.1's test case input" not in header


def test_the_0_8_2_baseline_says_no_stale_uncommitted_and_keeps_each_table_whole():
    text = (ROOT / "evals/BASELINE.md").read_text(encoding="utf-8")
    part = text[:text.index("### Rounds and rulings (0.8.1)")]  # the 0.8.2 tasks' records
    assert "(uncommitted)" not in part
    lines = part.split("\n")
    split = [n + 1 for n in range(1, len(lines) - 1) if lines[n] == "" and lines[n - 1].startswith("|") and lines[n + 1].startswith("|")]
    assert split == []
