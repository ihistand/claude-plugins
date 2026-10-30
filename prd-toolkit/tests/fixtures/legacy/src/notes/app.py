"""A tiny in-memory notes service."""

_NOTES: dict[int, str] = {}


def add_note(text: str) -> int:
    """Store a note and return its id."""
    note_id = len(_NOTES) + 1
    _NOTES[note_id] = text
    return note_id


def search_notes(term: str) -> list[str]:
    """Return the notes that contain `term`."""
    return [t for t in _NOTES.values() if term in t]  # apparent bug: case-sensitive
