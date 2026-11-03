"""Pins for the 0.8.0 release text: versions, the README's packs, languages and judged-case parts, the format and
contract references, the template's profile hints and the spec's Revisions."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
FORMAT = (ROOT / "references/prd-format.md").read_text(encoding="utf-8")
SPEC_REL = "docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.0-design.md"
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
    assert plugin["version"] == "0.8.0"
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"] == ["0.8.0"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    block = js[js.index("id: 'prd-toolkit'"):]
    assert "version: '0.8.0'" in block and "prd-toolkit-0.8.0-design.md" in block
    assert "Version 0.8.0." in README
    assert f"(../{SPEC_REL})" in README


def test_description_names_the_new_parts():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert "packs, languages and judged test cases" in plugin["description"]
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    entry = next(p for p in market["plugins"] if p["name"] == "prd-toolkit")
    assert entry["description"] == plugin["description"]
    js = (REPO / "web/src/data/plugins.js").read_text()
    assert "description: '" + plugin["description"] + "'" in js


def test_builtin_packs_need_toolkit_0_8_0():
    for name in ("service", "document"):
        text = (ROOT / f"packs/{name}/pack.yaml").read_text()
        assert 'toolkit: ">=0.8.0,<0.9"' in text, name


def test_readme_rules_and_sections():
    import prdlint.rules  # noqa: F401
    from prdlint.registry import RULES

    assert len(RULES) == 40
    assert "a 40-rule linter" in flat(README) and "prints the 40 rules" in flat(README)
    assert "36-rule" not in README
    p = flat(section(README, "Packs"))
    for needle in ("pack.yaml", "prd_lint.py --list-packs", "<name> <version> (<source>) — <description>",
                   "prd-packs/<name>/", ".prd-toolkit/packs/<name>/", "prd_hooks.py install", "service", "document",
                   "Pack:", "Target:", "${PACK}", "pack-resolves", "platform-word", "output language"):
        assert needle in p, needle
    lang = flat(section(README, "Languages"))
    for needle in ("language:", "en", "es", "references/languages/", "languages/", "language-table", "Cuando"):
        assert needle in lang, needle
    j = flat(section(README, "Judged cases"))
    for needle in ("rubric:", "threshold:", "runs:", "prd_judge.py", "median", "quote", ".prd-judge/", "exit 2",
                   "judged-case", "grader:", "claude -p"):
        assert needle in j, needle


def test_readme_known_limits_and_changelog():
    k = flat(section(README, "Known limits (0.8.0)"))
    for needle in ("not deterministic", "PRD_PLUGINS_FILE", "--plugin-dir", "installed_plugins.json", "Markdown only"):
        assert needle in k, needle
    assert README.index("## Known limits (0.8.0)") < README.index("## Known limits (0.7.1)")
    c = section(README, "Changelog")
    assert c.index("- **0.8.0:**") < c.index("- **0.7.2:**")
    e = flat(c[c.index("- **0.8.0:**"):c.index("- **0.7.2:**")])
    for needle in ("packs", "languages", "judged", "prd_judge.py", "--list-packs", "40", "warn", "platform-word",
                   "prd_hooks.py install", "format: target profiles (prd-toolkit 0.8)", "No 0.7 PRD needs an edit"):
        assert needle in e, needle


def test_format_documents_profiles():
    f = flat(FORMAT)
    for needle in ("`language`", "- Pack: <name> <X.Y.Z> (<source>)", "- Output language: <code>", "Target: pack",
                   "Target: output language", "`pack` Validator", "| outline | `contracts/outline.yaml` | pack |",
                   "- Profile: [ASSUMPTION A-nn", "only when it differs from `language:`",
                   "rubric:", "threshold:", "judged-case", "<file>:<line>: warn: <rule>: <message>",
                   "format: target profiles (prd-toolkit 0.8)"):
        assert needle in f, needle


def test_format_documents_language_tables():
    f = flat(FORMAT)
    for key in ("`openers`", "`ubiquitous`", "`ubiquitous_hint`", "`modal`", "`modal_word`", "`vague`", "`labels`",
                "references/languages/<code>.yaml", "languages/<code>.yaml"):
        assert key in f, key


def test_format_documents_pack_resolves_messages():
    f = flat(FORMAT)
    for msg in ("Pack: must be <name> <X.Y.Z> (<source>)",
                "Output language: must be a BCP 47 tag such as es or pt-BR",
                "Target: must be pack <name> <X.Y.Z> (<source>)[, output language <code>] or output language <code>",
                "Target: must come before the first requirement",
                "Target: must come after the file's level-1 heading",
                "vendored <name> <v1>, the PRD names <v2>; run prd_hooks.py install",
                "pack <name> named at <v1> and <v2>; one version per PRD",
                "pack <name> <X.Y.Z> (<source>) not found; looked in:"):
        assert msg in f, msg


def test_contract_types_has_pack_and_outline():
    c = (ROOT / "references/contract-types.md").read_text()
    assert "\n## pack\n" in c and "\n## outline\n" in c
    assert "${PACK}" in flat(c) and "validate_outline.py" in c


def test_test_levels_and_clarify():
    t = flat((ROOT / "references/test-levels.md").read_text())
    for needle in ("judged", "checks", "prd_judge.py", "rubric"):
        assert needle in t, needle
    cl = flat((ROOT / "references/clarify-categories.md").read_text())
    assert "target profile" in cl and "output language" in cl


def test_template_hints_profile_lines_inside_comments():
    t = (ROOT / "templates/prd/prd.md").read_text()
    s1 = t[t.index("## 1. Metadata"):t.index("## 2.")]
    assert "<!-- " in s1 and "Pack:" in s1 and "Output language:" in s1
    for line in s1.splitlines():
        if line.startswith("- Pack:") or line.startswith("- Output language:"):
            raise AssertionError("an unparsed hint must sit inside a comment: " + line)


def test_spec_revisions_name_each_ruling():
    rev = flat(re.sub(r"^> ?", "", SPEC[:SPEC.index("## 1. Scope")], flags=re.M))
    for needle in ("whitespace", "--strict-mcp-config", "--setting-sources", "--list-packs", "no new script",
                   "after `shlex.split`", "Target: must come before the first requirement",
                   "`PRD_PLUGINS_FILE` list, since discovery does not see `--plugin-dir` plugins",
                   "(R28)"):
        assert needle in rev, needle


def test_spec_known_limits_name_the_plugin_dir_gap():
    s = flat(SPEC[SPEC.index("## 15. Known limits"):SPEC.index("## 16.")])
    assert "--plugin-dir" in s and "PRD_PLUGINS_FILE" in s
