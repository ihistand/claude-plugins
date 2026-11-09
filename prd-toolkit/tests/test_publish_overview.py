"""prd_publish.py render: the Overview tab, its parts and the mermaid fence."""
import re
from datetime import date
from pathlib import Path

import pytest
from conftest import edit
from prd_publish import main as publish_main
from prdlint import diagrams, model, overview, publish
from test_publish import stub_svg

TODAY = date(2026, 11, 1)
FIX = Path(__file__).parent / "fixtures/publish"


def page_of(root, summaries=None):
    return publish.render_page(model.load(root), root.parent.parent.parent, summaries, TODAY)


@pytest.fixture(autouse=True)
def as_source(monkeypatch):
    """The renderer stubbed to fall back, so every page here shows its diagrams as today's source."""
    def fallback(source, number):
        raise diagrams.Fallback("x")
    monkeypatch.setattr(diagrams, "render_svg", fallback)


def panel(page, name):
    m = re.search(rf'<section class="panel" id="{name}">\n(.*?)\n</section>', page, re.S)
    assert m, name
    return m.group(1)


def test_overview_first_and_checked(prd):
    page = page_of(prd)
    assert page.index('id="tab-overview"') < page.index('id="tab-business"') < page.index('id="tab-technical"')
    assert re.search(r'<input[^>]*id="tab-overview" checked>', page)
    assert not re.search(r'<input[^>]*id="tab-business" checked>', page)
    assert page.count(" checked>") == 1
    assert '<label for="tab-overview">Overview</label>' in page


def test_other_panels_unchanged(prd):
    old = (FIX / "orders_before_overview.html").read_text(encoding="utf-8")
    page = page_of(prd)
    old = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', old, flags=re.S)  # the one intended change
    assert panel(page, "business") == panel(old, "business")
    assert panel(page, "technical") == panel(old, "technical")


def test_all_parts_present(greet):
    p = panel(page_of(greet), "overview")
    f = overview.facts(model.load(greet))
    assert f"{f.version} · {f.status} · Owner: {f.owner} · Updated {f.updated}" in p
    for h in ("What it is", "Principles", "Architecture", "Areas", "Open errors", "Getting started"):
        assert f"<h2>{h}</h2>" in p, h
    assert "greet service says hello" in p and "<strong>Plain.</strong>" in p and "Install the service." in p
    assert "<th>Area</th><th>Adoption</th><th>Requirements</th>" in p
    assert "<td>api</td><td>adopted</td>" in p and "<td>import</td><td>confirmed</td>" in p
    assert "1 open error; the Technical tab lists them" in p
    assert "Linked PRDs" not in p  # greet has no links.md
    assert f"A snapshot of the PRD at version {f.version}. The PRD in the repository is the authority." in p
    assert p.index("What it is") < p.index("Principles") < p.index("Architecture") < p.index("Areas") < p.index("Open errors") < p.index("Getting started") < p.index("A snapshot")


def test_counts_line(greet):
    p = panel(page_of(greet), "overview")
    f = overview.facts(model.load(greet))
    for a in f.areas:
        want = ", ".join(f"{n} {k}" for k, n in a.counts.items()) or "-"
        assert f"<td>{a.name}</td><td>{a.adoption}</td><td>{want}</td>" in p


def test_counts_order_and_removed_left_out(greet):
    edit(greet, "features/import.md", "Status: live (since 1.0.0)", "Status: removed")
    p = panel(page_of(greet), "overview")
    assert "removed</td>" not in p


def test_parts_absent_from_notes(notes):
    p = panel(page_of(notes), "overview")
    for h in ("Principles", "Linked PRDs", "Getting started"):
        assert f"<h2>{h}</h2>" not in p
    assert "No open errors." in p and "open error" not in p.replace("No open errors.", "")
    assert "A snapshot of the PRD at version" in p
    assert "<td>-</td>" in p or "<td>import</td><td>-</td>" in p


