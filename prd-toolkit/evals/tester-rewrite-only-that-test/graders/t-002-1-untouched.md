---
type: regex
pattern: '^from notes\.app import add_note, search_notes\n\n\ndef test_search_ignores_case\(\):\n    """@prd T-002\.1"""\n    add_note\("Buy Milk"\)\n    add_note\("call bob"\)\n    assert search_notes\("milk"\) == \["Buy Milk"\]\n$'
target: { source: file, path: tests/test_t002.py }
---

T-002.1's case did not change, so its test file is byte for byte what the scaffold wrote: only the test named on
the `Rewrite:` line may change. (It fails against the code, which is case-sensitive; that is a `fail` to report,
never a reason to touch the test.)
