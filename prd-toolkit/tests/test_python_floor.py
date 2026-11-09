"""Every script declares a Python floor; the plugin's code and its vendored copy must compile on that floor."""
import os
import re
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPO = PLUGIN_ROOT.parent


def _floor() -> str:
    """The `requires-python = ">=X.Y"` every uv script header declares, as `X.Y`."""
    floors = set()
    for script in sorted((PLUGIN_ROOT / "scripts").glob("prd_*.py")):
        text = script.read_text(encoding="utf-8")
        if "# /// script" not in text:
            continue
        m = re.search(r'^# requires-python = ">=(\d+\.\d+)"$', text, re.M)
        assert m, f"{script.name}: no requires-python line in its script header"
        floors.add(m.group(1))
    assert floors, "no script declares a floor"
    assert len(floors) == 1, f"the scripts declare different floors: {sorted(floors)}"
    return floors.pop()


@pytest.mark.parametrize("rel", ["prd-toolkit/scripts", ".prd-toolkit", "prd-toolkit/tests", "prd-toolkit/evals"])
def test_the_code_compiles_on_the_declared_python_floor(rel, tmp_path):
    run = subprocess.run(["uv", "run", "--python", _floor(), "--no-project", "python", "-m", "compileall", "-q", "-f", rel],
                         cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=600,
                         env={**os.environ, "PYTHONPYCACHEPREFIX": str(tmp_path / "pyc")})
    assert run.returncode == 0, run.stdout + run.stderr
