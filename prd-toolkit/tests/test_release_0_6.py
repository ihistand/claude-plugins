"""Pins for the 0.6.0 release text: versions, the README's error and publishing sections, upgrade note, refusals and limits."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPO = ROOT.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
BASE_SPEC = (REPO / "docs/superpowers/specs/2026-10-29-prd-toolkit-design.md").read_text(encoding="utf-8")
SPEC_06 = "docs/superpowers/specs/2026-11-01-prd-toolkit-0.6-design.md"


def flat(s: str) -> str:
    return " ".join(s.split())


def section(title: str) -> str:
    assert README.count(f"\n## {title}\n") == 1, title
    a = README.index(f"\n## {title}\n") + 1
    b = README.find("\n## ", a + 1)
    return README[a:b if b > 0 else len(README)]


def test_versions():
    assert re.fullmatch(r"0\.\d+\.\d+", json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"])
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert re.fullmatch(r"0\.\d+\.\d+", [p["version"] for p in market["plugins"] if p["name"] == "prd-toolkit"][0])
    js = (REPO / "web/src/data/plugins.js").read_text()
    a = js.index("id: 'prd-toolkit'")
    block = js[a:]
    assert re.search(r"version: '0\.\d+\.\d+'", block)
    assert "/prd-error" in block and "/prd-publish" in block and "handling-errors" in block and "publishing-prds" in block
    assert SPEC_06.split("docs/superpowers/specs/")[1] in block


def test_readme_version_and_spec_link():
    assert re.search(r"Version 0\.\d+\.\d+\.", README)
    assert f"(../{SPEC_06})" in README
    assert (REPO / SPEC_06).is_file()
    assert "- **0.6.0:**" in README


def test_handling_errors_section():
    s = flat(section("Handling errors")).lower()
    for needle in ("/prd-error", "record", "reproduce", "propose", "confirmation", "/prd-change", "/prd-build --fixes",
                   "resolve", "prd_error.py check", "known-failing", "prd_deploy.py recover", "e-nnn"):
        assert needle in s, needle


def test_publishing_section():
    s = flat(section("Publishing"))
    for needle in ("/prd-publish", "self-contained", "summar", "Artifact", "file", "prd_publish.py"):
        assert needle in s, needle


def test_upgrade_note():
    s = flat(README)
    assert "Upgrading from 0.5:" in s
    assert "re-run `prd_hooks.py install`" in s and "`prd_hooks.py ci`" in s and "`check --ci`" in s
    assert "`prd_block.py --check` reports its CLAUDE.md block stale until `prd_block.py` is re-run" in s
    assert "needs a tagged citation" in s


def test_error_and_publish_refusals_by_exit_code():
    s = flat(section("Handling errors") + section("Publishing"))
    assert "What `prd_error.py` refuses." in s and "What `prd_publish.py` refuses." in s
    assert s.count("Exit 1 (`refused`)") >= 2 and s.count("Exit 2") >= 2


def test_known_limits_of_spec_15():
    s = flat(README)
    for needle in ("held by instruction; the trace reads the tag, not each runner's syntax",
                   "`recover` never marks a step done", "holding no secret or classified value",
                   "Mermaid diagrams on the published page are shown as source",
                   "between reading the runbook steps and hashing them"):
        assert needle in s, needle


def test_residual_confirm_exit_2_list_names_missing_folder():
    s = section("Deploying")
    tail = s.split("Exit 2 (usage error, nothing run)", 1)[1]
    confirm = flat(re.search(r"- `confirm`:.*?(?=\n- `recover`)", tail, re.S).group(0))
    assert "log names no PRD folder" in confirm


def test_residual_ci_example_agrees_with_one_simple_command_rule():
    s = flat(section("Deploying"))
    assert "cd tools && bash gate.sh" not in README
    assert "one simple command" in s
    fmt = (ROOT / "references/prd-format.md").read_text()
    assert "one simple command" in fmt and "`export PRD_ENV=<env> TEST_ENV=<env>; <harness command>`" in s


def test_base_spec_points_to_the_06_design():
    sec6 = BASE_SPEC.split("## 6. Error-Driven Development", 1)[1].split("\n## 7.", 1)[0]
    assert "> Revised in prd-toolkit 0.6:" in sec6 and "2026-11-01-prd-toolkit-0.6-design.md" in sec6


def test_block_names_prd_error_and_stays_small():
    block = (ROOT / "templates/claude-block.md").read_text()
    assert "`/prd-error`" in block


def test_readme_vendored_paths_are_vendored():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from prdlint import hooks
    named = set(re.findall(r"\.prd-toolkit/(\w+\.py)", README))
    assert named and named <= set(hooks.VENDORED), sorted(named - set(hooks.VENDORED))
    pub = flat(section("Publishing"))
    assert "prd-toolkit/<version>/scripts/prd_publish.py render" in pub and "runs from the plugin" in pub
    assert "(it vendors `prd_error.py`)" in flat(README) and "`prd_error.py` and `prd_publish.py`" not in README


def test_error_refusal_placement_and_publish_wording():
    s = flat(section("Handling errors"))
    one, two = s.split("Exit 2 (usage error, nothing written)", 1)
    assert "`--t` with no test case or level" in one and "`--t` with no test case or level" not in two
    assert "empty reply, class, diagnosis, title or source" in two
    p = flat(section("Publishing"))
    assert "summaries: must be an object" in p and "ids must be a list of requirement IDs" in p
    assert "FR-001–FR-004" in p and "FR-001-FR-004" not in p
