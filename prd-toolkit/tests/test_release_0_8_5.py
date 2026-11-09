"""Pins for the 0.8.5 release text: versions, the README's parts for each item, the upgrade note and the changelog entry."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-08-prd-toolkit-0.8.5-design.md"
SPEC84_REL = "docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(text: str, title: str) -> str:
    assert text.count(f"\n## {title}\n") == 1, title
    a = text.index(f"\n## {title}\n") + 1
    b = text.find("\n## ", a + 1)
    return text[a:b if b > 0 else len(text)]


def entry(ver: str, nxt: str) -> str:
    c = section(README, "Changelog")
    return flat(c[c.index(f"- **{ver}:**"):c.index(f"- **{nxt}:**")])


def test_versions():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert plugin["version"] == "0.8.5"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.8.5"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert "version: '0.8.5'" in block
    assert "{ label: 'Design spec (0.8.5)', url: 'https://github.com/ihistand/claude-plugins/blob/main/" + SPEC_REL + "' }" in block
    assert "Version 0.8.5." in README
    assert f"(../{SPEC_REL})" in README and (REPO / SPEC_REL).is_file()
    assert (REPO / ".prd-toolkit/VERSION").read_text().strip() == "0.8.5"


def test_changelog_entry():
    c = section(README, "Changelog")
    assert c.index("- **0.8.5:**") < c.index("- **0.8.4:**")
    e = entry("0.8.5", "0.8.4")
    assert f"[design spec](../{SPEC_REL})" in e
    for needle in (
        "prd_deploy.py confirm", "`--step N --reply TEXT`",                      # 1
        "`prd_error.py new`", "uncommitted",                         # 2
        "`Timeout`", "`--timeout`",                                  # 3
        "`Branch`", "the close is on",                               # 4
        "matches `<pattern>`",                                                 # 5
        "`prd_change.py pack`", "no dry run (pack version only)",    # 6
        "`MOVED: line", "pulled in; not counted",                    # 7
        "--sources <file>",                                               # 8
        "inline SVG", "mermaidx==0.11.3", "diagram at <file>:<line> shown as source",  # 9
        "`--pyargs`", "unquoted glob",                               # 10
        "pytest-xdist", "-n auto",                                   # 11
        "Item A", "Item B",
        "6.0.0", "5.2.0", "FR-016", "FR-017", "FR-018", "FR-010",
        "Upgrading from 0.8.4",
        "re-run `prd_hooks.py install docs/prd/<slug>`", "no PRD changes", "ends with `prd_change.py pack`",
    ):
        assert needle in e, needle


def test_084_entry_holds_the_live_proof():
    e = entry("0.8.4", "0.8.3")
    assert "Proven live after the merge on 2026-11-08" in e
    assert "five checked greps with no refusal" in e and "`uv run --directory`" in e
    assert "drawing it is 0.8.5's item 9" not in e


def test_readme_says_where_a_diagram_draws():
    s = flat(README)
    assert "No viewer draws it" not in s
    assert "Mermaid diagrams on the published page are shown as source, and the page's own labels are English. (0.8.4" in s  # 0.8.0 limit stays
    p = flat(section(README, "Publishing"))
    assert "inline SVG" in p and "its own Artifact" in p and "never as a file inside another" in p
    k = flat(section(README, "Known limits (0.8.5)"))
    assert README.index("## Known limits (0.8.5)") < README.index("## Known limits (0.8.4)")
    for needle in ("quickjs-ng", "not across time", "uv run --script", "stops the publish", "macOS, manylinux, musllinux, Windows",
                   "prd_publish: diagram at <file>:<line> shown as source: <reason>", "journey", "foreignObject",
                   "`Diagram source`", "English on every page", "`mermaidx`",
                   "`prd_tester_guard: unquoted glob in <arg>`", "jest", "positional",
                   "`-o addopts`", "`--doctest-glob`", "`--confcutdir`"):
        assert needle in k, needle


def test_parts_for_each_item():
    d = flat(section(README, "Deploying"))
    for needle in ("--step N --reply TEXT", "`Timeout` column", "`Branch` column", "matches `<pattern>`",
                   "the close is on <current>, not <branch>; push the close commit to <branch> too"):
        assert needle in d, needle
    p = flat(section(README, "Packs"))
    assert "prd_change.py pack" in p and "no dry run (pack version only)" in p
    h = flat(section(README, "Hooks and CI"))
    assert "-n auto" in h and "pytest-xdist" in h
    t = flat(section(README, "Testing from the PRD"))
    assert "--pyargs" in t and "unquoted glob" in t
