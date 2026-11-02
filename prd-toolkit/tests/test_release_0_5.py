"""Pins for the 0.5.0 release text: the README's Deploying section, upgrade note and shell commands (R22)."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ROOT_README = (ROOT.parent / "README.md").read_text(encoding="utf-8")
SPEC = (ROOT.parent / "docs/superpowers/specs/2026-11-01-prd-toolkit-0.5-design.md").read_text(encoding="utf-8")
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
    assert re.search(r"Version 0\.\d+\.0\.", README)  # the 0.6 release pins the current one
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


def refusal_bullets() -> dict[str, dict[str, str]]:
    """The refusal lists of the Deploying section: exit code -> command -> its bullet, flattened."""
    s = section("Deploying")
    one = s.split("**What `prd_deploy.py` refuses.** Exit 1 (`refused`)", 1)[1].split("\nExit 2 (usage error, nothing run)", 1)[0]
    two = s.split("\nExit 2 (usage error, nothing run)", 1)[1]

    def bullets(block: str) -> dict[str, str]:
        listed = block.split("\n\n", 2)[1]  # the list after the heading line
        out = {}
        for b in listed.strip().removeprefix("- ").split("\n- "):
            b = flat(b)
            m = re.match(r"`(\w+)`(?: or `(\w+)`)?:", b)
            assert m, b
            for name in filter(None, m.groups()):
                out[name] = b
        return out
    return {"1": bullets(one), "2": bullets(two)}


REFUSALS = {
    "1": {
        "run": ["the tracked working tree is dirty", "`built`", "reaches a production environment", "no test cites",
                "another `prd_deploy` command is running in this repository"],
        "resume": ["another PRD's run", "names no PRD folder", "HEAD or the PRD version moved", "the tree changed",
                   "the runbook changed", "has no step records", "is done", "did not stop at a human step",
                   "is not a human step of the runbook", "has no `confirm`", "was already used",
                   "started and did not finish", "the run failed", "working on this run", "running in this repository"],
        "rollback": ["another PRD's run", "names no PRD folder", "HEAD or the PRD version moved", "the tracked tree is dirty",
                     "the runbook changed", "working on this run", "running in this repository"],
        "check": ["another PRD's run", "names no PRD folder"],
    },
    "2": {
        "plan": ["would take a production step along"],
        "rollback": ["second rollback", "not the run's failed step", "no `Rollback:`"],
        "confirm": ["another PRD's run", "working on this run", "already has a `confirm` record",
                    "not the human step the run stopped at", "empty reply"],
    },
}


def test_refusals_split_by_exit_code():
    s = flat(section("Deploying"))
    assert "a `tests` step runs a deploy-gate test" not in s
    got = refusal_bullets()
    for code, commands in REFUSALS.items():
        for command, phrases in commands.items():
            assert command in got[code], (code, command, sorted(got[code]))
            for phrase in phrases:
                assert phrase in got[code][command], (code, command, phrase)
    assert "second rollback" not in " ".join(got["1"].values())
    assert "already has a `confirm` record" not in " ".join(got["1"].values())
    assert "reaches a production environment" not in " ".join(got["2"].values())


def test_repo_lock_and_stopped_runs():
    s = flat(section("Deploying"))
    assert ("`run`, `resume` and `rollback` hold a repository-wide lock while they run commands; a run stopped "
            "at a human step holds none, and `plan`, `check` and `confirm` take none.") in s


UPGRADE_SCRIPTS = ("After upgrading the plugin, run `prd_hooks.py install` from it again, so `.prd-toolkit/` gains "
                   "`prd_deploy.py`, `prd_drift.py`, `prd_block.py` and the block template "
                   "(`templates/claude-block.md`), then `prd_hooks.py ci` again for the manual deploy jobs. Until then "
                   "`prd_hooks.py check` reports the stale copy.")


def test_upgrade_note_revendors_and_regenerates_ci():
    assert UPGRADE_SCRIPTS in flat(README)
    assert UPGRADE_SCRIPTS in flat(SPEC.split("### Migration from 0.4", 1)[1].split("\n## ", 1)[0])


def test_spec_records_the_final_review():
    revisions = flat(SPEC.split("> **Revisions.**", 1)[1].split("\n## 1.", 1)[0].replace("\n>", "\n"))
    for needle in ("(R7)", "a `start` record", "a `resume` record", "a rollback `start` record",
                   "the PRD folder", "sha256 of `operations.md` and `testing.md`", "`<log dir>/.active`"):
        assert needle in revisions, needle
    limits = flat(SPEC.split("## 12. Known limits", 1)[1].split("\n## 13.", 1)[0])
    assert ("A step killed between its `start` record and its completion cannot be rolled back through the tool: "
            "`rollback` needs the step's `fail` record. Recovering it is 0.6.") in limits


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
