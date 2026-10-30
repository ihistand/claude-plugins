"""prd_tester_guard.py: the tester is confined to the PRD folder, the scratchpad and the test roots."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/prd_tester_guard.py"
TESTING = """# Testing

## Levels

| Level | Harness command | Environment |
|---|---|---|
| unit | `uv run pytest tests/unit` | local |
| integration | `uv run pytest tests/integration` | ci |

## Harness

- **Layout.** `tests/<level>/test_<area>.py`. Test roots: `tests/`.
"""


def run_raw(stdin: str | bytes):
    data = stdin.encode() if isinstance(stdin, str) else stdin
    r = subprocess.run([sys.executable, str(GUARD)], input=data, capture_output=True)
    r.stderr = r.stderr.decode("utf-8", "replace")
    return r


def assert_blocked(r, verb=None):
    """A denial (not a crash): exit 2, one stderr line, `prd-tester may only [verb] under: ...`."""
    assert r.returncode == 2, r.stderr
    assert len(r.stderr.strip().splitlines()) == 1, r.stderr
    assert r.stderr.startswith("prd-tester may only "), r.stderr
    if verb:
        assert r.stderr.startswith(f"prd-tester may only {verb} under: "), r.stderr


def run(payload: dict):
    return run_raw(json.dumps(payload))


def make_repo(tmp_path: Path, testing: str | None = TESTING) -> Path:
    repo = tmp_path / "repo"
    (repo / "docs/prd/x").mkdir(parents=True)
    (repo / "docs/prd/x/prd.md").write_text("# x\n")
    (repo / "docs/prd-evil").mkdir()
    (repo / "docs/prd-evil/secret.md").write_text("s\n")
    (repo / "docs/prd/x-evil").mkdir()  # a string-prefix sibling of the PRD folder, and no PRD itself
    (repo / "docs/prd/x-evil/secret.md").write_text("s\n")
    (repo / "tests-evil").mkdir()  # a string-prefix sibling of the test root
    (repo / "tests-evil/secret.py").write_text("s\n")
    (repo / "docs/prd/x/testing.md").unlink(missing_ok=True)
    if testing is not None:
        (repo / "docs/prd/x/testing.md").write_text(testing)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print(1)\n")
    (repo / "tests/integration").mkdir(parents=True)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def call(repo: Path, tool: str, agent="prd-tester", **tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(repo),
               "scratchpad_dir": str(repo.parent / "scratch")}
    if agent is not None:
        payload["agent_type"] = agent
    return run(payload)


def bash(repo: Path, command: str):
    return call(repo, "Bash", command=command)


def test_non_tester_sessions_always_pass(tmp_path):
    repo = make_repo(tmp_path)
    bare = tmp_path / "bare"
    bare.mkdir()
    for agent in (None, "Explore", "prd-tester-extra", "xprd-tester"):
        assert call(repo, "Read", agent=agent, file_path="src/app.py").returncode == 0, agent
        assert call(repo, "Bash", agent=agent, command="cat src/app.py").returncode == 0, agent
    assert call(bare, "Read", agent=None, file_path="src/app.py").returncode == 0
    assert run_raw("not json").returncode == 0
    assert run_raw("[1]").returncode == 0


def test_tester_reads_prd_tests_and_scratch_but_not_src(tmp_path):
    repo = make_repo(tmp_path)
    assert call(repo, "Read", file_path="docs/prd/x/prd.md").returncode == 0
    assert call(repo, "Read", file_path=str(repo / "tests/integration/t.py")).returncode == 0
    assert call(repo, "Write", file_path=str(tmp_path / "scratch/t.py"), content="x").returncode == 0
    assert call(repo, "Edit", file_path="tests/t.py", old_string="a", new_string="b").returncode == 0
    assert call(repo, "NotebookEdit", notebook_path="tests/n.ipynb").returncode == 0
    r = call(repo, "Read", file_path="src/app.py")
    assert_blocked(r)
    assert r.stderr.startswith("prd-tester may only read under: ")
    assert str(repo / "docs/prd/x") in r.stderr and len(r.stderr.strip().splitlines()) == 1
    assert_blocked(call(repo, "Write", file_path="src/app.py", content="x"))
    assert_blocked(call(repo, "NotebookEdit", notebook_path="src/n.ipynb"))
    assert_blocked(call(repo, "Read"))


def test_glob_grep_without_path_is_blocked(tmp_path):
    repo = make_repo(tmp_path)
    assert_blocked(call(repo, "Glob", pattern="**/*.py"))
    assert_blocked(call(repo, "Grep", pattern="def "))
    assert call(repo, "Glob", pattern="**/*.py", path="tests").returncode == 0
    assert call(repo, "Grep", pattern="def ", path="docs/prd/x").returncode == 0
    assert_blocked(call(repo, "Grep", pattern="def ", path="src"))
    assert_blocked(call(repo, "Glob", pattern="../src/*", path="tests"))
    assert_blocked(call(repo, "Glob", pattern=str(repo / "src/*"), path="tests"))


def test_traversal_and_symlink_escapes_are_blocked(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "tests/link").symlink_to(repo / "src")
    (repo / "tests/filelink.py").symlink_to(repo / "src/app.py")
    for p in ("docs/prd/x/../../../src/app.py", str(repo / "src/app.py"), "tests/link/app.py", "tests/filelink.py",
              "docs/prd-evil/secret.md", str(repo / "docs/prd-evil/secret.md"), "tests/../src/app.py",
              "/etc/passwd"):
        assert_blocked(call(repo, "Read", file_path=p))
    assert call(repo, "Read", file_path="docs/prd/x/../x/prd.md").returncode == 0
    # a PRD folder that is a symlink to src is not a root
    (repo / "docs/prd/sneaky").symlink_to(repo / "src")
    assert_blocked(call(repo, "Read", file_path="docs/prd/sneaky/app.py"))
    repo2 = make_repo(tmp_path / "two", TESTING.replace("`tests/`", "`.`, `../scratch`"))
    assert_blocked(call(repo2, "Read", file_path="src/app.py"))


def test_harness_command_allowed_and_other_bash_blocked(tmp_path):
    repo = make_repo(tmp_path)
    assert bash(repo, "uv run pytest tests/integration -k x").returncode == 0
    assert bash(repo, "uv run pytest tests/integration -k x 2>&1").returncode == 0
    assert bash(repo, "uv run pytest tests/integration > /dev/null").returncode == 0
    assert bash(repo, "ls tests docs/prd/x").returncode == 0
    assert bash(repo, "ls -la tests").returncode == 0
    assert bash(repo, "mkdir -p tests/new").returncode == 0
    assert bash(repo, f"uv run python -m py_compile tests/a.py {tmp_path}/scratch/b.py").returncode == 0
    for cmd in ("cat src/app.py", "python3 src/app.py", "ls", "ls src", "ls tests/../src", "mkdir src/x",
                "uv run python -m py_compile src/app.py", "uv run pytest tests/unit_other",
                "uv run python src/app.py", "ls tests/{a,../src}", "ls $HOME", "ls ~", ""):
        assert_blocked(bash(repo, cmd))
    assert_blocked(bash(repo, "ls tests > src/out.txt"))
    assert_blocked(bash(repo, "ls tests >> src/out.txt"))
    assert_blocked(bash(repo, "ls tests < src/app.py"))
    assert_blocked(bash(repo, "ls tests <<EOF"))
    assert_blocked(bash(repo, "ls tests <<< x"))
    assert bash(repo, "ls tests > tests/out.txt").returncode == 0


@pytest.mark.parametrize("cmd", [
    "uv run pytest tests/integration && cat src/app.py",
    "uv run pytest tests/integration || cat src/app.py",
    "ls tests; cat src/app.py",
    "ls tests | cat src/app.py",
    "ls tests\ncat src/app.py",
    "ls tests & cat src/app.py",
    "ls tests && cd src",
    "ls tests && env cat src/app.py",
    "ls tests && bash -c 'cat src/app.py'",
    "ls tests && sh x",
    "ls tests && zsh x",
    "ls tests && eval cat",
    "ls tests && exec cat",
    "ls tests $(cat src/app.py)",
    "ls `cat src/app.py`",
    "ls <(cat src/app.py)",
    "ls tests >(cat)",
    "echo '$(x)'",
    "ls tests && (cat src/app.py)",
    "ls 'unterminated",
])
def test_compound_command_with_one_forbidden_segment_is_blocked(tmp_path, cmd):
    assert_blocked(bash(make_repo(tmp_path), cmd))


def test_compound_of_allowed_segments_passes(tmp_path):
    repo = make_repo(tmp_path)
    assert bash(repo, "mkdir -p tests/a && ls tests/a; uv run pytest tests/unit | ls tests").returncode == 0
    assert bash(repo, "ls tests\nls docs/prd/x").returncode == 0


def test_missing_testing_md_allows_only_prd_reads(tmp_path):
    repo = make_repo(tmp_path, testing=None)
    assert call(repo, "Read", file_path="docs/prd/x/prd.md").returncode == 0
    assert call(repo, "Glob", pattern="*.md", path="docs/prd/x").returncode == 0
    assert call(repo, "Grep", pattern="x", path="docs/prd/x").returncode == 0
    assert_blocked(call(repo, "Read", file_path="tests/t.py"))
    assert_blocked(call(repo, "Read", file_path=str(tmp_path / "scratch/a")))
    for r in (call(repo, "Write", file_path="docs/prd/x/new.md", content="x"),
              call(repo, "Edit", file_path="docs/prd/x/prd.md", old_string="a", new_string="b"),
              bash(repo, "ls docs/prd/x"), bash(repo, "mkdir docs/prd/x/y")):
        assert_blocked(r)
        assert "testing.md" in r.stderr and "Test roots:" in r.stderr
    # unparsable: a template marker only, and a layout bullet with no Test roots
    for n, text in enumerate((TESTING.replace("`tests/`", "[NEEDS CLARIFICATION: the test directories, each in backticks]"),
                              TESTING.replace(" Test roots: `tests/`.", ""))):
        repo2 = make_repo(tmp_path / f"again{n}", text)
        assert_blocked(call(repo2, "Read", file_path="tests/t.py"))
        assert_blocked(bash(repo2, "uv run pytest tests/integration"))
        assert call(repo2, "Read", file_path="docs/prd/x/prd.md").returncode == 0


def test_no_prd_folder_blocks_the_tester(tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    assert_blocked(call(bare, "Read", file_path="README.md"))


def test_an_uppercase_prd_md_folder_is_not_a_read_root(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "docs/prd/x/prd.md").rename(repo / "docs/prd/x/PRD.md")
    assert_blocked(call(repo, "Read", file_path="docs/prd/x/PRD.md"))
    assert_blocked(call(repo, "Read", file_path="docs/prd/x/testing.md"))


def test_plugin_suffixed_agent_type_is_the_tester(tmp_path):
    repo = make_repo(tmp_path)
    assert_blocked(call(repo, "Read", agent="prd-toolkit:prd-tester", file_path="src/app.py"))
    assert call(repo, "Read", agent="prd-toolkit:prd-tester", file_path="tests/t.py").returncode == 0


def test_tester_never_fails_open(tmp_path):
    repo = make_repo(tmp_path)
    assert call(repo, "WebFetch", url="x").returncode == 2  # unknown tool
    assert run({"agent_type": "prd-tester", "tool_name": "Read", "tool_input": {"file_path": "a"}}).returncode == 2  # no cwd
    assert run({"agent_type": "prd-tester", "tool_name": "Read", "tool_input": "x", "cwd": str(repo)}).returncode == 2
    assert run_raw('{"agent_type": "prd-tester", broken').returncode == 2
    assert run({"agent_type": "prd-tester", "tool_name": "Bash", "tool_input": {"command": 7}, "cwd": str(repo)}).returncode == 2


def test_guard_and_prdlint_agree_on_the_fixture(tmp_path):
    import importlib.util

    from prdlint import model

    spec = importlib.util.spec_from_file_location("prd_tester_guard", GUARD)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    fixtures = Path(__file__).parent / "fixtures/valid/orders/testing.md"
    texts = [fixtures.read_text(), TESTING, TESTING.replace("`tests/`", "`tests/`, `z_tests/`"),
             TESTING.replace("`tests/`", "[NEEDS CLARIFICATION: the test directories, each in backticks]"),
             TESTING.replace("`tests/`", "[NEEDS CLARIFICATION: e.g. `tests/`] `a/`"),
             TESTING.replace(" Test roots: `tests/`.", ""),
             TESTING.replace("Test roots: `tests/`.", "Test roots: see below")]
    for text in texts:
        prd = tmp_path / "docs/prd/orders"
        prd.mkdir(parents=True, exist_ok=True)
        (prd / "testing.md").write_text(text)
        (prd / "prd.md").write_text("---\nstatus: draft\n---\n# P\n")
        assert guard.parse_test_roots(text) == model.load(prd).testing.harness.test_roots, text
    assert guard.parse_test_roots(fixtures.read_text()) == ["tests/"]
    assert guard.parse_harness_commands(fixtures.read_text())[0] == ["pytest", "tests/unit"]


def test_prefix_siblings_are_not_inside_a_root(tmp_path):
    repo = make_repo(tmp_path)
    assert_blocked(call(repo, "Read", file_path="tests-evil/secret.py"), "read")
    assert_blocked(call(repo, "Read", file_path="docs/prd/x-evil/secret.md"), "read")
    assert_blocked(call(repo, "Read", file_path=str(tmp_path / "scratch-evil/a")), "read")


def test_the_tester_cannot_write_its_own_policy(tmp_path):
    repo = make_repo(tmp_path)
    assert_blocked(call(repo, "Write", file_path="docs/prd/x/testing.md", content="`src/`"), "write")
    assert_blocked(call(repo, "Edit", file_path="docs/prd/x/testing.md", old_string="a", new_string="b"), "write")
    assert_blocked(call(repo, "Write", file_path="docs/prd/x/new.md", content="x"), "write")
    assert_blocked(call(repo, "NotebookEdit", notebook_path="docs/prd/x/n.ipynb"), "write")
    assert_blocked(bash(repo, "mkdir docs/prd/x/y"), "write")
    assert_blocked(bash(repo, "ls tests > docs/prd/x/out.txt"), "write")
    assert_blocked(bash(repo, "uv run python -m py_compile docs/prd/x/a.py"), "write")
    r = call(repo, "Write", file_path="docs/prd/x/testing.md", content="x")
    assert str(repo / "docs/prd/x") not in r.stderr and str(repo / "tests") in r.stderr
    assert_blocked(call(repo, "Read", file_path="src/app.py"), "read")
    # reads of the PRD stay allowed
    assert call(repo, "Read", file_path="docs/prd/x/testing.md").returncode == 0
    assert bash(repo, "ls docs/prd/x").returncode == 0


def test_a_test_root_that_holds_or_is_inside_a_prd_is_dropped(tmp_path):
    for n, root in enumerate(("docs/", "docs/prd/", "docs/prd/x/tests/", "docs/prd/x/")):
        repo = make_repo(tmp_path / f"r{n}", TESTING.replace("`tests/`", f"`{root}`"))
        assert_blocked(call(repo, "Write", file_path="docs/guide.md", content="x"))
        assert_blocked(call(repo, "Write", file_path="docs/prd/x/testing.md", content="x"))
        assert_blocked(call(repo, "Read", file_path="src/app.py"))
        assert_blocked(call(repo, "Write", file_path="tests/t.py", content="x"))


def test_undecodable_stdin_does_not_fail_open(tmp_path):
    repo = make_repo(tmp_path)
    payload = (b'{"agent_type": "prd-tester", "tool_name": "Read", "tool_input": {"file_path": "src/\xff"}, "cwd": "'
               + str(repo).encode() + b'"}')
    r = run_raw(payload)
    assert r.returncode == 2, r.stderr
    assert_blocked(r)
    assert run_raw(b"\xff\xfe not json").returncode == 0


@pytest.mark.parametrize("cmd", ["ls tests > tests/[l]ink/app.py", "ls tests/*/..", "ls tests/l?nk", "mkdir tests/[a]",
                                 "uv run python -m py_compile tests/*.py", "ls tests > tests/o*.txt"])
def test_shell_globs_in_path_arguments_are_blocked(tmp_path, cmd):
    assert_blocked(bash(make_repo(tmp_path), cmd))


@pytest.mark.parametrize("cmd", [
    "uv run pytest tests/integration --junitxml=src/app.py",
    "uv run pytest tests/integration --junitxml src/app.py",
    "uv run pytest tests/integration --basetemp src",
    "uv run pytest tests/integration --basetemp=src",
    "uv run pytest tests/integration --rootdir=src",
    "uv run pytest tests/integration --rootdir src",
    "uv run pytest tests/integration -c src/pytest.ini",
    "uv run pytest tests/integration -c src",
    "uv run pytest tests/integration -csrc/x.ini",
    "uv run pytest tests/integration -o cache_dir=src",
    "uv run pytest tests/integration -o cache_dir=src/.cache",
    "uv run pytest tests/integration --override-ini=cache_dir=src",
    "uv run pytest tests/integration --override-ini cache_dir=src",
    "uv run pytest tests/integration -vo cache_dir=src",
    "uv run pytest tests/integration -vocache_dir=src",
    "uv run pytest tests/integration -ocache_dir=src",
    "uv run pytest tests/integration -vo cache_dir=../src",
    "uv run pytest tests/integration -vc src/pytest.ini",
    "uv run pytest tests/integration -vcsrc/pytest.ini",
    "uv run pytest tests/integration -o junit_logging=src/app.py",
    "uv run pytest tests/integration src/app.py",
    "uv run pytest tests/integration src/app.py::test_x",
    "uv run pytest tests/integration ../src/app.py",
    "uv run pytest tests/integration /etc/passwd",
    "uv run pytest tests/integration tests/[l]ink/app.py",
])
def test_harness_option_and_positional_paths_must_stay_in_writable_roots(tmp_path, cmd):
    assert_blocked(bash(make_repo(tmp_path), cmd))


def test_harness_ordinary_options_pass(tmp_path):
    repo = make_repo(tmp_path)
    for cmd in ('uv run pytest tests/integration -k "not slow"', "uv run pytest tests/integration -m smoke -x -q",
                "uv run pytest tests/integration --junitxml=tests/out.xml",
                "uv run pytest tests/integration --junitxml tests/out.xml",
                f"uv run pytest tests/integration --basetemp={tmp_path}/scratch/bt",
                "uv run pytest tests/integration -o cache_dir=tests/.cache",
                "uv run pytest tests/integration -vo cache_dir=tests/c",
                "uv run pytest tests/integration --override-ini cache_dir=tests/c",
                "uv run pytest tests/integration --override-ini=cache_dir=tests/c",
                "uv run pytest tests/integration -v -k x",
                "uv run pytest tests/integration -vk x",
                "uv run pytest tests/integration -vkfoo",
                "uv run pytest tests/integration -rA -p no:cacheprovider",
                "uv run pytest tests/integration tests/integration/test_a.py::test_x[1]",
                'uv run pytest tests/integration -k "a/b"'):
        r = bash(repo, cmd)
        assert r.returncode == 0, (cmd, r.stderr)


def test_one_broken_prd_leaves_the_others_roots_alone(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "docs/prd/y").mkdir()
    (repo / "docs/prd/y/prd.md").write_text("# y\n")  # no testing.md
    assert call(repo, "Write", file_path="tests/t.py", content="x").returncode == 0
    assert bash(repo, "uv run pytest tests/integration").returncode == 0
    assert call(repo, "Read", file_path="docs/prd/y/prd.md").returncode == 0
    r = call(repo, "Write", file_path="src/a.py", content="x")
    assert_blocked(r, "write")
    assert "y/testing.md is missing" in r.stderr
    assert_blocked(call(repo, "Write", file_path="docs/prd/y/testing.md", content="x"), "write")


def test_a_harness_row_starting_with_a_shell_word_is_still_blocked(tmp_path):
    import importlib.util

    text = TESTING.replace("| integration | `uv run pytest tests/integration` | ci |\n",
                           "| integration | `uv run pytest tests/integration` | ci |\n| e2e | `bash run.sh` | ci |\n")
    assert text != TESTING
    spec = importlib.util.spec_from_file_location("prd_tester_guard_row", GUARD)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    assert ["bash", "run.sh"] in guard.parse_harness_commands(text)  # the row really is a harness command
    repo = make_repo(tmp_path, text)
    assert_blocked(bash(repo, "bash run.sh"), "run")
    assert_blocked(bash(repo, "bash run.sh && ls tests"), "run")
    assert bash(repo, "uv run pytest tests/integration").returncode == 0


def test_a_crash_prints_a_different_line_from_a_denial(monkeypatch, capsys):
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("prd_tester_guard_crash", GUARD)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)

    def boom(data):
        raise RuntimeError("boom")

    monkeypatch.setattr(guard, "check", boom)
    payload = json.dumps({"agent_type": "prd-tester", "tool_name": "Read"}).encode()
    monkeypatch.setattr(sys, "stdin", type("S", (), {"buffer": io.BytesIO(payload)})())
    assert guard.main() == 2
    err = capsys.readouterr().err
    assert err.strip() == "prd-tester guard error: RuntimeError: boom (blocked)"
    assert not err.startswith("prd-tester may only ")


def test_hooks_json_points_at_the_guard():
    cfg = json.loads((ROOT / "hooks/hooks.json").read_text())
    (entry,) = cfg["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Read|Glob|Grep|Write|Edit|NotebookEdit|Bash"
    (hook,) = entry["hooks"]
    assert hook == {"type": "command", "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/scripts/prd_tester_guard.py"'}
    assert GUARD.is_file()


SYSTEM_PY = Path("/usr/bin/python3")


def _system_py_version():
    if not SYSTEM_PY.is_file():
        return None
    r = subprocess.run([str(SYSTEM_PY), "-c", "import sys; print(*sys.version_info[:2])"],
                       capture_output=True, text=True)
    return tuple(int(x) for x in r.stdout.split()) if r.returncode == 0 else None


@pytest.mark.skipif((_system_py_version() or (0, 0)) < (3, 9), reason="no /usr/bin/python3 3.9 or later")
def test_the_guard_runs_and_blocks_under_the_system_python(tmp_path):
    """The hook runs `python3`, which on macOS is /usr/bin/python3 (3.9): an import-time TypeError there
    exits 1, which Claude Code treats as non-blocking, so the guard would fail open."""
    compiled = subprocess.run([str(SYSTEM_PY), "-c", "import sys, py_compile; py_compile.compile(sys.argv[1], "
                               "cfile=sys.argv[2], doraise=True)", str(GUARD), str(tmp_path / "g.pyc")],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    imported = subprocess.run([str(SYSTEM_PY), "-c", "import importlib.util as u, sys; "
                               "s = u.spec_from_file_location('g', sys.argv[1]); s.loader.exec_module("
                               "u.module_from_spec(s))", str(GUARD)], capture_output=True, text=True)
    assert imported.returncode == 0, imported.stderr
    repo = make_repo(tmp_path)
    payload = {"agent_type": "prd-tester", "tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"},
               "cwd": str(repo), "scratchpad_dir": str(tmp_path / "scratch")}
    r = subprocess.run([str(SYSTEM_PY), str(GUARD)], input=json.dumps(payload).encode(), capture_output=True)
    r.stderr = r.stderr.decode("utf-8", "replace")
    assert_blocked(r, "read")
    ok = dict(payload, tool_input={"file_path": "docs/prd/x/prd.md"})
    assert subprocess.run([str(SYSTEM_PY), str(GUARD)], input=json.dumps(ok).encode()).returncode == 0


@pytest.mark.parametrize("raw, code", [(json.dumps({"agent_type": "prd-tester", "tool_name": "Read"}), 2),
                                       (json.dumps({"agent_type": "Explore", "tool_name": "Read"}), 0)])
def test_an_interpreter_older_than_3_9_blocks_only_the_tester(monkeypatch, capsys, raw, code):
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("prd_tester_guard_old", GUARD)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    monkeypatch.setattr(guard, "check", lambda data: None)  # would allow, so a 2 comes from the version check
    monkeypatch.setattr(guard.sys, "version_info", (3, 8, 18))
    monkeypatch.setattr(sys, "stdin", type("S", (), {"buffer": io.BytesIO(raw.encode())})())
    assert guard.main() == code
    err = capsys.readouterr().err
    assert ("3.9" in err) == (code == 2), err
