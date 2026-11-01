"""The Levels table's Gate column (build | deploy) and model.gate_of."""
from conftest import edit, lint
from prdlint import model


def drop_gate_column(prd):
    """Rewrite the Levels table of testing.md without its fourth column."""
    path = prd / "testing.md"
    out = []
    for ln in path.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("|") and ln.count("|") == 5:
            ln = ln[: ln.rstrip().rstrip("|").rfind("|")] + "|"
        out.append(ln)
    path.write_text("\n".join(out), encoding="utf-8")


def test_fixture_gates(prd):
    p = model.load(prd)
    assert p.testing.has_gate and model.gate_of(p, "unit") == "build" and model.gate_of(p, "e2e") == "deploy"


def test_missing_gate_column_names_the_migration(prd):
    drop_gate_column(prd)
    assert not model.load(prd).testing.has_gate
    f = [x for x in lint(prd) if x.rule == "test-level" and x.file == "testing.md"]
    assert [x.message for x in f] == [model.GATE_MIGRATION]


def test_bad_gate_value(prd):
    edit(prd, "testing.md", "| `pytest tests/unit` | local | build |", "| `pytest tests/unit` | local | merge |")
    assert any(x.rule == "test-level" and "Gate 'merge' is not one of build, deploy" in x.message for x in lint(prd))


def test_gate_of_unknown_level_is_none(prd):
    assert model.gate_of(model.load(prd), "nightly") is None
