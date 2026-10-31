---
description: Build an approved PRD change with prd-builder and prd-tester, reconcile each failure by quote, and move its requirements to built and verified (prd-toolkit)
---

Build an approved PRD change. Arguments, `<area> <IDs>`: $ARGUMENTS

1. Invoke the prd-toolkit:building-from-prds skill. You are the caller: never write the code or
   the tests yourself.
2. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
3. Map the arguments as `/prd-context` does. A token that starts with `UJ-`, `FR-`, `NFR-`, `AC-`,
   `T-` or `E-` is an ID; the first other token is the area. An AC or T-id maps to its FR
   (`AC-005.2` and `T-005.1` map to `FR-005`); an `E-nnn` passes as it is. With no area, find the
   area each ID's block lives in from the repo pack, or ask. With no IDs, ask: a build never
   guesses its scope.
4. Follow `${CLAUDE_PLUGIN_ROOT}/skills/building-from-prds/running-a-build.md` exactly, steps 1 to
   8, and report as its close says.
