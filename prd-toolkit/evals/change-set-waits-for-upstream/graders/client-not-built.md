---
type: regex
pattern: 'Status: (?:built|verified) \(since 1\.1\.0\)'
match: not_contains
target: { source: file, path: docs/prd/greet-client/features/welcome.md }
---

FR-001 of the client stays `approved (since 1.1.0)`: no build moved it. Fails once a build marks it `built` or `verified` since 1.1.0.
