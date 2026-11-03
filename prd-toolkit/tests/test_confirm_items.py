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


# ---- fix round 1 ----

def rewrite(prd, rel, old, new):
    f = prd / rel
    text = f.read_text()
    assert old in text, old
    f.write_text(text.replace(old, new, 1))


def ids(prd):
    return [i.id for i in confirm.build_items(model.load(prd), "notes")]


def test_question_ids_are_their_own(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "prd.md", "- Q-01 Should FR-001 keep empty notes?\n- Q-02 Is the retention period settled for FR-099?\n  It was never decided.",
            "- Q-01 Should FR-001 keep empty notes?\n- Q-02 Is X settled for FR-099?\n- Q-03 May FR-002 match case?\n- Does FR-001 need a limit?")
    got = [i for i in ids(prd) if i.startswith("Q-")]
    assert got == ["Q-01", "Q-03", "Q-04"]  # the unnumbered bullet is the 4th among all bullets


def test_indented_dash_continues_the_bullet(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "prd.md", "  It was never decided.", "  - a sub point")
    rewrite(prd, "prd.md", "- Q-01 Should", "- Q-01 Should FR-001\n  - first sub point\n- Q-05 Should")
    items = by_id(confirm.build_items(model.load(prd), "notes"))
    assert "Q-02" not in items and "first sub point" in items["Q-01"].text


