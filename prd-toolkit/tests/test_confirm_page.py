"""The confirmation form page: one self-contained file that loads nothing and inserts item text only as text."""
import json
import re
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path

import pytest
from confirm_fixture import make_confirm_repo
from prdlint import confirm, model

PAGE_FILE = Path(__file__).parent.parent / "templates/confirm/form.html"
HOSTILE = "<script>alert(1)</script>"


def page() -> str:
    return PAGE_FILE.read_text(encoding="utf-8")


def scripts() -> str:
    js = "\n".join(re.findall(r"<script>(.*?)</script>", page(), re.S))
    assert js.strip(), "the page has no inline script"
    return js


BANNED_JS = (r"outerHTML", r"insertAdjacentHTML", r"document\.write", r"\beval\s*\(", r"\bFunction\s*\(",
             r"setTimeout\s*\(\s*['\"`]", r"\.setAttribute\s*\(\s*['\"]on", r"srcdoc")


def unsafe_html(js: str) -> list[str]:
    """Every innerHTML use that is not a literal empty string, and every other HTML or code sink."""
    bad = [js[m.start():m.end() + 40] for m in re.finditer(r"innerHTML", js)
           if not re.match(r"innerHTML\s*=\s*(''|\"\")\s*[;\n]", js[m.start():])]
    return bad + [b for b in BANNED_JS if re.search(b, js)]


def test_loads_nothing():
    text = page()
    for banned in (r"<script\s+[^>]*src", r"<link\b", r"@import", r"url\s*\(", r"<img\b", r"<iframe\b", r"https?://"):
        assert not re.search(banned, text, re.I), banned


def test_one_inline_script_and_style():
    text = page()
    assert text.lower().startswith("<!doctype html>")
    assert len(re.findall(r"<script>", text)) == 1 and len(re.findall(r"<style>", text)) == 1
    assert len(text.splitlines()) <= 900


def test_unsafe_html_check_can_fail():
    assert unsafe_html("el.innerHTML = '';\nx.innerHTML = \"\";") == []
    for bad in ("el.innerHTML = item.title;", "el.innerHTML += '<b>';", "el.innerHTML = '' + t;",
                "el.innerHTML = `${t}`;", "x = el.innerHTML;", "el.insertAdjacentHTML('beforeend', t);",
                "eval(t);", "new Function(t)", "b.setAttribute('onclick', t)"):
        assert unsafe_html(bad), bad


def test_inner_html_only_with_literals():
    assert unsafe_html(scripts()) == []


def test_no_inline_handlers_in_markup():
    markup = re.sub(r"<script>.*?</script>", "", page(), flags=re.S)
    assert not re.search(r"\son[a-z]+\s*=", markup, re.I)


def test_names_every_request_and_decision():
    js = scripts()
    for path in ("/items", "/answer", "/undo", "/done"):
        assert f"'{path}'" in js, path
    assert "X-Prd-Token" in js and "URLSearchParams" in js
    for kind, decisions in confirm.ALLOWED.items():
        assert f"{kind}:" in js, kind
        for d in decisions:
            assert f"'{d}'" in js, d


def test_labels_and_states():
    text = page()
    for label in ("Confirm", "Correct…", "It's a bug…", "Someone else decides…", "Real bug — it should…",
                  "Intended — keep it", "Yes, intended", "No, fix it", "In my own words", "Answer",
                  "Show the code", "edit the criteria", "What should it do instead?", "Who decides?",
                  "Requirements", "Bugs", "Questions", "Settings", " of ", "Change", "Undo", "Done",
                  "changed since you answered", "you can close this tab", "resumes where you left off"):
        assert label in text, label
    for state in ("✓", "✎", "🐞", "⟳"):
        assert state in text, state


def test_keys_and_text_guard():
    js = scripts()
    for key in ("'c'", "'r'", "'b'", "'s'", "'ArrowLeft'", "'ArrowRight'"):
        assert key in js, key
    assert "TEXTAREA" in js and "INPUT" in js
    assert "textContent" in js


def test_calm_theme():
    text = page()
    assert "prefers-color-scheme: dark" in text and "--bg" in text and ":focus-visible" in text
    assert "system-ui" in text and "@media (max-width" in text
    assert "overflow-wrap" in text and "max-height" in text  # long words and a 200-line excerpt


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_script_parses(tmp_path):
    src = tmp_path / "form.js"
    src.write_text(scripts(), encoding="utf-8")
    out = subprocess.run(["node", "--check", str(src)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr


def test_served_page_is_the_file_and_items_are_json_text(tmp_path):
    repo, prd_dir = make_confirm_repo(tmp_path)
    features = prd_dir / "features/notes.md"
    text = features.read_text(encoding="utf-8")
    old = "- AC-001.2 The id shall grow by one for each note."
    assert text.count(old) == 1
    features.write_text(text.replace(old, f"- AC-001.2 The id shall grow {HOSTILE} by one."), encoding="utf-8")
    prd = model.load(prd_dir)
    items = confirm.build_items(prd, "notes")
    raw_page = page()
    server, token = confirm.make_server(prd, "notes", items, {}, raw_page)
    thread = threading.Thread(target=lambda: confirm.run(server))
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(f"{base}/?token={token}", timeout=10) as r:
            body = r.read()
            assert r.headers["Content-Type"].startswith("text/html")
        assert body == PAGE_FILE.read_bytes()
        assert b"alert(1)" not in body
        req = urllib.request.Request(base + "/items", headers={"X-Prd-Token": token})
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.headers["Content-Type"].startswith("application/json")
            listing = json.loads(r.read())
        fr1 = next(i for i in listing["items"] if i["id"] == "FR-001")
        assert ["AC-001.2", f"The id shall grow {HOSTILE} by one."] in fr1["acs"]
    finally:
        server.shutdown()
        thread.join(10)
        server.server_close()
