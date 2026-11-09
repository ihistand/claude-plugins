"""prdlint.diagrams: the renderer behind one function, the numbering of its IDs, and the check on what it returns."""
import json
import re
import subprocess
from pathlib import Path

import pytest
from prdlint import diagrams

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/prd_publish.py"
TOOLKIT_PRD = ROOT.parent / "docs/prd/prd-toolkit"


def pin() -> str:
    """The renderer's version, read from prd_publish.py's dependency header so the test and the script cannot drift."""
    m = re.search(r'"mermaidx==([^"]+)"', SCRIPT.read_text(encoding="utf-8").split("# ///", 2)[1])
    assert m, "prd_publish.py's dependency header pins mermaidx"
    return m.group(1)


def section4() -> str:
    text = (TOOLKIT_PRD / "prd.md").read_text(encoding="utf-8")
    m = re.search(r"^## 4\..*?^```mermaid\n(.*?)^```$", text, re.S | re.M)
    assert m, "the toolkit's §4 holds a mermaid diagram"
    return m.group(1)


def labels(source: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"\w\[\(?([^\]()]+)\)?\]", source)]


def text_of(svg: str) -> str:
    return " ".join(re.sub(r"<[^>]*>", " ", re.sub(r"<style>.*?</style>", " ", svg, flags=re.S)).split())


PROBE = """
import json, sys
sys.path.insert(0, sys.argv[1])
from prdlint import diagrams
source = sys.stdin.read()
out = {"one": diagrams.render_svg(source, 1), "two": diagrams.render_svg(source, 2)}
try:
    diagrams.render_svg("flowchart LR\\n  A --> (((\\n", 3)
    out["bad"] = None
except diagrams.Fallback as e:
    out["bad"] = e.reason
print(json.dumps(out))
"""


def test_the_toolkit_diagram_renders_for_real(tmp_path):
    """Never skipped: uv installs the pinned renderer in its own environment; the pytest one never holds it."""
    r = subprocess.run(["uv", "run", "--no-project", "--with", f"mermaidx=={pin()}", "python", "-I", "-c", PROBE,
                        str(ROOT / "scripts")], input=section4(), capture_output=True, text=True, encoding="utf-8",
                       cwd=tmp_path, timeout=600)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    one, two = out["one"], out["two"]
    assert one.startswith('<svg id="diagram-1"') and two.startswith('<svg id="diagram-2"')
    drawn = "".join(text_of(one).split())  # a long label wraps over tspans, even inside a word
    for label in labels(section4()):
        assert "".join(label.split()) in drawn, label
    assert diagrams.check_svg(one) is None and "<foreignObject" not in one
    ids1, ids2 = (set(re.findall(r'(?<=\s)id="([^"]*)"', s)) for s in (one, two))
    assert all(i == "diagram-1" or i.startswith("diagram-1-") for i in ids1), ids1
    assert all(i == "diagram-2" or i.startswith("diagram-2-") for i in ids2), ids2
    assert not ids1 & ids2
    for ref in re.findall(r"url\(#([^)]+)\)", one):  # every url(#…) points inside its own diagram
        assert ref in ids1, ref
    assert "#my-svg" not in one  # the style is scoped to the diagram's own ID
    assert out["bad"].startswith("the renderer failed: "), out["bad"]


