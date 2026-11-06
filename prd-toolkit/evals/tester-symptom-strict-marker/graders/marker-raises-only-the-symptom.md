---
type: regex
pattern: '"name":"(?:Write|Edit)","input":\{(?:"replace_all":(?:true|false),)?"file_path":"[^"]*tests/[^"]*\.py",(?:"old_string":"(?:[^"\\]|\\.)*",)?"(?:content|new_string)":"(?=(?:[^"\\]|\\.)*@prd T-002\.1 known-failing E-001)(?=(?:[^"\\]|\\.)*xfail\([^)]*strict\s*=\s*True)(?=(?:[^"\\]|\\.)*raises\s*=\s*(?!AssertionError\b|Exception\b|BaseException\b)([A-Za-z_]\w*))(?=(?:[^"\\]|\\.)*\braise\s+\1\b)(?=(?:[^"\\]|\\.)*search_notes\()'
target: trace
---

One Write (or Edit, whose input may lead with `replace_all`) of a `tests/*.py` file holds T-002.1's test: it cites `@prd T-002.1 known-failing E-001`, is marked
`xfail(strict=True, ...)` with `raises=<X>` where `<X>` is neither `AssertionError` nor `Exception`/`BaseException`,
calls `search_notes(`, and raises that same `<X>` itself (`raise <X>`). Every lookahead is held inside that one call's
`content` (or `new_string`) string, so text elsewhere in the trace cannot satisfy it. The tester picks the test file's
name (the first RED run wrote `tests/test_search.py`), so the grader reads the trace, not a file. The unchanged text
writes `xfail(strict=True)` alone, so it fails on it.
