"""prd_block.py writes the PRD folder's README and the parent's, beside the CLAUDE.md block."""
import json
import os
import shutil
from pathlib import Path

import prd_block
import pytest
from conftest import FIXTURE, edit
from prd_block import main

START, END = "<!-- prd-toolkit:start -->", "<!-- prd-toolkit:end -->"


@pytest.fixture(autouse=True)
def _nohome(monkeypatch, tmp_path):
    monkeypatch.setattr(prd_block, "PLUGIN_JSON", tmp_path / "no-plugin.json")
    monkeypatch.setattr(prd_block, "HOMEPAGE_FILE", tmp_path / "no-HOMEPAGE")
    monkeypatch.setattr(prd_block, "VENDORED", False)


def run(prd, *extra):
    return main([str(prd), "--claude-md", str(prd.parents[2] / "CLAUDE.md"), *extra])


def readme(prd):
    return (prd / "README.md").read_text()


def parent(prd):
    return (prd.parent / "README.md").read_text()


def test_greet_slots(greet):
    assert run(greet) == 0
    t = readme(greet)
    assert t.startswith(START + "\n# greet — product requirements\n") and t.endswith(END + "\n")
    assert "It is maintained with prd-toolkit, a Claude Code plugin (see [../README.md](../README.md) to set it up)." in t
    assert "Version 1.0.0 · " in t and "· Owner: " in t and "· Updated " in t
    assert "> The greet service says hello to a named person\n> and counts how often it did. It is small.\n" in t
    assert ("| Area | Adoption | File |\n|---|---|---|\n"
            "| api | adopted | [features/api.md](features/api.md) |\n") in t
    assert "| import | confirmed | [features/import.md](features/import.md) |" in t
    assert "{{" not in t
    assert "## Linked PRDs" not in t


def test_unknown_for_missing_frontmatter_key(greet):
    edit(greet, "prd.md", "owner:", "ownerx:")
    run(greet)
    assert "· Owner: unknown ·" in readme(greet)


def test_notes_areas_dash_and_files(notes):
    run(notes)
    t = readme(notes)
    assert "| - | [features/" in t or "| - |" in t
    assert "adoption.md" not in t.split("## What is in this folder")[1].split("## Reading")[0]


def test_files_only_existing_in_order_with_fixed_text(greet):
    run(greet)
    sec = readme(greet).split("## What is in this folder\n\n")[1].split("\n\n## ")[0]
    rows = sec.splitlines()
    assert rows[0] == "| Path | Holds |"
    paths = [r.split("|")[1].strip().strip("`") for r in rows[2:]]
    order = ["prd.md", "features/", "test-cases/", "contracts/", "testing.md", "errors.md", "operations.md",
             "nfr.md", "adoption.md", "links.md"]
    assert paths == [p for p in order if p in paths] and "prd.md" in paths and "adoption.md" in paths
    assert "links.md" not in paths
    assert "| `prd.md` | The overview: goals, glossary, architecture, the requirement index, open questions, changelog |" in sec
    assert "| `errors.md` | The error ledger: every bug, its class and its fix (`E-nnn`) |" in sec


def test_links_on_orders(orders):
    run(orders)
    t = readme(orders)
    assert "## Linked PRDs" in t
    assert "[../billing](../billing)" in t
    assert "`https://example.com/acme/reports.git#reports`" in t
    assert t.index("## Linked PRDs") < t.index("## Reading and changing it")
    assert "| `links.md` | The PRDs whose contracts this one uses or provides |" in t


def test_parent_link_only_under_docs_prd(tmp_path, greet):
    other = tmp_path / "docs/requirements/greet"
    other.parent.mkdir(parents=True)
    shutil.copytree(greet, other)
    assert main([str(other), "--claude-md", str(tmp_path / "CLAUDE.md")]) == 0
    assert "set it up" not in (other / "README.md").read_text()
    assert not (other.parent / "README.md").exists()
    run(greet)
    assert "set it up" in readme(greet) and (greet.parent / "README.md").exists()


