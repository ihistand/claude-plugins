---
type: regex
pattern: 'Source: src/notes/[^\s:]+:\d+ @[0-9a-f]{7,40}'
target: { source: file, path: docs/prd/notes/features/notes.md }
---

The notes area was extracted into its feature file: `docs/prd/notes/features/notes.md` holds at
least one requirement with a checked `Source: <file>:<line> @<commit>` line into `src/notes/`. The
prompt names the folder, so the path is fixed. Renaming the template's `features/core.md` (the
bound step) leaves no such line, and neither does a flat `docs/prd/notes.md`, so neither passes.
