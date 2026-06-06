---
description: Run/deploy a tested sqlanvil project to its warehouse with pre-flight checks
---

You are running a sqlanvil project against its real warehouse (production).

**Workflow:**

1. Invoke the sqlanvil-engineering-fundamentals skill.
2. Confirm the model was already validated in dev (`/sqlanvil-test`). If not, do that first.
3. Pre-flight:
   - `sqlanvil compile <dir>` passes with no graph errors.
   - Documentation present (`description:` + `columns: {}` on tables).
4. Run: `sqlanvil run <dir> --credentials <dir>/.df-credentials.json`. Scope with `--actions <name> --include-deps`; add `--full-refresh` to rebuild incrementals from scratch.
5. Verify the target tables/views exist and report row counts.

**Critical**: dev-test before production. `.df-credentials.json` is gitignored and holds the warehouse password — never commit it.