def test_empty_summary(notes):
    edit(notes, "prd.md", "The notes service stores short notes. It has no accounts! Anyone may read them?", "")
    edit(notes, "prd.md", "Goals:", "Goals:")
    run(notes)
    assert "_No summary yet: prd.md §2 is empty._" in readme(notes)


def test_parent_three_rows(greet, orders, notes):
    assert run(greet) == 0
    t = parent(greet)
    rows = [r for r in t.splitlines() if r.startswith("| [")]
    assert len(rows) == 3
    names = [r.split("]")[0][3:] for r in rows]
    assert names == sorted(names) == ["greet", "notes", "orders"]
    assert "| [notes](notes/) | 1.0.0 |" in t
    assert "| The notes service stores short notes. |" in t
    assert "| PRD | Version | Status | Covers |" in t
    assert "Install the prd-toolkit plugin for Claude Code." in t and "Claude Code: " not in t


def test_parent_unreadable_sibling(greet, capsys):
    bad = greet.parent / "broken"
    bad.mkdir()
    (bad / "prd.md").write_bytes(b"\xff\xfe not utf-8 \x80\n")
    (greet.parent / "empty").mkdir()
    assert run(greet) == 0
    t = parent(greet)
    assert "| broken | - | could not be read | - |" in t
    assert "empty" not in t
    assert "broken" in capsys.readouterr().err


def test_homepage_sources(greet, tmp_path, monkeypatch):
    plugin = tmp_path / "plugin.json"
    plugin.write_text(json.dumps({"name": "prd-toolkit", "homepage": "https://example.com/p"}))
    monkeypatch.setattr(prd_block, "PLUGIN_JSON", plugin)
    assert prd_block.homepage() == "https://example.com/p"
    run(greet)
    assert "Install the prd-toolkit plugin for Claude Code: https://example.com/p\n" in parent(greet)
    monkeypatch.setattr(prd_block, "VENDORED", True)  # a vendored run reads only HOMEPAGE
    hp = tmp_path / "HOMEPAGE"
    hp.write_text("https://example.com/v\n")
    monkeypatch.setattr(prd_block, "HOMEPAGE_FILE", hp)
    assert prd_block.homepage() == "https://example.com/v"
    run(greet)
    assert "Claude Code: https://example.com/v\n" in parent(greet)


def test_vendored_run_ignores_a_host_plugin_manifest(tmp_path, monkeypatch):
    host = tmp_path / "host.json"
    host.write_text(json.dumps({"name": "host-plugin", "homepage": "https://example.com/host"}))
    monkeypatch.setattr(prd_block, "PLUGIN_JSON", host)
    monkeypatch.setattr(prd_block, "VENDORED", True)
    assert prd_block.homepage() is None
    empty = tmp_path / "HOMEPAGE"
    empty.write_text("\n")
    monkeypatch.setattr(prd_block, "HOMEPAGE_FILE", empty)
    assert prd_block.homepage() is None


def test_plugin_run_ignores_a_manifest_that_is_not_the_toolkits(tmp_path, monkeypatch):
    host = tmp_path / "host.json"
    host.write_text(json.dumps({"name": "host-plugin", "homepage": "https://example.com/host"}))
    monkeypatch.setattr(prd_block, "PLUGIN_JSON", host)
    assert prd_block.homepage() is None


def test_no_homepage(monkeypatch):
    assert prd_block.homepage() is None


def test_merge_top_keeps_old_text_and_refresh_only_between_markers(greet):
    (greet / "README.md").write_bytes(b"# Mine\n\nold text\nno newline")
    run(greet)
    b = (greet / "README.md").read_bytes()
    assert b.startswith(START.encode()) and b.endswith(b"\n\n# Mine\n\nold text\nno newline")
    (greet / "README.md").write_bytes(b + b"\nmore\n")
    edit(greet, "prd.md", "version: 1.0.0", "version: 1.1.0")
    run(greet)
    b2 = (greet / "README.md").read_bytes()
    assert b"Version 1.1.0" in b2 and b2.endswith(b"\n\n# Mine\n\nold text\nno newline\nmore\n")


