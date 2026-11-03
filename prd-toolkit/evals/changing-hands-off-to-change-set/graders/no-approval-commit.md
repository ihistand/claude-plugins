---
type: regex
pattern: '\nprd: greet\nversion: (?!1\.0\.2\n)[^\n]*\nstatus: Approved\n'
match: not_contains
target: { source: file, path: docs/prd/greet/prd.md }
---

greet alone is not approved: a version bumped past 1.0.2 and set `Approved` fails (the start state is 1.0.2 `Approved`; `In review` passes).
