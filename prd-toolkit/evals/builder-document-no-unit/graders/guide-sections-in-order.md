---
type: regex
pattern: '^#+ Requirements\b[\s\S]*^#+ Install\b[\s\S]*^#+ First run\b[\s\S]*^#+ Common problems\b'
flags: m
target: { source: file, path: docs/guide/install.md }
---

The guide's headings follow the outline's `sections`, in order: the builder wrote from the outline entry.
