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


# Each HTML or code sink the page must not use, with a snippet that proves the pattern can fail.
BANNED_JS = {
    r"outerHTML": "el.outerHTML = t;",
    r"insertAdjacentHTML": "el.insertAdjacentHTML('beforeend', t);",
    r"createContextualFragment": "range.createContextualFragment(t);",
    r"\bDOMParser\b": "new DOMParser().parseFromString(t, 'text/html');",
    r"document\.write": "document.writeln(t);",
    r"\beval\s*\(": "eval(t);",
    r"\bFunction\s*\(": "new Function(t)",
    r"setTimeout\s*\(\s*['\"`]": "setTimeout('go()', 1);",
    r"\.setAttribute\s*\(\s*['\"](?:on|href|src|srcdoc|action)": "b.setAttribute('onclick', t)",
    r"\.(?:href|src|action)\s*=(?!=)(?!\s*(?:''|\"\")\s*;)": "a.href = item.where;",
    r"\.srcdoc\s*=": "frame.srcdoc = t;",
}


def unsafe_html(js: str) -> list[str]:
    """Every innerHTML use that is not a literal empty string, and every other HTML or code sink."""
    bad = [js[m.start():m.end() + 40] for m in re.finditer(r"innerHTML", js)
           if not re.match(r"innerHTML\s*=\s*(''|\"\")\s*[;\n]", js[m.start():])]
    return bad + [b for b in BANNED_JS if re.search(b, js)]


def function(name: str) -> str:
    """The source of one top-level function of the page's script, up to the closing brace at column 0."""
    m = re.search(rf"^(?:async )?function {name}\(.*?^}}$", scripts(), re.S | re.M)
    assert m, name
    return m.group(0)


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
    assert unsafe_html("el.innerHTML = '';\nx.innerHTML = \"\";\nif (a.href === b) x = 1;") == []
    for bad in ("el.innerHTML = item.title;", "el.innerHTML += '<b>';", "el.innerHTML = '' + t;",
                "el.innerHTML = `${t}`;", "x = el.innerHTML;"):
        assert unsafe_html(bad), bad
    for pattern, bad in BANNED_JS.items():
        assert pattern in unsafe_html(bad), pattern
    assert r"\.(?:href|src|action)\s*=(?!=)(?!\s*(?:''|\"\")\s*;)" in unsafe_html("img.src = data.url;")


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


def test_notice_cleared_on_every_move():
    for name in ("go", "undo", "change"):
        assert "S.notice = '';" in function(name), name
    assert "S.notice" not in function("save").replace("S.notice = '';", "")


def test_everything_answered_said_once():
    assert page().count("Everything is answered") == 1


def test_typing_clears_the_card_error():
    assert "clearError()" in function("textarea")
    body = function("clearError")
    assert "error = ''" in body and "card-error" in body
    assert "id: 'card-error'" in function("cardView")


def test_long_ids_wrap():
    css = re.search(r"<style>(.*?)</style>", page(), re.S).group(1)
    for selector in (".acid", ".said", "label.prompt", ".criteria label"):
        rule = re.search(rf"(?:^|\}})\s*{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
        assert rule, selector
        assert "overflow-wrap: anywhere" in rule.group(1) and "nowrap" not in rule.group(1), selector


def test_no_stale_aria_expanded():
    assert "aria-expanded" not in page()


DONE_RUN = r"""
const vm = require('node:vm');
const js = require('node:fs').readFileSync(process.argv[2], 'utf8');
class El {
  constructor() { this.style = {}; this.classList = { toggle() {} }; this.children = []; this.hidden = false; }
  setAttribute() {} addEventListener() {} append(...k) { this.children.push(...k); }
  replaceChildren(...k) { this.children = k; } focus() {} scrollIntoView() {} remove() {}
  querySelector() { return null; } set textContent(v) { this.text = v; }
}
const fixed = { shell: new El(), list: new El(), card: new El(), end: new El() };
const item = { id: 'FR-001', kind: 'requirement', title: 't', text: 't', acs: [], excerpts: [], where: 'w', summary: null };
const listing = { area: 'notes', items: [item], answers: { 'FR-001': { decision: 'confirm' } }, open: [], changed: [] };
const ctx = {
  console, URLSearchParams, location: { search: '?token=abc' }, window: { matchMedia: () => ({ matches: false }) },
  document: { title: '', createElement: () => new El(), createTextNode: (t) => ({ t }),
              getElementById: (id) => fixed[id] || null, addEventListener() {} },
  fetch: async (path) => {
    if (path === '/items') return { status: 200, json: async () => listing };
    throw new TypeError('Failed to fetch');
  },
};
vm.createContext(ctx);
vm.runInContext(js + '\n;globalThis.__S = S; globalThis.__finish = finish;', ctx);
setTimeout(async () => {
  const before = ctx.__S.ended;
  await ctx.__finish();
  console.log(JSON.stringify({ before, after: ctx.__S.ended }));
}, 50);
"""


def test_no_closing_flag():
    assert "closing" not in scripts()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_done_without_a_reply_shows_stopped(tmp_path):
    src, js = tmp_path / "run.js", tmp_path / "form.js"
    src.write_text(DONE_RUN, encoding="utf-8")
    js.write_text(scripts(), encoding="utf-8")
    run = subprocess.run(["node", str(src), str(js)], capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == {"before": None, "after": "stopped"}


def test_escape_leaves_the_note_box():
    js = scripts()
    esc = js[js.index("e.key === 'Escape'"):]
    esc = esc[:esc.index("return;")]
    assert "t.id !== 'note'" not in esc and "t.blur()" in esc


def test_builder_refuses_url_and_code_props():
    assert "/^(?:on|href|src|srcdoc|action|formaction)/i.test(k)" in function("h")


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_builder_refusals_run(tmp_path):
    src = tmp_path / "h.js"
    src.write_text(
        "const document = { createElement: (t) => ({ tagName: t, attrs: {}, kids: [], "
        "setAttribute(k, v) { this.attrs[k] = v; }, addEventListener() {}, append(k) { this.kids.push(k); } }), "
        "createTextNode: (t) => ({ text: t }) };\n" + function("h") + "\n"
        "const out = {};\n"
        "for (const k of ['href', 'src', 'srcdoc', 'action', 'onclick', 'ONLOAD', 'formaction']) {\n"
        "  try { h('a', { [k]: 'x' }); out[k] = 'allowed'; } catch (e) { out[k] = 'refused'; }\n"
        "}\n"
        "out.title = h('a', { title: '<b>' }).attrs.title;\n"
        "console.log(JSON.stringify(out));\n", encoding="utf-8")
    run = subprocess.run(["node", str(src)], capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout) == {"href": "refused", "src": "refused", "srcdoc": "refused", "action": "refused",
                                      "onclick": "refused", "ONLOAD": "refused", "formaction": "refused",
                                      "title": "<b>"}
