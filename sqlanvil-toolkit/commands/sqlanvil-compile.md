---
description: Compile a sqlanvil project and surface graph/config errors (no warehouse needed)
---

You are compiling a sqlanvil (PostgreSQL/Supabase) project.

**Workflow:**

1. Invoke the sqlanvil-engineering-fundamentals skill.
2. Ask which project directory to compile (default: current directory).
3. Run `sqlanvil compile <dir>` — this is static and needs no database connection.
4. If there are compilation errors, read them carefully and fix the offending config/SQL. Common causes: BigQuery-isms (`bigquery: {}`, `partitionBy`, `clusterBy`), `method: "btree"` as a string instead of the numeric enum, `;` used as a statement separator instead of `---`, or a `connection:`-tagged declaration missing `columnTypes`.
5. Report the compiled action count and any graph errors.

**Note**: compile validates config + the dependency graph only; it does not execute SQL. Use `/sqlanvil-test` to validate against a dev schema.
