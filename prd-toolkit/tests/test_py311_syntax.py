"""The scripts declare requires-python >= 3.11: none may use syntax that only parses on 3.12 or later.

`ast.parse(feature_version=(3, 11))` does not reject PEP 701 f-strings, so the f-string rule is checked on the tokens.
"""
import ast
import io
import tokenize
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FILES = sorted([*SCRIPTS.glob("prd_*.py"), *SCRIPTS.glob("prdlint/**/*.py")])


def _quote(token_text: str) -> str:
    """The closing quote (one or three characters) of a string or f-string start token."""
    body = token_text.lstrip("rRbBfFuU")
    return body[:3] if body[:3] in ('"""', "'''") else body[:1]


def reused_quotes(source: str) -> list[int]:
    """Lines where a string inside an f-string replacement field uses the f-string's own quote (3.12+ only)."""
    start = getattr(tokenize, "FSTRING_START", None)
    if start is None:
        return []
    stack: list[str] = []
    lines = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == start:
            if stack and _quote(tok.string) == stack[-1]:
                lines.append(tok.start[0])
            stack.append(_quote(tok.string))
        elif tok.type == tokenize.FSTRING_END:
            stack.pop()
        elif tok.type == tokenize.STRING and stack and _quote(tok.string) == stack[-1]:
            lines.append(tok.start[0])
    return lines


def test_the_checker_flags_reused_quotes():
    assert reused_quotes('x = f"a {d["k"]} b"\n') == [1]
    assert reused_quotes("x = f\"a {d['k']} b\"\n") == []


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SCRIPTS).as_posix())
def test_parses_as_python_311(path):
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path), feature_version=(3, 11))
    assert reused_quotes(source) == [], f"{path.name}: a quote reused inside an f-string needs Python 3.12"
