---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?!uv run --script \S*prd_error\.py\s)(?:[^"\\]|\\.)*?(?:\bsed\s+-i\S*\s(?:[^"\\]|\\.)*?(?:src|tests)/|>>?\s*(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/|\btee\s+(?:-a\s+)?(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/|(?:src|tests)/(?:[^"\\]|\\.)*?\.(?:write_text|write_bytes|write)\(|\bopen\(\s*(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/[^,)]*,\s*(?:\\"|'')?[wa])'
min: 0
max: 0
---

No write under `src/` or `tests/` through Bash either (`sed -i`, a `>` or `>>` redirect, `tee`, a Python one-off that writes): RED's E5 fixed the code that way. A `prd_error.py` call is never counted: its text may quote a command it does not run.
