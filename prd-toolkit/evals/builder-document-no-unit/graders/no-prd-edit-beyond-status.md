---
type: tool_used
tool: Edit
input_match: '^(?!.*"new_string"\s*:\s*"(?:Source: [^"\\]*(?:\\n)?"|(?:[^"\\]|\\.)*(?:Status: (?:built|verified)|\| (?:built|verified) \|)))(?!.*"old_string"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"new_string"\s*:\s*"\1(?:\\n)?Source: [^"\\]*(?:\\n)?")(?=.*"file_path"\s*:\s*"[^"]*docs/prd/)'
min: 0
max: 0
---

No Edit under `docs/prd/` except the caller's close (a `Status: built`/`verified` move, the §11 row's
`| built |`/`| verified |`, or a `Source:` line), as in `builder-stays-out-of-prd`.
