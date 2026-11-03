---
type: tool_used
tool: Bash
input_match: '"command"\s*:\s*"(?!uv run --script \S*prd_links\.py\s)(?:[^"\\]|\\.)*?(?:\bsed\s+-i\S*\s(?:[^"\\]|\\.)*?contracts/upstream/|\bperl\s+(?:-\S+\s+)*-\S*i\S*\s(?:[^"\\]|\\.)*?contracts/upstream/|\b(?:cp|mv|install|rsync)\s(?:[^"\\]|\\.)*?contracts/upstream/|>>?\s*(?:\\"|'')?(?:[^\s"''\\]*/)?contracts/upstream/|\btee\s+(?:-a\s+)?(?:\\"|'')?(?:[^\s"''\\]*/)?contracts/upstream/|contracts/upstream/(?:[^"\\]|\\.)*?\.(?:write_text|write_bytes|write)\(|\bopen\(\s*(?:\\"|'')?(?:[^\s"''\\]*/)?contracts/upstream/[^,)]*,\s*(?:\\"|'')?[wa])'
min: 0
max: 0
---

No write under `contracts/upstream/` through Bash either (`sed -i`, a `>` or `>>` redirect, `tee`, a Python one-off). A `prd_links.py` call is never counted: `sync` is the tool that writes the snapshot, and its text may quote a path. Fails on `sed -i s/x/y/ docs/prd/greet-client/contracts/upstream/greet/cli.yaml`, `perl -pi -e s/x/y/ <snapshot file>`, `cp /tmp/x docs/prd/greet-client/contracts/upstream/greet/cli.yaml`, `mv` (or `install`, `rsync`) into that folder, a redirect or `tee` into it, and a Python `open(<snapshot file>, 'w')` or `.write_text(`.
