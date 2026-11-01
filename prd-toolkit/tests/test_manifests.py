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
    for cmd in ("/prd-build", "/prd-status"):
        assert cmd in plugin["description"]


def test_web_description_matches():
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(p for p in market["plugins"] if p["name"] == "prd-toolkit")
    js = (ROOT / "web/src/data/plugins.js").read_text()
    assert re.search(r"description: '" + re.escape(entry["description"]) + "'", js)