def test_two_open_errors(greet):
    (greet / "errors.md").write_text((greet / "errors.md").read_text()
                                     + "\n### E-003 Another\nDetected: 2026-11-01, manual\nClassification: unclassified\nResolution: open\n")
    assert "2 open errors; the Technical tab lists them" in panel(page_of(greet), "overview")


def test_es_labels_on_orders(orders):
    page = page_of(orders)
    p = panel(page, "overview")
    assert '<label for="tab-overview">Resumen general</label>' in page
    for h in ("Qué es", "Principios", "Áreas", "PRD enlazados", "Primeros pasos"):
        assert f"<h2>{h}</h2>" in p, h
    assert "Una instantánea del PRD en la versión" in p
    assert "Responsable: " in p and "Actualizado " in p
    assert "Open errors" not in p and "Owner:" not in p


def test_linked_prds_as_the_readme_shows(orders):
    p = panel(page_of(orders), "overview")
    assert "<code>../billing</code>" in p  # a relative target would break the page's no-relative-href rule
    assert "<code>https://example.com/acme/reports.git#reports</code>" in p


MERMAID = "```mermaid\ngraph TD\n  A[<b>x</b> & y] --> B\n```"


ESCAPED = "graph TD\n  A[&lt;b&gt;x&lt;/b&gt; &amp; y] --&gt; B\n"


def fence_line(prd) -> int:
    lines = (prd / "prd.md").read_text(encoding="utf-8").split("\n")
    return next(i for i, ln in enumerate(lines, 1) if ln == "```mermaid" and lines[i] == "graph TD")


def publish_cli(prd, tmp_path, capsys):
    out = tmp_path / "page.html"
    code = publish_main(["render", str(prd), "--out", str(out)])
    return code, capsys.readouterr().err, out.read_text(encoding="utf-8")


def test_mermaid_fence_drawn(prd, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(diagrams, "render_svg", stub_svg)
    edit(prd, "prd.md", "## 5.", MERMAID + "\n\n## 5.")
    code, err, page = publish_cli(prd, tmp_path, capsys)
    assert code == 0 and "shown as source" not in err
    source = f'<details><summary>Diagram source</summary><pre class="mermaid-source">{ESCAPED}</pre></details>'
    for name in ("overview", "technical"):
        p = panel(page, name)
        assert p.count('<figure class="diagram"><svg id="diagram-') == 2, name  # the fixture's diagram and this one
        assert p.count(source) == 1, name
        assert 'pre class="mermaid"' not in p and "<details open" not in p, name
    ids = re.findall(r'<svg id="(diagram-\d+)"', page)
    assert ids == [f"diagram-{n}" for n in range(1, 5)]  # numbered in page order, never repeated
    for tag in ("<script", "<link", "@import"):
        assert tag not in page
    assert "url(" not in page.split("</style>")[0]


def test_mermaid_fence_as_source(prd, tmp_path, capsys):
    edit(prd, "prd.md", "## 5.", MERMAID + "\n\n## 5.")
    code, err, page = publish_cli(prd, tmp_path, capsys)
    assert code == 0
    want = f'<pre class="mermaid">{ESCAPED}</pre>'
    assert panel(page, "overview").count(want) == 1 and panel(page, "technical").count(want) == 1
    assert "<figure" not in page and "mermaid-source" not in page
    assert f"prd_publish: diagram at prd.md:{fence_line(prd)} shown as source: x\n" in err
    assert err.count(f"prd.md:{fence_line(prd)} ") == 1  # one line per diagram, though both tabs show it
    for tag in ("<script", "<link", "@import"):
        assert tag not in page
    assert "url(" not in page.split("</style>")[0]


def test_plain_fence_unchanged(prd):
    edit(prd, "prd.md", "## 5.", "```sh\necho hi\n```\n\n## 5.")
    assert '<pre><code class="language-sh">echo hi' in page_of(prd)


def test_overview_is_not_an_area(prd):
    with pytest.raises(publish.Refused) as e:
        page_of(prd, {"version": "1.0.0", "areas": {"overview": {"text": "x", "ids": []}}})
    assert e.value.reasons == ["summaries: area 'overview' does not exist"]
