---
type: regex
pattern: '\nprd: greet\nversion: (?!1\.0\.2\n)[^\n]*\nstatus: In review\n'
match: contains
target: { source: file, path: docs/prd/greet/prd.md }
---

The hand-off to `/prd-change-set` is a stop with the edit in the tree and nothing committed (changing-prds step 4: the text names the command, no tool call carries it), so greet's PRD ends at a bumped version, `In review`. Fails if the PRD was never edited, was approved, or was reset to its 1.0.2 start.
