"""The confirmation form's items: what an area asks its owner, in order, with summaries and fingerprints."""
import hashlib
import json

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, model

from legacy import commit, git


def build(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    return repo, prd, confirm.build_items(model.load(prd), "notes")


def by_id(items):
    return {i.id: i for i in items}


def test_items_in_order(tmp_path):
    _, _, items = build(tmp_path)
    assert [(i.id, i.kind) for i in items] == [("FR-001", "requirement"), ("FR-002", "requirement"),
                                               ("E-001", "bug"), ("Q-01", "question"),
                                               ("config.yaml:NOTES_LIMIT.owner", "marker")]


def test_requirement_item_carries_acs_and_excerpt(tmp_path):
    _, _, items = build(tmp_path)
    fr1, fr2 = by_id(items)["FR-001"], by_id(items)["FR-002"]
    assert fr1.title == "Add a note"
    assert fr1.acs == [("AC-001.1", "When a note is added, the service shall store it and return its id."),
                       ("AC-001.2", "The id shall grow by one for each note.")]
    assert fr1.where == "src/notes/app.py:13"
    ex = fr1.excerpts[0].split("\n")
    assert ex[0] == "   3 | _NOTES: dict[int, str] = {}"
    assert "  12 | def add_note(text):" in ex
    assert ex[-1].startswith("  23 | ")
    assert len(fr2.excerpts) == 2  # one per Source line


def test_other_kinds_where_and_excerpts(tmp_path):
    _, _, items = build(tmp_path)
    got = by_id(items)
    assert got["E-001"].where == "errors.md" and got["E-001"].title == "Search is case-sensitive"
    assert "  17 | def search(term):" in got["E-001"].excerpts[0]
    assert got["Q-01"].where == "prd.md §13" and "FR-001" in got["Q-01"].text
    m = got["config.yaml:NOTES_LIMIT.owner"]
    assert m.where == "contracts/config.yaml NOTES_LIMIT.owner" and "who owns the limit" in m.text


def test_missing_commit_or_file(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    f = prd / "features/notes.md"
    text = f.read_text()
    sha = text.split("app.py:13 @")[1].split()[0]
    f.write_text(text.replace(f"app.py:13 @{sha}\nAcceptance", "app.py:13 @deadbee\nAcceptance", 1)
                 .replace("src/notes/app.py:17 @" + sha, "src/gone.py:17 @" + sha))
    items = by_id(confirm.build_items(model.load(prd), "notes"))
    assert items["FR-001"].excerpts == ["(code not available at deadbee)"]
    assert items["FR-002"].excerpts[0] == f"(code not available at {sha})"
    assert "FR-001" in items


def test_not_as_built_and_resolved_are_not_items(tmp_path):
    _, _, items = build(tmp_path)
    ids = {i.id for i in items}
    assert "FR-003" not in ids and "E-002" not in ids


def test_unknown_or_empty_area(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    with pytest.raises(confirm.Refused) as e:
        confirm.build_items(model.load(prd), "x")
    assert str(e.value) == "area x is not in adoption.md"
    (prd / "adoption.md").write_text((prd / "adoption.md").read_text() + "| empty | extracted | `src/e/**` |\n")
    with pytest.raises(confirm.Refused) as e:
        confirm.build_items(model.load(prd), "empty")
    assert str(e.value) == "area empty has no item to confirm"


def test_fingerprint_changes_with_text(tmp_path):
    repo, prd, items = build(tmp_path)
    before = by_id(items)
    f = prd / "features/notes.md"
    f.write_text(f.read_text().replace("grow by one", "grow by two"))
    after = by_id(confirm.build_items(model.load(prd), "notes"))
    assert after["FR-001"].fingerprint != before["FR-001"].fingerprint
    assert all(after[i].fingerprint == before[i].fingerprint for i in before if i != "FR-001")
    assert before["FR-001"].fingerprint == hashlib.sha256(before["FR-001"].text.encode("utf-8")).hexdigest()


def test_summaries_rules(tmp_path):
    _, _, items = build(tmp_path)
    p = tmp_path / "s.json"

    def load(obj):
        p.write_text(json.dumps(obj))
        return confirm.load_summaries(p, items, "notes")

    good = {"FR-001": "FR-001 stores a note.", "E-001": "E-001 is a case bug."}
    assert load(good) == good
    for obj, msg in (({"FR-009": "FR-009 x"}, "summary for FR-009 names no item of notes"),
                     ({"FR-001": "stores a note"}, "summary for FR-001 does not mention FR-001"),
                     ({"FR-001": "FR-001 " + "x" * 400}, "summary for FR-001 is over 400 characters")):
        with pytest.raises(confirm.Refused) as e:
            load(obj)
        assert str(e.value) == msg
