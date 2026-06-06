# SQLAnvil Toolkit

Engineering best practices for writing [**sqlanvil**](https://github.com/sqlanvil/sqlanvil) data projects on **PostgreSQL** and **Supabase**.

sqlanvil is a fork of Dataform repositioned for Postgres/Supabase. Your Dataform/BigQuery instincts are *mostly* right — but a handful of differences (config blocks, credentials, DDL, statement separators, CLI verbs) silently produce broken sqlanvil code. This plugin is that delta.

## What's Included

### Skills

**sqlanvil-engineering-fundamentals** — the deltas that bite when you assume Dataform/BigQuery:
- `workflow_settings.yaml` (flat `warehouse:`), flat `PostgresConnection` `.df-credentials.json`, `sqlanvilCoreVersion` (not `dataformCoreVersion`)
- First-class `postgres: {}` config — indexes (numeric `method` enum), partitioning, storage options, materialized views — never hand-rolled DDL
- `---` statement separator (never `;`), procedures/functions via `type: "operations"`
- Supabase extras: RLS policies, Realtime, pgvector
- **Named connections** — read a table from *another* warehouse (BigQuery, a second Postgres) as a live foreign table via the auto-generated FDW bridge, generated with `./scripts/run introspect`
- The CLI is `./scripts/run <verb>` — no global `dataform`, no `npm run`

The skill is designed to be bulletproof against rationalization — it fires especially when you're under time pressure or reaching for a BigQuery habit.

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
- **dataform-engineering-fundamentals** — the warehouse-agnostic architecture/`${ref()}`/documentation rules carry over; this skill is the Postgres/Supabase delta on top
- **elements-of-style:writing-clearly-and-concisely** — clear documentation writing

## Official Documentation

- **Code** — [github.com/sqlanvil/sqlanvil](https://github.com/sqlanvil/sqlanvil)
- **Docs** — [sqlanvil.com/docs](https://sqlanvil.com/docs/) (see `named-connections.md` for the cross-warehouse workflow)

## License

Created by Ivan Histand (ivan@histand.net).
