"""prdlint.overview: the facts a PRD's README and its Overview tab share, and §2's two optional parts."""
import shutil
from pathlib import Path

import pytest
import yaml
from conftest import edit, lint

from prdlint import languages, model, overview

TEMPLATE = Path(__file__).parent.parent / "templates/prd"
LANG_DIR = Path(__file__).parent.parent / "references/languages"


def facts(root):
    return overview.facts(model.load(root))


def test_greet_facts(greet):
    f = facts(greet)
    assert (f.slug, f.version, f.status, f.owner, f.updated) == ("greet", "1.0.0", "Approved", "Sample Owner", "2026-10-29")
    assert f.summary == "The greet service says hello to a named person\nand counts how often it did. It is small."
    assert f.first_sentence == "The greet service says hello to a named person and counts how often it did."
    assert f.principles == "- **Plain.** One call, one answer.\n- **Counted.** Every greeting is stored."
    assert f.getting_started == "1. Install the service.\n2. Call `GET /hello/<name>`."
    assert [(a.name, a.file, a.adoption) for a in f.areas] == [("api", "features/api.md", "adopted"), ("import", "features/import.md", "confirmed")]
    assert all(a.counts == {"live": n} for a, n in zip(f.areas, (2, 1)))
    assert f.open_errors == 1
    assert (f.upstreams, f.consumers) == ([], [])
    assert f.files == ["prd.md", "features/", "test-cases/", "contracts/", "testing.md", "errors.md", "operations.md", "nfr.md", "adoption.md"]


def test_orders_facts(orders):
    f = facts(orders)
    assert f.slug == "orders"
    assert f.summary == "El servicio de pedidos importa archivos del almacén."
    assert f.principles == "- **Idempotente.** Una fila repetida se omite."
    assert f.getting_started == "1. Instale el servicio.\n2. Importe un archivo."
    assert [a.adoption for a in f.areas] == ["-", "-"]
    assert f.open_errors == 0
    assert f.upstreams == ["`../billing`"]
    assert f.consumers == ["`https://example.com/acme/reports.git#reports`"]
    assert "links.md" in f.files and "adoption.md" not in f.files


def test_notes_facts(notes):
    f = facts(notes)
    assert f.summary == "The notes service stores short notes. It has no accounts! Anyone may read them?"
    assert f.first_sentence == "The notes service stores short notes."
    assert (f.principles, f.getting_started) == (None, None)
    assert [a.adoption for a in f.areas] == ["-", "-"]
    assert f.open_errors == 0 and f.upstreams == [] and f.consumers == []


def test_missing_frontmatter_key_is_unknown(notes):
    edit(notes, "prd.md", "owner: Sample Owner\n", "")
    assert facts(notes).owner == "unknown"


def _status(path, block, status):
    text = path.read_text()
    head, rest = text.split(f"### {block} ", 1)
    path.write_text(head + f"### {block} " + rest.replace("Status: live (since 1.0.0)", f"Status: {status}", 1))


def test_counts_leave_out_removed_and_user_journeys(greet):
    _status(greet / "features/api.md", "UJ-01", "built")
    _status(greet / "features/api.md", "FR-002", "approved")
    _status(greet / "features/api.md", "FR-003", "removed")
    _status(greet / "features/import.md", "FR-001", "as-built")
    areas = {a.name: a.counts for a in facts(greet).areas}
    assert areas == {"api": {"approved": 1}, "import": {"as-built": 1}}


def test_counts_in_the_order_live_verified_built_approved_as_built(greet):
    imp = greet / "features/import.md"
    for n, status in enumerate(["as-built", "approved", "built", "verified", "live in staging", "live (since 1.0.0)"], 7):
        imp.write_text(imp.read_text() + f"\n### FR-0{n:02d} Extra {n}\nStatus: {status}\n\n- AC-0{n:02d}.1 x\n")
    counts = {a.name: a.counts for a in facts(greet).areas}["import"]
    assert list(counts.items()) == [("live", 3), ("verified", 1), ("built", 1), ("approved", 1), ("as-built", 1)]


def test_section2_part_label_ends_at_next_label(greet):
    prd = model.load(greet)
    assert overview.section2_part(prd, "principles") == "- **Plain.** One call, one answer.\n- **Counted.** Every greeting is stored."
    assert overview.section2_part(prd, "getting_started").endswith("`GET /hello/<name>`.")


def test_section2_part_keeps_text_on_the_label_line(greet):
    edit(greet, "prd.md", "Principles:\n\n- **Plain.**", "Principles: Keep it small.\n\n- **Plain.**")
    assert overview.section2_part(model.load(greet), "principles").startswith("Keep it small.\n")


def test_section2_part_only_at_line_start(greet):
    edit(greet, "prd.md", "Personas: a visitor.", "Personas: a visitor. Getting started: no.")
    assert overview.section2_part(model.load(greet), "getting_started").startswith("1. Install")


