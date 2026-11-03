"""plugin.json and marketplace.json describe the toolkit identically."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def test_descriptions_match_and_name_new_commands():
    plugin = json.loads((ROOT / "prd-toolkit/.claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(p for p in market["plugins"] if p["name"] == "prd-toolkit")
    assert plugin["description"] == entry["description"]
    assert plugin["version"] == entry["version"]
    for cmd in ("/prd-build", "/prd-status", "/prd-deploy", "/prd-change-set"):
        assert cmd in plugin["description"]


def test_versions_agree_and_are_semver():
    plugin = json.loads((ROOT / "prd-toolkit/.claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(p for p in market["plugins"] if p["name"] == "prd-toolkit")
    assert plugin["version"] == entry["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", plugin["version"])


def test_web_description_matches():
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(p for p in market["plugins"] if p["name"] == "prd-toolkit")
    js = (ROOT / "web/src/data/plugins.js").read_text()
    assert re.search(r"description: '" + re.escape(entry["description"]) + "'", js)


def test_description_says_links_across_repositories():
    plugin = json.loads((ROOT / "prd-toolkit/.claude-plugin/plugin.json").read_text())
    assert "links PRDs across repositories" in plugin["description"]


def test_version_is_0_7_1():
    plugin = json.loads((ROOT / "prd-toolkit/.claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.7.1"
