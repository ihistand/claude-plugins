"""lint-cli FR-013: --list-packs (test-cases/lint-cli.yaml)."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lint_cli_support import (  # noqa: E402
    PLUGINS_NONE,
    REPO,
    in_relative_order,
    run,
    vendored_fixture,  # noqa: F401  (pytest fixture `vendored`: repo/vendored, testing.md Fixtures)
)

DOCUMENT = (
    "document 1.0.0 (prd-toolkit) — Markdown documents written for people: a user guide, "
    "a runbook for humans, a policy."
)
SERVICE = (
    "service 1.0.0 (prd-toolkit) — Services with an API, a database or events; "
    "the PRD of prd-toolkit 0.7."
)
DOCUMENT_DEMO = (
    "document 1.0.0 (demo@local) — Markdown documents written for people: a user guide, "
    "a runbook for humans, a policy."
)


def test_t013_1_list_packs_toolkit_only(tmp_path, monkeypatch):
    """@prd T-013.1"""
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_NONE))
    for args in (["--list-packs"], ["--list-packs", str(tmp_path / "missing")]):
        r = run(args, cwd=tmp_path)
        assert r.exit == 0, args
        assert r.stderr == "", (args, r.stderr)
        assert r.stdout_lines == [DOCUMENT, SERVICE], (args, r.stdout)


def test_t013_2_list_packs_toolkit_then_plugin(tmp_path, monkeypatch):
    """@prd T-013.2"""
    shutil.copytree(REPO / "prd-toolkit" / "packs" / "document",
                    tmp_path / "plugin" / "prd-packs" / "document")
    resolved = Path(tmp_path).resolve()
    plugins = tmp_path / "plugins.json"
    plugins.write_text(
        json.dumps({"version": 2,
                    "plugins": {"demo@local": [{"installPath": f"{resolved}/plugin"}]}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins))
    r = run(["--list-packs"], cwd=tmp_path)
    assert r.exit == 0
    assert r.stderr == "", r.stderr
    assert in_relative_order(r.stdout_lines, [DOCUMENT, SERVICE, DOCUMENT_DEMO]), r.stdout


VENDORED_STDERR = (
    "prd_lint: listed from the vendored copy: service is vendored in .prd-toolkit/packs/, "
    "each with the source it was vendored from; the plugin's own scripts/prd_lint.py "
    "--list-packs lists every pack on this machine\n"
)


def test_t013_3_list_packs_vendored_copy(tmp_path, monkeypatch, vendored):
    """@prd T-013.3"""
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_NONE))
    r = run(["--list-packs"], cwd=tmp_path, script=vendored / "prd_lint.py")
    assert r.exit == 0, (r.stdout, r.stderr)
    assert r.stdout == (
        "service 1.0.0 (prd-toolkit) — Services with an API, a database or events; "
        "the PRD of prd-toolkit 0.7.\n"
    ), r.stdout
    assert r.stderr == VENDORED_STDERR, r.stderr


def test_t013_4_list_packs_vendored_copy_no_sources(tmp_path, monkeypatch, vendored):
    """@prd T-013.4"""
    (vendored / "pack-sources.json").unlink()
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_NONE))
    r = run(["--list-packs"], cwd=tmp_path, script=vendored / "prd_lint.py")
    assert r.exit == 0, (r.stdout, r.stderr)
    assert r.stdout == (
        "service 1.0.0 (source not recorded) — Services with an API, a database or events; "
        "the PRD of prd-toolkit 0.7.\n"
    ), r.stdout
    assert r.stderr == VENDORED_STDERR, r.stderr
