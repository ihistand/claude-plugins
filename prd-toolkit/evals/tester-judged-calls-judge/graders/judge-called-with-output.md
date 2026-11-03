---
type: tool_used
tool: Write
input_match: '^(?=[\s\S]*"file_path"\s*:\s*"[^"]*tests/)(?=[\s\S]*T-010\.2)(?=[\s\S]*prd_judge\.py)(?=[\s\S]*docs/prd/greet)(?=[\s\S]*install\.md)(?=[\s\S]*(?:returncode\s*==\s*0|check\s*=\s*True))'
min: 1
---

A test file under `tests/` cites T-010.2 and calls `prd_judge.py` with the PRD folder, the T-id and the
guide (all three positionals), asserting exit 0. D3's RED run left the output file out.
