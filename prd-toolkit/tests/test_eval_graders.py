"""Eval graders that depend on the template: the marks-unknowns lookahead must list every template marker."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "templates/prd/prd.md"
GRADER = ROOT / "evals/authoring-new-prd/graders/marks-unknowns.md"
OWNER_FILL = "who owns this product"  # authoring-prds fills {{owner}} with this marker


def pattern() -> re.Pattern:
    m = re.search(r"^pattern: '(.*)'$", GRADER.read_text(encoding="utf-8"), re.M)
    assert m, "no single-quoted pattern in the grader"
    return re.compile(m.group(1))


def template_copy() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    for slot, value in {"{{project}}": "link-shortener", "{{owner}}": f"[NEEDS CLARIFICATION: {OWNER_FILL}]",
                        "{{date}}": "2026-10-30", "{{sql_dialect}}": "postgres"}.items():
        text = text.replace(slot, value)
    return text


def test_lookahead_lists_every_template_marker():
    texts = set(re.findall(r"NEEDS CLARIFICATION: ([^\]]*)\]", TEMPLATE.read_text(encoding="utf-8"))) | {OWNER_FILL}
    body = re.search(r"\(\?!\(\?:(.*)\)\\\]\)", pattern().pattern).group(1)
    listed = {re.sub(r"\\(.)", r"\1", alt) for alt in re.split(r"(?<!\\)\|", body)}  # an escaped \| is text
    assert listed == texts


def test_template_copy_and_invented_edits_do_not_pass():
    copy = template_copy()
    edited = copy.replace("[NEEDS CLARIFICATION: database and version]", "PostgreSQL 16")
    edited = edited.replace("[NEEDS CLARIFICATION: framework and version]", "FastAPI 0.115")
    for text in (copy, edited):  # a read-only grep leaves the copy as it was: the first case
        assert not pattern().search(text)


def test_real_unknowns_pass():
    copy = template_copy()
    assert pattern().search(copy.replace("[NEEDS CLARIFICATION: database and version]",
                                         "[NEEDS CLARIFICATION: which Postgres version runs in production]"))
    assert pattern().search(copy.replace("|---|---|---|\n\n## 13", "|---|---|---|\n| A-01 | Links never expire | open |\n\n## 13"))
    assert pattern().search("- AC-001.1 ... [ASSUMPTION A-02: a code is 7 characters]")


def test_the_adoption_map_marker_names_the_exact_table():
    text = TEMPLATE.read_text(encoding="utf-8")
    marker = text.split("## 8. Adoption map\n", 1)[1].split("\n## ", 1)[0]
    assert "or the `| Area | State | Boundary |` table]" in marker and "Area/State" not in marker


GLOB_GRADER = ROOT / "evals/tester-stays-out-of-src/graders/dry-run-no-test-root-glob.md"


def _glob_counts(tool_input: dict) -> bool:
    import json

    m = re.search(r"^input_match: '(.*)'$", GLOB_GRADER.read_text(encoding="utf-8"), re.M)
    assert m, "no single-quoted input_match"
    return bool(re.search(m.group(1), json.dumps(tool_input, separators=(",", ":"))))


def test_the_dry_run_glob_grader_counts_test_root_listings_only():
    counted = [{"pattern": "**/*.py", "path": "tests"}, {"pattern": "*", "path": "/repo/tests/"},
               {"pattern": "tests/**/*.py"}, {"pattern": "**/*"}, {"pattern": "*.py", "path": "tests/unit"},
               {"path": "tests", "pattern": ".prd-dry-run-x/../test_notes.py"}]
    exempt = [{"path": "tests", "pattern": ".prd-dry-run-*"}, {"pattern": ".prd-dry-run-*", "path": "tests"},
              {"pattern": "tests/.prd-dry-run-*/**"}, {"pattern": "**/*", "path": "tests/.prd-dry-run-20261030T120000"},
              {"pattern": "**/prd-tester*"}, {"pattern": "**/*.md", "path": "docs/prd/notes"}]
    for ti in counted:
        assert _glob_counts(ti), ti
    for ti in exempt:
        assert not _glob_counts(ti), ti