def test_two_start_markers_exit_2_write_nothing(greet):
    (greet / "README.md").write_text(START + "\n" + START + "\n" + END + "\n")
    before = (greet / "README.md").read_bytes()
    assert run(greet) == 2
    assert (greet / "README.md").read_bytes() == before
    assert not (greet.parent / "README.md").exists()
    assert not (greet.parents[2] / "CLAUDE.md").exists()


def test_fenced_markers_are_not_markers(greet):
    (greet / "README.md").write_text("```\n" + START + "\nx\n" + END + "\n```\n")
    assert run(greet) == 0
    assert readme(greet).count(START) == 2 and readme(greet).startswith(START + "\n# greet")


def test_claude_md_block_stays_at_end(greet):
    cm = greet.parents[2] / "CLAUDE.md"
    cm.write_text("# Mine\n")
    run(greet)
    assert cm.read_text().startswith("# Mine\n") and cm.read_text().rstrip().endswith(END)


def test_check_one_stale(greet, capsys):
    run(greet)
    assert run(greet, "--check") == 0
    (greet / "README.md").write_text((greet / "README.md").read_text().replace("Version 1.0.0", "Version 9"))
    capsys.readouterr()
    assert run(greet, "--check") == 1
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 1 and out[0].startswith("stale: ") and out[0].endswith("README.md")


def test_check_names_each_stale_file(greet, capsys):
    assert run(greet, "--check") == 1
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 3 and all(o.startswith("stale: ") for o in out)
    assert not (greet / "README.md").exists()


def test_check_prints_repo_relative_paths(greet, tmp_path, capsys):
    os.system(f"git -C {tmp_path} init -q")
    run(greet, "--check")
    out = capsys.readouterr().out.splitlines()
    assert "stale: CLAUDE.md" in out and "stale: docs/prd/greet/README.md" in out and "stale: docs/prd/README.md" in out


def test_crlf_readme_owner_text_unchanged(greet):
    owner = b"# Mine\r\nkeep\r\n"
    (greet / "README.md").write_bytes(owner)
    run(greet)
    assert (greet / "README.md").read_bytes().endswith(owner)
    edit(greet, "prd.md", "version: 1.0.0", "version: 1.1.0")
    run(greet)
    b = (greet / "README.md").read_bytes()
    assert b"Version 1.1.0" in b and b.endswith(owner) and b.count(owner) == 1
    assert run(greet, "--check") == 0


def test_folder_name_with_space_is_percent_encoded(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(Path(FIXTURE).parent.parent / "installed_plugins.json"))
    dest = tmp_path / "docs/prd/my notes"
    shutil.copytree(FIXTURE, dest)
    assert main([str(dest), "--claude-md", str(tmp_path / "CLAUDE.md")]) == 0
    assert "[my notes](my%20notes/)" in (dest.parent / "README.md").read_text()


def test_symlinked_readme_is_written_through(greet, tmp_path):
    real = tmp_path / "real-readme.md"
    real.write_text("# Real\n")
    (greet / "README.md").symlink_to(real)
    assert run(greet) == 0
    assert (greet / "README.md").is_symlink()
    assert real.read_text().startswith(START) and real.read_text().endswith("\n\n# Real\n")


def test_marker_in_summary_exits_2_writes_nothing(greet, capsys):
    edit(greet, "prd.md", "It is small.", "It is small. " + END)
    assert run(greet) == 2
    assert "prd_block: prd.md §2 holds a prd-toolkit marker" in capsys.readouterr().err
    assert not (greet / "README.md").exists() and not (greet.parents[2] / "CLAUDE.md").exists()
    assert not (greet.parent / "README.md").exists()
