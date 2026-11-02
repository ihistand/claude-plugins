"""The `Change-set:` trailer in the trace (`commit-refs`) and the commit-msg hook (prd-toolkit 0.7, Task 7)."""
import pytest
from legacy import commit, git
from prdlint import githook, model, trace

FORM = "`Change-set: {}` must be orders/CS-nnn"
NO_RECORD = "Change-set: orders/CS-002 has no record in changes/"


@pytest.fixture
def repo(prd):
    root = prd.parent.parent.parent
    git(root, "init", "-q")
    (prd / "changes").mkdir()
    (prd / "changes/CS-001.md").write_text("# CS-001 Orders daily\n", encoding="utf-8")
    return root


def load(repo):
    return model.load(repo / "docs/prd/orders")


def msg(*trailers):
    return "Add x\n\nRefs: none (no behaviour change)\n" + "".join(f"{t}\n" for t in trailers)


def hook(repo, *trailers, staged=("src/app.py",), merging=False):
    return githook.commit_msg(load(repo), repo, msg(*trailers), list(staged), merging)


def test_good_trailer_passes_hook(repo):
    assert hook(repo, "Change-set: orders/CS-001") == []


def test_other_prd_passes_hook(repo):
    assert hook(repo, "Change-set: transform/CS-002") == []


def test_no_prefix_fails_hook(repo):
    assert FORM.format("CS-001") in hook(repo, "Change-set: CS-001")


def test_short_number_fails_hook(repo):
    assert FORM.format("Orders/CS-1") in hook(repo, "Change-set: Orders/CS-1")


def test_empty_value_fails_hook(repo):
    assert FORM.format("") in hook(repo, "Change-set:")


def test_missing_record_fails_hook(repo):
    assert NO_RECORD in hook(repo, "Change-set: orders/CS-002")


def test_outside_boundary_bad_trailer_still_fails_hook(repo):
    assert FORM.format("CS-001") in hook(repo, "Change-set: CS-001", staged=("docs/prd/orders/prd.md",))
    assert hook(repo, "Change-set: CS-001", staged=("docs/prd/orders/prd.md",), merging=True) == []


def test_changeset_problems_unit(repo):
    p = load(repo)
    assert trace.changeset_problems(p, "x\n") == []
    assert trace.changeset_problems(p, "x\n\nChange-set: orders/CS-001\nChange-set: orders/CS-002\n") == [NO_RECORD]


def trace_msgs(repo, *trailers):
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src/app.py").write_text("x = 1\n")
    commit(repo, msg(*trailers), "src/app.py", "docs")
    return [f.message for f in trace.run_trace(load(repo), repo, "HEAD") if f.rule == "commit-refs"]


def test_trace_good_trailer_passes(repo):
    assert trace_msgs(repo, "Change-set: orders/CS-001") == []


def test_trace_bad_trailer_fails(repo):
    out = trace_msgs(repo, "Change-set: CS-001")
    assert len(out) == 1 and FORM.format("CS-001") in out[0] and "commit " in out[0]


def test_trace_missing_record_and_other_prd(repo):
    out = trace_msgs(repo, "Change-set: orders/CS-002", "Change-set: transform/CS-002")
    assert len(out) == 1 and NO_RECORD in out[0]


def test_trace_outside_boundary_commit_checked(repo):
    out = trace_msgs(repo, "Change-set: CS-001")  # also touches docs; now a docs-only commit
    (repo / "docs/prd/orders/notes.txt").write_text("n\n")
    commit(repo, msg("Change-set: Orders/CS-1"), "docs/prd/orders/notes.txt")
    found = [f.message for f in trace.run_trace(load(repo), repo, "HEAD~1..HEAD") if f.rule == "commit-refs"]
    assert any(FORM.format("Orders/CS-1") in m for m in found)
