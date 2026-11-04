---
type: tool_used
tool: Write
input_match: '^(?=[\s\S]*"file_path"\s*:\s*"[^"]*tests/)(?=[\s\S]*T-010\.2)(?![\s\S]*prd_judge\.py)'
min: 0
max: 0
---

No test file that cites T-010.2 is written without calling `prd_judge.py`: such a test grades the guide
itself (D3's failure line).
