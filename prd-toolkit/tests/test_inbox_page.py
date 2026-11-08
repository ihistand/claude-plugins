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


def test_the_host_is_set_before_the_panel_script_reads_it():
    text = page()
    assert text.index("window.PANEL_HOST = {") < text.index("const HOST = window.PANEL_HOST")


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_the_panel_sees_the_host_when_the_scripts_run_in_page_order(tmp_path):
    js = (HARNESS.replace("PANEL_HOST: {}", "") + "\n".join(re.findall(r"<script>(.*?)</script>", page(), re.S)).replace("'use strict';", "")
          + """
const card = gateCard({ key: 'k', g: { id: 'signoff:T-1', kind: 'signoff', title: 't', question: 'q', evidence: [] }, wt: { path: '/w', branch: 'b' } }, new Map());
console.log(HOST !== null && HOST === window.PANEL_HOST, card.tag, typeof card.append);
""")
    src = tmp_path / "order.js"
    src.write_text(js, encoding="utf-8")
    out = subprocess.run(["node", str(src)], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "true section function"  # an element, not a string or the panel's cardView


def test_the_two_scripts_share_no_top_level_name():
    inbox, panel = (re.findall(r"^(?:async )?function (\w+)|^(?:const|let|var|class) (\w+)", js, re.M)
                    for js in re.findall(r"<script>(.*?)</script>", page(), re.S))  # page order: inbox, panel
    names = lambda found: {a or b for a, b in found}  # noqa: E731
    assert names(inbox) and names(panel)
    assert names(inbox) & names(panel) == set()


# --- the page in a small DOM: moving a node out of its parent drops the focus inside it, as a browser does ---

DOM_RUN = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const [pageFile, driverFile, base] = process.argv.slice(2);
const DOM = { active: null, hostMoves: 0, host: null };
const camel = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
class Nd {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.parentNode = null; this.childNodes = []; this.attrs = {}; this.dataset = {};
    this.hidden = false; this.style = {}; this.className = ''; this._text = ''; this.value = ''; this.disabled = false;
    this.classList = { toggle() {} }; this.selectionStart = 0; this.selectionEnd = 0;
  }
  get isConnected() { for (let n = this; n; n = n.parentNode) if (n === html) return true; return false; }
  contains(o) { for (let n = o; n; n = n.parentNode) if (n === this) return true; return false; }
  _take(node) {
    const was = node.isConnected;
    this.childNodes.splice(this.childNodes.indexOf(node), 1);
    node.parentNode = null;
    if (was && DOM.active && node.contains(DOM.active)) DOM.active = body;
    if (was && DOM.host && node.contains(DOM.host)) DOM.hostMoves++;
  }
  _put(node, at) { if (node.parentNode) node.parentNode._take(node); node.parentNode = this; this.childNodes.splice(at, 0, node); }
  append(...ns) { for (const n of ns) this._put(n, this.childNodes.length); }
  replaceChildren(...ns) {
    for (const n of ns) if (n.parentNode) n.parentNode._take(n);
    for (const c of [...this.childNodes]) this._take(c);
    this.append(...ns);
  }
  before(...ns) { const p = this.parentNode; for (const n of ns) { if (n.parentNode) n.parentNode._take(n); p._put(n, p.childNodes.indexOf(this)); } }
  after(...ns) { const p = this.parentNode; let ref = this; for (const n of ns) { if (n.parentNode) n.parentNode._take(n); p._put(n, p.childNodes.indexOf(ref) + 1); ref = n; } }
  remove() { if (this.parentNode) this.parentNode._take(this); }
  setAttribute(k, v) { this.attrs[k] = v; if (k === 'id') this.id = v; if (k.startsWith('data-')) this.dataset[camel(k.slice(5))] = v; }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  addEventListener() {}
  set textContent(v) { for (const c of [...this.childNodes]) this._take(c); this._text = String(v); }
  get textContent() { return this._text + this.childNodes.map((c) => c.textContent).join(''); }
  focus() { if (this.isConnected) DOM.active = this; }
  blur() { if (DOM.active === this) DOM.active = body; }
  setSelectionRange(a, b) { this.selectionStart = a; this.selectionEnd = b; }
  scrollIntoView() {}
  all(test, out = []) { for (const c of this.childNodes) { if (test(c)) out.push(c); c.all(test, out); } return out; }
  querySelectorAll(sel) {
    const tests = { '[data-fk]': (n) => 'fk' in n.dataset, '.gtitle': (n) => n.className.split(' ').includes('gtitle') };
    return tests[sel] ? this.all(tests[sel]) : [];
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
}
const el = (tag, id, ...kids) => { const n = new Nd(tag); if (id) n.setAttribute('id', id); n.append(...kids); return n; };
const host = el('div', 'panel-host', el('div', 'shell', el('aside', 'list'), el('main', 'card')), el('div', 'end'));
host.hidden = true;
const body = el('body', '', el('header', 'inbox-bar', el('span', 'inbox-status')), el('div', 'inbox-root'), el('div', 'inbox-end'), host);
const html = el('html', '', body);
DOM.host = host;
DOM.active = body;
const document = {
  body, documentElement: html, title: '',
  get activeElement() { return DOM.active; },
  createElement: (t) => new Nd(t),
  createTextNode: (s) => { const n = new Nd('#text'); n._text = String(s); return n; },
  getElementById: (id) => (id === 'panel-host' ? host : html.all((n) => n.id === id)[0] || null),
  addEventListener() {},
};
const route = { handler: null };
const ctx = {
  console, URLSearchParams, setTimeout, clearTimeout, setInterval: () => 0, clearInterval() {}, DOM, document,
  location: { search: '?token=tok', hash: '' },
  window: { addEventListener() {}, matchMedia: () => ({ matches: false }) },
  route,
  fetch: async (path, opts) => {
    if (base) {
      const { cache, ...rest } = opts || {};
      return fetch(base + path + (path.includes('?') ? '&' : '?') + 'token=' + process.env.PRD_TOKEN, rest);
    }
    const data = route.handler(path, opts && opts.body ? JSON.parse(opts.body) : undefined);
    return { status: data.status || 200, json: async () => data.body };
  },
};
vm.createContext(ctx);
for (const js of fs.readFileSync(pageFile, 'utf8').split('\n//--- next script ---\n')) vm.runInContext(js, ctx);
vm.runInContext(fs.readFileSync(driverFile, 'utf8'), ctx);
"""


def run_page(tmp_path, driver: str, base: str = "", token: str = ""):
    """Run the page's two scripts, in page order, in DOM_RUN's small DOM, then the driver; return its last stdout line as JSON."""
    import json
    import os

    files = {"run.js": DOM_RUN, "page.js": "\n//--- next script ---\n".join(re.findall(r"<script>(.*?)</script>", page(), re.S)),
             "driver.js": f"(async () => {{\n{driver}\n}})().catch((e) => {{ console.log(JSON.stringify({{ error: String(e.stack) }})); }});"}
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    env = {**os.environ, "PRD_TOKEN": token}
    out = subprocess.run(["node", str(tmp_path / "run.js"), str(tmp_path / "page.js"), str(tmp_path / "driver.js"), base],
                         capture_output=True, text=True, timeout=120, env=env)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert "error" not in got, got["error"]
    return got


OPEN_ADOPTION = r"""
const gatesDoc = (open, extra) => ({ prd: 'orders', answers: [], worktrees: [
  { path: '/w', branch: 'main', gates: [...extra, { id: 'adoption:import', kind: 'adoption', area: 'import', title: 'Confirm import',
    question: `${open} of 1 items in import are open`, evidence: [] }] },
  { path: '/w2', branch: 'feature-x', gates: [] }] });
const listing = { area: 'import', items: [{ id: 'E-003', kind: 'bug', title: 'Importer reads the wrong key', text: 't', acs: [], excerpts: [], where: 'w', summary: null }],
  answers: {}, open: ['E-003'], changed: [] };
let doc = gatesDoc(1, []);
route.handler = (path) => (path === '/gates' ? { body: doc } : { body: listing });
const wait = () => new Promise((r) => setTimeout(r, 20));
await refresh();
const entry = [...I.seen.values()].find((e) => e.g.kind === 'adoption');
openAdoption(entry);
await wait();
pick(cur(), ACTIONS.bug[0]);  // "Real bug — it should…": the panel focuses its text box
const box = document.getElementById('answer-text');
box.value = 'it should read the order key'; box.selectionStart = 3; box.selectionEnd = 9;
const before = document.activeElement === box;
DOM.hostMoves = 0;
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_a_redraw_never_moves_the_open_panel_and_keeps_its_focus(tmp_path):
    # /gates changes while the panel is open: the adoption question counts down, and another worktree gains a gate
    got = run_page(tmp_path, OPEN_ADOPTION + r"""
doc = gatesDoc(0, [{ id: 'signoff:T-1', kind: 'signoff', title: 't', question: 'q', evidence: [] }]);
doc.worktrees[1].gates.push({ id: 'error-class:E-009', kind: 'error-class', title: 'e', question: 'q', evidence: [] });
await refresh();
await refresh();
console.log(JSON.stringify({ before, redrew: I.raw === JSON.stringify(doc), moves: DOM.hostMoves, focused: document.activeElement === box,
  selection: [box.selectionStart, box.selectionEnd], inCard: I.cards.get(entry.key).contains(document.getElementById('panel-host')),
  shown: !document.getElementById('panel-host').hidden, cardInPage: I.cards.get(entry.key).isConnected }));
""")
    assert got == {"before": True, "redrew": True, "moves": 0, "focused": True, "selection": [3, 9], "inCard": True,
                   "shown": True, "cardInPage": True}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_a_move_of_the_panel_restores_its_focus_and_selection(tmp_path):
    got = run_page(tmp_path, OPEN_ADOPTION + r"""
I.slot = null;  // forget the slot the panel sits in, so the next redraw has to move it
doc = gatesDoc(0, []);
await refresh();
console.log(JSON.stringify({ moves: DOM.hostMoves, focused: document.activeElement === box, selection: [box.selectionStart, box.selectionEnd] }));
""")
    assert got["moves"] >= 1  # the panel did move: the restore is what kept the focus
    assert got["focused"] is True and got["selection"] == [3, 9]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_done_right_after_the_last_answer_is_accepted(tmp_path, monkeypatch):
    # the page against a real inbox: the question the page last listed counts one item open; Done must send the current one
    import json

    from conftest import PLUGINS_FILE
    from inbox_fixture import AREA
    from prdlint import confirm
    from test_inbox_server import Inbox

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    box = Inbox(tmp_path / "repo")
    try:
        got = run_page(tmp_path, f"""
await refresh();
const entry = [...I.seen.values()].find((e) => e.g.kind === 'adoption' && e.wt.path === {json.dumps(str(box.repo))});
openAdoption(entry);
const shown = window.PANEL_HOST.question;
await new Promise((r) => setTimeout(r, 300));
await save(S.order.find((it) => it.id === 'E-003'), 'intended', '', null);
const stale = window.PANEL_HOST.question === shown;
await finish();
console.log(JSON.stringify({{ stale, ended: S.ended, notice: S.notice, open: I.panelKey }}));
""", base=box.base, token=box.token)
        assert got == {"stale": True, "ended": "done", "notice": "", "open": None}
        assert json.loads(confirm.answers_path(box.repo, AREA).read_text(encoding="utf-8"))["done"] is True
        assert [line["reply"] for line in box.log()] == ["Done (form)"]
    finally:
        box.stop()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_a_deploy_step_answered_in_another_worktree_shows_its_reply(tmp_path):
    # a deploy step is repo-wide, as wait_gate matches it: its answer from any worktree is its answer
    got = run_page(tmp_path, r"""
const answers = [{ worktree: '/w2', gate: 'deploy-step:r1:3', reply: 'deployed (form)', by: 'form', at: 't' },
                 { worktree: '/w2', gate: 'signoff:T-1', reply: 'Pass (form)', by: 'form', at: 't' }];
const at = (id) => ({ g: { id, kind: id.split(':')[0] }, wt: { path: '/w' } });
const deploy = latestAnswer(answers, at('deploy-step:r1:3'));
console.log(JSON.stringify({ deploy: deploy && deploy.reply, signoff: latestAnswer(answers, at('signoff:T-1')) }));
""")
    assert got == {"deploy": "deployed (form)", "signoff": None}


NO_WAIT = "No session is waiting on this gate. Answering it still records the answer."


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_a_card_nobody_waits_on_says_so_in_one_muted_line(tmp_path):
    got = run_page(tmp_path, r"""
const g = (waiting) => ({ id: 'error-class:E-003', kind: 'error-class', title: 't', question: 'q', evidence: [], waiting });
const lines = (card) => card.all((n) => n.className.split(' ').includes('gnowait')).map((n) => [n.className, n.textContent]);
const entry = (w, gone) => ({ key: `/w\n${w}`, g: g(w), wt: { path: '/w', branch: 'main' }, gone, answer: null });
console.log(JSON.stringify({ no: lines(gateCard(entry(false, false), new Map())), yes: lines(gateCard(entry(true, false), new Map())),
  gone: lines(gateCard(entry(false, true), new Map())) }));
""")
    assert got["no"] == [["muted gnowait", NO_WAIT]]
    assert got["yes"] == [] and got["gone"] == []
    assert NO_WAIT in page()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_an_unreadable_run_log_card_shows_its_reason_and_no_answer_controls(tmp_path):
    got = run_page(tmp_path, r"""
const g = (extra) => ({ id: 'deploy-step:r1:3', kind: 'deploy-step', title: 't', question: 'q', evidence: [], run: 'r1', step: 3,
  env: 'production', actor: 'human', do: 'd', check: 'c', waiting: false, ...extra });
const bad = { id: 'deploy-step:r1:unreadable', kind: 'deploy-step', title: 'run log r1 could not be read',
  question: 'Expecting value: line 1 column 1 (char 0)', evidence: [], choices: [], run: 'r1', unreadable: true, waiting: false };
const entry = (gate) => ({ key: `/w\n${gate.id}`, g: gate, wt: { path: '/w', branch: 'main' }, gone: false, answer: null });
const shape = (card) => ({
  controls: card.all((n) => ['TEXTAREA', 'BUTTON', 'SELECT'].includes(n.tagName)).length,
  text: card.textContent,
  nowait: card.all((n) => n.className.split(' ').includes('gnowait')).length,
});
console.log(JSON.stringify({ bad: shape(gateCard(entry(bad), new Map())), good: shape(gateCard(entry(g({})), new Map())) }));
""")
    assert got["bad"]["controls"] == 0
    assert "Expecting value: line 1 column 1 (char 0)" in got["bad"]["text"] and "r1" in got["bad"]["text"]
    assert got["bad"]["nowait"] == 0  # "Answering it still records the answer" would be false
    assert got["good"]["controls"] >= 2 and got["good"]["nowait"] == 1  # a readable step keeps its reply box
