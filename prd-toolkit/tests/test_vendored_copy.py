"""This repository's own `.prd-toolkit/` is the plugin's bytes: CI's `check --ci` compares only the generated CI files."""
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO = PLUGIN_ROOT.parent


def test_the_vendored_copy_matches_the_plugin():
    run = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_hooks.py"), "check", "docs/prd/prd-toolkit"],
                         cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr  # refresh it with the vendor-only snippet
