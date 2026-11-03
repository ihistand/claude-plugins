"""lint-cli FR-003 and FR-004: --list-rules and the command line (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import run, s0  # noqa: E402

# T-003.1 stdout_exact_lines: every registered rule as `<name> <severity>`, sorted by name.
RULES = [
    "ac-ears error", "ac-has-test error", "assumption-indexed error", "change-sets error",
    "classified-fixtures error", "contracts-valid error", "deny-tested error", "drift-rows error",
    "error-codes error", "error-entries error", "fr-has-ac error", "frontmatter error",
    "glossary-synonym error", "id-format error", "id-removed-reused error", "id-unique error",
    "index-consistent error", "judged-case error", "language-table error", "links-format error",
    "markers-open error", "nfr-bound error", "open-questions-empty error", "pack-resolves error",
    "placeholder error", "platform-word warn", "production-gate error", "registries error",
    "runbook-env error", "runbook-steps error", "runbook-tests error", "schema-refs error",
    "sections error", "snapshot-cited error", "sufficiency error", "test-cases-consistent error",
    "test-level error", "test-refs error", "upstream-refs error", "vague-word error",
]

# AC-004.1: the one-line usage.
USAGE = "usage: prd_lint.py [-h] [--list-rules] [--list-packs] [--ci] [--sample-tids N] [prd_dir]"


def test_t003_1_list_rules(tmp_path):
    """@prd T-003.1"""
    for args in (["--list-rules"], ["--list-rules", str(tmp_path / "missing")]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stderr == "", args
        assert r.stdout_lines == RULES, (args, r.stdout)


def test_t004_1_no_folder_prints_usage(tmp_path):
    """@prd T-004.1"""
    r = run([], cwd=tmp_path, env={"COLUMNS": "40"})
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == USAGE + "\n"


def test_t004_2_argparse_errors(tmp_path, monkeypatch):
    """@prd T-004.2"""
    s0(tmp_path, monkeypatch)
    cases = [
        (["--bogus", "docs/prd/orders"], "prd_lint.py: error: unrecognized arguments: --bogus"),
        (["--sample-tids", "x", "docs/prd/orders"],
         "prd_lint.py: error: argument --sample-tids: invalid int value: 'x'"),
    ]
    for args, last in cases:
        r = run(args, cwd=tmp_path)
        assert r.exit == 2, args
        assert r.stdout == "", args
        lines = r.stderr_lines
        assert lines, args
        assert lines[0].startswith("usage: prd_lint.py"), (args, r.stderr)
        assert lines[-1] == last, (args, r.stderr)


def test_t004_3_help(tmp_path):
    """@prd T-004.3"""
    for flag in ("--help", "-h"):
        r = run([flag], cwd=tmp_path, env={"COLUMNS": "200"})
        assert r.exit == 0, flag
        assert r.stderr == "", flag
        assert r.stdout_lines, (flag, r.stdout)
        assert r.stdout_lines[0] == USAGE, (flag, r.stdout)
        assert "Lint a PRD folder." in r.stdout, (flag, r.stdout)
        assert "skip the checks that need this machine's skills and linters" in r.stdout, (
            flag, r.stdout)


def test_t004_4_negative_sample(tmp_path):
    """@prd T-004.4"""
    r = run(["--sample-tids", "-1", str(tmp_path / "missing")], cwd=tmp_path)
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == "prd_lint: --sample-tids N must be >= 0\n"
