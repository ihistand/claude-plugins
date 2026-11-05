"""The decision inbox page: one self-contained file that loads nothing and inserts gate text only as text."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from prdlint import formserver
from test_confirm_page import BANNED_JS, unsafe_html

TEMPLATES = Path(__file__).parent.parent / "templates"
PAGE_FILE = TEMPLATES / "gates/inbox.html"
BUTTON_KEYS = ("approve", "changes", "confirm", "correct", "send", "pass", "fail")
RENDERERS = ("renderApproval", "renderErrorClass", "renderDeployStep", "renderSignoff", "renderAdoption")


def page() -> str:
    return formserver.assemble(PAGE_FILE, include_dir=TEMPLATES / "confirm")


def scripts() -> str:
    js = "\n".join(re.findall(r"<script>(.*?)</script>", page(), re.S))
    assert js.strip(), "the page has no inline script"
    return js


def function(name: str) -> str:
    """The source of one top-level function of the page's scripts, up to the closing brace at column 0."""
    m = re.search(rf"^(?:async )?function {name}\(.*?^}}$", scripts(), re.S | re.M)
    assert m, name
    return m.group(0)


def test_panel_is_included():
    raw = PAGE_FILE.read_text(encoding="utf-8")
    assert "<!-- include: panel.html -->" in raw.splitlines()
    assert "<!-- include:" not in page()
    for name in ("cardView", "listView", "finish", "decideView"):  # the panel's own functions
        assert f"function {name}(" in page(), name


def test_loads_nothing():
    text = page()
    for banned in (r"<script\s+[^>]*src", r"<link\b", r"@import", r"url\s*\(", r"<img\b", r"<iframe\b", r"https?://"):
        assert not re.search(banned, text, re.I), banned


def test_inline_script_and_style_only():
    text = page()
    assert text.lower().startswith("<!doctype html>")
    # the panel's own script and style, and the inbox's: the include brings the first of each
    assert len(re.findall(r"<script>", text)) == 2 and len(re.findall(r"<style>", text)) == 2
    assert not re.search(r"\son[a-z]+\s*=", re.sub(r"<script>.*?</script>", "", text, flags=re.S), re.I)


def test_no_unsafe_html():
    assert unsafe_html(scripts()) == []
    assert unsafe_html("el.innerHTML = g.question;") and "outerHTML" in BANNED_JS  # the check can fail


def test_each_kind_has_its_renderer_and_the_page_refreshes_every_5_seconds():
    for name in RENDERERS:
        assert function(name)
    assert function("refresh")
    assert re.search(r"setInterval\(\s*refresh\s*,\s*5000\s*\)", scripts())


def test_every_button_key_is_named():
    js = scripts()
    for key in BUTTON_KEYS:
        assert f"'{key}'" in js, key
    for label in ("Approve", "Request changes…", "Confirm the class", "Correct it to…", "Send reply", "Pass", "Fail…"):
        assert label in page(), label
    for cls in ("code bug", "spec gap", "invalid requirement", "environment", "standard"):
        assert f"'{cls}'" in js, cls


def test_a_deploy_step_is_typed_never_clicked_through():
    body = function("renderDeployStep")
    assert "answerBox(" in body and "'send'" in body and "needs: true" in body
    assert "h('textarea'" in function("answerBox")  # the box every kind shares holds the text box
    assert "'approve'" not in body and "'pass'" not in body and "'confirm'" not in body


def test_words_required_buttons_say_why_before_any_request():
    body = function("answerBox")
    assert "needs" in body and body.index("needs") < body.index("send(")  # the check runs first
    assert "needs your words" in scripts()


def test_every_answer_carries_the_question_the_page_showed():
    body = function("send")
    assert "question: g.question" in body and "worktree: wt.path" in body and "'/answer'" in scripts()
    assert "409" in body  # a changed gate is marked, not answered


def test_the_adoption_card_hosts_the_panel_and_sends_its_question():
    assert "PANEL_HOST" in scripts() and "/adoption/" in scripts() and "wt=" in scripts()
    assert "HOST.question" in function("finish")  # Done carries the gate's question
    assert "location.hash" in scripts() and "#gate=" in page()


def test_answered_and_changed_states():
    js = scripts()
    for text in ("changed", "answered", "no longer pending", "Open", "inbox has stopped"):
        assert text in js, text


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_script_parses(tmp_path):
    src = tmp_path / "inbox.js"
    src.write_text(scripts(), encoding="utf-8")
    out = subprocess.run(["node", "--check", str(src)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr


HARNESS = r"""
class N { constructor(t) { this.tag = t; this.kids = []; this.attrs = {}; this.dataset = {}; this.textContent = ''; }
  append(...k) { for (const x of k) this.kids.push(typeof x === 'string' ? { tag: '#t', text: x, kids: [] } : x); }
  setAttribute(k, v) { this.attrs[k] = v; } addEventListener() {}
  get text() { return this.textContent + this.kids.map((k) => (k.tag === '#t' ? k.text : k.text)).join(''); } }
global.window = { addEventListener() {}, PANEL_HOST: {} };
global.document = { addEventListener() {}, createElement: (t) => new N(t), createTextNode: (s) => ({ tag: '#t', text: s, kids: [] }), body: new N('body') };
global.location = { search: '?token=x', hash: '' };
const walk = (n, out) => { if (n.tag === 'button') out.push(n.text); (n.kids || []).forEach((k) => walk(k, out)); return out; };
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_each_button_reads_its_label_once(tmp_path):
    js = (HARNESS + scripts().replace("'use strict';", "") + r"""
const spec = { prompt: 'p', buttons: [{ key: 'approve', label: 'Approve' }, { key: 'changes', label: 'Request changes…', needs: true }] };
console.log(JSON.stringify(walk(answerBox({ key: 'k', g: { id: 'x' }, wt: { path: '/w' } }, spec), [])));
""")
    src = tmp_path / "labels.js"
    src.write_text(js, encoding="utf-8")
    out = subprocess.run(["node", str(src)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == '["Approve","Request changes…"]'
