"""Pins for the 0.7.0 release text: versions, the README's Links and Change sets sections, the format reference and the spec's Revisions."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
FORMAT = (ROOT / "references/prd-format.md").read_text(encoding="utf-8")
BASE_SPEC = (REPO / "docs/superpowers/specs/2026-10-29-prd-toolkit-design.md").read_text(encoding="utf-8")
SPEC_07 = "docs/superpowers/specs/2026-11-02-prd-toolkit-0.7-design.md"
SPEC = (REPO / SPEC_07).read_text(encoding="utf-8")
TRAILER_RE = r"^Change-set:[ \t]*([a-z][a-z0-9-]*/CS-\d{3})[ \t]*$"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.7.0"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.7.0"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert "version: '0.7.0'" in block
    assert "/prd-change-set" in block and "coordinating-prds" in block
    assert SPEC_07.split("docs/superpowers/specs/")[1] in block
    assert "links PRDs across repositories" in plugin["description"] and "/prd-change-set" in plugin["description"]


def test_readme_version_spec_link_and_rules():
    assert "Version 0.7.0." in README
    assert f"(../{SPEC_07})" in README and (REPO / SPEC_07).is_file()
    assert "a 36-rule linter" in flat(README) and "prints the 36 rules" in flat(README)
    assert "- **0.7.0:**" in README


def test_links_and_change_sets_sections():
    s = flat(section(README, "Links"))
    for needle in ("links.md", "prd_links.py add", "sync", "check", "impact", "contracts/upstream/", "Needs",
                   "<kind>:<prd>/<name>", "check --ci", "exit 3", "git URL", "asyncapi"):
        assert needle in s, needle
    c = flat(section(README, "Change sets"))
    for needle in ("/prd-change-set", "changes/CS-nnn.md", "prd_links.py changeset", "one approval", "Merge order",
                   "Change-set:", "cs-<nnn>-<slug>", "nothing is pushed", "resume"):
        assert needle in c or needle.lower() in c.lower(), needle


def test_headless_note_and_upgrade_note():
    s = flat(README)
    assert "A headless run registers only `prd-toolkit:<command>`" in s
    assert "Upgrading from 0.6:" in s
    up = s.split("Upgrading from 0.6:", 1)[1]
    assert "re-run `prd_hooks.py install`" in up and "`prd_hooks.py ci`" in up
    assert "A PRD without `links.md` needs no edit" in up
    assert "re-run `prd_block.py`" in up and "vendored block templates are stale" in up.replace("vendored block template is stale", "vendored block templates are stale")


def test_format_reference():
    s = flat(FORMAT)
    assert "## links.md" in FORMAT
    for needle in ("contracts/upstream/<prd>/", "Snapshot of <prd> <version> at <commit>, written by prd_links.py sync. Do not edit.",
                   " Type: <kind>.", " Dialect: <dialect>.", "changes/CS-nnn.md", "Change-set: <prd>/CS-nnn",
                   "<kind>:<prd>/<name>", "`<prd>/<table>.<column>`", "`/* */` comments", "asyncapi"):
        assert needle in s, needle
    assert TRAILER_RE in FORMAT
    assert re.search(TRAILER_RE, "Change-set: greet/CS-001", re.M)


REVISION_NEEDLES = {
    "stop on Status": "stopped: <prd>: <reason>",
    "snapshot header": "Type: <kind>.",
    "check --ci": "`check --ci`",
    "prefix": "`<a>/<t>.<c>`",
    "empty Needs": "first `deploy`-gate level",
    "latest-env Target": "later in the upstream's `operations.md` Environments table",
    "consumers": "default branch",
    "R-2a": "R-2a",
    "R-8a": "R-8a",
    "R-8b": "R-8b",
    "R-10b": "R-10b",
    "R-10c": "R-10c",
    "R-11b": "R-11b",
    "R-11c": "R-11c",
    "R-11d": "R-11d",
    "R-11e": "R-11e",
}


def test_spec_revisions_name_each_ruling():
    head = SPEC.split("\n## 1. Scope", 1)[0]
    assert "> **Revisions.**" in head
    h = flat(head)
    for name, needle in REVISION_NEEDLES.items():
        assert needle in h, name


def test_spec_body_carries_the_revisions():
    s = flat("## 1. Scope" + SPEC.split("\n## 1. Scope", 1)[1])
    assert "One session drives a change set" not in s
    assert "asyncapi items cannot be cited across repositories" in s.split("## 15. Known limits", 1)[1]
    assert "the last `check` line" not in s
    assert "one resume per member" in s
    q2 = flat(section(SPEC, "13. Proof: hello-world, slice 4"))
    assert "resume" in q2


def test_base_spec_points_to_the_07_design():
    sec3 = BASE_SPEC.split("\n## 3.", 1)[1].split("\n## 4.", 1)[0]
    assert "> Revised in prd-toolkit 0.7:" in sec3 and "2026-11-02-prd-toolkit-0.7-design.md" in sec3