def test_marker_named_only_by_own_area_test_cases(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: none")
    (prd / "test-cases").mkdir()
    (prd / "test-cases/other.yaml").write_text("T-009.1:\n  target: config:NOTES_LIMIT\n")
    assert "config.yaml:NOTES_LIMIT.owner" not in ids(prd)
    (prd / "test-cases/notes.yaml").write_text("T-001.1:\n  target: config:NOTES_LIMIT\n")
    assert "config.yaml:NOTES_LIMIT.owner" in ids(prd)


def test_dotted_traces_names_the_key(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: `settings.NOTES_LIMIT`")
    assert "config.yaml:NOTES_LIMIT.owner" in ids(prd)


def test_same_named_keys_get_distinct_ids(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: `owner`")
    (prd / "contracts/config.yaml").write_text(
        'settings:\n  A:\n    owner: "[NEEDS CLARIFICATION: a]"\n  B:\n    owner: "[NEEDS CLARIFICATION: b]"\n')
    got = [i for i in ids(prd) if i.endswith("owner")]
    assert got == ["config.yaml:A.owner", "config.yaml:B.owner"]


def test_two_markers_in_one_string(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    (prd / "contracts/config.yaml").write_text(
        'settings:\n  NOTES_LIMIT:\n    owner: "[NEEDS CLARIFICATION: a] and [NEEDS CLARIFICATION: b]"\n')
    got = [i for i in ids(prd) if i.startswith("config")]
    assert got == ["config.yaml:NOTES_LIMIT.owner", "config.yaml:NOTES_LIMIT.owner#2"]


def test_subfolder_contract_ids_carry_the_path(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    (prd / "contracts/sub").mkdir()
    (prd / "contracts/sub/config.yaml").write_text('NOTES_LIMIT:\n  owner: "[NEEDS CLARIFICATION: x]"\n')
    assert "sub/config.yaml:NOTES_LIMIT.owner" in ids(prd)


def test_detected_time_is_not_a_citation(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "errors.md", "wrong result at src/notes/app.py:17", "seen at 12:30 on host:8080")
    assert by_id(confirm.build_items(model.load(prd), "notes"))["E-001"].excerpts == []


def test_one_git_show_per_file_and_commit(tmp_path, monkeypatch):
    _, prd = make_confirm_repo(tmp_path)
    calls = []
    real = confirm.subprocess.run
    monkeypatch.setattr(confirm.subprocess, "run", lambda cmd, **kw: (calls.append(cmd), real(cmd, **kw))[1])
    confirm.build_items(model.load(prd), "notes")
    shows = [c for c in calls if c[:2] == ["git", "show"]]
    assert len(shows) == len(set(map(tuple, shows))) and shows


def test_summaries_stricter(tmp_path):
    _, _, items = build(tmp_path)
    p = tmp_path / "s2.json"

    def load(raw):
        p.write_text(raw)
        return confirm.load_summaries(p, items, "notes")

    for raw in ("{not json", '["FR-001"]'):
        with pytest.raises(confirm.Refused):
            load(raw)
    with pytest.raises(confirm.Refused) as e:
        load('{"FR-001": 5}')
    assert str(e.value) == "summary for FR-001 must be text"
    with pytest.raises(confirm.Refused) as e:
        load(json.dumps({"FR-001": "FR-0010 is it"}))
    assert str(e.value) == "summary for FR-001 does not mention FR-001"
    ok = "FR-001 " + "x" * 393
    assert len(ok) == 400 and load(json.dumps({"FR-001": ok}))
    with pytest.raises(confirm.Refused):
        load(json.dumps({"FR-001": ok + "x"}))


# ---- final-review fix ----

def test_duplicate_item_id_is_refused(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "prd.md", "- Q-01 Should FR-001 keep empty notes?\n- Q-02 Is the retention period settled for FR-099?\n  It was never decided.",
            "- Q-01 Should FR-001 keep empty notes?\n- Should FR-002 trim terms?\n- Q-02 Does FR-002 page?")
    with pytest.raises(confirm.Refused) as e:
        confirm.build_items(model.load(prd), "notes")
    assert str(e.value) == "item ID Q-02 appears twice in prd.md §13"


def test_requirement_lists_the_open_entries_that_touch_it(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "errors.md", "### E-002 Empty id", "### E-003 Ids skip\nDetected: 2026-10-30, review\nTouches: FR-002, FR-001\n"
            "Diagnosis: x\nResolution: open\n\n### E-002 Empty id")
    got = by_id(confirm.build_items(model.load(prd), "notes"))
    assert got["FR-001"].related == ["E-003"]  # E-002 touches FR-001 but is resolved
    assert got["FR-002"].related == ["E-001", "E-003"]
    assert all(got[i].related == [] for i in got if got[i].kind != "requirement")


def test_a_prose_word_on_traces_names_nothing(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    (prd / "contracts/config.yaml").write_text(
        (prd / "contracts/config.yaml").read_text() + '  store:\n    owner: "[NEEDS CLARIFICATION: prose]"\n')
    got = ids(prd)
    assert "config.yaml:NOTES_LIMIT.owner" in got  # the backticked span still names its key
    assert not [i for i in got if "store" in i]


def test_bare_dotted_traces_names_its_identifier(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: settings.NOTES_LIMIT")
    assert "config.yaml:NOTES_LIMIT.owner" in ids(prd)


def test_unbackticked_identifier_on_traces_names_the_key(tmp_path):
    # 0.7.1 proof F-1: FR-008's Traces named its setting without backticks, and the marker was never served
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store",
            "Traces: cli:notes; setting NOTES_LIMIT (contracts/config.yaml)")
    (prd / "contracts/config.yaml").write_text(
        (prd / "contracts/config.yaml").read_text() + '  OTHER_LIMIT:\n    owner: "[NEEDS CLARIFICATION: unnamed]"\n')
    got = ids(prd)
    assert "config.yaml:NOTES_LIMIT.owner" in got
    assert not [i for i in got if "OTHER" in i]  # an identifier-shaped key the line does not name is not served


def test_unbackticked_camel_case_and_kind_name_name_their_keys(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: maxSize; cli:notes_cli")
    (prd / "contracts/config.yaml").write_text(
        'settings:\n  maxSize:\n    owner: "[NEEDS CLARIFICATION: a]"\n'
        '  notes_cli:\n    owner: "[NEEDS CLARIFICATION: b]"\n')
    got = ids(prd)
    assert "config.yaml:maxSize.owner" in got and "config.yaml:notes_cli.owner" in got


def test_ids_caps_words_digits_and_paths_on_traces_name_nothing(tmp_path):
    # review of 0.7.2: requirement IDs, all-caps prose, versions and path parts are not key names
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store",
            "Traces: FR-001; AC-008.2; UJ-02 UNIQUE; POST /orders; src/utils_2/x.py; api v2; fixture orders/one_existing")
    keys = ["FR", "AC", "UJ", "UNIQUE", "POST", "utils_2", "v2", "one_existing", "orders"]
    (prd / "contracts/config.yaml").write_text(
        "settings:\n" + "".join(f'  {k}:\n    owner: "[NEEDS CLARIFICATION: {k}]"\n' for k in keys))
    assert [i for i in ids(prd) if i.startswith("config.yaml:")] == []


def test_plain_prose_words_on_traces_name_nothing(tmp_path):
    _, prd = make_confirm_repo(tmp_path)
    rewrite(prd, "features/notes.md", "Traces: `NOTES_LIMIT` caps the store", "Traces: Store setting, see Contracts")
    (prd / "contracts/config.yaml").write_text(
        'settings:\n  Store:\n    owner: "[NEEDS CLARIFICATION: a]"\n  setting:\n    owner: "[NEEDS CLARIFICATION: b]"\n'
        '  Contracts:\n    owner: "[NEEDS CLARIFICATION: c]"\n')
    assert [i for i in ids(prd) if i.startswith("config.yaml:")] == []


def test_extensionless_detected_file_is_cited(tmp_path):
    repo, prd = make_confirm_repo(tmp_path)
    (repo / "Makefile").write_text("".join(f"rule{n}:\n" for n in range(1, 20)))
    commit(repo, "Add a Makefile", "Makefile")
    rewrite(prd, "errors.md", "wrong result at src/notes/app.py:17", "wrong result at Makefile:10")
    ex = by_id(confirm.build_items(model.load(prd), "notes"))["E-001"].excerpts
    assert len(ex) == 1 and "  10 | rule10:" in ex[0]
    rewrite(prd, "errors.md", "wrong result at Makefile:10", "wrong result at Nofile:10")
    assert by_id(confirm.build_items(model.load(prd), "notes"))["E-001"].excerpts == []
