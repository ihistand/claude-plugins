---
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, Write, Edit, Bash]
---

Dispatch the prd-tester agent with exactly this prompt and nothing else, then show me its report as it gave it.
Do not ask me questions.

```
Mode: suite
PRD: docs/prd/notes/
T-ids (one per line, each with its test-case file):
T-001.1 (docs/prd/notes/test-cases/notes.yaml)
T-002.1 (docs/prd/notes/test-cases/notes.yaml)
Rewrite: T-001.1
```
