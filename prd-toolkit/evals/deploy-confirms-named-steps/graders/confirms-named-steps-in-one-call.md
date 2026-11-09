---
type: tool_used
tool: Bash
input_match: 'prd_deploy\.py(?:\\")?\s+confirm\b(?:[^"\\]|\\.)*?--step\s+2\b(?:[^"\\]|\\.)*?--step\s+3\b(?:[^"\\]|\\.)*?--step\s+4\b'
min: 1
---

One `prd_deploy.py confirm` carries steps 2, 3 and 4, in order: the owner's reply names 3 and 4 as done, so they
are confirmed with step 2, never asked about again and never left to stop the run one by one.
