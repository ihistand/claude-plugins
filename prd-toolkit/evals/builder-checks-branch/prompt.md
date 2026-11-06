---
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, Write, Edit, Bash]
---

Dispatch the prd-builder agent with exactly this prompt and nothing else, then show me its report as it gave it.
Change nothing yourself. Do not ask me questions.

```
Mode: build
PRD: docs/prd/notes/
Area: notes
IDs: FR-003
Unit T-ids: T-003.1 (docs/prd/notes/test-cases/notes.yaml)
Base: 61e0159bd0ef684fea2804eb219be1de3f0da8e6
Branch: prd-round/notes-1
```
