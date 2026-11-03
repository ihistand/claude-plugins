---
type: regex
target: trace
pattern: 'prd-lint-exit=0'
---

The PRD lint run ended with exit 0. With `outline.yaml` on disk, that needs a pack that declares `outline`
named in section 1 or a `Target:` line (otherwise `contracts-valid` reports the type). The skills never hold
the literal, so the skill text loaded into the trace cannot pass it.
