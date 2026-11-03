"""Failing cases for the pack, language and judged-case rules (0.8.0); each task that adds a rule appends here."""
import pytest
from conftest import Case, edit, fired
from doc_fixture import document_prd
from packs_fixture import plugins_file, write_pack

from prdlint import model, packs, registry


def lint(root, warnings=True):
    """Every rule, warnings included (platform-word is a warn)."""
    return registry.run(model.load(root), warnings=warnings)

CASES = [
    Case("language-table", "unknown language", lambda root: edit(root, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: fr")),
    Case("pack-resolves", "malformed Pack line", lambda root: edit(root, "prd.md", "- Not used: message brokers, ORMs, front-end frameworks",
                                                                   "- Not used: message brokers, ORMs, front-end frameworks\n- Pack: document 1.0")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.rule}:{c.name}")
def test_rule_fires(prd, case):
    case.mutate(prd)
    assert case.rule in fired(lint(prd))


# --- judged-case ---------------------------------------------------------------------------------------------------

def _judged(tmp_path, old=None, new=None):
    root = document_prd(tmp_path)
    if old is not None:
        edit(root, "test-cases/install.yaml", old, new)
    return [f for f in lint(root) if f.rule in ("judged-case", "sufficiency")]


RUBRIC = "rubric:\n      - Each step in Install names one action the reader performs\n      - No step relies on a tool that Requirements does not list\n"


def test_judged_case_passes_without_output(tmp_path):
    assert _judged(tmp_path) == []


@pytest.mark.parametrize("new", ["rubric: []\n", 'rubric: "x"\n', 'rubric: ["", "a"]\n', "rubric: [1]\n"])
def test_rubric_shape(tmp_path, new):
    got = _judged(tmp_path, RUBRIC, new)
    assert [f.message for f in got] == ["T-001.2: rubric must be a non-empty list of non-empty strings"]


@pytest.mark.parametrize("new", ["", "    threshold: 0\n", "    threshold: 1.5\n", '    threshold: "0.8"\n', "    threshold: true\n"])
def test_threshold(tmp_path, new):
    got = _judged(tmp_path, "    threshold: 0.67\n", new)
    assert [f.message for f in got] == ["T-001.2: threshold must be a number in (0, 1]"]


@pytest.mark.parametrize("v", ["0", "2.5", "true", '"3"'])
def test_runs(tmp_path, v):
    got = _judged(tmp_path, "    threshold: 0.67\n", f"    threshold: 1\n    runs: {v}\n")
    assert [f.message for f in got] == ["T-001.2: runs must be an integer of at least 1"]


def test_runs_and_threshold_bounds_pass(tmp_path):
    assert _judged(tmp_path, "    threshold: 0.67\n", "    threshold: 1\n    runs: 1\n") == []


def test_judged_case_has_no_output(tmp_path):
    got = _judged(tmp_path, "    threshold: 0.67\n", "    threshold: 0.67\n    output: {x: y}\n")
    assert [f.message for f in got] == ["T-001.2: a judged case has no expect.output"]


def test_missing_rubric_is_not_judged(tmp_path):
    got = _judged(tmp_path, "    " + RUBRIC, "")
    assert [f.rule for f in got] == ["sufficiency"] and "output" in got[0].message


def _make_judged(root):
    edit(root, "test-cases/api.yaml", "    output:\n      status: 200\n      body: {id: 1, order_key: K-1000, customer_id: 1, status: open}",
         "    rubric: x")


CASES.append(Case("judged-case", "rubric not a list", _make_judged))


# --- platform-word -------------------------------------------------------------------------------------------------

S1_ANCHOR = "- Not used: message brokers, ORMs, front-end frameworks"


def _demo(tmp_path, monkeypatch, vocabulary=("explore", "data tile")):
    install = tmp_path / "plug/demo"
    write_pack(install / "prd-packs", "demo", "1.0.0", description="Demo pack.", vocabulary=list(vocabulary))
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@test": install})))
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")


def _words(root):
    return [f for f in lint(root) if f.rule == "platform-word"]


def _named(prd, tmp_path, monkeypatch, **kw):
    _demo(tmp_path, monkeypatch, **kw)
    edit(prd, "prd.md", S1_ANCHOR, S1_ANCHOR + "\n- Pack: demo 1.0.0 (demo@test)")


def _first_ac(prd):
    for f in sorted((prd / "features").glob("*.md")):
        for n, line in enumerate(f.read_text().split("\n"), 1):
            if line.startswith("- AC-") and "(removed" not in line:
                return f, n, line
    raise AssertionError


def _set_first_ac(prd, text):
    f, n, line = _first_ac(prd)
    ac = line.split(" ", 2)[1]
    lines = f.read_text().split("\n")
    lines[n - 1] = f"- {ac} {text}"
    f.write_text("\n".join(lines))
    return f.relative_to(prd).as_posix(), n, ac


def test_platform_word_warns_and_exits_0(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    before = [f for f in lint(prd, warnings=False)]
    rel, n, ac = _set_first_ac(prd, "When asked, the system shall show an Explore to the user.")
    got = _words(prd)
    assert [str(f) for f in got] == [
        f"{rel}:{n}: warn: platform-word: {ac} names 'explore', a word of pack demo: "
        "move it to a contract, a Harness slot or the area's Target"]
    assert lint(prd, warnings=False) == before  # the warning never blocks


def test_platform_word_whole_words_only(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    _set_first_ac(prd, "When asked, the system shall show a data tile; the tiled explorer is not one.")
    assert [f.message.split("'")[1] for f in _words(prd)] == ["data tile"]
    _set_first_ac(prd, "When asked, the system shall show a tiled explorer.")
    assert _words(prd) == []


def test_platform_word_once_per_ac_and_word(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    _set_first_ac(prd, "When asked, the system shall explore, then Explore again.")
    assert len(_words(prd)) == 1


def test_platform_word_skips_removed_ac(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    _set_first_ac(prd, "(removed in 0.2.0) When asked, the system shall explore.")
    assert _words(prd) == []


def test_platform_word_checks_titles_and_nfr(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    f = next(p for p in sorted((prd / "features").glob("*.md")) if "### FR-" in p.read_text())
    text = f.read_text()
    i = text.index("### FR-")
    j = text.index("\n", i)
    f.write_text(text[:j] + " explore" + text[j:])
    got = _words(prd)
    assert len(got) == 1 and got[0].line == text[:j].count("\n") + 1 and "names 'explore'" in got[0].message
    nfr = (prd / "nfr.md")
    t = nfr.read_text()
    k = t.index("### NFR-")
    e = t.index("\n", k)
    nfr.write_text(t[:e] + " data tile" + t[e:])
    assert {f.file for f in _words(prd)} == {f.relative_to(prd).as_posix(), "nfr.md"}


def test_platform_word_not_for_an_area_targeting_another_pack(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    f, n, _ = _first_ac(prd)
    area = f.stem
    title = next(l for l in f.read_text().split("\n") if l.startswith("# "))
    edit(prd, f.relative_to(prd).as_posix(), title + "\n", f"{title}\n\nTarget: pack document 1.0.0 (prd-toolkit)\n")
    _set_first_ac(prd, "When asked, the system shall explore.")
    assert _words(prd) == []


def test_platform_word_silent_without_a_pack(prd):
    _set_first_ac(prd, "When asked, the system shall explore.")
    assert _words(prd) == []


def test_platform_word_silent_when_pack_fails(prd, tmp_path, monkeypatch):
    _demo(tmp_path, monkeypatch)
    edit(prd, "prd.md", S1_ANCHOR, S1_ANCHOR + "\n- Pack: demo 9.9.9 (demo@test)")
    _set_first_ac(prd, "When asked, the system shall explore.")
    assert _words(prd) == []


def test_each_named_pack_resolves_once_per_lint(prd, tmp_path, monkeypatch):
    _named(prd, tmp_path, monkeypatch)
    _set_first_ac(prd, "When asked, the system shall explore.")
    real, calls = packs.resolve, []
    monkeypatch.setattr(packs, "resolve", lambda ref, *a, **k: calls.append(ref.name) or real(ref, *a, **k))
    lint(prd)
    assert calls.count("demo") == 1 and calls.count("service") <= 1



def _platform_word(root):
    write_pack(root / ".prd-toolkit/packs", "demo", "1.0.0", toolkit=">=0.7", description="Demo pack.", vocabulary=["explore", "data tile"])
    edit(root, "prd.md", S1_ANCHOR, S1_ANCHOR + "\n- Pack: demo 1.0.0 (demo@test)")
    _set_first_ac(root, "When asked, the system shall explore.")


CASES.append(Case("platform-word", "vocabulary word in an AC", _platform_word))
