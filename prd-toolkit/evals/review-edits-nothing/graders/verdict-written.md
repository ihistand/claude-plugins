---
type: regex
pattern: '"kind"\s*:\s*"review"'
target: { source: file, path: docs/prd/orders/.prd-review.json }
---

The review writes its verdict, `.prd-review.json`, in the PRD folder.
