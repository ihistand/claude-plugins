---
type: tool_used
tool: Write
input_match: '^(?=[\s\S]*"file_path"\s*:\s*"[^"]*tests/)(?=[\s\S]*T-010\.2)(?=[\s\S]*(?:Each step in Install|names one action|does not list))'
min: 0
max: 0
---

The judged test does not copy rubric items into its own assertions: the rubric stays in the test case and
the grader scores it.
