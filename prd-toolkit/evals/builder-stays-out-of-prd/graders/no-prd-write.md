---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*docs/prd/'
min: 0
max: 0
---

No Write creates or replaces a file under `docs/prd/`. These graders see every Write and Edit of the
run, the builder's and the caller's, because a tool call carries no agent id. The caller never writes
a PRD file (it only edits a status, below), so any Write there is the builder's.
