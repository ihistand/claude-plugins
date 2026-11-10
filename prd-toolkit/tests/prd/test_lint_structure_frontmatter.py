"""lint-structure FR-020 and FR-021: the prd.md frontmatter and the language table."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_structure_support import KnownFailure, Orders, check, symptom  # noqa: E402

P = "docs/prd/orders/prd.md"


def test_missing_owner(tmp_path, monkeypatch):
    """@prd T-020.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").delete(5)
    check(o.run(), exit=1, contains_line=f"{P}:1: frontmatter: missing key 'owner'", stderr="")


def test_no_frontmatter(tmp_path, monkeypatch):
    """@prd T-020.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").delete(1, 8)
    check(
        o.run(),
        exit=1,
        in_order=[
            f"{P}:1: frontmatter: missing key 'prd'",
            f"{P}:1: frontmatter: missing key 'version'",
            f"{P}:1: frontmatter: missing key 'status'",
            f"{P}:1: frontmatter: missing key 'owner'",
            f"{P}:1: frontmatter: missing key 'updated'",
        ],
        stderr="",
    )


def test_prd_not_lowercase(tmp_path, monkeypatch):
    """@prd T-020.3"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(2, "prd: Orders")
    check(o.run(), exit=1, contains_line=f"{P}:2: frontmatter: 'prd: Orders' must be a lowercase slug equal to the folder name 'orders'", stderr="")


def test_prd_not_folder_name(tmp_path, monkeypatch):
    """@prd T-020.4"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(2, "prd: sales")
    check(o.run(), exit=1, contains_line=f"{P}:2: frontmatter: 'prd: sales' must be a lowercase slug equal to the folder name 'orders'", stderr="")


def test_bad_version(tmp_path, monkeypatch):
    """@prd T-020.5"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(3, "version: 1.0")
    check(o.run(), exit=1, contains_line=f"{P}:3: frontmatter: 'version: 1.0' must be X.Y.Z, digits only", stderr="")


def test_bad_status(tmp_path, monkeypatch):
    """@prd T-020.6"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(4, "status: Done")
    check(o.run(), exit=1, contains_line=f"{P}:4: frontmatter: 'status: Done' must be Draft, In review or Approved", stderr="")


def test_empty_owner(tmp_path, monkeypatch):
    """@prd T-020.7"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(5, "owner:")
    check(o.run(), exit=1, contains_line=f"{P}:5: frontmatter: 'owner: ' must not be empty", stderr="")


def test_bad_updated(tmp_path, monkeypatch):
    """@prd T-020.8"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(6, "updated: 2026/10/29")
    check(o.run(), exit=1, contains_line=f"{P}:6: frontmatter: 'updated: 2026/10/29' must be YYYY-MM-DD", stderr="")


def test_bad_language(tmp_path, monkeypatch):
    """@prd T-020.9"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").insert_before(8, "language: EN")
    check(
        o.run(),
        exit=1,
        contains_line=f"{P}:8: frontmatter: 'language: EN' must match ^[a-z]{{2,3}}$",
        not_contains="language-table",
        stderr="",
    )


def test_sql_dialect_absent(tmp_path, monkeypatch):
    """@prd T-020.10"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").delete(7)
    check(o.run(), exit=1, contains_line=f"{P}:1: frontmatter: missing key 'sql-dialect' (required because contracts/schema.sql exists)", stderr="")


def test_sql_dialect_unknown(tmp_path, monkeypatch):
    """@prd T-020.11"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(7, "sql-dialect: nosuch")
    check(o.run(), exit=1, contains=f"{P}:7: frontmatter: 'sql-dialect: nosuch' is not a sqlglot dialect (", stderr="")


def test_sql_dialect_empty(tmp_path, monkeypatch):
    """@prd T-020.12"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").replace(7, "sql-dialect:")
    check(o.run(), exit=1, contains_line=f"{P}:7: frontmatter: missing key 'sql-dialect' (required because contracts/schema.sql exists)", stderr="")


def test_no_schema_no_dialect_check(tmp_path, monkeypatch):
    """@prd T-020.13"""
    o = Orders(tmp_path, monkeypatch)
    o.delete("contracts/schema.sql")
    o.lines("prd.md").delete(7)
    check(o.run(), exit=1, not_contains="sql-dialect", stderr="")


@pytest.mark.xfail(strict=True, raises=KnownFailure, reason="E-012")
def test_missing_owner_despite_later_line(tmp_path, monkeypatch):
    """@prd T-020.14 known-failing E-012"""
    o = Orders(tmp_path, monkeypatch)
    edit = o.lines("prd.md").delete(5).replace(53, "owner: ops")
    r = o.run()
    body = edit.text().splitlines().index("owner: ops") + 1
    symptom(
        f"{P}:{body}: frontmatter: missing key 'owner'" in r.stdout.splitlines(),
        "E-012",
        "the missing key is reported at the body line that starts with the key, not at prd.md:1",
        r,
    )
    check(r, exit=1, contains_line=f"{P}:1: frontmatter: missing key 'owner'", stderr="")


def test_language_without_table(tmp_path, monkeypatch):
    """@prd T-021.1"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").insert_before(8, "language: fr")
    check(o.run(), exit=1, contains_line=f"{P}:8: language-table: language 'fr' has no table", stderr="")


def test_language_with_table(tmp_path, monkeypatch):
    """@prd T-021.2"""
    o = Orders(tmp_path, monkeypatch)
    o.lines("prd.md").insert_before(8, "language: es")
    check(o.run(), not_contains="language-table", stderr="")
