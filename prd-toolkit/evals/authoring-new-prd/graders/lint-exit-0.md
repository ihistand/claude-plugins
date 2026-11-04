---
type: regex
target: trace
pattern: '"id":"(toolu_[A-Za-z0-9]+)","name":"Bash","input":\{"command":"(?:[^"\\]|\\.)*?prd_lint\.py(?:\\")?\s+(?:\\")?(?:docs/prd/|\$)(?:[^"\\]|\\.)*"[\s\S]*?"tool_use_id":"\1","type":"tool_result","content":"(?:[^"\\]|\\.)*?prd-lint-exit=0'
---

The PRD lint run ended with exit 0, not only a mention of lint.

The match is bound to one call: a Bash `tool_use` whose command runs `prd_lint.py` on `docs/prd/…` (or on a
shell variable, as `$D`), and the `tool_result` with that call's id, whose content holds `prd-lint-exit=0`.
Before R26 (0.8.0) the pattern was the bare literal, which phase 1's `--list-packs; echo "prd-lint-exit=$?"`
put in the trace before any PRD existed; `--list-packs` now echoes `prd-list-packs-exit=`, and a listing, a
lint that exits 1 and the session's own prose no longer pass (`tests/test_eval_graders.py`).
