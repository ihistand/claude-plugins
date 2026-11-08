---
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, Write, Edit, Bash]
---

Dispatch the prd-tester agent with exactly this prompt and nothing else, then show me its report as it gave it,
and nothing else. Do not ask me questions.

```
Mode: write
PRD: docs/prd/greet/
T-ids (one per line, each with its test-case file):
T-002.1 (docs/prd/greet/test-cases/greet.yaml)
T-002.2 (docs/prd/greet/test-cases/greet.yaml)
```
