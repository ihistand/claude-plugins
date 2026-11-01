---
type: regex
pattern: '\|\s*FR-001\s*\|[^|\n]*\|\s*live\s*\|[^|\n]*\|\s*1\.0\.0\s*\|[\s\S]*\|\s*FR-002\s*\|[^|\n]*\|\s*live\s*\|[^|\n]*\|\s*1\.0\.0\s*\|'
match: contains
target: { source: file, path: docs/prd/greet/prd.md }
---

The §11 index rows move with the blocks.
