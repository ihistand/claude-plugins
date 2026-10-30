"""Shared helpers for prd_context.py tests: an adopted, two-area PRD and a pack runner."""
import contextlib
import io
import re
import shutil
from pathlib import Path

from conftest import FIXTURE, edit, lint

ADOPTION = "# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/import/**` |\n| api | confirmed | `src/api/**` |\n"


def _entry(eid: str, title: str, touches: str | None) -> str:
    touch = f"Touches: {touches}\n" if touches else ""
    return f"\n### {eid} {title}\nDetected: 2026-10-30, review\nClassification: code bug\n{touch}Diagnosis: under review\nResolution: open\nRecurrence of: -\n"


def context_prd(tmp_path: Path) -> Path:
    """The valid fixture at tmp_path/docs/prd/orders, adopted, with entries in every part a pack draws on."""
    root = tmp_path / "docs/prd/orders"
    shutil.copytree(FIXTURE, root)
    (root / "adoption.md").write_text(ADOPTION)
    edit(root, "prd.md", "Not applicable: new project.", "See adoption.md.")
    edit(root, "features/api.md", "Traces: UJ-01; `orders.id`", "Traces: UJ-01; NFR-004; `orders.id`")
    edit(root, "prd.md", "| customer | The person or company an order belongs to | client |\n",
         "| customer | The person or company an order belongs to | client |\n"
         "| importer | The job that loads an orders file | loader |\n"
         "| invoice | A bill sent after shipping | bill |\n")
    errors = root / "errors.md"
    errors.write_text(errors.read_text()
                      + _entry("E-002", "Duplicate check ignores case", "FR-001")
                      + _entry("E-003", "Lookup returns deleted orders", "FR-002")
                      + _entry("E-004", "Logs carry no request id", None))
    edit(root, "prd.md", "## 13. Open questions\n\nNone.\n", "## 13. Open questions\n\n"
         "- Q-01 Should FR-001 skip blank rows?\n"
         "- Q-02 Does the import area accept CSV only?\n"
         "- Q-03 Is AC-002.1 still wanted?\n"
         "- Q-04 Who owns the product?\n"
         "- Q-05 Should import-batch retry?\n")
    rows = "".join(f"| {v} | 2026-10-30 | {c} | {i} |\n" for v, c, i in (
        ("1.1.0", "import: blank rows", "FR-001"),
        ("1.2.0", "api: 410 for deleted", "FR-003"),
        ("1.3.0", "import: trim keys", "FR-001"),
        ("1.4.0", "import: log the file name", "FR-001"),
        ("1.5.0", "import: reject a missing header", "FR-001")))
    prd_md = root / "prd.md"
    prd_md.write_text(prd_md.read_text().rstrip("\n") + "\n" + rows)
    edit(root, "prd.md", "version: 1.0.0", "version: 1.5.0")
    edit(root, "prd.md", "status: Approved", "status: In review")  # open-questions-empty: an Approved PRD has no §13 items
    assert lint(root) == [], lint(root)
    return root


def pack(root: Path, *args: str) -> tuple[int, str, str]:
    """Run prd_context.main on `root`; return (exit code, stdout, stderr)."""
    from prd_context import main

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(root), *args])
    return code, out.getvalue(), err.getvalue()


def parts(stdout: str) -> dict[str, str]:
    """{part name: its text} for each `## <part>` heading of a text pack."""
    chunks = re.split(r"^## (.+)$", stdout, flags=re.M)
    return {chunks[i].strip(): chunks[i + 1] for i in range(1, len(chunks), 2)}
