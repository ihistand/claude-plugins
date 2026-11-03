"""Eval graders that depend on the template: the marks-unknowns lookahead must list every template marker."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "templates/prd/prd.md"
GRADER = ROOT / "evals/authoring-new-prd/graders/marks-unknowns.md"
OWNER_FILL = "who owns this product"  # authoring-prds fills {{owner}} with this marker


def pattern() -> re.Pattern:
    m = re.search(r"^pattern: '(.*)'$", GRADER.read_text(encoding="utf-8"), re.M)
    assert m, "no single-quoted pattern in the grader"
    return re.compile(m.group(1))


def template_copy() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    for slot, value in {"{{project}}": "link-shortener", "{{owner}}": f"[NEEDS CLARIFICATION: {OWNER_FILL}]",
                        "{{date}}": "2026-10-30", "{{sql_dialect}}": "postgres"}.items():
        text = text.replace(slot, value)
    return text


def test_lookahead_lists_every_template_marker():
    texts = set(re.findall(r"NEEDS CLARIFICATION: ([^\]]*)\]", TEMPLATE.read_text(encoding="utf-8"))) | {OWNER_FILL}
    body = re.search(r"\(\?!\(\?:(.*)\)\\\]\)", pattern().pattern).group(1)
    listed = {re.sub(r"\\(.)", r"\1", alt) for alt in re.split(r"(?<!\\)\|", body)}  # an escaped \| is text
    assert listed == texts


def test_template_copy_and_invented_edits_do_not_pass():
    copy = template_copy()
    edited = copy.replace("[NEEDS CLARIFICATION: database and version]", "PostgreSQL 16")
    edited = edited.replace("[NEEDS CLARIFICATION: framework and version]", "FastAPI 0.115")
    for text in (copy, edited):  # a read-only grep leaves the copy as it was: the first case
        assert not pattern().search(text)


def test_real_unknowns_pass():
    copy = template_copy()
    assert pattern().search(copy.replace("[NEEDS CLARIFICATION: database and version]",
                                         "[NEEDS CLARIFICATION: which Postgres version runs in production]"))
    assert pattern().search(copy.replace("|---|---|---|\n\n## 13", "|---|---|---|\n| A-01 | Links never expire | open |\n\n## 13"))
    assert pattern().search("- AC-001.1 ... [ASSUMPTION A-02: a code is 7 characters]")


def test_the_adoption_map_marker_names_the_two_bodies():
    text = TEMPLATE.read_text(encoding="utf-8")
    marker = text.split("## 8. Adoption map\n", 1)[1].split("\n## ", 1)[0]
    assert "See adoption.md." in marker and "Not applicable: new project" in marker


GLOB_GRADER = ROOT / "evals/tester-stays-out-of-src/graders/dry-run-no-test-root-glob.md"


def _glob_counts(tool_input: dict) -> bool:
    import json

    m = re.search(r"^input_match: '(.*)'$", GLOB_GRADER.read_text(encoding="utf-8"), re.M)
    assert m, "no single-quoted input_match"
    return bool(re.search(m.group(1), json.dumps(tool_input, separators=(",", ":"))))


def test_the_dry_run_glob_grader_counts_test_root_listings_only():
    counted = [{"pattern": "**/*.py", "path": "tests"}, {"pattern": "*", "path": "/repo/tests/"},
               {"pattern": "tests/**/*.py"}, {"pattern": "**/*"}, {"pattern": "*.py", "path": "tests/unit"},
               {"path": "tests", "pattern": ".prd-dry-run-x/../test_notes.py"}]
    exempt = [{"path": "tests", "pattern": ".prd-dry-run-*"}, {"pattern": ".prd-dry-run-*", "path": "tests"},
              {"pattern": "tests/.prd-dry-run-*/**"}, {"pattern": "**/*", "path": "tests/.prd-dry-run-20261030T120000"},
              {"pattern": "**/prd-tester*"}, {"pattern": "**/*.md", "path": "docs/prd/notes"}]
    for ti in counted:
        assert _glob_counts(ti), ti
    for ti in exempt:
        assert not _glob_counts(ti), ti


# --- the 0.4 building evals, and a structural check over every eval ---

import json  # noqa: E402

import yaml  # noqa: E402

EVALS = ROOT / "evals"
BUILDING = ["building-trigger", "building-not-for-plain-code", "builder-stays-out-of-prd", "build-gap-stops", "build-close-no-bump"]


def _grader(case: str, name: str) -> dict:
    text = (EVALS / case / "graders" / f"{name}.md").read_text(encoding="utf-8")
    cfg = yaml.safe_load(text.split("---\n")[1])
    cfg["body"] = text.split("---\n", 2)[2].strip()
    return cfg


def _tool_input_counts(case: str, name: str, tool_input: dict) -> bool:
    return bool(re.search(_grader(case, name)["input_match"], json.dumps(tool_input, separators=(",", ":"))))


def test_every_eval_is_well_formed():
    cases = sorted(p.parent for p in EVALS.glob("*/prompt.md"))
    assert {c.name for c in cases} >= set(BUILDING)
    for case in cases:
        fm = yaml.safe_load((case / "prompt.md").read_text(encoding="utf-8").split("---\n")[1])
        assert fm["max_turns"] and fm["allowed_tools"], case
        graders = sorted((case / "graders").glob("*.md"))
        assert graders, case
        if (case / "case.yaml").exists():
            cy = yaml.safe_load((case / "case.yaml").read_text(encoding="utf-8"))
            assert cy["name"] == case.name
            script = case / cy["context"]["scaffold_script"]
            assert script.is_file() and script.stat().st_mode & 0o111, script
        for g in graders:
            cfg = yaml.safe_load(g.read_text(encoding="utf-8").split("---\n")[1])
            assert cfg["type"] in {"tool_used", "regex", "file_exists"}, g
            if cfg["type"] == "tool_used":
                re.compile(cfg.get("input_match", ""))
                if cfg.get("max") == 0:
                    assert cfg.get("min") == 0, f"{g}: a lone max: 0 reads as expected 1..0"
            if cfg["type"] == "regex":
                re.compile(cfg["pattern"])
                assert cfg.get("match", "contains") in {"contains", "not_contains"}, g


def test_the_building_evals_use_the_committed_scaffold():
    assert not (EVALS / "scaffolds/build_repo.sh").exists()
    for case in ("building-trigger", "builder-stays-out-of-prd", "build-gap-stops", "build-close-no-bump"):
        assert 'scaffolds/build_repo.py" "$PWD"' in (EVALS / case / "scaffold.sh").read_text(encoding="utf-8")


def test_the_builder_graders_see_the_callers_close_but_not_a_prd_edit():
    n = "no-prd-edit-beyond-status"
    base = "/w/docs/prd/notes/features/notes.md"
    close = [{"replace_all": False, "file_path": base, "old_string": "### FR-003 Count notes\nStatus: approved\n",
              "new_string": "### FR-003 Count notes\nStatus: verified\nSource: src/notes/app.py:20 @abc1234\n"},
             {"file_path": "/w/docs/prd/notes/prd.md", "old_string": "| FR-003 | Count notes | approved |",
              "new_string": "| FR-003 | Count notes | verified |"},
             {"file_path": base, "old_string": "Status: approved", "new_string": "Status: built"}]
    prd_edits = [{"file_path": base, "old_string": "return the number of stored notes.", "new_string": "return the number of live notes."},
                 {"file_path": "/w/docs/prd/notes/test-cases/notes.yaml", "old_string": "output: 0", "new_string": "output: 1"}]
    for ti in close:
        assert not _tool_input_counts("builder-stays-out-of-prd", n, ti), ti
    for ti in prd_edits:
        assert _tool_input_counts("builder-stays-out-of-prd", n, ti), ti
    assert not _tool_input_counts("builder-stays-out-of-prd", n, {"file_path": "/w/src/notes/app.py", "old_string": "a", "new_string": "b"})
    w = "no-prd-write"
    assert _tool_input_counts("builder-stays-out-of-prd", w, {"file_path": "/w/docs/prd/notes/features/x.md", "content": "x"})
    assert not _tool_input_counts("builder-stays-out-of-prd", w, {"file_path": "/w/tests/test_notes_unit.py", "content": "x"})


def test_the_tester_file_graders_catch_a_unit_case_in_it_and_pass_the_testers_own_edits():
    t = "/w/tests/test_notes.py"
    for name in ("no-tester-file-edit", "no-tester-file-write"):
        assert _tool_input_counts("builder-stays-out-of-prd", name, {"file_path": t, "old_string": "a", "new_string": '"""@' 'prd T-003.1"""'})
        assert _tool_input_counts("builder-stays-out-of-prd", name, {"file_path": t, "content": '"""@' 'prd T-003.1"""'})
        assert not _tool_input_counts("builder-stays-out-of-prd", name, {"file_path": t, "old_string": "a", "new_string": '"""@' 'prd T-003.2"""'})
        assert not _tool_input_counts("builder-stays-out-of-prd", name, {"file_path": "/w/tests/test_notes_unit.py", "content": '"""@' 'prd T-003.1"""'})


def test_the_file_graders_hold_on_the_start_repo_and_catch_a_reworded_ac(tmp_path):
    import subprocess
    import sys

    dst = tmp_path / "repo"
    subprocess.run([sys.executable, "-B", str(EVALS / "scaffolds/build_repo.py"), str(dst)], check=True, capture_output=True)
    feature = (dst / "docs/prd/notes/features/notes.md").read_text(encoding="utf-8")
    cases = (dst / "docs/prd/notes/test-cases/notes.yaml").read_text(encoding="utf-8")
    assert re.search(_grader("builder-stays-out-of-prd", "ac-and-cases-unchanged")["pattern"], feature)
    assert re.search(_grader("builder-stays-out-of-prd", "test-cases-unchanged")["pattern"], cases)
    assert not re.search(_grader("builder-stays-out-of-prd", "ac-and-cases-unchanged")["pattern"], feature.replace("stored notes", "live notes"))
    assert not re.search(_grader("builder-stays-out-of-prd", "test-cases-unchanged")["pattern"], cases.replace("output: 0", "output: 1"))
    assert re.search(_grader("build-close-no-bump", "fr003-verified")["pattern"], feature.replace("Status: approved", "Status: verified"))
    assert not re.search(_grader("build-close-no-bump", "fr003-verified")["pattern"], feature)
    gap = _grader("build-gap-stops", "fr003-still-approved")["pattern"]
    assert not re.search(gap, feature) and not re.search(gap, feature.replace("Status: approved", "Status: built"))
    assert re.search(gap, feature.replace("Status: approved", "Status: verified"))
    prd = (dst / "docs/prd/notes/prd.md").read_text(encoding="utf-8")
    assert re.search(_grader("build-close-no-bump", "no-version-bump")["pattern"], prd)
    assert not re.search(_grader("build-close-no-bump", "no-new-changelog-row")["pattern"], prd)
    assert re.search(_grader("build-close-no-bump", "no-new-changelog-row")["pattern"], prd + "| 1.2.0 | 2026-11-01 | x | y |\n")


def test_the_gap_graders_allow_built_and_catch_a_guessed_count():
    ed = "no-status-edit"
    mk = lambda s: {"file_path": "/w/docs/prd/notes/features/notes.md", "old_string": "x", "new_string": s}  # noqa: E731
    assert _tool_input_counts("build-gap-stops", ed, mk("### FR-003 Count notes\nStatus: verified\n"))
    assert not _tool_input_counts("build-gap-stops", ed, mk("### FR-003 Count notes\nStatus: built\n"))
    pat = _grader("build-gap-stops", "no-guessed-archive-count")["pattern"]
    guess = 'notes.app.archive_note(2)\n    assert notes.app.count_notes() == 2'
    assert re.search(pat, guess) and re.search(pat, "archive_note(2)\n    assert count_notes() == len(_NOTES)")
    assert not re.search(pat, "archive_note(2)\n    assert isinstance(result, int)")
    assert not re.search(pat, "def archive_note(note_id: int) -> None:\n    assert add_note('a') == 1")


def test_the_version_graders_look_at_prd_md_only():
    prd = "/w/docs/prd/notes/prd.md"
    assert _tool_input_counts("build-close-no-bump", "no-version-edit", {"file_path": prd, "old_string": "version: 1.1.0", "new_string": "version: 1.2.0"})
    assert not _tool_input_counts("build-close-no-bump", "no-version-edit", {"file_path": "/w/src/notes/cfg.py", "old_string": "version: 1", "new_string": "version: 2"})
    assert not _tool_input_counts("build-close-no-bump", "no-version-edit", {"file_path": prd, "old_string": "Status: approved", "new_string": "Status: built"})
    assert _tool_input_counts("build-close-no-bump", "no-version-write", {"file_path": prd, "content": "---\nversion: 2.0.0\nupdated: x"})
    assert not _tool_input_counts("build-close-no-bump", "no-version-write", {"file_path": prd, "content": "---\nversion: 1.1.0\nupdated: x"})
    assert not _tool_input_counts("build-close-no-bump", "no-version-write", {"file_path": "/w/pkg.py", "content": "version: 2"})


# --- 0.7.1: adopting-confirm-headless-fallback ---

CONFIRM = "adopting-confirm-headless-fallback"


def test_the_confirm_graders_catch_a_live_status_by_edit_or_write_and_pass_other_edits():
    base = "/w/docs/prd/notes/features/notes.md"
    live_edits = [{"file_path": base, "old_string": "Status: as-built", "new_string": "Status: live (since 1.0.0)"},
                  {"file_path": "/w/docs/prd/notes/prd.md", "old_string": "x",
                   "new_string": "| FR-001 | Add a note | live | features/notes.md | 1.0.0 |"}]
    for ti in live_edits:
        assert _tool_input_counts(CONFIRM, "no-edit-sets-live", ti), ti
    for ti in ({"file_path": base, "old_string": "a", "new_string": "Status: as-built\nSource: x"},
               {"file_path": base, "old_string": "a", "new_string": "Status: approved"}):
        assert not _tool_input_counts(CONFIRM, "no-edit-sets-live", ti), ti
    assert _tool_input_counts(CONFIRM, "no-write-sets-live", {"file_path": base, "content": "### FR-001\nStatus: live (since 1.0.0)\n"})
    assert not _tool_input_counts(CONFIRM, "no-write-sets-live", {"file_path": base, "content": "Status: as-built\n"})
    assert not _tool_input_counts(CONFIRM, "no-write-sets-live", {"file_path": "/w/.prd-confirm-notes.md", "content": "Status: live"})


def test_the_confirm_file_graders_hold_on_the_extracted_start_repo_and_fail_on_a_confirmation(tmp_path):
    import subprocess
    import sys

    dst = tmp_path / "repo"
    subprocess.run([sys.executable, "-B", str(EVALS / "scaffolds/notes_repo.py"), str(dst), "extracted"], check=True, capture_output=True)
    feature = (dst / "docs/prd/notes/features/notes.md").read_text(encoding="utf-8")
    adoption = (dst / "docs/prd/notes/adoption.md").read_text(encoding="utf-8")
    live = _grader(CONFIRM, "no-block-live")["pattern"]
    extracted = _grader(CONFIRM, "area-stays-extracted")["pattern"]
    assert feature.count("Status: as-built") == 2 and not re.search(live, feature)
    assert re.search(live, feature.replace("Status: as-built", "Status: live (since 1.0.0)", 1))
    assert re.search(extracted, adoption)
    assert not re.search(extracted, adoption.replace("| notes | extracted |", "| notes | confirmed |"))
    lint = subprocess.run([sys.executable, str(ROOT / "scripts/prd_lint.py"), str(dst / "docs/prd/notes")],
                          capture_output=True, text=True)
    assert lint.returncode == 0, lint.stdout + lint.stderr


# --- R26: lint-exit-0 needs a lint of the PRD folder whose own result is prd-lint-exit=0 ---

LINT_EXIT_CASES = ("authoring-new-prd", "authoring-proposes-pack", "authoring-spanish-ears")


def _tool_use(i: str, cmd: str) -> str:
    return json.dumps({"type": "tool_use", "id": i, "name": "Bash", "input": {"command": cmd}}, separators=(",", ":"))


def _tool_result(i: str, content: str) -> str:
    return json.dumps({"tool_use_id": i, "type": "tool_result", "content": content}, separators=(",", ":"))


def test_lint_exit_0_graders_need_a_lint_of_the_prd_folder():
    gate = '; echo "prd-lint-exit=$?"'
    passing = [
        _tool_use("toolu_A", "uv run --script /p/scripts/prd_lint.py docs/prd/greet" + gate) + "\n" + _tool_result("toolu_A", "prd-lint-exit=0"),
        _tool_use("toolu_B", 'uv run --script "/p q/prd_lint.py" docs/prd/greet' + gate) + "\n" + _tool_result("toolu_B", "prd-lint-exit=0"),
        _tool_use("toolu_C", "uv run --script $P/scripts/prd_lint.py $D" + gate) + "\n" + _tool_result("toolu_C", "prd-lint-exit=0"),
    ]
    failing = [
        # a listing echoed with the lint tag (the 0.8.0 review's case): 0 before any PRD exists
        _tool_use("toolu_D", "uv run --script /p/scripts/prd_lint.py --list-packs" + gate) + "\n" + _tool_result("toolu_D", "demo 1.0.0\nprd-lint-exit=0"),
        _tool_use("toolu_E", "uv run --script /p/scripts/prd_lint.py docs/prd/greet" + gate) + "\n" + _tool_result("toolu_E", "x: y\nprd-lint-exit=1"),
        _tool_use("toolu_F", "uv run --script /p/scripts/prd_lint.py docs/prd/greet" + gate) + "\n" + _tool_result("toolu_F", "prd-lint-exit=1")
        + "\n" + _tool_use("toolu_G", "uv run --script /p/scripts/prd_lint.py --list-packs" + gate) + "\n" + _tool_result("toolu_G", "prd-lint-exit=0"),
        '{"type":"text","text":"it passes lint (`prd-lint-exit=0`)"}',
    ]
    patterns = {_grader(c, "lint-exit-0")["pattern"] for c in LINT_EXIT_CASES}
    assert len(patterns) == 1, "the three lint-exit-0 graders share one pattern"
    for c in LINT_EXIT_CASES:
        assert _grader(c, "lint-exit-0")["target"] == "trace"
    pattern = re.compile(patterns.pop())
    for t in passing:
        assert pattern.search(t), t
    for t in failing:
        assert not pattern.search(t), t
