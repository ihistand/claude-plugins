---
description: Print the focused context pack for one PRD task (prd-toolkit)
---

Print the prd-toolkit context pack. Arguments: $ARGUMENTS

1. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
2. Map the arguments. The first argument that is neither an ID (`FR-005`, `NFR-002`) nor
   `implement` is the area: pass it as `--area <area>`. Every ID argument goes into one
   `--req <ID>[,<ID>…]`. The word `implement` becomes `--for implement`. With no area, the
   pack is the repo pack: the stack and one line per area.
3. Run the script in one Bash call, with the literal PRD folder:
   `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"`
   Leave out the options the arguments did not give. `--req` and `--for implement` both need `--area`.
4. Print the output as it is, and work from it.
5. On `prd-context-exit=1`, at least one source is STALE: re-read the regions marked STALE
   before relying on them. On `prd-context-exit=2`, the call was wrong and nothing printed:
   fix the arguments.
