# SQLAnvil Toolkit

Engineering best practices for writing [**sqlanvil**](https://github.com/sqlanvil/sqlanvil) data projects on **PostgreSQL**, **Supabase**, and **MySQL/MariaDB**.

The skill is a copy of the canonical one in [SQLAnvil/agent-skills](https://github.com/SQLAnvil/agent-skills), synced by `scripts/sync-skills.sh` and pinned to the current sqlanvil release. Outside Claude Code, `npx skills add SQLAnvil/agent-skills` installs the same skill.

sqlanvil is a fork of Dataform repositioned for Postgres/Supabase. Your Dataform/BigQuery instincts are *mostly* right — but a handful of differences (config blocks, credentials, DDL, statement separators, CLI verbs) silently produce broken sqlanvil code. This plugin is that delta.

## What's Included

### Skills

**sqlanvil-engineering-fundamentals** — the deltas that bite when you assume Dataform/BigQuery:
- `workflow_settings.yaml` (flat `warehouse:`), flat `PostgresConnection` `.df-credentials.json`, `sqlanvilCoreVersion` (not `dataformCoreVersion`)
- First-class `postgres: {}` config — indexes (numeric `method` enum), partitioning, storage options, materialized views — never hand-rolled DDL
- `---` statement separator (never `;`), procedures/functions via `type: "operations"`
- Supabase extras: RLS policies, Realtime, pgvector
- **Named connections** — read a table from *another* warehouse (BigQuery, a second Postgres) as a live foreign table via the auto-generated FDW bridge, generated with `sqlanvil introspect`
- The CLI is the global `sqlanvil` (`npm i -g @sqlanvil/cli`) — no `dataform`, no `npm run`; `./scripts/run <verb>` only inside a sqlanvil repo checkout

The skill is designed to be bulletproof against rationalization — it fires especially when you're under time pressure or reaching for a BigQuery habit.

**sqlanvil-sqlx-lint** — runs the [sqlanvil-sqlx-lint](https://github.com/SQLAnvil/sqlanvil-sqlx-lint) convention checker on `.sqlx` files an agent writes or edits, and when its pre-commit hook fails. It checks what SQL linters and `sqlanvil compile` cannot see: `columns` documentation, `${ref()}` usage, schema suffixes, directory policies, and Dataform habits sqlanvil ignores or fails on at run time (BigQuery options on Postgres, `;` instead of `---`, unguarded DDL on incrementals). Needs the linter installed (`pip install sqlanvil-sqlx-lint`).

### Slash Commands

| Command | Purpose |
|---------|---------|
| `/sqlanvil-compile` | Compile + surface config/graph errors (static, no warehouse) |
| `/sqlanvil-test` | Validate model(s) against a `--schema-suffix dev` sandbox |
| `/sqlanvil-run` | Run/deploy to the warehouse with pre-flight checks |
| `/sqlanvil-new-table` | Create a new table via TDD (RED → GREEN → REFACTOR) |
| `/sqlanvil-introspect` | Generate a cross-warehouse source declaration from a named connection |

Commands use the global `sqlanvil` CLI (`npm i -g @sqlanvil/cli`).

## Installation

```bash
# Add the marketplace (once)
/plugin marketplace add ihistand/claude-plugins

# Install
/plugin install sqlanvil-toolkit@ihistand
```

Then restart Claude Code. The skill auto-activates when you edit `.sqlx`, `workflow_settings.yaml`, or `.df-credentials.json` in a Postgres/Supabase sqlanvil project.

## Related Skills

- **superpowers:test-driven-development** — foundational TDD principles
- **elements-of-style:writing-clearly-and-concisely** — clear documentation writing

## Official Documentation

- **Code** — [github.com/sqlanvil/sqlanvil](https://github.com/sqlanvil/sqlanvil)
- **Docs** — [sqlanvil.com/docs](https://sqlanvil.com/docs/) (see `named-connections.md` for the cross-warehouse workflow)

## License

Created by Ivan Histand (ivan@histand.net).
