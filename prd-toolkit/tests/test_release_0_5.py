"""Pins for the 0.5.0 release text: the README's Deploying section, upgrade note and shell commands (R22)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ROOT_README = (ROOT.parent / "README.md").read_text(encoding="utf-8")
UPGRADE = ("Upgrading a 0.4 PRD: lint fails `runbook-steps` until each runbook step carries `(env: …)` and its "
           "labels, and `runbook-env` until Environments has a Production column; a patch bump with the §14 row "
           "`format: runbook steps (prd-toolkit 0.5)`.")


def flat(s: str) -> str:
    return " ".join(s.split())


def section(title: str) -> str:
    assert README.count(f"\n## {title}\n") == 1, title
    a = README.index(f"\n## {title}\n") + 1
    b = README.find("\n## ", a + 1)
    return README[a:b if b > 0 else len(README)]


def test_version_and_spec_link():
    assert "Version 0.5.0." in README
    assert "(../docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md)" in README
    assert (ROOT.parent / "docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md").is_file()


def test_no_plugin_root_variable_in_shell_blocks():
    blocks = re.findall(r"```\n(.*?)```", README, re.S)
    assert blocks and not [b for b in blocks if "CLAUDE_PLUGIN_ROOT" in b]
    assert "~/.claude/plugins/cache/ihistand/prd-toolkit/<version>/scripts/" in README
    assert "claude plugin list" in README


def test_deploying_section():
    s = flat(section("Deploying"))
    for needle in ("/prd-deploy", "prd_deploy.py", "prd_drift.py", "(actor: agent) (env: production)", "Run:", "Check:",
                   "Rollback:", "Do:", "tests <level>", "prints", "## Deployed", "## Drift", "production gate",
                   "drift-<env>", "test-deploy-<env>", "never deploy", "dirty", "built", "approval", "confirm",
                   "second rollback", "trusted to be the user's"):
        assert needle in s, needle


def test_upgrade_note_shows_both_runbooks():
    assert UPGRADE in flat(README)
    assert "1. Deploy the build with `./deploy.sh staging`, then run the system tests. (actor: agent)" in README
    assert "1. Deploy to staging (actor: agent) (env: staging)" in README


def test_changelog_and_command_row():
    assert "- **0.5.0:**" in README
    assert "| `/prd-deploy [--until <env>] [<run id>]` | `prd-toolkit:deploying-from-prds` |" in README


def test_root_readme_lists_deploy():
    assert "/prd-deploy" in ROOT_README and "deploying-from-prds" in ROOT_README


def test_refusals_split_by_exit_code():
    s = flat(section("Deploying"))
    assert "Exit 2" in s and "second rollback" in s and "already has a `confirm` record" in s
    assert "reaches a production environment" in s and "no test cites" in s
    assert "a `tests` step runs a deploy-gate test" not in s


def test_readmes_rule_counts_match_registry():
    import subprocess
    out = subprocess.run(["uv", "run", "--script", str(ROOT / "scripts/prd_lint.py"), "--list-rules"],
                         capture_output=True, text=True, check=True).stdout
    n = len(out.split())
    found = 0
    for text in (README, ROOT_README):
        for line in text.splitlines():
            if "**0.1.0:**" in line:
                continue  # history
            for m in re.finditer(r"(\d+)[- ]rules?\b", line):
                found += 1
                assert int(m.group(1)) == n, line
    assert found >= 4
