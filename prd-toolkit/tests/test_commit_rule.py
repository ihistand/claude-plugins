"""The commit rule: Boundary for a new project, and what a `Refs:` trailer may cite."""
import pytest
from conftest import edit
from prdlint import model, trace


@pytest.fixture
def loaded(prd):
    edit(prd, "features/api.md", "### FR-003 Delete an order\nStatus: live (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed (since 1.1.0)")
    edit(prd, "prd.md", "| FR-003 | Delete an order | live |", "| FR-003 | Delete an order | removed |")
    return model.load(prd)


@pytest.mark.parametrize("msg", ["x\n\nRefs: FR-001", "x\n\nRefs: FR-001,FR-002", "x\n\nRefs: FR-001 , E-001",
                                 "x\n\nRefs: FR-001\nRefs: NFR-004", "x\n\nRefs: none (no behaviour change)",
                                 "x\n\nTicket: ABC-12\nRefs: FR-001"])
def test_accepted(loaded, msg):
    assert trace.refs_problems(loaded, msg) == []


@pytest.mark.parametrize("msg,needle", [
    ("x", "no `Refs:` trailer"), ("x\n\nrefs: FR-001", "no `Refs:` trailer"),
    ("x\n\nRefs: FR-099", "FR-099 is not defined in the PRD"), ("x\n\nRefs: FR-003", "FR-003 is removed"),
    ("x\n\nRefs: E-099", "E-099 is not defined in the PRD"),
    ("x\n\nRefs: ABC-12", "`ABC-12` is not a PRD ID; give other keys their own trailer"),
    ("x\n\nRefs: none", "`none` alone is not accepted; write `Refs: none (no behaviour change)`"),
    ("x\n\nRefs: FR-001\nRefs: FR-099", "FR-099 is not defined in the PRD")])
def test_rejected(loaded, msg, needle):
    assert any(needle in p for p in trace.refs_problems(loaded, msg))


def test_new_project_boundary_is_everything_but_the_prd(loaded, tmp_path):
    inside = trace.in_boundary(loaded, tmp_path)
    assert inside("src/app.py") and inside("README.md")
    assert not inside("docs/prd/orders/prd.md") and not inside(".prd-toolkit/prd_lint.py")
