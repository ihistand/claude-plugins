"""Turn a copy of the orders fixture into C2's start: FR-003 removed in 2.0.0, deleteOrder gone."""
import re, sys
from pathlib import Path
r = Path(sys.argv[1])
def sub(rel, old, new, count=1):
    p = r / rel; s = p.read_text()
    assert s.count(old) == count, (rel, old, s.count(old))
    p.write_text(s.replace(old, new))
# index row, version, changelog
sub("prd.md", "| FR-003 | Delete an order | live | features/api.md | 1.0.0 |", "| FR-003 | Delete an order | removed | features/api.md | 1.0.0 |")
sub("prd.md", "version: 1.0.0", "version: 2.0.0")
sub("prd.md", "| 1.0.0 | 2026-10-29 | Initial release | UJ-01, FR-001, FR-002, FR-003, NFR-004 |",
    "| 1.0.0 | 2026-10-29 | Initial release | UJ-01, FR-001, FR-002, FR-003, NFR-004 |\n| 2.0.0 | 2026-10-29 | Removed order deletion | FR-003 |")
sub("prd.md", "lets sales reps look up\nand admins delete orders through an HTTP API.", "lets sales reps and admins\nlook up orders through an HTTP API.")
sub("prd.md", "Personas: a sales rep (looks up own orders) and an admin (also deletes orders).", "Personas: a sales rep (looks up own orders) and an admin (looks up any order).")
sub("prd.md", "The API reads and deletes orders.", "The API reads orders.")
# block
sub("features/api.md", "### FR-003 Delete an order\nStatus: live (since 1.0.0)", "### FR-003 Delete an order\nStatus: removed (since 2.0.0)")
sub("features/api.md", "Tests: T-003.1 [integration], T-003.2 [integration]  (test-cases/api.yaml)", "Tests: -")
sub("features/api.md", "Errors: FORBIDDEN (contracts/errors.yaml)", "Errors: -")
sub("features/api.md", "Traces: FR-002, FR-003", "Traces: FR-002")
# test cases
p = r / "test-cases/api.yaml"; s = p.read_text()
s = re.sub(r"(?ms)^T-003\.1:\n.*", "", s).rstrip("\n") + "\n"
p.write_text(s)
# openapi: drop delete op
p = r / "contracts/openapi.yaml"; s = p.read_text()
s = re.sub(r"(?ms)^    delete:\n.*?(?=^components:)", "", s)
s = s.replace("description: Look up and delete orders.", "description: Look up orders.")
p.write_text(s)
# permissions, errors, observability
sub("contracts/permissions.yaml", "  deleteOrder: {allow: [admin], deny: [rep]}\n", "")
p = r / "contracts/errors.yaml"; s = p.read_text()
s = re.sub(r"(?ms)^FORBIDDEN:\n.*?(?=^GEOCODER_TIMEOUT:)", "", s); p.write_text(s)
sub("nfr.md", "| orders_forbidden_total | FORBIDDEN | more than 20 in 5 minutes |\n", "")
