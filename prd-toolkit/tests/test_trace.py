"""prd_trace.py: the four trace rules against the synthetic legacy repo."""
from pathlib import Path

from legacy import commit, make_legacy_repo
from prd_trace import main
from prdlint import model, trace

ADOPTED = "| notes | adopted | `src/**` |"
HEADER = "| Area | State | Boundary |\n|---|---|---|\n"


def block(fr: str, status: str, tids: list[str]) -> str:
    tests = ", ".join(f"{t} [unit]" for t in tids)
    return f"### {fr} A behaviour\nStatus: {status} (since 1.0.0)\nTests: {tests}  (test-cases/x.yaml)\n\n"


def build(tmp_path: Path, adoption: str | None = ADOPTED, features: dict[str, str] | None = None, roots: str = "`tests/`") -> Path:
    """The legacy repo with a minimal PRD at docs/prd/notes. `adoption` is table rows, or None for 'new project'."""
    repo = make_legacy_repo(tmp_path / "legacy")
    prd = repo / "docs/prd/notes"
    (prd / "features").mkdir(parents=True)
    section = "Not applicable: new project." if adoption is None else "See adoption.md."
    (prd / "prd.md").write_text(f"# Notes\n\n## 8. Adoption map\n\n{section}\n\n## 9. Versioning\n", encoding="utf-8")
    if adoption is not None:
        (prd / "adoption.md").write_text("# Adoption map\n\n" + HEADER + adoption + "\n", encoding="utf-8")
    (prd / "testing.md").write_text(f"# Testing\n\n## Harness\n- **Layout.** Test roots: {roots}.\n", encoding="utf-8")
    for name, text in (features or {"notes": block("FR-001", "live", ["T-001.1"])}).items():
        (prd / (name if name.endswith(".md") else f"features/{name}.md")).write_text(f"# {name}\n\n{text}", encoding="utf-8")
    return prd


def trace_rules(prd: Path, rng: str | None = None):
    loaded = model.load(prd)
    return trace.run_trace(loaded, model.repo_root(prd), rng)


def rules(findings) -> list[str]:
    return [f.rule for f in findings]


def test_clean_when_every_tid_is_cited(tmp_path):
    assert trace_rules(build(tmp_path)) == []


def test_citations_map_tid_to_file_and_line(tmp_path):
    prd = build(tmp_path)
    cites = trace.citations(model.load(prd), model.repo_root(prd))
    assert cites == {"T-001.1": [("tests/test_notes.py", 10)]}


def test_uncited_tid_fires_t_implemented(tmp_path):
    prd = build(tmp_path, features={"notes": block("FR-001", "approved", ["T-001.1", "T-001.2"])})
    f = trace_rules(prd)
    assert rules(f) == ["t-implemented"] and "T-001.2" in f[0].message and f[0].file == "features/notes.md"


def test_citation_prefix_does_not_count(tmp_path):
    prd = build(tmp_path)
    (prd.parents[2] / "tests/test_notes.py").write_text('def test_x():\n    """@prd T-001.10"""\n', encoding="utf-8")
    f = trace_rules(prd)
    assert [x.message.split()[0] for x in f if x.rule == "t-implemented"] == ["T-001.1"]
    assert "T-001.10" in " ".join(x.message for x in f if x.rule == "test-cites-live")


def test_citation_of_unknown_or_removed_tid_fires_test_cites_live(tmp_path):
    feats = {"notes": block("FR-001", "live", ["T-001.1"]) + block("FR-002", "removed", ["T-002.1"])}
    prd = build(tmp_path, features=feats)
    (prd.parents[2] / "tests/test_extra.py").write_text('"""@prd T-002.1 @prd T-009.9"""\n', encoding="utf-8")
    f = [x for x in trace_rules(prd) if x.rule == "test-cites-live"]
    assert len(f) == 2
    msgs = " ".join(x.message for x in f)
    assert "T-009.9" in msgs and "T-002.1" in msgs and "removed" in msgs


def test_live_requirement_with_uncited_tid_fires_status_current(tmp_path):
    prd = build(tmp_path, features={"notes": block("FR-001", "live", ["T-001.1", "T-001.2"])})
    f = trace_rules(prd)
    assert sorted(rules(f)) == ["status-current", "t-implemented"]
    assert "FR-001" in next(x for x in f if x.rule == "status-current").message


def test_built_requirement_does_not_fire_status_current(tmp_path):
    prd = build(tmp_path, features={"notes": block("FR-001", "built", ["T-001.1", "T-001.2"])})
    assert rules(trace_rules(prd)) == ["t-implemented"]


def test_out_of_scope_area_is_ignored(tmp_path):
    feats = {"notes": block("FR-001", "live", ["T-001.1"]), "other": block("FR-002", "live", ["T-002.1"])}
    prd = build(tmp_path, adoption=ADOPTED + "\n| other | confirmed | `lib/**` |", features=feats)
    assert trace_rules(prd) == []


def test_empty_adoption_map_covers_no_area(tmp_path):
    prd = build(tmp_path, adoption="", features={"notes": block("FR-001", "live", ["T-001.1", "T-001.2"])})
    assert model.load(prd).adoption == []
    assert trace_rules(prd) == []


def test_new_project_covers_every_area_including_nfr(tmp_path):
    feats = {"notes": block("FR-001", "approved", ["T-001.1"]), "nfr.md": block("NFR-001", "approved", ["T-005.1"])}
    prd = build(tmp_path, adoption=None, features=feats)
    f = trace_rules(prd)
    assert [(x.rule, x.file) for x in f] == [("t-implemented", "nfr.md")]


