from conftest import edit
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
    assert len({line.split()[0] for line in capsys.readouterr().out.splitlines()}) == 3


def test_sample_tids_name_the_file_that_holds_each_case(prd, capsys):
    # found in the 0.1 acceptance run: a tester never opened test-cases/nfr.yaml for T-003.1
    assert main(["--sample-tids", "99", str(prd)]) == 0
    for line in capsys.readouterr().out.splitlines():
        tid, rel = line.split()
        assert rel.startswith("test-cases/") and f"{tid}:" in (prd / rel).read_text(encoding="utf-8")


def _levels(prd):
    from prdlint import model

    return {t.id: t.data.get("level") for t in model.load(prd).test_cases}


def test_sample_tids_never_picks_unit(prd, capsys):
    levels = _levels(prd)
    assert "unit" in levels.values(), "the fixture needs a unit case for this test to mean anything"
    assert main(["--sample-tids", "99", str(prd)]) == 0
    picked = [line.split()[0] for line in capsys.readouterr().out.splitlines()]
    assert sorted(picked) == sorted(t for t, lv in levels.items() if lv != "unit")


def test_sample_tids_with_only_unit_cases_exits_1(prd, capsys):
    import re

    for p in (prd / "test-cases").glob("*.yaml"):
        p.write_text(re.sub(r"level: \w+", "level: unit", p.read_text(encoding="utf-8")), encoding="utf-8")
    assert set(_levels(prd).values()) == {"unit"}
    assert main(["--sample-tids", "3", str(prd)]) == 1
    out = capsys.readouterr()
    assert out.out == "" and "prd_lint: no non-unit T-ids to sample" in out.err


def _lint_in_c_locale(prd):
    """Run the CLI in a C locale with UTF-8 mode off, where open() without an encoding is ASCII."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).parent.parent / "scripts/prd_lint.py"
    env = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
    return subprocess.run([sys.executable, str(script), str(prd)], env=env, capture_output=True, encoding="utf-8")


def test_lint_runs_under_a_c_locale(prd):
    r = _lint_in_c_locale(prd)
    assert (r.returncode, r.stdout, r.stderr) == (0, "", "")


def test_lint_prints_non_ascii_findings_under_a_c_locale(prd):
    (prd / "contracts/config.yaml").unlink()
    r = _lint_in_c_locale(prd)
    assert r.returncode == 1 and "— reason" in r.stdout and r.stderr == ""


def test_unexpected_load_error_exits_2_without_traceback(prd, capsys, monkeypatch):
    def boom(_):
        raise OSError("disk gone")

    monkeypatch.setattr("prdlint.model.load", boom)
    assert main([str(prd)]) == 2
    err = capsys.readouterr().err
    assert "internal error: OSError" in err and "Traceback" not in err


def test_invalid_utf8_exits_2(prd, capsys):
    with open(prd / "prd.md", "ab") as f:
        f.write(b"\xff\xfe")
    assert main([str(prd)]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_negative_sample_tids_is_usage_error(prd, capsys):
    assert main(["--sample-tids", "-1", str(prd)]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_non_ascii_validator_output_under_a_c_locale_is_a_finding(prd):
    # parked minor from the final review: validator output was decoded with the locale
    edit(prd, "prd.md", '`python3 -c "import sys; sys.exit(0)"`',
         '`python3 -c "import sys; sys.stderr.buffer.write(chr(252).encode() + b\' bad\\\\n\'); sys.exit(1)"`')
    r = _lint_in_c_locale(prd)
    assert r.returncode == 1 and "contracts-valid" in r.stdout and "Traceback" not in r.stderr
