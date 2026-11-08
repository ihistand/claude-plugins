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


def lint(root: Path) -> list:
    """Run every registered rule against the PRD at `root`."""
    from prdlint import model, registry

    return registry.run(model.load(root))


def fired(findings) -> set[str]:
    return {f.rule for f in findings}


@pytest.fixture
def ctx(tmp_path, monkeypatch) -> Path:
    """The context-pack PRD (tests/context_fixture.py) at tmp_path/docs/prd/orders."""
    from context_fixture import context_prd

    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    return context_prd(tmp_path)


# -- the PRD-facts fixtures (greet, orders, notes), each a copy of the valid fixture under tmp_path/docs/prd/<slug> --

_SECTION_2 = "## 2. Summary & goals\n"
_TEMPLATE_COMMENT = ("<!-- Optional parts, after Goals, Personas and Out of scope: `Principles:` and "
                     "`Getting started:`. A PRD without them is complete. -->")


def _facts_prd(tmp_path: Path, monkeypatch, slug: str, section2: str, extra_frontmatter: str = "") -> Path:
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(PLUGINS_FILE))
    dest = tmp_path / "docs/prd" / slug
    shutil.copytree(FIXTURE, dest)
    text = (dest / "prd.md").read_text()
    head, rest = text.split(_SECTION_2, 1)
    _, tail = rest.split("## 3. Glossary", 1)
    head = head.replace("prd: orders", f"prd: {slug}").replace("sql-dialect: postgres", "sql-dialect: postgres" + extra_frontmatter)
    (dest / "prd.md").write_text(head + _SECTION_2 + "\n" + section2.strip("\n") + "\n\n## 3. Glossary" + tail)
    return dest


@pytest.fixture
def greet(tmp_path, monkeypatch) -> Path:
    """Both §2 parts, an adoption map for two areas, one open error and no links.md."""
    dest = _facts_prd(tmp_path, monkeypatch, "greet", """
The greet service says hello to a named person
and counts how often it did. It is small.

Goals:

- Answer a greeting within 100 ms.

Personas: a visitor.

Principles:

- **Plain.** One call, one answer.
- **Counted.** Every greeting is stored.

Out of scope: farewells.

Getting started:

1. Install the service.
2. Call `GET /hello/<name>`.
""")
    (dest / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n"
                                      "| api | adopted | `src/api/**` |\n| import | confirmed | `src/import/**` |\n")
    edit(dest, "prd.md", "Not applicable: new project.", "See adoption.md.")
    (dest / "errors.md").write_text((dest / "errors.md").read_text()
                                    + "\n### E-002 A name with a space is cut\nDetected: 2026-11-01, manual\n"
                                      "Classification: unclassified\nResolution: open\n")
    return dest


@pytest.fixture
def orders(tmp_path, monkeypatch) -> Path:
    """A Spanish PRD: Principios and Primeros pasos, links.md with a relative path and a git URL, no adoption.md."""
    dest = _facts_prd(tmp_path, monkeypatch, "orders", """
El servicio de pedidos importa archivos del almacén.

Objetivos:

- Importar 10 000 filas en menos de 60 segundos.

Principios:

- **Idempotente.** Una fila repetida se omite.

Primeros pasos:

1. Instale el servicio.
2. Importe un archivo.
""", "\nlanguage: es")
    (dest / "links.md").write_text(
        "# Links\n\n## Upstreams\n\n| Upstream | Location | Version | Commit | Needs |\n|---|---|---|---|---|\n"
        "| billing | `../billing` | | | |\n\n## Consumers\n\n| Consumer | Location |\n|---|---|\n"
        "| reports | `https://example.com/acme/reports.git#reports` |\n")
    return dest


@pytest.fixture
def notes(tmp_path, monkeypatch) -> Path:
    """Neither §2 part; §2 opens on the template's HTML comment; no adoption.md, no links.md, no open errors."""
    return _facts_prd(tmp_path, monkeypatch, "notes", _TEMPLATE_COMMENT + """

The notes service stores short notes. It has no accounts! Anyone may read them?

Goals:

- Store a note in under 50 ms.
""")
