---
type: regex
pattern: '"greet"\s*:\s*\{[^{}]*"FR-00[12]"'
match: contains
target: { source: file, path: greet-prd-1.0.0.summaries.json }
---

The summaries file the skill names holds a summary of the `greet` area citing its own IDs. A run that
writes no summaries file (RED's U1) fails: a missing file is an error (observed in the 0.6 without-plugin run).
