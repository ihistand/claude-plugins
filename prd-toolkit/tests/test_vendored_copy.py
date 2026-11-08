"""This repository's own `.prd-toolkit/` is the plugin's bytes: CI's `check --ci` compares only the generated CI files."""
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO = PLUGIN_ROOT.parent


def test_the_vendored_copy_matches_the_plugin():
    run = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts/prd_hooks.py"), "check", "docs/prd/prd-toolkit"],
                         cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=120)
    # TASK 9 REMOVES THIS FILTER: until it writes this repo's two READMEs, `check` reports them stale (exit 1)
    block_lines = [x for x in run.stdout.splitlines() if x.startswith(("stale: docs/prd/README.md;", "stale: docs/prd/prd-toolkit/README.md;"))]
    left = [x for x in run.stdout.splitlines() if x not in block_lines]
    assert run.returncode == (1 if block_lines else 0) and not left and not run.stderr, run.stdout + run.stderr  # refresh it with the vendor-only snippet
