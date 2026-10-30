---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*/tests/\.prd-dry-run-[^"/]+/'
min: 1
---

The run is a dry run: the tester writes its tests into its own `tests/.prd-dry-run-*` directory.
Only the tester writes there, so this pass also shows that the `max: 0` graders see the tester's
own tool calls, not only the caller's.
