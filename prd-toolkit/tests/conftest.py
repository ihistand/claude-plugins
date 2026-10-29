"""Shared pytest helpers: a copy of the valid fixture PRD and a one-edit mutator."""
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures/valid/orders"
PLUGINS_FILE = Path(__file__).parent / "fixtures/installed_plugins.json"


@pytest.fixture
def prd(tmp_path, monkeypatch) -> Path:
    """A fresh copy of the valid fixture at tmp_path/docs/prd/orders."""
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    dest = tmp_path / "docs/prd/orders"
    shutil.copytree(FIXTURE, dest)
    return dest


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace the single occurrence of `old` in root/rel with `new`."""
    path = root / rel
    text = path.read_text()
    assert text.count(old) == 1, f"{rel}: expected exactly one {old!r}, found {text.count(old)}"
    path.write_text(text.replace(old, new))


@dataclass
class Case:
    rule: str
    name: str
    mutate: Callable[[Path], None]
