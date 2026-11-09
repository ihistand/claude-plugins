"""Mermaid diagrams as inline SVG for the published page: the renderer sits behind `render_svg`, and every SVG is
checked before it is used. The renderer (mermaidx) is imported inside the render only, so this module, vendored or
not, imports without it."""
import functools
import html
import re

CONFIG = {"htmlLabels": False, "flowchart": {"htmlLabels": False}, "securityLevel": "strict"}


class Fallback(Exception):
    """The diagram is shown as its source; `reason` says why."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _render(source: str) -> str:
    import mermaidx  # the one place the renderer is needed
    return mermaidx.render(source, config=CONFIG).svg()


def _first_line(e: Exception) -> str:
    text = str(e).strip()
    return text.splitlines()[0] if text else type(e).__name__


@functools.lru_cache(maxsize=None)
def _raw(source: str) -> tuple[str, str]:
    """(SVG, "") or ("", reason); a page shows its §4 diagram twice, and it is drawn once."""
    try:
        return _render(source), ""
    except ImportError as e:
        return "", f"the renderer cannot load: {_first_line(e)}"
    except Exception as e:  # noqa: BLE001 - any failure of the renderer shows the source
        return "", f"the renderer failed: {_first_line(e)}"


def render_svg(source: str, number: int) -> str:
    """The diagram as an SVG whose IDs all belong to `diagram-<number>`; raises Fallback for any failure."""
    svg, reason = _raw(source)
    if reason:
        raise Fallback(reason)
    svg = _number(svg, number)
    refused = check_svg(svg)
    if refused:
        raise Fallback(refused)
    return svg


# ---- IDs -----------------------------------------------------------------------------------------

_ID = re.compile(r'(?<=\s)id="([^"]*)"')
_ARIA = re.compile(r'(\saria-(?:labelledby|describedby)=")([^"]*)"')
_MARKUP = re.compile(r"<style\b[^>]*>.*?</style>|<[^>]*>", re.S)


def _number(svg: str, number: int) -> str:
    """The root SVG's ID becomes `diagram-<number>` and every other ID `diagram-<number>-<id>`, with each `#id`
    reference and aria ID list in the markup and the style following; text between tags is left alone."""
    root = re.match(r'\s*<svg\b[^>]*?\sid="([^"]*)"', svg)
    ids = set(_ID.findall(svg))
    new = {i: f"diagram-{number}" if root and i == root.group(1) else f"diagram-{number}-{i}" for i in ids}
    if not new:
        return svg
    ref = re.compile("#(" + "|".join(re.escape(i) for i in sorted(new, key=len, reverse=True)) + r")(?![\w-])")

    def markup(m: re.Match) -> str:
        s = _ID.sub(lambda k: f'id="{new[k.group(1)]}"', m.group(0))
        s = _ARIA.sub(lambda k: k.group(1) + " ".join(new.get(t, t) for t in k.group(2).split()) + '"', s)
        return ref.sub(lambda k: "#" + new[k.group(1)], s)

    return _MARKUP.sub(markup, svg)


# ---- the check -----------------------------------------------------------------------------------

# SVG elements an HTML page may hold inline; any other tag (an HTML element breaks out of the SVG) is refused, as are
# script, foreignObject, the animation elements (they can set an href) and image/feImage (they only load).
_SVG_TAGS = frozenset(t.lower() for t in (
    "a circle clipPath defs desc ellipse feBlend feColorMatrix feComponentTransfer feComposite feConvolveMatrix "
    "feDiffuseLighting feDisplacementMap feDistantLight feDropShadow feFlood feFuncA feFuncB feFuncG feFuncR "
    "feGaussianBlur feMerge feMergeNode feMorphology feOffset fePointLight feSpecularLighting feSpotLight feTile "
    "feTurbulence filter g line linearGradient marker mask metadata path pattern polygon polyline radialGradient rect "
    "stop style svg switch symbol text textPath title tspan use view").split())
_TAG = re.compile(r"</?([A-Za-z][^\s/>]*)")
_ON = re.compile(r"(?<![\w-])on\w*\s*=")
_HREF = re.compile(r"""href\s*=\s*(?:"\s*([^"]*)"|'\s*([^']*)'|([^\s>]*))""")
_URL = re.compile(r"""url\((?!\s*["']?\s*#)""")
_LOADS = ("@import", "@font-face", "image-set(", "image(", "src(", "src=")


def check_svg(svg: str) -> str | None:
    """Why this SVG may not go on the page, or None. Tags are read as written; everything else is read with
    character references decoded, as a browser reads attribute values and SVG style, so `&#x75;rl(` is `url(`."""
    raw = svg.lower()
    text = html.unescape(svg).lower()
    if "<script" in raw or ":script" in raw:
        return "the SVG holds <script"
    if "<foreignobject" in raw:
        return "the SVG holds <foreignObject"
    if _ON.search(text):
        return "the SVG holds an on…= attribute"
    if any(not next(v for v in m.groups() if v is not None).startswith("#") for m in _HREF.finditer(text)):
        return "the SVG holds an href that is not #…"
    if _URL.search(text):
        return "the SVG holds a url( that is not url(#…)"
    tag = next((t for t in _TAG.findall(raw) if t not in _SVG_TAGS), None)
    if tag:
        return f"the SVG holds <{tag}>, which is not a drawing element"
    if "\\" in text:
        return "the SVG holds a backslash, which CSS can use to hide url( or @import"
    load = next((w for w in _LOADS if w in text), None)
    if load:
        return f"the SVG holds {load}"
    return None
