---
type: regex
pattern: '^(?=[\s\S]*@prd T-001\.1)(?=[\s\S]*\badd_note\()(?=[\s\S]*"call bob"[\s\S]*==\s*2\b)(?![\s\S]*(?:==\s*1\b|skip|xfail))[\s\S]*$'
target: { source: file, path: tests/test_t001.py }
---

T-001.1's test now adds the note `call bob` through any `add_note(...)` call form and expects id 2 (the corrected
case), still cites `@prd T-001.1`, no longer asserts `== 1`, and holds no `skip` or `xfail`. The unchanged test
asserts `== 1`, so this fails on it.
