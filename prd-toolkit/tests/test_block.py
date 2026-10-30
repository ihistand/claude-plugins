from conftest import edit
from prd_block import main


def test_creates_claude_md_with_block(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; assert main([str(prd), "--claude-md", str(cm)]) == 0
    t = cm.read_text()
    assert "`superpowers:writing-plans` for plans" in t and "Adopted areas: all (new project)" in t
    assert "version 1.0.0" in t

def test_preserves_surrounding_text_and_is_idempotent(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_text("# Mine\n\nkeep me\n")
    main([str(prd), "--claude-md", str(cm)]); first = cm.read_text()
    main([str(prd), "--claude-md", str(cm)])
    assert cm.read_text() == first and first.startswith("# Mine\n\nkeep me\n")

def test_check_detects_stale(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; main([str(prd), "--claude-md", str(cm)])
    edit(prd, "prd.md", "version: 1.0.0", "version: 1.1.0")
    assert main([str(prd), "--claude-md", str(cm), "--check"]) == 1

def test_unbalanced_markers_exit_2_and_do_not_write(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_text("<!-- prd-toolkit:start -->\nhalf\n")
    assert main([str(prd), "--claude-md", str(cm)]) == 2 and cm.read_text().endswith("half\n")

def test_update_in_place_keeps_text_byte_for_byte(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_bytes(b"top\r\n\nno newline")
    main([str(prd), "--claude-md", str(cm)])
    edit(prd, "prd.md", "version: 1.0.0", "version: 1.1.0")
    cm.write_bytes(cm.read_bytes() + b"\nafter\n")
    main([str(prd), "--claude-md", str(cm)])
    t = cm.read_bytes()
    assert t.startswith(b"top\r\n\nno newline\n\n<!-- prd-toolkit:start -->") and t.endswith(b"end -->\n\nafter\n")
    assert b"version 1.1.0" in t and t.count(b"prd-toolkit:start") == 1
    assert main([str(prd), "--claude-md", str(cm), "--check"]) == 0

def test_two_blocks_and_missing_prd_exit_2(prd, tmp_path, capsys):
    cm = tmp_path / "CLAUDE.md"; main([str(prd), "--claude-md", str(cm)])
    original = cm.read_text(); cm.write_text(original + original)
    assert main([str(prd), "--claude-md", str(cm)]) == 2 and cm.read_text() == original + original
    assert main([str(tmp_path / "nope"), "--claude-md", str(cm)]) == 2
    assert "Traceback" not in capsys.readouterr().err

def test_check_missing_file_is_stale(prd, tmp_path):
    assert main([str(prd), "--claude-md", str(tmp_path / "CLAUDE.md"), "--check"]) == 1

def test_adopted_areas_from_rows(prd, tmp_path):
    edit(prd, "prd.md", "Not applicable: new project.", "See adoption.md.")
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | State |\n|---|---|\n| billing | adopted |\n| search | extracted |\n| auth | adopted |\n")
    cm = tmp_path / "CLAUDE.md"; main([str(prd), "--claude-md", str(cm)])
    assert "Adopted areas: billing, auth\n" in cm.read_text()

def test_symlinked_claude_md_survives(prd, tmp_path):
    real = tmp_path / "real.md"; real.write_text("# Agents\n")
    cm = tmp_path / "CLAUDE.md"; cm.symlink_to(real)
    assert main([str(prd), "--claude-md", str(cm)]) == 0
    assert cm.is_symlink() and "prd-toolkit:start" in real.read_text()
    assert real.read_text().startswith("# Agents\n")

def test_markers_inside_code_fence_are_not_the_block(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"
    doc = "# Docs\n\n```\n<!-- prd-toolkit:start -->\nexample\n<!-- prd-toolkit:end -->\n```\n"
    cm.write_text(doc)
    assert main([str(prd), "--claude-md", str(cm)]) == 0
    t = cm.read_text()
    assert t.startswith(doc) and t.count("prd-toolkit:start") == 2
    assert t[len(doc):].lstrip("\n").startswith("<!-- prd-toolkit:start -->\n## Product")

def test_unclosed_fence_converges(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; cm.write_text("# D\n\n```\nunclosed example\n")
    assert main([str(prd), "--claude-md", str(cm)]) == 0
    assert main([str(prd), "--claude-md", str(cm), "--check"]) == 0
    for _ in range(2):
        assert main([str(prd), "--claude-md", str(cm)]) == 0
    assert cm.read_text().count("prd-toolkit:start") == 1

def test_closed_fence_protected_when_later_fence_unclosed(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"
    doc = "# D\n\n```\n<!-- prd-toolkit:start -->\nexample\n<!-- prd-toolkit:end -->\n```\n\ntext\n\n```\nunclosed\n"
    cm.write_text(doc)
    assert main([str(prd), "--claude-md", str(cm)]) == 0
    assert main([str(prd), "--claude-md", str(cm), "--check"]) == 0
    for _ in range(2):
        assert main([str(prd), "--claude-md", str(cm)]) == 0
    t = cm.read_text()
    assert t.startswith(doc) and t.count("prd-toolkit:start") == 2 and t.count("prd-toolkit:end") == 2


def test_block_routes_lint_through_the_skills(prd, tmp_path):
    cm = tmp_path / "CLAUDE.md"; assert main([str(prd), "--claude-md", str(cm)]) == 0
    t = cm.read_text(encoding="utf-8")
    assert "Lint runs inside the prd-toolkit skills; after any PRD edit, finish through `/prd-change`." in t
    assert "<prd-toolkit>" not in t and "prd_lint.py" not in t
