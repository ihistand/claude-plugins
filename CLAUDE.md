# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository containing data engineering and business intelligence workflow plugins. The primary plugin is **dataform-toolkit**, which provides comprehensive BigQuery Dataform development support with enforced engineering best practices.

**Author**: Ivan Histand (ihistand@rotoplas.com)

## Repository Architecture

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration (name: "ihistand")
├── dataform-toolkit/             # Primary plugin
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin metadata
│   ├── skills/
│   │   └── dataform-engineering-fundamentals.md  # Core TDD/safety skill
│   ├── commands/
│   │   ├── dataform-test.md      # Test tables in dev environment
│   │   ├── dataform-deploy.md    # Deploy to production safely
│   │   ├── dataform-new-table.md # TDD workflow for new tables
│   │   └── dataform-etl.md       # Launch ETL agent
│   └── README.md
└── README.md
```

### Key Concepts

**Marketplace Structure**: This repository is structured as a Claude Code marketplace with the marketplace ID "ihistand". The `.claude-plugin/marketplace.json` defines available plugins that can be installed via `/plugin install`.

**Plugin Organization**: Each plugin lives in its own directory with a `.claude-plugin/plugin.json` manifest. Plugins contain:
- **Skills**: Long-form guidance documents that enforce discipline and best practices
- **Commands**: Quick-access slash commands for common workflows

## Plugin Development Patterns

### Skills Design Philosophy

Skills in this repository follow the "superpowers framework" approach:
- **Enforce discipline**, not just provide information
- Must be **bulletproof against rationalization** (especially under time pressure)
- Include **red flags** to catch deviation attempts
- Document **common mistakes** with corrections
- Reference **related skills** for workflow chains
- Use **non-negotiable language** for critical practices

Example from dataform-engineering-fundamentals:
- "ALWAYS use ${ref()}" not "Consider using ${ref()}"
- "Non-Negotiable Safety Practices" section
- "Red Flags - STOP Immediately" section
- "Common Rationalizations (And Why They're Wrong)" table

### Slash Command Structure

Commands are markdown files with YAML frontmatter:

```markdown
---
description: Brief description for command palette
---

Command instructions here...
```

Commands should:
1. Invoke relevant skills first
2. Ask clarifying questions
3. Follow structured workflows
4. Report results clearly

## Installation and Testing

### Local Testing

```bash
# Add marketplace locally
/plugin marketplace add /path/to/claude-plugins

# Install plugin
/plugin install dataform-toolkit@dev

# Restart Claude Code for changes to take effect
```

### Publishing Workflow

Once published to GitHub:

```bash
# Users can install via
/plugin marketplace add ihistand/claude-plugins
/plugin install dataform-toolkit@ihistand
```

## Dataform-Toolkit Plugin Details

### Core Philosophy

The dataform-toolkit enforces **Test-Driven Development (TDD)** for BigQuery Dataform transformations. Key principles:

1. **Safety First**: `--schema-suffix dev` and `--dry-run` are ALWAYS required
2. **Dependency Management**: ALWAYS use `${ref()}`, NEVER hardcoded table paths
3. **Documentation**: `columns: {}` blocks mandatory for all tables
4. **Tests First**: Write assertions before implementation (RED-GREEN-REFACTOR)
5. **No Shortcuts**: Time pressure does not justify skipping best practices

### Available Commands

| Command | Purpose | Key Workflow |
|---------|---------|--------------|
| `/dataform-test` | Test table in dev | compile → dry-run → dev execution → validation |
| `/dataform-deploy` | Deploy to production | Verify dev testing → Check tests pass → Production deploy |
| `/dataform-new-table` | Create new table | TDD cycle: RED (tests fail) → GREEN (tests pass) → REFACTOR |
| `/dataform-etl` | Launch ETL agent | Complex transformations, troubleshooting, data quality |

### Skills Integration

The **dataform-engineering-fundamentals** skill builds upon:
- `superpowers:test-driven-development` - Core TDD principles
- `superpowers:brainstorming` - Requirements refinement before coding
- `superpowers:systematic-debugging` - Structured troubleshooting
- `superpowers:root-cause-tracing` - Error source identification
- `elements-of-style:writing-clearly-and-concisely` - Clear documentation

### Non-Negotiable Practices

When working on dataform-toolkit or using it in other projects:

1. **ALWAYS use ${ref()}** - Never hardcoded table paths
2. **Create source declarations first** - Before using any external tables
3. **Use .sqlx files for NEW declarations** - Not .js files
4. **Include columns: {} documentation** - For every table with type: "table"
5. **Test in dev before production** - `--schema-suffix dev` required
6. **Write tests first (TDD)** - Assertions before implementation
7. **No schema: config in operations/tests** - Uses defaults from workflow_settings.yaml

## Common Development Tasks

### Adding a New Slash Command

1. Create markdown file in `dataform-toolkit/commands/`
2. Add YAML frontmatter with description
3. Write clear workflow instructions
4. Reference relevant skills
5. Test locally before committing

### Updating the Engineering Fundamentals Skill

**Critical**: This skill is designed to prevent rationalization. When updating:

1. **Maintain non-negotiable language** - Don't soften "ALWAYS" to "Consider"
2. **Add to red flags section** - If new shortcuts are attempted
3. **Document new mistakes** - Add to "Common Mistakes" section
4. **Update troubleshooting** - Reference official Dataform docs
5. **Keep TDD focus** - Tests-first approach is foundational

### Version Updates

Update version in:
- `.claude-plugin/marketplace.json` (plugins array)
- `dataform-toolkit/.claude-plugin/plugin.json` (version field)

## Git Workflow

**Author**: Ivan Histand <ihistand@rotoplas.com>
**Branch**: `main` (production)

Standard git practices:
- Commit messages should be clear and concise
- Reference issue numbers if applicable
- Test plugins locally before pushing

## Documentation Philosophy

Following Strunk & White principles (elements-of-style skill):
- **Omit needless words** - Be concise
- **Use active voice** - "Use ${ref()}" not "ref() should be used"
- **Be specific** - Concrete examples over abstract concepts
- **Avoid qualifiers** - "very", "rather", "pretty" add little value

## Related Resources

- [Claude Code Plugin Development Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Superpowers Framework](https://github.com/obra/superpowers)
- [Dataform Documentation](https://cloud.google.com/dataform/docs)
- [BigQuery GoogleSQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql)

## Notes for Future Development

**Adding New Plugins**: Follow the dataform-toolkit structure:
- Create plugin directory
- Add `.claude-plugin/plugin.json`
- Organize skills/ and commands/ subdirectories
- Update root `marketplace.json`
- Document in root README.md

**Testing New Plugins**: Always test locally using `/plugin marketplace add` with local path before publishing.

**Skill Design**: When creating new skills, study dataform-engineering-fundamentals as a reference for:
- Non-negotiable language patterns
- Red flags and common rationalizations
- Integration with other skills
- Practical examples with "WRONG" vs "CORRECT" comparisons
