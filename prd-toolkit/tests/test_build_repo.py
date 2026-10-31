"""The build_repo eval scaffold: the notes PRD Approved at 1.1.0 with FR-003 approved, unimplemented."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "evals/scaffolds/build_repo.py"
LINT = ROOT / "scripts/prd_lint.py"
PLUGINS_FILE = Path(__file__).parent / "fixtures/installed_plugins.json"


def test_build_repo_is_a_clean_approved_prd_with_fr_003_unimplemented(tmp_path):
    dst = tmp_path / "repo"
    subprocess.run([sys.executable, "-B", str(SCRIPT), str(dst)], check=True, capture_output=True, text=True)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=dst, capture_output=True, text=True).stdout.strip()
    assert branch == "base"
    prd = dst / "docs/prd/notes"
    assert "Status: approved" in (prd / "features/notes.md").read_text(encoding="utf-8").split("### FR-003")[1]
    assert "| FR-003 | Count notes | approved |" in (prd / "prd.md").read_text(encoding="utf-8")
    assert "count_notes" not in "".join(p.read_text(encoding="utf-8") for p in (dst / "src").rglob("*.py"))
    env = {**os.environ, "PRD_PLUGINS_FILE": str(PLUGINS_FILE)}
    r = subprocess.run(["uv", "run", "--script", str(LINT), str(prd)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
