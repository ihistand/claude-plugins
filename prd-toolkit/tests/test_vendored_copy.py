"""This repository's own `.prd-toolkit/` is the plugin's bytes: CI's `check --ci` compares only the generated CI files."""
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO = PLUGIN_ROOT.parent


def test_the_vendored_copy_matches_the_plugin():
    run = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_hooks.py"), "check", "docs/prd/prd-toolkit"],
                         cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    # a stale README or CLAUDE.md block is a different check (test_hooks_blocks.py); this one is about the vendored bytes
    left = [x for x in run.stdout.splitlines() if "; run prd_block.py" not in x]
    assert not left and not run.stderr, run.stdout + run.stderr  # refresh it with the vendor-only snippet
