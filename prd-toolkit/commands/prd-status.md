---
description: Print where every requirement of the PRD stands (prd-toolkit)
---

Print the prd-toolkit status report. Arguments: $ARGUMENTS

1. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
2. Run the script in one Bash call, with the literal PRD folder:
   `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_status.py" docs/prd/<slug>; echo "prd-status-exit=$?"`
   Add `--json` only when asked for JSON. Never pipe, filter or truncate the output (no `| head`,
   no `| grep`): `prd-status-exit=` then reports the filter's status, not the script's.
3. Print the output as it is. The report has eight parts: Header, Requirements, Adoption map,
   Not built, Not verified, Open errors, Deployed and Matrix. It is read-only.
4. On `prd-status-exit=2`, the call was wrong and nothing printed: fix the path.
