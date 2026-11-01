---
type: regex
pattern: 'AC-003\.1 When `notes\.app\.count_notes\(\)` is called on a store holding notes, it shall return the number of stored notes\.\n- AC-003\.2 When `notes\.app\.count_notes\(\)` is called on an empty store, it shall return `0`\.\n'
match: contains
target: { source: file, path: docs/prd/notes/features/notes.md }
---

FR-003's acceptance criteria read as the PRD approved them: the builder did not reword an AC to fit
its code, by any tool.