def test_the_toolkit_page_draws_its_diagrams_for_real(tmp_path):
    """The real prd_publish.py, its renderer installed by uv from the dependency header, on the toolkit's own PRD."""
    from test_publish import assert_loads_nothing
    out = tmp_path / "page.html"
    r = subprocess.run(["uv", "run", "--script", str(SCRIPT), "render", str(TOOLKIT_PRD), "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr
    assert "shown as source" not in r.stderr, r.stderr
    page = out.read_text(encoding="utf-8")
    assert '<figure class="diagram"><svg id="diagram-1"' in page and '<figure class="diagram"><svg id="diagram-2"' in page
    assert 'pre class="mermaid"' not in page
    assert_loads_nothing(page)


# ---- numbering, with the renderer's output stood in ----------------------------------------------

MERMAIDISH = ('<svg id="my-svg" aria-labelledby="chart-title-my-svg"><title id="chart-title-my-svg">t</title>'
              '<style>#my-svg{fill:#333}#my-svg .edge{stroke:#000}</style>'
              '<defs><marker id="my-svg_arrow"></marker><filter id="my-svg-shadow"></filter></defs>'
              '<g id="L_a_0"><path id="my-svg-L_a_0" marker-end="url(#my-svg_arrow)" style="filter:url(#my-svg-shadow)"></path></g>'
              '<use href="#L_a_0"></use><text>#my-svg and L_a_0</text></svg>')


def test_ids_are_numbered_per_diagram(monkeypatch):
    monkeypatch.setattr(diagrams, "_render", lambda source: MERMAIDISH)
    two = diagrams.render_svg("graph TD\n  numbered\n", 2)
    assert two == ('<svg id="diagram-2" aria-labelledby="diagram-2-chart-title-my-svg"><title id="diagram-2-chart-title-my-svg">t</title>'
                   '<style>#diagram-2{fill:#333}#diagram-2 .edge{stroke:#000}</style>'
                   '<defs><marker id="diagram-2-my-svg_arrow"></marker><filter id="diagram-2-my-svg-shadow"></filter></defs>'
                   '<g id="diagram-2-L_a_0"><path id="diagram-2-my-svg-L_a_0" marker-end="url(#diagram-2-my-svg_arrow)" '
                   'style="filter:url(#diagram-2-my-svg-shadow)"></path></g>'
                   '<use href="#diagram-2-L_a_0"></use><text>#my-svg and L_a_0</text></svg>')
    assert diagrams.render_svg("graph TD\n  numbered\n", 2) == two  # the same every time
    assert diagrams.render_svg("graph TD\n  numbered\n", 1).startswith('<svg id="diagram-1" aria-labelledby="diagram-1-chart')


def test_a_renderer_that_cannot_load_is_a_fallback(monkeypatch):
    def missing(source):
        raise ImportError("No module named 'mermaidx'")
    monkeypatch.setattr(diagrams, "_render", missing)
    with pytest.raises(diagrams.Fallback) as e:
        diagrams.render_svg("graph TD\n  missing\n", 1)
    assert e.value.reason == "the renderer cannot load: No module named 'mermaidx'"


def test_a_render_error_is_a_fallback_of_one_line(monkeypatch):
    def broken(source):
        raise RuntimeError("Mermaid rendering failed: Error: Parse error on line 2:\n...\n----^")
    monkeypatch.setattr(diagrams, "_render", broken)
    with pytest.raises(diagrams.Fallback) as e:
        diagrams.render_svg("graph TD\n  broken\n", 1)
    assert e.value.reason == "the renderer failed: Mermaid rendering failed: Error: Parse error on line 2:"


def test_a_refused_svg_is_a_fallback(monkeypatch):
    monkeypatch.setattr(diagrams, "_render", lambda source: '<svg id="my-svg"><script>x</script></svg>')
    with pytest.raises(diagrams.Fallback) as e:
        diagrams.render_svg("graph TD\n  refused\n", 1)
    assert e.value.reason == diagrams.check_svg('<svg id="diagram-1"><script>x</script></svg>')


def test_the_vendorable_module_needs_no_renderer():
    src = Path(diagrams.__file__).read_text(encoding="utf-8")
    assert not re.search(r"^(import|from) mermaidx", src, re.M)  # imported inside the render only


# ---- check_svg -----------------------------------------------------------------------------------

SAFE = ('<svg id="diagram-1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<style>#diagram-1 .edge{stroke:#333;filter:url(#diagram-1-shadow)}@keyframes dash{to{stroke-dashoffset:0}}</style>'
        '<defs><marker id="arrow"></marker><filter id="diagram-1-shadow"><feDropShadow dx="1"></feDropShadow></filter></defs>'
        '<path marker-end="url(#arrow)" style="filter: url( \'#arrow\' )"></path><use href="#arrow"></use>'
        '<a xlink:href="#arrow"><text data-id="x">turn it on, A &amp; B &lt;b&gt;</text></a>%s</svg>')


def test_a_clean_svg_passes():
    assert diagrams.check_svg(SAFE % "") is None


@pytest.mark.parametrize("bad", [
    "<script>x</script>", "<SCRIPT>x</SCRIPT>", "<svg:script>x</svg:script>",
    '<g onload="x">', '<g ONLOAD="x">', '<g\nonclick\t=\n"x">', '<g/onmouseover=x>', '<g x="1"onload="x">',
    '<a href="https://evil.example/">', '<a href="http://evil.example/">', "<a xlink:href='http://x'>", '<a href = "javascript:x">',
    '<a href=data:text/html,x>', '<image href="data:image/png;base64,AAAA"></image>', '<use href="https://x.example/a.svg#a">',
    '<a href="">', '<a href="&#x68;ttps://x">',
    "<foreignObject><div>x</div></foreignObject>", "<FOREIGNOBJECT>",
    '<path style="fill:url(http://x)">', '<path style="fill:URL( \'https://x\' )">', '<path style="fill:&#x75;rl(http://x)">',
    "<style>a{background:url(http://x)}</style>", r"<style>a{background:u\72l(http://x)}</style>",
    '<style>@import "https://x.example/a.css";</style>', "<style>@IMPORT url(x)</style>",
    '<style>@font-face{font-family:x;src:local(y)}</style>', '<style>a{background:image-set("https://x" 1x)}</style>',
    '<img src="https://x">', '<g src="x">', "<iframe>", "<embed>", "<object>", "<link>", "<meta>", "<base>",
    "<b>x</b>", "<div>x</div>", '<table background="https://x">',
    '<set attributeName="href" to="https://x"></set>', '<animate attributeName="href"></animate>', "<feImage></feImage>",
])
def test_check_svg_refuses(bad):
    assert diagrams.check_svg(SAFE % bad) is not None, bad


@pytest.mark.parametrize("bad, reason", [
    ("<script>x</script>", "the SVG holds <script"),
    ('<g onload="x">', "the SVG holds an on…= attribute"),
    ('<a href="http://evil.example/">', "the SVG holds an href that is not #…"),
    ("<foreignObject></foreignObject>", "the SVG holds <foreignObject"),
    ('<path style="fill:url(http://x)">', "the SVG holds a url( that is not url(#…)"),
])
def test_check_svg_names_the_spec_reasons(bad, reason):
    assert diagrams.check_svg(SAFE % bad) == reason
