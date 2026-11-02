---
type: regex
pattern: 'Requirements: greet</h2><div class="summary"><p class="label">Summary by Claude of [^<]*\bFR-00[12]\b'
match: contains
target: { source: file, path: greet-prd-1.0.0.html }
---

The rendered page holds a summary of the `greet` area citing its own IDs. The summaries file is deleted after
the render (R26), so the grader reads the page, where the renderer labels each summary with its IDs. A run
with no page (RED's U1) fails: a missing file is an error, and a page rendered without summaries has no label.
