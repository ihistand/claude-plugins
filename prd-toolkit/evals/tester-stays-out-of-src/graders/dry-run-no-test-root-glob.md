---
type: tool_used
tool: Glob
input_match: '^(?!.*"pattern"\s*:\s*"\.prd-dry-run-(?![^"]*\.\.))(?=.*"path"\s*:\s*"(?:[^"]*/)?tests(?:/(?!\.prd-dry-run-)[^"]*)?/?")|"pattern"\s*:\s*"(?:[^"]*/)?tests/(?!\.prd-dry-run-)|^\{\s*"pattern"\s*:\s*"(?:\*\*/)*\*(?!\*/)(?![^"]*\.prd-dry-run-)[^"]*"\s*\}$'
min: 0
max: 0
---

A dry run does not list the test root. No Glob whose `path` is `tests/` or under it outside
`tests/.prd-dry-run-*` (absolute or relative), whose pattern reaches into `tests/` outside it, or
that has no `path` and a pattern that starts with a wildcard (`**/*.py`, `**/*`): that lists the whole
repository, test root included. A pathless lookup by name (`**/prd-tester*`), a pattern under
`docs/prd/`, and the caller's stale-directory lookup for `.prd-dry-run-*` do not count, in either
form: the pattern `tests/.prd-dry-run-*/**`, or `path: tests` with a pattern that starts with
`.prd-dry-run-` and holds no `..`.

Hand-made inputs, each checked in `tests/test_eval_graders.py` with Python `re` (and checked once
by hand under Node's `RegExp`, with the same results): counted are `{pattern: **/*.py, path: tests}`, `{pattern: tests/**/*.py}`,
`{pattern: **/*}` and `{path: tests, pattern: .prd-dry-run-x/../test_notes.py}`; not counted are
`{path: tests, pattern: .prd-dry-run-*}` (keys in either order), `{pattern: tests/.prd-dry-run-*/**}`
and `{pattern: **/*, path: tests/.prd-dry-run-<ts>}`.
