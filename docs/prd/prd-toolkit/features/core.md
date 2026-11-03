<!-- Format: references/prd-format.md, "Requirement blocks". -->

# Core features

<!--
Block shape (EARS = Easy Approach to Requirements Syntax; each AC starts with When, While, If, Where or "The system shall"):

```
### FR-001 <title>
Status: approved
Flow: 1. step -> 2. step -> 3a. branch  3b. branch
Acceptance (EARS):
- AC-001.1 When <trigger>, the <system> shall <response>.
- AC-001.2 If <condition>, the <system> shall <response>.
Errors: CODE_ONE, CODE_TWO (contracts/errors.yaml)   (or: Errors: -)
Edge cases: <case> -> AC-001.1
Tests: T-001.1 [unit], T-001.2 [integration]  (test-cases/core.yaml)
Traces: UJ-01; `table.column`
```

A UJ block has Status, Flow and Traces only: no ACs, no tests.
-->

[NEEDS CLARIFICATION: add `### UJ-01 title` and `### FR-001 title` blocks here, then list them in prd.md section 11]
