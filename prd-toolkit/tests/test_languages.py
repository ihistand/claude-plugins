"""PRD languages: the en and es tables, `language:` frontmatter and the language-table rule."""
import shutil
from pathlib import Path

import pytest
from conftest import edit

from prdlint import languages, model, registry

AC1 = "When an imported row has a new order_key, the importer shall insert the row\n  into `orders`."


def _run(prd, rule):
    return [f for f in registry.run(model.load(prd), only={rule})]


def _set(prd, language=None, ac=None):
    if language:
        edit(prd, "prd.md", "sql-dialect: postgres", f"sql-dialect: postgres\nlanguage: {language}")
    if ac:
        edit(prd, "features/import.md", AC1, ac)


def test_en_ears_message_unchanged(prd):
    _set(prd, ac="Rows get inserted.")
    msgs = [f.message for f in _run(prd, "ac-ears")]
    assert msgs == ["AC-001.1 must start with When, While, If, Where or 'The <thing> shall'"]


@pytest.mark.parametrize("ac", [
    "Cuando el archivo está vacío, el importador deberá omitir la fila.",
    "El importador deberá omitir la fila.",
])
def test_es_ears_accepts(prd, ac):
    _set(prd, "es", ac)
    assert [f for f in _run(prd, "ac-ears") if "AC-001.1" in f.message] == []


def test_es_ears_rejects_english_opener(prd):
    _set(prd, "es")  # AC-001.1 keeps its English text
    msgs = [f.message for f in _run(prd, "ac-ears")]
    assert "AC-001.1 must start with Cuando, Mientras, Si, Donde or 'El/La/Los/Las <cosa> deberá'" in msgs


@pytest.mark.parametrize("ac,hit", [
    ("Rápido al importar la fila.", True),
    ("Cuando falla, el importador deberá ser fácil de usar.", True),
    ("Cuando falla, el importador deberá responder rápido en 200 ms.", False),
])
def test_es_vague(prd, ac, hit):
    _set(prd, "es", ac)
    assert any("AC-001" in f.message or f.line == 8 for f in _run(prd, "vague-word")) is hit


def test_unknown_language_reported_and_ears_runs_with_en(prd):
    _set(prd, "fr")
    found = _run(prd, "language-table")
    assert [(f.file, f.message) for f in found] == [("prd.md", "language 'fr' has no table")]
    assert found[0].line == 8
    assert _run(prd, "ac-ears") == []  # en table applied to the English ACs


def test_uppercase_language_is_a_frontmatter_finding(prd):
    _set(prd, "ES")
    msgs = [f.message for f in _run(prd, "frontmatter")]
    assert any("language" in m and "^[a-z]{2,3}$" in m for m in msgs)
    assert _run(prd, "language-table") == []


def test_absent_language_is_en(prd):
    p = model.load(prd)
    assert languages.code(p) == "en"
    assert languages.for_prd(p).code == "en"


def test_tables_match_the_spec():
    en = languages.load("en")
    assert en.openers == ["When", "While", "If", "Where"]
    assert en.ubiquitous.pattern == r"^The \S.*? shall\b"
    assert en.vague.pattern == r"\b(fast|secure|scalable|robust|intuitive|seamless|user-friendly)\b"
    assert languages.load("xx") is None


def test_vendored_layout_uses_scripts_languages(tmp_path, monkeypatch):
    scripts = tmp_path / ".prd-toolkit"
    (scripts / "languages").mkdir(parents=True)
    shutil.copy(languages.TABLES_DIR / "en.yaml", scripts / "languages/en.yaml")
    (scripts / "languages/zz.yaml").write_text("language: zz\nears:\n  openers: [Za]\n  ubiquitous: '^Zz'\nvague: [zed]\nlabels: {}\n")
    monkeypatch.setattr(languages, "SCRIPTS", scripts)
    monkeypatch.setattr(languages, "PLUGIN_ROOT", scripts.parent)
    assert not languages.is_plugin()
    assert languages.toolkit_dir() == scripts / "languages"
    assert languages.load("zz").openers == ["Za"]
