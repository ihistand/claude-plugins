"""The interface envelope (interface 1) on prd_trace.py, prd_status.py and prd_context.py."""
import contextlib
import io
import json

import pytest
from conftest import FIXTURE, PLUGINS_FILE
from context_fixture import pack
from legacy import make_legacy_repo
from prd_context import main as context_main
from prd_status import main as status_main
from prd_trace import main as trace_main
from prdlint import interface

MAINS = {"trace": trace_main, "status": status_main, "context": context_main}


def call(main, *argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def prd(tmp_path, monkeypatch):
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    import shutil
    shutil.copytree(FIXTURE, tmp_path / "docs/prd/orders")
    return tmp_path / "docs/prd/orders"


def test_envelope_helpers():
    assert interface.INTERFACE == 1
    assert interface.dump("x", {"a": "é"}) == '{"interface": 1, "kind": "x", "a": "é"}\n'
    assert json.loads(interface.error("x", "m")) == {"interface": 1, "kind": "x", "error": "m"}
    assert interface.check_version(None) is None and interface.check_version("1") is None
    assert interface.check_version("2") == "unsupported interface 2; this toolkit speaks 1"
    assert interface.wants_json(["a", "--json"]) and interface.wants_json(["--json=2"]) and not interface.wants_json(["a"])


@pytest.mark.parametrize("kind", MAINS)
def test_interface_flag_prints_1_without_a_folder(kind):
    assert call(MAINS[kind], "--interface") == (0, "1\n", "")


@pytest.mark.parametrize("kind", MAINS)
def test_json_document_starts_with_interface_and_kind(kind, prd):
    code, out, _ = call(MAINS[kind], str(prd), "--json")
    assert code in (0, 1) and out.count("\n") >= 1
    doc = json.loads(out)
    assert list(doc)[:2] == ["interface", "kind"] and doc["interface"] == 1 and doc["kind"] == kind
    assert json.loads(call(MAINS[kind], str(prd), "--json=1")[1]) == doc


@pytest.mark.parametrize("kind", MAINS)
def test_json_takes_the_folder_in_either_order(kind, prd):
    a = call(MAINS[kind], "--json", str(prd))
    b = call(MAINS[kind], str(prd), "--json")
    assert a[0] == b[0] and a[0] in (0, 1) and json.loads(a[1]) == json.loads(b[1])
    assert json.loads(call(MAINS[kind], "--json=1", str(prd))[1]) == json.loads(a[1])
    assert "[--json] [--interface]" in " ".join(call(MAINS[kind], "--help")[1].split())


@pytest.mark.parametrize("kind", MAINS)
def test_unsupported_version_is_an_error_document(kind, prd):
    code, out, err = call(MAINS[kind], str(prd), "--json=2")
    assert code == 2 and err
    assert json.loads(out) == {"interface": 1, "kind": kind, "error": "unsupported interface 2; this toolkit speaks 1"}


@pytest.mark.parametrize("kind", MAINS)
def test_argparse_failure_with_json_is_an_error_document(kind, prd):
    code, out, err = call(MAINS[kind], str(prd), "--json", "--bogus")
    doc = json.loads(out)
    assert code == 2 and err and doc["kind"] == kind and (doc["error"].startswith("unrecognized arguments: --bogus") or "--bogus" in doc["error"])
    assert not doc["error"].startswith(("usage:", "prd_"))


@pytest.mark.parametrize("kind", MAINS)
def test_missing_folder_is_an_error_document_and_text_stays_on_stderr(kind, tmp_path):
    code, out, err = call(MAINS[kind], str(tmp_path / "nope"), "--json")
    doc = json.loads(out)
    assert code == 2 and doc["kind"] == kind and doc["error"] and doc["error"] in err
    assert err.splitlines()[0].endswith(doc["error"])


@pytest.mark.parametrize("kind", MAINS)
def test_no_json_leaves_exit_2_stdout_empty(kind, tmp_path):
    code, out, err = call(MAINS[kind], str(tmp_path / "nope"))
    assert code == 2 and out == "" and err


def test_trace_json_holds_findings_and_counts(tmp_path, monkeypatch):
    from test_trace import build
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    prd = build(tmp_path)
    monkeypatch.chdir(prd.parents[2])
    code, out, _ = call(trace_main, str(prd), "--range", "HEAD", "--json")
    doc = json.loads(out)
    assert code == 1 and doc["kind"] == "trace"
    assert doc["dir"] == "docs/prd/notes" and doc["errors"] == len(doc["findings"]) and doc["warnings"] == 0
    assert doc["prd"] is None and doc["version"] is None   # the legacy fixture has no frontmatter
    f = next(f for f in doc["findings"] if f["rule"] == "commit-refs")
    assert set(f) == {"file", "line", "rule", "severity", "message"} and f["severity"] == "error"
    clean = json.loads(call(trace_main, str(prd), "--json")[1])
    assert clean["errors"] == len(clean["findings"])


def test_trace_document_carries_frontmatter(prd, tmp_path):
    doc = json.loads(call(trace_main, str(prd), "--json")[1])
    assert doc["prd"] == "orders" and doc["version"] and isinstance(doc["findings"], list)


def test_status_document_wraps_the_items(prd):
    doc = json.loads(call(status_main, str(prd), "--json")[1])
    assert doc["prd"] == "orders" and doc["version"] and doc["items"]
    assert {"part", "id", "text"} <= set(doc["items"][0])


def test_context_parts_follow_the_text_pack(ctx):
    _, text, _ = pack(ctx, "--area", "api", "--req", "fr-002")
    code, out, _ = pack(ctx, "--area", "api", "--req", "fr-002", "--json")
    doc = json.loads(out)
    assert code == 0 and doc["mode"] == "decide" and doc["area"] == "api" and doc["ids"] == ["FR-002"]
    titles = []
    for p in doc["parts"]:
        assert {"title", "id", "file", "line", "text", "stale"} <= set(p)
        if p["title"] not in titles:
            titles.append(p["title"])
    assert titles == [h[3:] for h in text.splitlines() if h.startswith("## ")]
    assert json.loads(pack(ctx, "--json")[1])["area"] is None
