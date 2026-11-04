"""`base`: the orders fixture's one required skill row made `recommended`, since the eval sandbox has no installed
plugins and lint would fail on it. `change`: a change edited and not yet approved, a new AC-001.4 (with a doubled
"the" for the prompt's "just fix the AC") and its unit case T-001.5, the PRD In review."""
import sys
from pathlib import Path

r, state = Path(sys.argv[1]), sys.argv[2]


def sub(rel, old, new):
    p = r / rel
    s = p.read_text()
    assert s.count(old) == 1, (rel, old, s.count(old))
    p.write_text(s.replace(old, new))


if state == "base":
    sub("prd.md", "| plans | superpowers:writing-plans | required |", "| plans | superpowers:writing-plans | recommended |")
    sys.exit(0)
assert state == "change", state
sub("features/import.md", "  log `IMPORT_EMPTY` and insert no rows.\n",
    "  log `IMPORT_EMPTY` and insert no rows.\n"
    "- AC-001.4 When an import file holds a blank line between two rows, the importer shall skip the\n"
    "  the blank line and import the other rows.\n")
sub("features/import.md", "T-001.4 [acceptance]  (test-cases/import.yaml)",
    "T-001.4 [acceptance], T-001.5 [unit]  (test-cases/import.yaml)")
sub("prd.md", "status: Approved", "status: In review")
p = r / "test-cases/import.yaml"
p.write_text(p.read_text().rstrip("\n") + "\n" + """
T-001.5:
  ac: AC-001.4
  level: unit
  target: code:importer.import_file
  environment: local
  identity: none
  preconditions: []
  input:
    content: "order_key,customer_id\\nK-1,1\\n\\nK-2,1\\n"
  expect:
    output: {status: done, inserted: 2, skipped: 0}
    effects:
      - "orders: two rows written"
    errors: []
    leaks: none
""")
