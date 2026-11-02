---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?:[^"\\]|\\.)*?(?:\bsed\s+-i\S*\s(?:[^"\\]|\\.)*?(?:src|tests)/|>>?\s*(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/|\btee\s+(?:-a\s+)?(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/|(?:src|tests)/(?:[^"\\]|\\.)*?\.(?:write_text|write_bytes|write)\(|\bopen\(\s*(?:\\"|'')?(?:[^\s"''\\]*/)?(?:src|tests)/[^,)]*,\s*(?:\\"|'')?[wa])'
min: 0
max: 0
---

No write under `src/` or `tests/` through Bash either (`sed -i`, a `>` or `>>` redirect, `tee`, a Python one-off that writes): RED's E5 fixed the code that way.
