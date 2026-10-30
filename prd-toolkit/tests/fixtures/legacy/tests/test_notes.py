import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from notes.app import add_note, search_notes  # noqa: E402


def test_add_note_returns_an_id():
    """@prd T-001.1"""
    assert add_note("buy milk") == 1


def test_search_finds_a_note():
    assert "buy milk" in search_notes("milk")
