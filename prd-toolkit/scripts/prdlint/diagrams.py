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
_START = re.compile(r"<[A-Za-z]")
_SHAPE = re.compile(r"\s*(?:<\?xml[^>]*\?>\s*)?(<svg\b.*</svg>)\s*", re.S | re.I)
_ON = re.compile(r"(?<![\w-])on\w*\s*=")
_URL = re.compile(r"url\(")
_LOADS = ("@import", "@font-face", "image-set(", "image(", "src(", "src=")
_WS = "\t\n\f\r "  # the HTML tokenizer's whitespace


def _tag_at(s: str, i: int) -> list[tuple[str, str]] | None:
    """The attributes of the start tag at `s[i]` (a `<` and a letter), read as the HTML tokenizer reads them: names
    lowercased, values with character references decoded. None when the text ends inside the tag."""
    n, j = len(s), i + 1
    while j < n and s[j] not in _WS + "/>":
        j += 1
    attrs: list[tuple[str, str]] = []
    while True:
        while j < n and (s[j] in _WS or s[j] == "/"):  # before an attribute name; a `/` not before `>` is skipped
            j += 1
        if j >= n:
            return None
        if s[j] == ">":
            return attrs
        k = j + 1  # a name may start with `=`, and holds quotes and `<` as written
        while k < n and s[k] not in _WS + "/>=":
            k += 1
        name, j, value = s[j:k].lower(), k, ""
        while j < n and s[j] in _WS:
            j += 1
        if j < n and s[j] == "=":
            j += 1
            while j < n and s[j] in _WS:
                j += 1
            if j >= n:
                return None
            if s[j] in "\"'":
                end = s.find(s[j], j + 1)
                if end < 0:
                    return None
                value, j = s[j + 1 : end], end + 1
            elif s[j] != ">":
                k = j
                while k < n and s[k] not in _WS + ">":
                    k += 1
                value, j = s[j:k], k
        attrs.append((name, html.unescape(value)))


def check_svg(svg: str) -> str | None:
    """Why this SVG may not go on the page, or None. It must be one `<svg>` whose root ID is `diagram-<n>`; each tag's
    attributes are read as a browser reads them, and every href and url( must point into `diagram-<n>`. Tag names are
    read as written; the rest is also read with character references decoded, as a browser reads attribute values and
    SVG style, so `&#x75;rl(` is `url(`."""
    shape = _SHAPE.fullmatch(svg)
    if not shape:
        return "the SVG is not one <svg> element"
    root = dict(reversed(_tag_at(svg, shape.start(1)) or []))  # the first of a repeated attribute wins
    number = re.fullmatch(r"diagram-(\d+)", root.get("id", ""))
    if not number:
        return "the SVG's root has no diagram-<n> ID"
    own = rf"#diagram-{number.group(1)}(?!\d)"
    href_ok = re.compile(own)  # a value is a URL: anything before the `#` makes it a relative one
    url_ok = re.compile(rf"[{_WS}]*[\"']?[{_WS}]*{own}")  # CSS may quote and space the target, with its own whitespace
    raw = svg.lower()
    text = html.unescape(svg).lower()
    tags = [_tag_at(svg, m.start()) for m in _START.finditer(svg)]  # from every `<`: a decoy cannot hide a tag
    attrs = [a for t in tags if t is not None for a in t]
    if "<script" in raw or ":script" in raw:
        return "the SVG holds <script"
    if "<foreignobject" in raw:
        return "the SVG holds <foreignObject"
    if _ON.search(text) or any(name.startswith("on") for name, _ in attrs):
        return "the SVG holds an on…= attribute"
    if any((name == "href" or name.endswith(":href")) and not href_ok.match(value.strip(_WS)) for name, value in attrs):
        return "the SVG holds an href that is not #…"
    if any(not url_ok.match(text, m.end()) for m in _URL.finditer(text)):
        return "the SVG holds a url( that is not url(#…)"
    tag = next((t for t in _TAG.findall(raw) if t not in _SVG_TAGS), None)
    if tag:
        return f"the SVG holds <{tag}>, which is not a drawing element"
    if None in tags:
        return "the SVG holds a tag that does not close"
    if "\\" in text:
        return "the SVG holds a backslash, which CSS can use to hide url( or @import"
    load = next((w for w in _LOADS if w in text), None)
    if load:
        return f"the SVG holds {load}"
    return None
