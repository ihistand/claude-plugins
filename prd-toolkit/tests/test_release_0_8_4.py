"""Pins for the 0.8.4 release text: versions, the README's part on the PRD READMEs and the Overview tab, the upgrade note and the changelog entry."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def entry() -> str:
    c = section(README, "Changelog")
    assert c.index("- **0.8.4:**") < c.index("- **0.8.3:**")
    return flat(c[c.index("- **0.8.4:**"):c.index("- **0.8.3:**")])


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])  # the current release is pinned in the newest test_release_*.py
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == [plugin["version"]]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert f"version: '{plugin['version']}'" in block
    assert "{ label: 'Design spec (0.8.4)', url: 'https://github.com/ihistand/claude-plugins/blob/main/" + SPEC_REL + "' }" in block
    assert re.search(r"Version \d+\.\d+\.\d+\.", README)
    assert f"(../{SPEC_REL})" in README and (REPO / SPEC_REL).is_file()
    assert (REPO / ".prd-toolkit/VERSION").read_text().strip() == plugin["version"]


def test_readme_part_names_the_readmes_and_the_tab():
    s = flat(section(README, "READMEs and the Overview tab"))
    for needle in ("docs/prd/<slug>/README.md", "docs/prd/README.md", "<!-- prd-toolkit:start -->",
                   "<!-- prd-toolkit:end -->", "prd_block.py", "check --ci", "stale: <file>; run prd_block.py docs/prd/<slug>",
                   "Overview", "Principles:", "Getting started:", "optional", "never edited by hand",
                   "CLAUDE.md", "prd_hooks.py install"):
        assert needle in s, needle


def test_upgrade_watch_item_and_known_limit():
    s = flat(section(README, "READMEs and the Overview tab"))
    assert "hand-edited" in s and "fails `check --ci` until" in s
    k = flat(section(README, "Known limits (0.8.4)"))
    assert "Two branches" in k and "prd_block.py" in k
    assert README.index("## Known limits (0.8.4)") < README.index("## Known limits (0.8.2)")


def test_guard_list_names_the_checked_grep():
    t = flat(section(README, "Testing from the PRD"))
    assert "a checked `grep`" in t and "`ls`, `mkdir`" in t


def test_changelog_entry():
    e = entry()
    assert f"[design spec](../{SPEC_REL})" in e
    for needle in (
        "docs/prd/README.md", "docs/prd/<slug>/README.md", "Overview", "Principles:", "Getting started:",
        "`check --ci`", "stale", "hand-edited", "two branches", "FR-015", "5.1.0",
        # the ten fixes of spec section 16
        "`symptom:` line",                                   # 1
        "`--directory <d>`",                                     # 2
        "checked `grep`", "`--include`", "`--exclude`", "before the pattern",  # 3
        "--literal-pathspecs",                         # 4
        "base or the working tree",                          # 5
        "executable bit", "timed out after",                 # 6
        "`deploy-step:<run id>:unreadable`",                 # 7
        "`gates`", "`change`", "`judge`", "`packs`", "`not started`",  # 8
        "first non-blank stdout line",                       # 9
        "PR #18", "5.0.0", "first ships to installs in 0.8.4",  # 10
    ):
        assert needle in e, needle
    assert "The fixes from the 0.8.2 proof" in flat(section(README, "Changelog"))  # the 0.8.3 entry stays
    assert "a directory or broken link named `<name>.yaml`" in flat(section(README, "Changelog"))
