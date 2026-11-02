---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?!uv run --script \S*prd_links\.py\s)(?:[^"\\]|\\.)*?(?:\bsed\s+-i\S*\s(?:[^"\\]|\\.)*?contracts/upstream/|>>?\s*(?:\\"|'')?(?:[^\s"''\\]*/)?contracts/upstream/|\btee\s+(?:-a\s+)?(?:\\"|'')?(?:[^\s"''\\]*/)?contracts/upstream/|contracts/upstream/(?:[^"\\]|\\.)*?\.(?:write_text|write_bytes|write)\()'
min: 0
max: 0
---

No write under `contracts/upstream/` through Bash either (`sed -i`, a `>` or `>>` redirect, `tee`, a Python one-off). A `prd_links.py` call is never counted: `sync` is the tool that writes the snapshot, and its text may quote a path. Fails on `sed -i s/x/y/ docs/prd/greet-client/contracts/upstream/greet/cli.yaml`.
