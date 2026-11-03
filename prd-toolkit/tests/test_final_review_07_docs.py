"""prd-toolkit 0.7 final review, the documentation items 9, 10 and 12."""
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_changing_prds_says_add_writes_the_upstreams_consumers_row():
    text = _flat(ROOT / "skills/changing-prds/SKILL.md")
    assert ("`prd_links.py add` writes the upstream's `links.md` Consumers row, uncommitted, in the upstream "
            "repository") in text
    assert "its own `/prd-change` there (a patch bump)" in text
    assert "until it lands, `check` reports `missing row`" in text


def test_root_readme_lists_the_change_set_command_and_skill():
    text = (ROOT.parent / "README.md").read_text(encoding="utf-8")
    assert "`/prd-change-set`" in text
    assert "**coordinating-prds skill**" in text


def test_baseline_row_points_at_the_rerun():
    text = (ROOT / "evals/baselines/coordinating-prds.md").read_text(encoding="utf-8")
    row = next(x for x in text.splitlines() if x.startswith("| `change-set-no-push`"))
    assert "rerun" in row and "1.00/0.00 over two runs" in row, row
