---
type: tool_used
tool: Write
input_match: '^(?=[\s\S]*"file_path"\s*:\s*"[^"]*tests/)(?=[\s\S]*(?:Bonjour|[Ff]rench|[Ff]ran[cç]ais))'
min: 0
max: 0
---

No test file under `tests/` is written from the README: only the README's hand-written note says `greet` answers in
French (`Bonjour, World!`); every PRD file says the greeting comes from the environment's setting (`Hi` on staging).