def test_nfr_area_is_scoped_by_its_adoption_row(tmp_path):
    feats = {"notes": block("FR-001", "approved", ["T-001.1"]), "nfr.md": block("NFR-001", "approved", ["T-005.1"])}
    assert trace_rules(build(tmp_path, features=feats)) == []
    prd = build(tmp_path / "b", adoption=ADOPTED + "\n| nfr | adopted | `src/**` |", features=feats)
    assert rules(trace_rules(prd)) == ["t-implemented"]


def test_commit_in_boundary_without_refs_fires_commit_refs(tmp_path):
    prd = build(tmp_path)
    f = [x for x in trace_rules(prd, "HEAD") if x.rule == "commit-refs"]
    assert len(f) == 1 and "src/notes/" in f[0].message and f[0].file == "prd.md"
    assert f[0].line == 1  # a file-level finding, as lint's are


def test_refs_none_trailer_is_accepted(tmp_path):
    prd = build(tmp_path)
    repo = prd.parents[2]
    (repo / "src/notes/app.py").write_text("# comment\n" + (repo / "src/notes/app.py").read_text(), encoding="utf-8")
    commit(repo, "Tidy\n\nRefs: none (no behaviour change)", "src")
    assert trace_rules(prd, "HEAD~1..HEAD") == []
    (repo / "src/notes/app.py").write_text("# again\n" + (repo / "src/notes/app.py").read_text(), encoding="utf-8")
    commit(repo, "Tidy again", "src")
    assert rules(trace_rules(prd, "HEAD~1..HEAD")) == ["commit-refs"]


def test_commit_outside_boundary_needs_no_refs(tmp_path):
    prd = build(tmp_path)
    (prd.parents[2] / "README.md").write_text("changed\n", encoding="utf-8")
    commit(prd.parents[2], "Docs only", "README.md")
    assert trace_rules(prd, "HEAD~1..HEAD") == []


def test_no_range_skips_commit_refs(tmp_path):
    assert "commit-refs" not in rules(trace_rules(build(tmp_path)))


def test_cli_exit_codes(tmp_path, capsys, monkeypatch):
    prd = build(tmp_path)
    monkeypatch.chdir(prd.parents[2])
    assert main([str(prd)]) == 0 and capsys.readouterr().out == ""
    assert main([str(prd), "--range", "HEAD"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("docs/prd/notes/prd.md:1: commit-refs:")
    (prd.parents[2] / "tests/test_notes.py").write_text("", encoding="utf-8")
    assert main([str(prd)]) == 1
    assert "docs/prd/notes/features/notes.md:" in capsys.readouterr().out
    assert main([str(tmp_path)]) == 2 and "no prd.md" in capsys.readouterr().err
    assert main([str(prd), "--range", "nope..HEAD"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("prd_trace: bad --range nope..HEAD: ") and "internal error" not in err
    assert main([str(prd), "--range=--output=x"]) == 2
    assert "bad --range --output=x" in capsys.readouterr().err


def test_non_ascii_path_in_boundary_still_matches(tmp_path):
    prd = build(tmp_path)
    repo = prd.parents[2]
    (repo / "src/notes/café.py").write_text("x = 1\n", encoding="utf-8")
    commit(repo, "Add cafe", "src")
    f = trace_rules(prd, "HEAD~1..HEAD")
    assert rules(f) == ["commit-refs"] and "café.py" in f[0].message


def test_empty_refs_line_does_not_match_across_a_newline(tmp_path):
    prd = build(tmp_path)
    repo = prd.parents[2]
    (repo / "src/notes/app.py").write_text("# c\n" + (repo / "src/notes/app.py").read_text(), encoding="utf-8")
    commit(repo, "Tidy\n\nRefs:\nsomething else", "src")
    assert rules(trace_rules(prd, "HEAD~1..HEAD")) == ["commit-refs"]


def test_commit_refs_never_fires_for_a_new_project(tmp_path):
    prd = build(tmp_path, adoption=None)
    assert [x for x in trace_rules(prd, "HEAD") if x.rule == "commit-refs"] == []


def test_a_leftover_dry_run_directory_does_not_count(tmp_path):
    """A dry run's tests are thrown away: a citation left in `.prd-dry-run-*` proves nothing."""
    prd = build(tmp_path, features={"notes": block("FR-001", "approved", ["T-001.1", "T-001.2"])})
    leftover = prd.parents[2] / "tests/.prd-dry-run-20261030T120000/nested"
    leftover.mkdir(parents=True)
    (leftover / "test_t0012.py").write_text('def test_x():\n    """@prd T-001.2"""\n', encoding="utf-8")
    assert "T-001.2" not in trace.citations(model.load(prd), model.repo_root(prd))
    f = trace_rules(prd)
    assert rules(f) == ["t-implemented"] and "T-001.2" in f[0].message


def test_unmigrated_02_prd_exits_2_with_the_migration_message(tmp_path, capsys):
    """A 0.2 PRD with the table still in §8 and no adoption.md is not a new project."""
    prd = build(tmp_path)
    (prd / "adoption.md").unlink()
    md = prd / "prd.md"
    md.write_text(md.read_text().replace("See adoption.md.", HEADER + ADOPTED), encoding="utf-8")
    assert main([str(prd), "--range", "HEAD"]) == 2
    out, err = capsys.readouterr()
    assert out == "" and "section 8: the adoption map moved to adoption.md in prd-toolkit 0.3" in err
