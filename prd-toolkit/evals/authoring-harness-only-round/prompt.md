---
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, Write, Edit, Bash]
---

docs/prd/notes/ is `In review`. Its last test-agent dry run (phase 6) failed. The sample was T-001.1, T-001.2,
T-002.1, T-002.2 and T-002.3. The report's QUESTIONS were:

1. T-001.1 (testing.md, Harness, Layout): the file a test is written in, and how it cites its T-id, are not stated.
2. T-002.1 (testing.md, Harness, Fixtures): how an input's `notes_added_first` list is applied is not stated.

My answers. Layout: a test lives in `tests/test_<area>.py`, and its docstring cites its T-id, for example
`@prd T-001.1`. Fixtures: the list is added with `notes.app.add_note`, in order, before the call under test.

Carry the PRD on from here until its gates pass. Do not approve it. Do not ask me questions: my answers are above.
