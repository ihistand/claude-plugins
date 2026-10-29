from prd_lint import main
from prdlint.findings import Finding
from prdlint.registry import RULES


def test_clean_fixture_exits_0(prd, capsys):          # holds for the rest of the plan
    assert main([str(prd)]) == 0 and capsys.readouterr().out == ""


def test_violation_format_and_exit_1(prd, capsys, monkeypatch):
    monkeypatch.setitem(RULES, "fake", lambda p: [Finding("prd.md", 3, "fake", "boom")])
    assert main([str(prd)]) == 1
    assert capsys.readouterr().out.strip().endswith("prd.md:3: fake: boom")


def test_rule_crash_exits_2_without_traceback(prd, capsys, monkeypatch):
    monkeypatch.setitem(RULES, "fake", lambda p: 1 / 0)
    assert main([str(prd)]) == 2
    err = capsys.readouterr().err
    assert "internal error in rule fake" in err and "Traceback" not in err


def test_not_a_prd_exits_2(tmp_path, capsys):
    assert main([str(tmp_path)]) == 2 and "no prd.md" in capsys.readouterr().err


def test_sample_tids(prd, capsys):
    assert main(["--sample-tids", "3", str(prd)]) == 0
    assert len(set(capsys.readouterr().out.split())) == 3
