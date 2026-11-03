"""Pins for the 0.7.3 release: versions and the changelog entry for the lint-cli fixes (E-001 to E-006) and the hook fix."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def flat(s: str) -> str:
    return " ".join(s.split())


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == [plugin["version"]]
    js = (REPO / "web/src/data/plugins.js").read_text()
    assert f"version: '{plugin['version']}'" in js[js.index("id: 'prd-toolkit'"):]
    assert re.search(r"Version \d+\.\d+\.\d+\.", README)


def test_changelog_entry():
    c = README[README.index("\n## Changelog\n"):]
    assert c.index("- **0.7.3:**") < c.index("- **0.7.2:**")
    e = flat(c[c.index("- **0.7.3:**"):c.index("- **0.7.2:**")])
    for needle in ("E-001", "E-006", "linked worktree", "GIT_DIR", "GIT_WORK_TREE", "prd_hooks.py install",
                   "No PRD needs an edit"):
        assert needle in e, needle
