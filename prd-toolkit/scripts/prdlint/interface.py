"""The machine interface: one JSON document per call, versioned, shared by every interface script."""
import contextlib
import io
import json
import re
import sys
from collections.abc import Callable

INTERFACE = 1
_PREFIX = re.compile(r"^(?:prd_\w+(?:\.py)?): (?:error: )?")


def dump(kind: str, payload: dict) -> str:
    """One line of JSON with `interface` and `kind` first."""
    return json.dumps({"interface": INTERFACE, "kind": kind, **payload}, ensure_ascii=False) + "\n"


def error(kind: str, message: str) -> str:
    return dump(kind, {"error": message})


def add_flags(parser) -> None:
    parser.add_argument("--json", nargs="?", const="1", metavar="N", help="print one JSON document (interface 1)")
    parser.add_argument("--interface", action="store_true", help="print the interface version and exit")


def wants_json(argv: list[str]) -> bool:
    return any(a == "--json" or a.startswith("--json=") for a in argv)


def check_version(value: str | None) -> str | None:
    """The error text for an unsupported interface N, or None."""
    if value is None or value == str(INTERFACE):
        return None
    return f"unsupported interface {value}; this toolkit speaks {INTERFACE}"


def run(main_text: Callable[[list[str]], int], kind: str, argv: list[str]) -> int:
    """Call main_text; when JSON is wanted, turn an exit-2 path into the error document. Stderr keeps its text."""
    if not wants_json(argv):
        return main_text(argv)
    captured = io.StringIO()
    with contextlib.redirect_stderr(captured):
        code = main_text(argv)
    text = captured.getvalue()
    sys.stderr.write(text)
    if code == 2:
        lines = [ln for ln in text.strip().splitlines() if ln.strip()]
        message = _PREFIX.sub("", lines[-1]) if lines else "usage error"
        sys.stdout.write(error(kind, message))
    return code
