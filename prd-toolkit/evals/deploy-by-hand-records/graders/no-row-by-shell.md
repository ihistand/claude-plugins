---
type: tool_used
tool: Bash
input_match: '>>?\s*["'']?\S*operations\.md|\btee\s+(?:-a\s+)?["'']?\S*operations\.md|\bsed\s+-i[\s\S]*operations\.md|\bperl\s+-\S*i[\s\S]*operations\.md|operations\.md[\s\S]*\b(?:write_text|write)\(|\b(?:write_text|write)\([\s\S]*operations\.md'
min: 0
max: 0
---

No Deployed row written by hand from the shell: no redirect, `tee`, `sed -i`, `perl -i` or Python write to
operations.md.
