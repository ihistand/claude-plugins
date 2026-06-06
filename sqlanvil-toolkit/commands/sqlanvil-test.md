---
description: Validate sqlanvil models against a dev schema with safety checks
---

You are testing sqlanvil models in a dev schema — never production.

**Workflow:**

1. Invoke the sqlanvil-engineering-fundamentals skill.
2. Ask which model(s) to test.
3. Safety checklist:
   - `sqlanvil compile <dir>` — check config + the graph.
   - `sqlanvil run <dir> --credentials <dir>/.df-credentials.json --schema-suffix dev --actions <model> --include-deps` — build into a `<schema>_dev` sandbox.
   - If unit tests exist: `sqlanvil test <dir> --credentials <dir>/.df-credentials.json`.
   - Run validation queries against the dev output (row counts, null checks on key columns).
4. Report results and any issues found.

**Critical**: always use `--schema-suffix dev` for testing. Declared sources are exempt from the suffix, so a dev run still reads your real sources while writing to suffixed output schemas. Never test directly in production.
