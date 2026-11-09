"""lint-cli FR-016, FR-017, FR-018: runbook table columns and Check lines (test-cases/lint-cli.yaml)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import run, s0  # noqa: E402


def _edit_lines(path: Path, changes: dict) -> None:
    """Edit 1-based lines of `path`: `changes` maps a line number to a function (or a replacement
    string) applied to the line's text without its line end; the line end is kept."""
    lines = path.read_bytes().decode("utf-8").splitlines(keepends=True)
    for number, change in changes.items():
        raw = lines[number - 1]
        body = raw.rstrip("\r\n")
        end = raw[len(body):]
        new = change(body) if callable(change) else change
        lines[number - 1] = new + end
    path.write_bytes("".join(lines).encode("utf-8"))


def _add(cell: str):
    return lambda body: body + cell


def m2(root: Path) -> None:
    """M2: the Levels table of testing.md gains a last column `Timeout`."""
    _edit_lines(
        root / "testing.md",
        {
            5: "| Level | Harness command | Environment | Gate | Timeout |",
            6: "|---|---|---|---|---|",
            7: _add(" |"),
            8: _add(" |"),
            9: _add(" |"),
            10: _add(" ten |"),
            11: _add(" 1200 |"),
            12: _add(" |"),
            13: _add(" 0 |"),
        },
    )


def m3(root: Path) -> None:
    """M3: the Environments table of operations.md gains a last column `Branch`."""
    _edit_lines(
        root / "operations.md",
        {
            5: "| Environment | URL | Production | Branch |",
            6: "|---|---|---|---|",
            7: _add(" |"),
            8: _add(" |"),
            9: _add(" release/staging |"),
            10: _add(" main..x |"),
        },
    )


def m4(root: Path) -> None:
    """M4: line 16 (step 1's Check) becomes a `matches` Check with a pattern that compiles."""
    _edit_lines(
        root / "operations.md",
        {16: "   Check: `curl -fsS https://orders-staging.example.com/health` matches `^ok$`"},
    )


def m5(root: Path) -> None:
    """M5: line 16 gets a pattern that does not compile; line 25 holds both prints and matches."""
    _edit_lines(
        root / "operations.md",
        {
            16: "   Check: `curl -fsS https://orders-staging.example.com/health` matches `^ok(`",
            25: "   Check: `curl -fsS https://orders.example.com/health` prints `ok` matches `^ok$`",
        },
    )


def test_t016_1_timeout_cell_must_be_whole_seconds(tmp_path, monkeypatch):
    """@prd T-016.1"""
    root = s0(tmp_path, monkeypatch)
    m2(root)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout_lines == [
        "docs/prd/orders/testing.md:10: runbook-tests: level 'system': Timeout 'ten' is not a whole "
        "number of seconds of at least 1",
        "docs/prd/orders/testing.md:13: runbook-tests: level 'smoke': Timeout '0' is not a whole "
        "number of seconds of at least 1",
    ]
    assert r.stderr == ""


def test_t017_1_branch_cell_must_be_a_valid_branch_name(tmp_path, monkeypatch):
    """@prd T-017.1"""
    root = s0(tmp_path, monkeypatch)
    m3(root)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout_lines == [
        "docs/prd/orders/operations.md:10: runbook-env: environment 'production': Branch 'main..x' "
        "is not a valid branch name"
    ]
    assert r.stderr == ""


def test_t018_1_check_with_matches_and_compiling_pattern_is_clean(tmp_path, monkeypatch):
    """@prd T-018.1"""
    root = s0(tmp_path, monkeypatch)
    m4(root)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert (r.exit, r.stdout, r.stderr) == (0, "", "")


def test_t018_2_bad_matches_pattern_and_prints_with_matches(tmp_path, monkeypatch):
    """@prd T-018.2"""
    root = s0(tmp_path, monkeypatch)
    m5(root)
    r = run(["docs/prd/orders"], cwd=tmp_path)
    assert r.exit == 1
    assert r.stdout_lines == [
        "docs/prd/orders/operations.md:16: runbook-steps: step 1: matches pattern '^ok(' does not "
        "compile: missing ), unterminated subpattern at position 3",
        "docs/prd/orders/operations.md:25: runbook-steps: step 4: Check: takes prints or matches, "
        "not both",
    ]
    assert r.stderr == ""