def test_section2_part_ignores_fences_and_comments(notes):
    edit(notes, "prd.md", "Goals:\n", "<!-- Principles:\n- hidden -->\n\n```\nGetting started:\n1. no\n```\n\nGoals:\n")
    prd = model.load(notes)
    assert overview.section2_part(prd, "principles") is None
    assert overview.section2_part(prd, "getting_started") is None


def test_section2_part_es_labels(orders):
    prd = model.load(orders)
    assert overview.section2_part(prd, "principles").startswith("- **Idempotente.**")
    assert overview.section2_part(prd, "getting_started").startswith("1. Instale")


def test_section2_part_ends_at_the_section(greet):
    prd = model.load(greet)
    assert "Glossary" not in overview.section2_part(prd, "getting_started")


def test_section2_part_unknown_key(greet):
    with pytest.raises(ValueError):
        overview.section2_part(model.load(greet), "goals")


def test_opening_with_goals_has_no_summary(notes):
    edit(notes, "prd.md", "The notes service stores short notes. It has no accounts! Anyone may read them?\n\n", "")
    assert overview.summary_paragraph(model.load(notes)) is None
    assert facts(notes).summary is None and facts(notes).first_sentence == ""


@pytest.mark.parametrize("label", ["Principles:", "Getting started:", "Personas: x", "Out of scope: y"])
def test_labelled_first_paragraph_is_no_summary(notes, label):
    edit(notes, "prd.md", "The notes service stores short notes. It has no accounts! Anyone may read them?", label)
    assert overview.summary_paragraph(model.load(notes)) is None


def test_template_comment_before_summary_is_skipped(notes):
    assert notes.joinpath("prd.md").read_text().count("Optional parts") == 1  # the fixture opens on the comment
    assert overview.summary_paragraph(model.load(notes)).startswith("The notes service")


def test_multiline_comment_skipped(notes):
    edit(notes, "prd.md", "<!-- Optional", "<!-- first\nsecond\n-->\n<!-- Optional")
    assert overview.summary_paragraph(model.load(notes)).startswith("The notes service")


def test_list_paragraph_keeps_its_markers(notes):
    edit(notes, "prd.md", "The notes service stores short notes. It has no accounts! Anyone may read them?", "- one\n- two")
    assert overview.summary_paragraph(model.load(notes)) == "- one\n- two"


def test_paragraph_ends_at_heading(notes):
    edit(notes, "prd.md", "Anyone may read them?\n", "Anyone may read them?\n### Detail\nmore\n")
    assert overview.summary_paragraph(model.load(notes)).endswith("read them?")


def test_empty_section2(notes):
    text = notes.joinpath("prd.md").read_text()
    head, rest = text.split("## 2. Summary & goals\n", 1)
    notes.joinpath("prd.md").write_text(head + "## 2. Summary & goals\n\n## 3. Glossary" + rest.split("## 3. Glossary", 1)[1])
    assert overview.summary_paragraph(model.load(notes)) is None


@pytest.mark.parametrize("text,want", [
    ("One. Two.", "One."), ("Really? Yes.", "Really?"), ("Stop! Go.", "Stop!"), ("No stop", "No stop"),
    ("Ends here.", "Ends here."), ("a\nb. c", "a b."), ("v1.2 is out. ok", "v1.2 is out."), ("", ""),
])
def test_first_sentence(text, want):
    assert overview.first_sentence(text) == want


def test_language_keys_in_both_tables():
    keys = ("overview", "what_it_is", "principles", "areas", "open_errors", "linked_prds", "getting_started",
            "snapshot_line", "part_principles", "part_getting_started")
    for code in ("en", "es"):
        labels = yaml.safe_load((LANG_DIR / f"{code}.yaml").read_text())["labels"]
        assert all(labels.get(k) for k in keys), code
    en, es = (yaml.safe_load((LANG_DIR / f"{c}.yaml").read_text())["labels"] for c in ("en", "es"))
    assert (en["part_principles"], en["part_getting_started"]) == ("Principles", "Getting started")
    assert (es["part_principles"], es["part_getting_started"]) == ("Principios", "Primeros pasos")
    assert "{version}" in en["snapshot_line"] and "{version}" in es["snapshot_line"]


def test_template_comment_names_both_parts_and_lints_clean(tmp_path):
    dst = tmp_path / "docs/prd/sample"
    shutil.copytree(TEMPLATE, dst)
    for p in dst.rglob("*"):
        if p.is_file() and p.name != ".gitkeep":
            p.write_text(p.read_text().replace("{{project}}", "sample").replace("{{owner}}", "Sample Owner")
                         .replace("{{date}}", "2026-10-29").replace("{{sql_dialect}}", "postgres"))
    sec2 = (dst / "prd.md").read_text().split("## 2. Summary & goals")[1].split("## 3.")[0]
    assert "<!--" in sec2 and "Principles:" in sec2 and "Getting started:" in sec2
    assert [str(f) for f in lint(dst)] == []
    prd = model.load(dst)
    assert overview.section2_part(prd, "principles") is None  # the comment is not a part
    assert overview.summary_paragraph(prd).startswith("[NEEDS CLARIFICATION")
