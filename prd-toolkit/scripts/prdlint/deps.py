"""Optional-import helper: a missing dependency prints an install hint and exits 2."""
import importlib
import sys
from pathlib import Path


def require(module: str, package: str):
    try:
        return importlib.import_module(module)
    except ImportError:
        script = Path(sys.argv[0]).name or "<script>"
        print(
            f"prd_lint: missing Python package '{package}'. Run with: uv run --script {script} …, "
            "or: pip install pyyaml sqlglot openapi-spec-validator",
            file=sys.stderr,
        )
        sys.exit(2)
