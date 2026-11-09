"""The toolkit's own adoption map (0.8.4 fix 8): every script of the plugin is named in exactly one area's Boundary."""
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parent
ADOPTION = REPO / "docs/prd/prd-toolkit/adoption.md"


def boundary_rows(text: str) -> dict[str, set[str]]:
    """Area -> the backticked paths of its Boundary cell, for each data row of the map's table."""
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else []
        if len(cells) < 3 or cells[0] == "Area" or set(cells[0]) <= set("-: "):
            continue
        rows[cells[0]] = set(re.findall(r"`([^`]+)`", cells[2]))
    return rows


def scripts() -> list[str]:
    return sorted(p.relative_to(REPO).as_posix() for p in (PLUGIN / "scripts").rglob("*.py") if "__pycache__" not in p.parts)


def unmapped(rows: dict[str, set[str]], names: list[str]) -> dict[str, list[str]]:
    """Each name not in exactly one row, with the rows that name it."""
    found = {n: sorted(area for area, paths in rows.items() if n in paths) for n in names}
    return {n: areas for n, areas in found.items() if len(areas) != 1}


def test_every_script_is_named_in_exactly_one_row():
    rows = boundary_rows(ADOPTION.read_text(encoding="utf-8"))
    names = scripts()
    assert len(names) > 40 and len(rows) > 10  # the walk and the parse found the real files
    assert unmapped(rows, names) == {}


def test_the_check_reports_a_script_in_no_row_or_in_two():
    rows = boundary_rows(ADOPTION.read_text(encoding="utf-8"))
    extra = "prd-toolkit/scripts/prdlint/nowhere.py"
    assert unmapped(rows, [*scripts(), extra]) == {extra: []}
    rows["twice"] = {"prd-toolkit/scripts/prd_lint.py"}
    assert unmapped(rows, scripts()) == {"prd-toolkit/scripts/prd_lint.py": ["lint-cli", "twice"]}
