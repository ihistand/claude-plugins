---
description: Create a new sqlanvil (Postgres/Supabase) table using TDD
---

You are creating a new sqlanvil table following test-driven development.

**Workflow:**

1. Invoke the sqlanvil-engineering-fundamentals skill and superpowers:test-driven-development.
2. Clarify the table's purpose, grain, source models, and unique key.
3. **RED** — write assertions first (`assertions: { uniqueKey, nonNull, rowConditions }` on the model, or a standalone `type: "assertion"` whose SELECT returns offending rows). Compile and confirm they fail (the table doesn't exist yet).
4. **GREEN** — write the minimal model: `config { type: "table" }`, `${ref()}` for every dependency (never hardcoded paths), `description:` + `columns: {}` documentation, and a `postgres: {}` block for indexes/storage if needed (numeric `method` enum — never `method: "btree"`).
5. Validate in dev with `/sqlanvil-test`; watch the assertions pass.
6. **REFACTOR** while keeping tests green.

**Critical**: tests first. ALWAYS `${ref()}`, never hardcoded table paths. Document every table. No BigQuery-isms (`bigquery: {}`, `partitionBy`, `clusterBy`, `OPTIONS(...)`).
