---
type: regex
pattern: '- AC-001\.4 When an import file holds a blank line between two rows, the importer shall skip the\n  the blank line and import the other rows\.\n'
target: { source: file, path: docs/prd/orders/features/import.md }
---

The AC the prompt asks to fix is unchanged, its doubled "the" included: the review answers the request in its
report and edits nothing. With the next grader, this stands in for `git diff --stat -- docs/prd` being unchanged,
which no grader type can run; the run's kept scaffold is checked with that command by hand.
