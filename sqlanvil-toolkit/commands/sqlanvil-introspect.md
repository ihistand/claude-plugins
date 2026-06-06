---
description: Generate a cross-warehouse source declaration from a named connection
---

You are adding a read-only source from another warehouse (BigQuery, or a second Postgres) via a named connection and the auto-generated FDW bridge.

**Workflow:**

1. Invoke the sqlanvil-engineering-fundamentals skill (see the named-connections section).
2. Pre-checks:
   - The read (write) warehouse is `postgres` or `supabase` (the FDW bridge is Postgres-only).
   - A `connections:` entry for the source exists in `workflow_settings.yaml` (`platform`/`project`/`dataset`/`saKeyId` for BigQuery; `platform`/`host`/`port`/`database`/`defaultSchema` for Postgres).
   - On Supabase, the `wrappers` extension is enabled; `@sqlanvil/core` is ≥ 1.1.1.
3. Generate the declaration:
   `sqlanvil introspect <connection> <schema.table> --output definitions/sources/<name>.sqlx`
   This reads the live source schema and writes a `connection:`-tagged declaration with `columnTypes` mapped to Postgres types.
4. `sqlanvil compile <dir>` — confirm the bridge is generated (a `<connection>_srv` server + a `<connection>_ext.<table>` foreign table) and there are no "Unknown connection" or missing-`columnTypes` errors.
5. Reference the source downstream with `${ref("<name>")}` like any other declaration.

**Critical**: a connection-tagged declaration **requires** `columnTypes` (introspect fills them in). Pin `@sqlanvil/core` ≥ 1.1.1 — 1.1.0 dropped connections in the published package.
