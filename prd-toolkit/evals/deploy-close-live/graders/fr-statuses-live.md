---
type: regex
pattern: '### FR-001 [^\n]*\nStatus: live \(since 1\.0\.0\)\n(?:[\s\S]*)### FR-002 [^\n]*\nStatus: live \(since 1\.0\.0\)\n'
match: contains
target: { source: file, path: docs/prd/greet/features/greet.md }
---

After the production finish both blocks read `Status: live (since 1.0.0)`.
