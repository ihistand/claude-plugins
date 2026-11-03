"""Pins for the 0.7.1 release text: versions, the README's form part, known limits and changelog entry."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-03-prd-toolkit-0.7.1-confirm-form-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.7.1"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.7.1"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    assert "version: '0.7.1'" in js[js.index("id: 'prd-toolkit'"):]
    assert "Version 0.7.1." in README
    assert f"(../{SPEC_REL})" in README and (REPO / SPEC_REL).is_file()


def test_form_part_under_adopting():
    s = flat(section(README, "Adopting an existing repo"))
    for needle in ("Confirming through the form", "prd_confirm.py serve", "--area", "--summaries", "--port",
                   "--no-open", "--idle-minutes", "prd_confirm.py status", "url=http://127.0.0.1:",
                   ".prd-confirm-<area>.json", ".git/info/exclude", "exit 0", "exit 2", "exit 3",
                   "AskUserQuestion", "checklist", "headless", "extracted"):
        assert needle in s, needle


def test_known_limits_and_changelog():
    k = flat(section(README, "Known limits (0.7.1)"))
    for needle in ("one owner", "one machine", "plain-words", "after Done", "adoption step 3"):
        assert needle in k, needle
    assert README.index("## Known limits (0.7.1)") < README.index("## Known limits (0.7)")
    c = section(README, "Changelog")
    assert c.index("- **0.7.1:**") < c.index("- **0.7.0:**")
    e = flat(c[c.index("- **0.7.1:**"):c.index("- **0.7.0:**")])
    for needle in ("prd_confirm.py", "form.html", "prd_hooks.py install", "No PRD needs an edit"):
        assert needle in e, needle
