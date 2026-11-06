---
type: regex
pattern: '(?:\bimport\w*\b[^\n]*(?:packs/ledger|vendored pack|ledger pack)|(?:packs/ledger|vendored pack|ledger pack)[^\n]*\bimport\w*\b)'
flags: i
target: last_message
---

The report says the test imports `stored_notes` from the vendored `ledger` pack, as the pack's harness says.
