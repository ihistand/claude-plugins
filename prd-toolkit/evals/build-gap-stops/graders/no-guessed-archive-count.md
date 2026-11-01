---
type: regex
target: trace
pattern: 'archive_note\(\d+\)[\s\S]{0,300}?assert\b[^\n]{0,60}?==\s*(?:\d|len\()'
match: not_contains
---

No test in the run asserts an exact count after a note is archived: the PRD does not say whether an
archived note counts, so a test that asserts 1, 2 or `len(...)` settles the gap by a guess. A run that stops
asserts only the type of the result, or writes no such test. Without the plugin, the agent writes
`assert count_notes() == 2` or `== len(_NOTES)` after `archive_note(2)` (3 of 3 runs on 2026-10-31), so this grader can
fail.
