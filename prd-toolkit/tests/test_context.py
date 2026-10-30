"""prd_context.py: the decide pack and the repo pack."""
import json
import re

import pytest

from conftest import edit
from context_fixture import pack, parts


def test_area_pack_holds_the_area_and_what_it_cites(ctx):
    code, out, _ = pack(ctx, "--area", "import")
    assert code == 0
    for s in ("### FR-001 Import an orders file", "IMPORT_DUPLICATE:", "IMPORT_EMPTY:", "### E-002", "| importer |", "Q-01", "Q-02", "## Stack"):
        assert s in out


def test_focus_area_pack_leaves_out_everything_else(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    for s in ("FR-002", "FR-003", "UJ-01", "### NFR-004", "ORDER_NOT_FOUND:", "### E-003", "### E-004", "### E-001", "| invoice |", "Q-03", "Q-04", "Q-05", "1.2.0"):
        assert s not in out
    assert "expect:" not in out   # no test-cases text; every case in the fixture has `expect:`
    assert "1 open errors.md entries name no requirement" in out
    assert "3 other open questions in prd.md §13" in out


def test_history_is_the_last_three_area_rows(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    hist = parts(out)["History"]
    assert [v for v in ("1.0.0", "1.1.0", "1.3.0", "1.4.0", "1.5.0") if v in hist] == ["1.3.0", "1.4.0", "1.5.0"]


def test_req_pulls_traced_uj_and_its_assumption(ctx):
    _, out, _ = pack(ctx, "--area", "api", "--req", "fr-002")
    assert "### FR-002" in out and "### UJ-01" in out and "| A-01 |" in out and "### NFR-004" in out
    assert "### FR-003" not in out and "### E-003" in out and "Q-03" in out


def test_cross_area_id_is_labelled(ctx):
    _, out, _ = pack(ctx, "--area", "api", "--req", "FR-002,FR-001")
    assert "(area: import)" in out


def test_slug_prefix_does_not_match(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    assert "Q-05" not in out


def test_repo_pack_lists_areas(ctx):
    code, out, _ = pack(ctx)
    assert code == 0 and "## Areas" in out and "import" in out and "adopted" in out and "src/api/**" in out
    assert "## Requirements" not in out


def test_repo_pack_without_adoption_file_lists_feature_slugs(prd):
    _, out, _ = pack(prd)
    assert "api" in parts(out)["Areas"] and "import" in parts(out)["Areas"]


@pytest.mark.parametrize("args", [["--area", "billing"], ["--area", "import", "--req", "FR-099"], ["--req", "FR-001"], ["--for", "implement"]])
def test_exit_2_prints_nothing(ctx, args):
    code, out, err = pack(ctx, *args)
    assert code == 2 and out == "" and err


def test_size_line_matches_the_bytes(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    m = re.search(r"pack ([\d,]+) bytes .*prd\.md ([\d,]+); features/import\.md ([\d,]+)", out)
    body = out.split("\n## Stack", 1)[1]
    assert int(m[1].replace(",", "")) == len(("## Stack" + body).encode())
    assert int(m[2].replace(",", "")) == (ctx / "prd.md").stat().st_size


def test_json_matches_text_and_runs_are_identical(ctx):
    _, text, _ = pack(ctx, "--area", "api")
    _, js, _ = pack(ctx, "--area", "api", "--json")
    items = json.loads(js)
    assert {i["part"] for i in items} == set(parts(text)) and all(set(i) == {"part", "id", "file", "line", "text", "stale"} for i in items)
    assert pack(ctx, "--area", "api")[1] == text


def test_decide_parts_come_in_spec_order(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    assert list(parts(out)) == ["Header", "Stack", "Glossary", "Requirements", "Cited", "Known defects", "Open questions", "History"]


def test_header_names_the_area_state_and_boundary(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    head = parts(out)["Header"]
    assert "version 1.5.0 mode decide" in head and "Area: import (adopted; Boundary: src/import/**)" in head


def test_custom_contract_item_is_cited(ctx):
    edit(ctx, "prd.md", "| lookml | `contracts/custom/*.lkml` |", "| looks | `contracts/custom/looks.yaml` | `python3 -c \"import sys; sys.exit(0)\"` |\n| lookml | `contracts/custom/*.lkml` |")
    (ctx / "contracts/custom/looks.yaml").write_text("daily_orders:\n  model: orders\nweekly_orders:\n  model: orders\n")
    edit(ctx, "features/import.md", "Edge cases: the same key twice", "Edge cases: feeds looks:daily_orders; the same key twice")
    _, out, _ = pack(ctx, "--area", "import")
    cited = parts(out)["Cited"]
    assert "daily_orders:\n  model: orders" in cited and "weekly_orders" not in cited


def test_area_without_features_file_has_no_requirements(ctx):
    (ctx / "adoption.md").write_text((ctx / "adoption.md").read_text() + "| billing | not started | `src/billing/**` |\n")
    code, out, _ = pack(ctx, "--area", "billing")
    assert code == 0 and "### FR-" not in parts(out)["Requirements"] and "Area: billing (not started; Boundary: src/billing/**)" in out
