---
type: regex
target: trace
pattern: 'prd-lint-exit=0'
---

The PRD lint run ended with exit 0, so `ac-ears` accepted every AC under the PRD's `language:`. The skills
never hold the literal, so the skill text loaded into the trace cannot pass it.
