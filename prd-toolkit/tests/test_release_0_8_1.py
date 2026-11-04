"""Pins for the 0.8.1 release text: versions, the README's machine interface, known limits and changelog, the
format reference and the spec's Revisions."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
FORMAT = (ROOT / "references/prd-format.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.1-design.md"
SPEC = (REPO / SPEC_REL).read_text(encoding="utf-8")


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.8.1"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.8.1"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert "version: '0.8.1'" in block
    assert "{ label: 'Design spec (0.8.1)', url: 'https://github.com/ihistand/claude-plugins/blob/main/" + SPEC_REL + "' }" in block
    assert "Version 0.8.1." in README
    assert f"(../{SPEC_REL})" in README


def test_readme_machine_interface():
    m = flat(section(README, "Machine interface"))
    for needle in ('"interface": 1', '"kind"', "--json", "--json=1", "--interface", "never removed or renamed",
                   "`0`", "`1`", "`2`", "prd_change.py ids next", "prd_change.py bump", "prd_change.py record",
                   "prd_change.py digest", "prd_change.py approve", "`needs judgment`", "`; pending`",
                   "`.prd-review.json`", "prd_gates.py list", "prd_gates.py answer", "--question",
                   "refused: the gate changed; list again", "`approve`", "`changes`", "--choice changes",
                   "/prd-change --review", "claude -p", "prd_confirm.py answer", "prd_confirm.py open",
                   "prd_confirm.py done", "edits nothing"):
        assert needle in m, needle
    order = m[m.index("The order a client runs"):]
    order = order[:order.index(".")]
    assert order.index("bump") < order.index("review") < order.index("record") < order.index("lint")
    assert README.index("## Machine interface") < README.index("## Known limits (0.8.1)")


def test_readme_known_limits():
    k = flat(section(README, "Known limits (0.8.1)"))
    for needle in ("conservative", "`needs judgment`", "held by instruction", "--question", "stdout is empty",
                   "Change-set:"):
        assert needle in k, needle
    assert README.index("## Known limits (0.8.1)") < README.index("## Known limits (0.8.0)")


def test_changelog_entry_names_the_json_break_and_fr_014():
    c = section(README, "Changelog")
    assert c.index("- **0.8.1:**") < c.index("- **0.8.0:**")
    e = flat(c[c.index("- **0.8.1:**"):c.index("- **0.8.0:**")])
    for needle in ("`prd_status.py --json` and `prd_context.py --json` printed a bare JSON list",
                   '`{"interface": 1, "kind": …}`', "anything that parses them must change",
                   "FR-014", "`--json`", "`--interface`", "4.0.0", "prd_change.py", "prd_gates.py",
                   "/prd-change --review", "prd_hooks.py install", "`.prd-review.json`", "No PRD needs an edit"):
        assert needle in e, needle


def test_format_documents_uj_pending_and_the_verdict():
    f = flat(FORMAT)
    six = flat(FORMAT[FORMAT.index("6. IDs are never reused."):FORMAT.index("## Test cases")])
    assert "The next free UJ number is the highest UJ number in the PRD, removed ones included, plus 1, written with two digits (`UJ-03`)" in six
    assert "`prd_change.py ids next <prd dir>" in six
    for needle in ("`<change>; pending`", "`prd_change.py record`", "`prd_change.py approve`",
                   "`.prd-review.json`", "never committed", "git-ignored"):
        assert needle in f, needle


def test_spec_revisions_name_each_ruling():
    head = SPEC[:SPEC.index("## 1. Scope")]
    assert "> **Revisions.**" in head
    rev = flat(re.sub(r"^> ?", "", head, flags=re.M))
    for needle in (
        "bare JSON list",                                            # status/context --json break
        "one entry per item",                                        # context parts
        "`unsupported interface <N>; this toolkit speaks 1`",        # lint/trace findings, --json=N
        '`"dir"`',
        "`<change>; pending`",                                       # §14 record token
        "two digits",                                                # ids next UJ
        "`change.BUMP_RULES`",                                       # bump rules as applied
        "`change.contract_items`",                                   # contract items
        "`docs(prd): approve <slug> <version>`",                     # approve commit
        "`prd_deploy.py confirm <prd dir> --run ID --step N --reply TEXT`",  # deploy argv, adoption items
        '`"items"`',
        "0.8.2 decision-inbox spec §6 (Ivan, 2026-11-04)",           # gate changes
        "(R7)", "(R8)", "(R9)", "(R11)", "(R12)",
    ):
        assert needle in rev, needle
