---
type: tool_used
tool: Grep
input_match: '"path"\s*:\s*"(?:[^"]*/)?tests(?:/(?!\.prd-dry-run-)[^"]*)?/?"|"glob"\s*:\s*"(?:[^"]*/)?tests/(?!\.prd-dry-run-)|^(?![\s\S]*"path"\s*:)\{[\s\S]*\}$'
min: 0
max: 0
---

A dry run does not search the test root. No Grep whose `path` is `tests/` or under it outside
`tests/.prd-dry-run-*` (absolute or relative), whose `glob` reaches into `tests/` outside it, or that
has no `path` at all (it then searches the whole repository, test root included).
