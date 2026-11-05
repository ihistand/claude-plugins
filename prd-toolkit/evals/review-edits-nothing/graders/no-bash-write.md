---
type: tool_used
tool: Bash
input_match: 'sed -i|perl -i|>>?\s*\S*docs/prd/orders/(?!\.prd-review\.json)|tee \S*docs/prd|git (?:commit|stash|checkout|restore|reset)\b|prd_change\.py\S* (?:record|approve)'
min: 0
max: 0
---

No Bash call writes the PRD (an in-place edit, a redirect to a PRD file other than the verdict, `tee`), touches
git's tree or index (`commit`, `stash`, `checkout`, `restore`, `reset`), or runs `record` or `approve`.
