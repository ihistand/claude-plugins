import json
from pathlib import Path

import pytest
from conftest import Case, edit, fired, lint

from prdlint import model
from prdlint.rules.registries import installed_skill

STD_ROW = "| `**/*.sql` | `python3 -m json.tool` |"
SKILL_ROW = "| plans | superpowers:writing-plans | required |"


def _edit(rel, old, new):
    return lambda root: edit(root, rel, old, new)


CASES: list[Case] = [
    Case("registries", "linter-not-on-path", _edit("prd.md", STD_ROW, "| `**/*.sql` | `no-such-linter-xyz` |")),
    Case("registries", "skill-not-installed", _edit("prd.md", SKILL_ROW, "| plans | nonexistent:skill | required |")),
    Case("registries", "decision-proposed-while-approved", _edit("prd.md", SKILL_ROW, "| plans | superpowers:writing-plans | proposed |")),
    Case("registries", "decision-outside-enum", _edit("prd.md", "| code, schema.sql | enforced |", "| code, schema.sql | maybe |")),
    Case("runbook-actors", "step-without-actor", _edit("operations.md", "2. Deploy to production with `./deploy.sh production` after the owner approves. (actor: human)", "2. Deploy to production with `./deploy.sh production` after the owner approves.")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


def test_proposed_is_fine_while_draft(prd):
    edit(prd, "prd.md", "status: Approved", "status: Draft")
    edit(prd, "prd.md", SKILL_ROW, "| plans | nonexistent:skill | proposed |")
    assert "registries" not in fired(lint(prd))


def test_declined_rows_are_not_checked(prd):
    edit(prd, "prd.md", STD_ROW, "| `**/*.sql` | `no-such-linter-xyz` |")
    edit(prd, "prd.md", "| code, schema.sql | enforced |", "| code, schema.sql | declined |")
    edit(prd, "prd.md", SKILL_ROW, "| plans | nonexistent:skill | recommended |")
    assert "registries" not in fired(lint(prd))


def test_fixture_registries_are_clean(prd):
    assert not {"registries", "runbook-actors"} & fired(lint(prd))


def test_plugin_skill_installed(tmp_path, monkeypatch):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"plugins": {"foo@market": [{}]}}))
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(f))
    assert installed_skill("foo:bar", tmp_path)
    assert not installed_skill("foobar:bar", tmp_path)


@pytest.mark.parametrize("content", [None, "not json", "[1]"])
def test_bad_plugins_file_means_not_installed(tmp_path, monkeypatch, content):
    f = tmp_path / "p.json"
    if content is not None:
        f.write_text(content)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(f))
    assert not installed_skill("foo:bar", tmp_path)


def test_bare_skill_in_home_or_repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    repo = tmp_path / "repo"
    assert not installed_skill("mine", repo)
    (home / ".claude/skills/mine").mkdir(parents=True)
    (home / ".claude/skills/mine/SKILL.md").write_text("x")
    assert installed_skill("mine", repo)
    (repo / ".claude/skills/other").mkdir(parents=True)
    (repo / ".claude/skills/other/SKILL.md").write_text("x")
    assert installed_skill("other", repo)


def test_repo_root_falls_back_to_the_path(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    assert model.repo_root(tmp_path) == tmp_path


def test_repo_root_finds_git_toplevel(tmp_path):
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a/b").mkdir(parents=True)
    assert model.repo_root(tmp_path / "a/b").resolve() == tmp_path.resolve()
