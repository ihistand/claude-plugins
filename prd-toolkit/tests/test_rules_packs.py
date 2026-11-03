"""Failing cases for the pack, language and judged-case rules (0.8.0); each task that adds a rule appends here."""
from conftest import Case, edit

CASES = [
    Case("language-table", "unknown language", lambda root: edit(root, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: fr")),
]
