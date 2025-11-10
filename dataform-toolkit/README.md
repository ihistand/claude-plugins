# Dataform Toolkit

Comprehensive toolkit for BigQuery Dataform development with engineering best practices. Enforces TDD workflow, proper ref() usage, comprehensive documentation, and safe development patterns.

## What's Included

### Skills

**dataform-engineering-fundamentals** - Complete guide for BigQuery Dataform development that enforces:
- Test-Driven Development (TDD) for data transformations
- Safety practices (`--schema-suffix dev`, `--dry-run`)
- Dependency management (ALWAYS `${ref()}`, NEVER hardcoded table paths)
- Comprehensive documentation (`columns: {}` blocks mandatory)
- Proper architecture patterns (layering, incremental processing, source declarations)

The skill is designed to be bulletproof against rationalization - it works especially when you're under time pressure, tired, or tempted to skip best practices.

### Slash Commands

**`/dataform-test`** - Test a Dataform table in dev environment with complete safety checks:
- Compile validation
- Dry-run SQL validation
- Dev environment execution
- Result verification

**`/dataform-deploy`** - Deploy a tested table to production with pre-deployment verification:
- Confirms dev testing completed
- Verifies tests passing
- Checks documentation completeness
- Safe production deployment

**`/dataform-new-table`** - Create new tables using TDD workflow:
- RED: Write tests first, watch them fail
- GREEN: Write minimal implementation, watch tests pass
- REFACTOR: Improve while keeping tests passing

**`/dataform-etl`** - Launch the ETL agent specialized in BigQuery Dataform development:
- Complex transformations
- Pipeline troubleshooting
- Data quality implementations
- ELT workflow coordination

## Installation

### Option 1: Install from Local Directory

```bash
# From your Claude Code session
/plugin marketplace add /path/to/plugins/dataform-toolkit
/plugin install dataform-toolkit@dev
```

Then restart Claude Code.

### Option 2: Install from Git Repository (Future)

Once published to a Git repository:

```bash
/plugin marketplace add <your-org>/<repository-name>
/plugin install dataform-toolkit@<marketplace-name>
```

## Usage Examples

### Testing a Table

```
User: I need to test my customer_metrics table
Claude: /dataform-test
[Follows complete testing workflow with safety checks]
```

### Creating a New Table

```
User: Help me create a new sales summary table
Claude: /dataform-new-table
[Guides through TDD workflow: tests first, then implementation]
```

### Deploying to Production

```
User: The customer_metrics table is ready for production
Claude: /dataform-deploy
[Verifies testing completed, then safely deploys]
```

### Complex Dataform Work

```
User: I need to build a complex pipeline that aggregates data from multiple sources
Claude: /dataform-etl
[Launches ETL agent with full Dataform expertise]
```

## Key Principles

### Non-Negotiable Safety Practices

1. **Always use `--schema-suffix dev` for testing** - Protects production data
2. **Always use `--dry-run` before execution** - Catches errors early
3. **Create source declarations before using ref()** - Enables dependency tracking
4. **ALWAYS use ${ref()} - NEVER hardcoded table paths** - Maintains dependency graph
5. **Use proper ref() syntax** - Single argument when source exists
6. **Add validation queries** - Verify results immediately

### Architecture Requirements

- **Layered structure**: sources/ → intermediate/ → output/
- **Incremental vs full refresh**: Choose based on data characteristics
- **Dataform assertions**: Automated data quality checks
- **Source declarations**: Use .sqlx files (not .js) for new declarations
- **Schema configuration**: No schema: config in operations/ or test/ files

### Documentation Standards

- **columns: {} mandatory** for all tables with `type: "table"`
- Get descriptions from source docs, API documentation, or business logic
- Document source declarations when applicable
- Clear, concise descriptions following Strunk's writing rules

### Test-Driven Development

1. **RED Phase**: Write assertions first, watch them fail
2. **GREEN Phase**: Write minimal implementation, watch tests pass
3. **REFACTOR Phase**: Improve while keeping tests passing

**Critical**: Tests-first means defining what should happen. Tests-after means checking what does happen.

## Time Pressure Protocol

Even under extreme time pressure (board meeting in 2 hours, production down, stakeholder waiting):

✅ **Still required**:
- Dev testing (3 minutes saves 60 minutes debugging)
- `--dry-run` validation
- Source declarations
- `columns: {}` documentation (2 minutes, saves hours)
- Tests first (TDD)
- Basic validation

⚠️ **Can skip** (but document as technical debt):
- Extensive documentation files
- Peer review
- Performance optimization

**Bottom line**: Safety practices save time. Skipping them wastes time.

## Common Mistakes to Avoid

1. ❌ Using tables before declaring sources → ✅ Create source declarations first
2. ❌ Hardcoded table paths → ✅ Use ${ref()} always
3. ❌ Skipping dev testing under pressure → ✅ Dev testing prevents production issues
4. ❌ Creating monolithic transformations → ✅ Break into intermediate tables
5. ❌ Missing columns: {} documentation → ✅ Document all tables immediately
6. ❌ Writing implementation before tests → ✅ Follow TDD cycle (RED-GREEN-REFACTOR)
7. ❌ Using .js files for NEW declarations → ✅ Use .sqlx files
8. ❌ Adding schema: to operations/tests → ✅ Use default schemas from workflow_settings.yaml

## Quick Reference Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `dataform compile` | Validate syntax | Check for errors |
| `dataform run --schema-suffix dev --dry-run --actions table` | Validate SQL | Check before execution |
| `dataform run --schema-suffix dev --actions table` | Test in dev | Safe execution |
| `dataform run --schema-suffix dev --include-deps --actions table` | Run with deps | Include upstream tables |
| `dataform run --schema-suffix dev --tags looker` | Run by tag | Execute tagged tables |
| `dataform run --actions table` | Production deploy | After dev testing succeeds |

## Related Skills

- **superpowers:test-driven-development** - Foundational TDD principles
- **superpowers:brainstorming** - Refine requirements before coding
- **superpowers:systematic-debugging** - Structured troubleshooting
- **superpowers:root-cause-tracing** - Trace errors to source
- **elements-of-style:writing-clearly-and-concisely** - Clear documentation writing

## Official Documentation

- [Dataform Documentation](https://cloud.google.com/dataform/docs)
- [Dataform Best Practices](https://cloud.google.com/dataform/docs/best-practices-repositories)
- [BigQuery GoogleSQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql)

## License

Created by Ivan Histand (ihistand@rotoplas.com)

## Contributing

This plugin follows the superpowers framework principles:
- Skills enforce discipline, not just provide information
- Must be bulletproof against rationalization
- Include red flags to catch deviation attempts
- Document common mistakes with corrections
- Reference related skills for workflow chains

For questions or contributions, contact Ivan Histand.
