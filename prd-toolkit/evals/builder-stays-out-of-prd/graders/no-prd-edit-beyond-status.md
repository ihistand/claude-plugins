---
type: tool_used
tool: Edit
input_match: '^(?!.*"new_string"\s*:\s*"(?:Source: [^"\\]*(?:\\n)?"|(?:[^"\\]|\\.)*(?:Status: (?:built|verified)|\| (?:built|verified) \|)))(?!.*"old_string"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"new_string"\s*:\s*"\1(?:\\n)?Source: [^"\\]*(?:\\n)?")(?=.*"file_path"\s*:\s*"[^"]*docs/prd/)'
min: 0
max: 0
---

No Edit under `docs/prd/` except the caller's close: an edit whose `new_string` writes `Status: built`
or `Status: verified` (or the §11 row's `| built |` / `| verified |`), or a `Source:` line. The
builder writes none of these, so any other Edit of a PRD file is a PRD edit by the builder.
Checked in `tests/test_eval_graders.py` against hand-made inputs. A Bash edit of the PRD (`sed -i`)
is caught by the two file graders below, which read the result.
