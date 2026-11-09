"""prd_context.py --for implement: code excerpts around cited Source lines, staleness, Levels."""
import json
import subprocess
from pathlib import Path

import pytest
from conftest import PLUGINS_FILE, edit
from context_fixture import context_prd, pack, parts

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


def git(root: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit(root: Path, msg: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    git(tmp_path, "init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/importer.py").write_text("".join(f"line {n}\n" for n in range(1, 61)))
    (tmp_path / "src/legacy.bin").write_bytes(b"ok\xff\xfe\n" * 30)
    commit(tmp_path, "code")
    sha = git(tmp_path, "rev-parse", "--short", "HEAD")
    prd = context_prd(tmp_path)
    edit(prd, "features/import.md", "Tests: T-001.1",
         f"Source: src/importer.py:30 @{sha}\n  src/legacy.bin:3 @{sha}\nTests: T-001.1")
    commit(tmp_path, "prd")
    return tmp_path, prd, sha


def test_excerpt_window_and_exit_0(repo):
    root, prd, sha = repo
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--context", "5")
    code_part = parts(out)["Code"]
    assert code == 0 and "line 25" in code_part and "line 35" in code_part and "line 24" not in code_part and "line 36" not in code_part
    assert "STALE" not in out and "## Levels" in out and "pytest tests/integration" in out


def test_every_ref_of_a_multi_line_source(repo):
    _, prd, _ = repo
    out = pack(prd, "--area", "import", "--for", "implement")[1]
    assert "src/importer.py:30" in out and "src/legacy.bin:3" in out and "�" in out


def test_changed_file_is_stale_exit_1(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("changed\n" * 10)
    commit(root, "change")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: the cited line's text is gone" in out
    assert "   10  changed" in out and "   11  changed" not in out  # window clamped to the 10-line file


def test_unknown_sha_and_missing_file_are_stale(repo):
    root, prd, sha = repo
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", "src/importer.py:30 @0000000")
    edit(prd, "features/import.md", f"src/legacy.bin:3 @{sha}", f"src/gone.py:3 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: unknown commit 0000000" in out and "STALE: file missing" in out


def test_line_past_end_is_stale(repo):
    root, prd, sha = repo
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", f"src/importer.py:99 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: line 99 is past the end (60 lines)" in out


def test_runs_from_another_directory(repo, monkeypatch):
    root, prd, _ = repo
    monkeypatch.chdir(prd / "features")
    code, out, _ = pack(Path(".."), "--area", "import", "--for", "implement")
    assert code == 0 and "line 30" in out


def test_implement_outside_git_exits_2(ctx):
    code, out, err = pack(ctx, "--area", "import", "--for", "implement")
    assert code == 2 and out == "" and "git" in err


def test_decide_ignores_staleness(repo):
    root, prd, _ = repo
    (root / "src/importer.py").write_text("x\n")
    assert pack(prd, "--area", "import")[0] == 0


def test_req_pack_holds_the_whole_block_and_each_code_excerpt(repo):
    _, prd, _ = repo
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--req", "FR-001")
    assert code == 0 and "FR-001" in out and "Source: src/importer.py:30" in out
    assert "src/legacy.bin:3" in out and "line 30" in parts(out)["Code"]


def test_uncommitted_edit_is_stale_exit_1(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("".join("edited\n" if n == 30 else f"line {n}\n" for n in range(1, 61)))
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: the cited line's text is gone" in out


def test_blank_cited_line_is_judged_by_the_whole_file(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("".join(f"line {n}\n" if n != 30 else "\n" for n in range(1, 61)))
    commit(root, "blank 30")
    sha2 = git(root, "rev-parse", "--short", "HEAD")
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", f"src/importer.py:30 @{sha2}")
    assert pack(prd, "--area", "import", "--for", "implement")[0] == 0
    (root / "src/importer.py").write_text("".join(f"line {n}\n" if n != 31 else "other\n" for n in range(1, 61)))
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: uncommitted changes; the cited line may have moved" in out
    commit(root, "edit 31")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and f"STALE: changed since {sha2}; the cited line may have moved" in out


def test_file_edited_elsewhere_is_current(repo):
    root, prd, _ = repo
    text = (root / "src/importer.py").read_text().replace("line 5\n", "five\n")
    (root / "src/importer.py").write_text(text)
    commit(root, "elsewhere")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 0 and "STALE" not in out and "MOVED" not in out


def test_inserted_lines_above_are_moved_exit_0(repo):
    root, prd, _ = repo
    (root / "src/importer.py").write_text("new a\nnew b\n" + (root / "src/importer.py").read_text())
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--context", "1")
    assert code == 0 and "MOVED: line 30 is now line 32" in out and "STALE" not in out
    assert "   32  line 30" in parts(out)["Code"]


def test_deleted_line_is_stale_gone(repo):
    root, prd, _ = repo
    lines = (root / "src/importer.py").read_text().splitlines(True)
    (root / "src/importer.py").write_text("".join(lines[:29] + lines[30:]))
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: the cited line's text is gone" in out


def test_text_on_two_lines_is_stale_ambiguous(repo):
    root, prd, _ = repo
    lines = (root / "src/importer.py").read_text().splitlines(True)
    lines[9] = lines[10] = "line 30\n"  # the cited text moves to 10 and 11; line 30 changes
    lines[29] = "other\n"
    (root / "src/importer.py").write_text("".join(lines))
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: the cited line's text appears 2 times" in out


def test_crlf_file_with_cited_line_unchanged_is_current(repo):
    root, prd, _ = repo
    (root / "src/importer.py").write_bytes((root / "src/importer.py").read_text().replace("\n", "\r\n").encode())
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 0 and "STALE" not in out and "MOVED" not in out


def test_path_missing_at_the_sha_is_stale(repo):
    root, prd, sha = repo
    (root / "src/new.py").write_text("x\n" * 5)
    commit(root, "new")
    edit(prd, "features/import.md", f"src/legacy.bin:3 @{sha}", f"src/new.py:3 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and f"STALE: src/new.py is not in {sha}" in out


def _api_sources(prd, sha_ok, sha_old):
    edit(prd, "features/api.md", "Traces: UJ-01; NFR-004; `orders.id`", f"Source: src/importer.py:30 @{sha_ok}\nTraces: UJ-01; NFR-004; `orders.id`")
    edit(prd, "features/api.md", "Traces: FR-002, FR-003", f"Source: src/importer.py:31 @{sha_old}\nTraces: FR-002, FR-003")


def test_pulled_in_stale_block_is_not_counted(repo):
    root, prd, sha = repo
    _api_sources(prd, sha, sha)
    (root / "src/importer.py").write_text((root / "src/importer.py").read_text().replace("line 31\n", "gone\n"))
    code, out, _ = pack(prd, "--area", "api", "--for", "implement", "--req", "FR-002")
    assert code == 0, out
    assert "STALE: the cited line's text is gone (pulled in; not counted)" in out
    # asked for directly, the same block counts
    assert pack(prd, "--area", "api", "--for", "implement", "--req", "UJ-01")[0] == 1


def test_an_asked_block_citing_a_pulled_in_blocks_ref_counts(repo):
    root, prd, sha = repo
    _api_sources(prd, sha, sha)  # UJ-01 (first in file order) cites src/importer.py:31; FR-002 cites :30
    edit(prd, "features/api.md", f"Source: src/importer.py:30 @{sha}", f"Source: src/importer.py:31 @{sha}")
    (root / "src/importer.py").write_text((root / "src/importer.py").read_text().replace("line 31\n", "gone\n"))
    code, out, _ = pack(prd, "--area", "api", "--for", "implement", "--req", "FR-002")
    assert code == 1, out
    assert "STALE: the cited line's text is gone" in out and "not counted" not in out
    code, js, _ = pack(prd, "--area", "api", "--for", "implement", "--req", "FR-002", "--json")
    code_parts = [p for p in json.loads(js)["parts"] if p["title"] == "Code"]
    assert code == 1 and [(p["id"], p["stale"], p["counted"]) for p in code_parts] == [("FR-002", True, True)]


def test_json_keeps_stale_raw_and_adds_counted_and_moved(repo):
    root, prd, sha = repo
    _api_sources(prd, sha, sha)  # FR-002 cites :30, UJ-01 (pulled in) cites :31
    text = (root / "src/importer.py").read_text().replace("line 31\n", "gone\n")
    (root / "src/importer.py").write_text("new\n" + text)  # line 30 moves to 31; line 31's text is gone
    code, js, _ = pack(prd, "--area", "api", "--for", "implement", "--req", "FR-002", "--json")
    by_id = {p["id"]: p for p in json.loads(js)["parts"] if p["title"] == "Code"}
    assert code == 0
    assert {k: by_id["UJ-01"][k] for k in ("stale", "counted", "moved")} == {"stale": True, "counted": False, "moved": None}
    assert {k: by_id["FR-002"][k] for k in ("stale", "counted", "moved")} == {"stale": False, "counted": True, "moved": 31}


def test_no_req_counts_every_block_of_the_area(repo):
    root, prd, sha = repo
    _api_sources(prd, sha, sha)
    (root / "src/importer.py").write_text((root / "src/importer.py").read_text().replace("line 31\n", "gone\n"))
    code, out, _ = pack(prd, "--area", "api", "--for", "implement")
    assert code == 1 and "not counted" not in out


def test_malformed_source_is_a_stale_code_item(repo):
    _, prd, sha = repo
    edit(prd, "features/import.md", f"Source: src/importer.py:30 @{sha}\n  src/legacy.bin:3 @{sha}", "Source: `src/importer.py:30`")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: Source not in <path>:<line> @<sha> form" in parts(out)["Code"]
    assert "None." not in parts(out)["Code"]
