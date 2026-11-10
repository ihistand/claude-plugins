"""Shared helpers for the black-box tests of nfr.md (testing.md Harness, Layout).

Everything here follows docs/prd/prd-toolkit/testing.md: the Subprocess environment rule,
the Fixtures table (lint-cli/orders, lint-cli/plugins_superpowers, repo/vendored) and the
Clean state rule for the test cache.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import yaml

# <repo>/prd-toolkit/tests/prd/nfr_support.py -> <repo>
REPO = Path(__file__).resolve().parents[3]
PRD_TOOLKIT = REPO / "prd-toolkit"
FIXTURES = REPO / "docs" / "prd" / "prd-toolkit" / "contracts" / "fixtures"

# testing.md Harness, Subprocess environment: removed from the runner's environment.
_DROPPED = ("PYTHONIOENCODING", "PYTHONPATH", "PYTHONHOME", "PRD_LINT_CI")


class VendoredFixtureError(RuntimeError):
    """The repo/vendored fixture's check failed: the test ends as an error, not a failure."""


def subprocess_env(extra: dict[str, str] | None = None,
                   drop: tuple[str, ...] = ()) -> dict[str, str]:
    """The runner's environment now, minus the Harness's dropped variables and `drop`,
    plus `extra` (the case's own env)."""
    env = {k: v for k, v in os.environ.items() if k not in _DROPPED and k not in drop}
    if extra:
        env.update(extra)
    return env


def test_cache_path() -> Path:
    """T-019.1 setup: PRD_TEST_UV_CACHE in the test's own environment (os.path.abspath of a
    relative value), or <repo>/prd-toolkit/.uv-test-cache when it is unset or empty."""
    value = os.environ.get("PRD_TEST_UV_CACHE", "")
    if value:
        return Path(os.path.abspath(value))
    return Path(os.path.abspath(PRD_TOOLKIT / ".uv-test-cache"))


# Not a test, despite its name.
test_cache_path.__test__ = False  # type: ignore[attr-defined]


def fixture_path(name: str, suffix: str) -> Path:
    """A fixture's file under contracts/fixtures/, e.g. ("lint-cli/orders", ".yaml")."""
    return FIXTURES / f"{name}{suffix}"


def load_orders(dest: Path) -> None:
    """Fixture lint-cli/orders: write each key's text to <dest>/<key>, creating parents."""
    data = yaml.safe_load(fixture_path("lint-cli/orders", ".yaml").read_text(encoding="utf-8"))
    for rel, text in data.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def plugins_superpowers_file() -> str:
    """Fixture lint-cli/plugins_superpowers: the file's absolute path for PRD_PLUGINS_FILE."""
    return str(fixture_path("lint-cli/plugins_superpowers", ".json").resolve())


def load_vendored(dest: Path) -> None:
    """Fixture repo/vendored: copy <repo>/.prd-toolkit to `dest` as plain files (symlinks
    followed), leaving out every __pycache__ folder, then run the fixture's check, raising
    VendoredFixtureError when it differs."""
    shutil.copytree(REPO / ".prd-toolkit", dest, symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__"))
    packs = dest / "packs"
    if not packs.is_dir():
        raise VendoredFixtureError(f"repo/vendored: {packs} is not a folder")
    visible = [p for p in packs.iterdir() if not p.name.startswith(".")]
    if len(visible) != 1 or visible[0].name != "service" or not visible[0].is_dir():
        raise VendoredFixtureError(
            f"repo/vendored: packs/ holds {sorted(p.name for p in visible)}, "
            "not only the folder 'service'")
    sources = dest / "pack-sources.json"
    try:
        parsed = json.loads(sources.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise VendoredFixtureError(f"repo/vendored: {sources} unreadable: {exc}") from exc
    if parsed != {"service": "prd-toolkit"}:
        raise VendoredFixtureError(
            f"repo/vendored: pack-sources.json is {parsed!r}, not {{'service': 'prd-toolkit'}}")
