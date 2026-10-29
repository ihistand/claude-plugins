"""The contract examples in references/contract-types.md must satisfy contracts-valid."""
import re
from pathlib import Path

from conftest import lint

REF = Path(__file__).parent.parent / "references"
FENCE = re.compile(r"^```[a-z]*\n(.*?)^```", re.S | re.M)
FILE_LINE = re.compile(r"^(?:#|--|<!--) file: (contracts/\S+?)(?: -->)?$")


def examples() -> list[tuple[str, str]]:
    out = []
    for block in FENCE.findall((REF / "contract-types.md").read_text()):
        m = FILE_LINE.match(block.split("\n", 1)[0])
        if m:
            out.append((m.group(1), block))
    return out


def test_every_contract_type_has_an_example():
    names = {name for name, _ in examples()}
    assert {"contracts/openapi.yaml", "contracts/schema.sql", "contracts/events.md", "contracts/errors.yaml",
            "contracts/permissions.yaml", "contracts/config.yaml", "contracts/data-classification.yaml",
            "contracts/dependencies/geocoder.yaml"} <= names


def test_contract_examples_are_valid(prd):
    for name, text in examples():
        (prd / name).write_text(text)
        bad = [str(f) for f in lint(prd) if f.rule == "contracts-valid"]
        assert not bad, f"{name}: {bad}"


def test_template_pointers_resolve():
    headings = {m.group(1) for m in re.finditer(r"^## (.+)$", (REF / "contract-types.md").read_text(), re.M)}
    for path in (REF.parent / "templates/prd").rglob("*"):
        if path.is_file():
            for m in re.finditer(r'contract-types\.md, "([^"]+)"', path.read_text()):
                assert m.group(1) in headings, f"{path}: no section {m.group(1)}"


def test_examples_can_fail(prd):
    """Prove the check is not vacuous: break an example and the rule fires."""
    name, text = next(e for e in examples() if e[0] == "contracts/errors.yaml")
    (prd / name).write_text(text.replace("  metric: orders_not_found_total\n", ""))
    assert any(f.rule == "contracts-valid" for f in lint(prd))
