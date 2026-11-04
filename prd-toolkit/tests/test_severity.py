from collections import Counter

import pytest

from deploy_fixture import deploy_repo
from prd_lint import main
from prdlint import deploy, model, registry
from prdlint.findings import Finding


def _warn(prd):
    return [Finding("prd.md", 1, "t-warn", "m", severity="warn")]


def _err(prd):
    return [Finding("prd.md", 2, "t-err", "e")]


@pytest.fixture
def warn_rule():
    registry.rule("t-warn", severity="warn")(_warn)
    yield
    registry.RULES.pop("t-warn", None)
    registry.SEVERITY.pop("t-warn", None)


@pytest.fixture
def err_rule():
    registry.rule("t-err")(_err)
    yield
    registry.RULES.pop("t-err", None)
    registry.SEVERITY.pop("t-err", None)


def test_warn_str_and_default_severity():
    assert str(Finding("prd.md", 1, "t-warn", "m", severity="warn")) == "prd.md:1: warn: t-warn: m"
    assert str(Finding("prd.md", 1, "r", "m")) == "prd.md:1: r: m"
    assert Finding("a", 1, "r", "m").severity == "error"


def test_severity_does_not_affect_equality_or_order():
    assert Finding("a", 1, "r", "m") == Finding("a", 1, "r", "m", severity="warn")


def test_rule_records_severity(warn_rule):
    assert registry.SEVERITY["t-warn"] == "warn"
    assert registry.SEVERITY.get("ac-ears", "error") == "error"


def test_run_drops_warns_unless_asked(prd, warn_rule):
    assert registry.run(model.load(prd)) == []
    assert [f.rule for f in registry.run(model.load(prd), warnings=True)] == ["t-warn"]


def test_cli_prints_warn_and_exits_0(prd, warn_rule, capsys):
    assert main([str(prd)]) == 0
    assert capsys.readouterr().out.strip().endswith("prd.md:1: warn: t-warn: m")


def test_cli_error_plus_warn_exits_1(prd, warn_rule, err_rule, capsys):
    assert main([str(prd)]) == 1
    out = capsys.readouterr().out
    assert "warn: t-warn: m" in out and "prd.md:2: t-err: e" in out


def test_list_rules_prints_severity(capsys, warn_rule):
    assert main(["--list-rules"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "ac-ears error" in lines and "t-warn warn" in lines


def test_preflight_ignores_a_warn(tmp_path, warn_rule, monkeypatch):
    monkeypatch.setenv("PRD_LINT_CI", "1")  # the scaffold's required skill is not installed on a CI runner
    repo = deploy_repo(tmp_path)
    reasons = deploy.preflight(model.load(repo / "docs/prd/orders"), repo)
    assert "prd_lint has findings" not in reasons


def test_prd_error_lint_step_ignores_a_warn(prd, monkeypatch):
    import prd_error

    registry.rule("t-warn", severity="warn")(lambda p: [Finding("errors.md", 1, "t-warn", "m", severity="warn")])
    try:
        assert prd_error._ledger_findings(prd) == Counter()
    finally:
        registry.RULES.pop("t-warn", None)
        registry.SEVERITY.pop("t-warn", None)
