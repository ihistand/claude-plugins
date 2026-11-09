"""Pins for the 0.8.3 release text: versions, the README's vendor row, local-testing note and changelog entry."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-06-prd-toolkit-0.8.3-backlog-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def entry() -> str:
    c = section(README, "Changelog")
    return flat(c[c.index("- **0.8.3:**"):c.index("- **0.8.2:**")])


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])  # the current release is pinned in the newest test_release_*.py
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == [plugin["version"]]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert f"version: '{plugin['version']}'" in block
    assert "{ label: 'Design spec (0.8.3)', url: 'https://github.com/ihistand/claude-plugins/blob/main/" + SPEC_REL + "' }" in block
    assert re.search(r"Version \d+\.\d+\.\d+\.", README)
    assert f"(../{SPEC_REL})" in README
    assert (REPO / ".prd-toolkit/VERSION").read_text().strip() == plugin["version"]


def test_changelog_entry():
    c = section(README, "Changelog")
    assert c.index("- **0.8.3:**") < c.index("- **0.8.2:**")
    e = entry()
    for needle in (
        "prd_hooks.py vendor", "`vendored the toolkit into .prd-toolkit/ (version <X.Y.Z>)`",
        "`<path>: differs from the plugin; refresh it with prd_hooks.py vendor`", "--diff", "byte for byte",
        "`prd_change.py record`", "Since", "contract item",
        "`prd_build_check: <prd> is not in a git working tree`", "`--stale`", "`--results`",
        "`base`", "`refs`", "`prd_deploy: internal error: <type>: <message>`", "`beforeDone`",
        "`prd_gates: standby: <type>: <message>`", "cannot start the inbox",
        "Upgrading from 0.8.2", "re-run `prd_hooks.py install docs/prd/<slug>`", "No PRD needs an edit",
        "written before the upgrade still makes a gate",
    ):
        assert needle in e, needle
    assert f"[design spec](../{SPEC_REL})" in e


def test_script_table_and_upgrade_name_vendor():
    row = next(line for line in README.splitlines() if line.startswith("| `prd_hooks.py vendor` |"))
    assert "`.prd-toolkit/`" in row and "install" in row
    hooks = flat(section(README, "Hooks and CI"))
    assert "prd_hooks.py vendor docs/prd/<slug>" in hooks and "This repository" in hooks


def test_local_testing_note():
    t = flat(section(README, "Tests and evals"))
    assert "claude --plugin-dir" in t and "`/prd-toolkit:prd-change`" in t and "bare `/prd-change`" in t

