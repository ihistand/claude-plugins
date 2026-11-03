"""lint-cli FR-003 and FR-004: --list-rules and the command line (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import run, s0  # noqa: E402

RULES = [
    "ac-ears", "ac-has-test", "assumption-indexed", "change-sets", "classified-fixtures",
    "contracts-valid", "deny-tested", "drift-rows", "error-codes", "error-entries", "fr-has-ac",
    "frontmatter", "glossary-synonym", "id-format", "id-removed-reused", "id-unique",
    "index-consistent", "links-format", "markers-open", "nfr-bound", "open-questions-empty",
    "placeholder", "production-gate", "registries", "runbook-env", "runbook-steps", "runbook-tests",
    "schema-refs", "sections", "snapshot-cited", "sufficiency", "test-cases-consistent",
    "test-level", "test-refs", "upstream-refs", "vague-word",
]

USAGE = "usage: prd_lint.py [-h] [--list-rules] [--ci] [--sample-tids N] [prd_dir]"


def test_t003_1_list_rules(tmp_path):
    """@prd T-003.1"""
    for args in (["--list-rules"], ["--list-rules", str(tmp_path / "missing")]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stderr == "", args
        assert r.stdout_lines == RULES, args


def test_t004_1_no_folder_prints_usage(tmp_path):
    """@prd T-004.1"""
    r = run([], cwd=tmp_path)
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
        r = run([flag], cwd=tmp_path)
        assert r.exit == 0, flag
        assert r.stderr == "", flag
        assert r.stdout_lines and r.stdout_lines[0].startswith(USAGE), (flag, r.stdout)
        assert "Lint a PRD folder." in r.stdout, (flag, r.stdout)
        assert "skip the checks that need this machine's skills and linters" in r.stdout, (
            flag, r.stdout)


def test_t004_4_negative_sample(tmp_path):
    """@prd T-004.4"""
    r = run(["--sample-tids", "-1", str(tmp_path / "missing")], cwd=tmp_path)
    assert r.exit == 2
    assert r.stdout == ""
    assert r.stderr == "prd_lint: --sample-tids N must be >= 0\n"
