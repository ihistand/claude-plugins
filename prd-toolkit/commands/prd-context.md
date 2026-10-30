---
description: Print the focused context pack for one PRD task (prd-toolkit)
---

Print the prd-toolkit context pack. Arguments: $ARGUMENTS

1. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
2. Map the arguments. A token that starts with `UJ-`, `FR-`, `NFR-`, `AC-`, `T-` or `E-` is an
   ID, never the area. The first argument that is neither an ID nor `implement` is the area: pass
   it as `--area <area>`. Pass only UJ, FR, NFR and E IDs, together as one `--req <ID>[,<ID>…]`:
   an AC or T id maps to its FR (`AC-005.2` and `T-005.1` map to `FR-005`), and an `E-nnn`
   passes as it is (the pack adds its `errors.md` entry and the blocks it reaches). The word `implement` becomes `--for implement`. Given
   IDs with no area, find the area each ID's block lives in from the repo pack, or ask. With no
   area and no IDs, the pack is the repo pack: the stack and one line per area.
3. Run the script in one Bash call, with the literal PRD folder:
   `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs> --for implement; echo "prd-context-exit=$?"`
   Leave out the options the arguments did not give. `--req` and `--for implement` both need `--area`.
   Never pipe, filter or truncate the pack's output (no `| head`, no `| grep`): `prd-context-exit=`
   then reports the filter's status, not the pack's.
4. Print the output as it is, and work from it.
5. On `prd-context-exit=1`, at least one source is STALE: re-read the regions marked STALE
   before relying on them. On `prd-context-exit=2`, the call was wrong and nothing printed:
   fix the arguments.
