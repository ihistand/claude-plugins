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
                   ".prd-confirm-<area>.json", ".git/info/exclude", "AskUserQuestion", "checklist", "headless",
                   "extracted"):
        assert needle in s, needle


def test_form_exit_codes_are_pinned_as_meanings():
    s = flat(section(README, "Adopting an existing repo"))
    for phrase in ("`serve` ends with exit 0 when Done: every item answered and none changed since",
                   "exit 2 for a usage error or a refusal, with `prd_confirm: <why>` on stderr",
                   "exit 3 when stopped without Done (Ctrl-C, SIGTERM or the idle time)",
                   "`status` prints `<answered>/<total>` and one `open <ID>` line per open item, and exits 0 when "
                   "it prints and 2 on error",
                   "adds the line `/.prd-confirm-*.json` to `.git/info/exclude`"):
        assert phrase in s, phrase


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
