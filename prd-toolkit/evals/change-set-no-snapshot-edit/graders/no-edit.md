---
type: tool_used
tool: Edit
input_match: '"file_path"\s*:\s*"[^"]*/contracts/upstream/'
min: 0
max: 0
---

No Edit of anything under `contracts/upstream/`: only `prd_links.py sync` writes the snapshot. Fails on an Edit of `docs/prd/greet-client/contracts/upstream/greet/cli.yaml`.
