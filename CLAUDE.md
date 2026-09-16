# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository containing data engineering and 3D-printing workflow plugins: **sqlanvil-toolkit** (PostgreSQL/Supabase data projects), **acuantia-dataform** (one team's Dataform conventions), and **stl-generator-toolkit**. The former **dataform-toolkit** plugin was retired 2026-09-15; its `dataform-engineering-fundamentals` skill now lives only in the `acuantia-gcp-dataform` repo (`.claude/skills/`).

**Author**: Ivan Histand (ihistand@rotoplas.com)

## Repository Architecture

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace configuration (name: "ihistand")
├── sqlanvil-toolkit/             # Example plugin layout
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin metadata
│   ├── skills/
│   │   └── sqlanvil-engineering-fundamentals.md  # Copy synced from claude-skills
│   ├── commands/                 # /sqlanvil-* slash commands
│   └── README.md
├── acuantia-dataform/
├── stl-generator-toolkit/
├── scripts/sync-skills.sh        # Copies canonical skills into plugins
├── web/                          # Docs site (vitest)
└── README.md
```

### Key Concepts

**Marketplace Structure**: This repository is structured as a Claude Code marketplace with the marketplace ID "ihistand". The `.claude-plugin/marketplace.json` defines available plugins that can be installed via `/plugin install`.

**Plugin Organization**: Each plugin lives in its own directory with a `.claude-plugin/plugin.json` manifest. Plugins contain:
- **Skills**: Long-form guidance documents that enforce discipline and best practices
- **Commands**: Quick-access slash commands for common workflows

## Plugin Development Patterns

### Skill Source of Truth — sync, don't hand-edit the plugin copies

The skill `.md` files under each plugin's `skills/` directory are **copies**. The
canonical source is the **claude-skills** repo (`~/projects/claude-skills/<skill>/SKILL.md`,
remote `ihistand/claude-skills`). A published plugin can't symlink to a path on your
machine, so it must ship a copy — but the copy must never drift from the canonical skill.

**Workflow:** edit the skill in `~/projects/claude-skills`, then from this repo run:

```bash
./scripts/sync-skills.sh     # copies canonical SKILL.md -> <plugin>/skills/<skill>.md
git status                   # review, then commit + push to publish
```

The script is idempotent and reports which copies changed. Add new skill↔plugin pairs to
the `SKILLS` array in `scripts/sync-skills.sh`. Do **not** edit the plugin `skills/*.md`
files directly — the next sync overwrites them.

Current mappings:
- `sqlanvil-engineering-fundamentals` → `sqlanvil-toolkit/skills/` (PostgreSQL/Supabase; named connections + introspect)

### Skills Design Philosophy

Skills in this repository follow the "superpowers framework" approach:
- **Enforce discipline**, not just provide information
- Must be **bulletproof against rationalization** (especially under time pressure)
- Include **red flags** to catch deviation attempts
- Document **common mistakes** with corrections
- Reference **related skills** for workflow chains
- Use **non-negotiable language** for critical practices

Example from sqlanvil-engineering-fundamentals:
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
/plugin install sqlanvil-toolkit@dev

# Restart Claude Code for changes to take effect
```

### Publishing Workflow

Once published to GitHub:

```bash
# Users can install via
/plugin marketplace add ihistand/claude-plugins
/plugin install sqlanvil-toolkit@ihistand
```

## Retired Plugins

**dataform-toolkit** (retired 2026-09-15). Never invoked after publication: its
`dataform-engineering-fundamentals` skill was shadowed by the repo-local copy in
`acuantia-gcp-dataform/.claude/skills` (now the only copy), `/dataform-deploy`
contradicted that repo's real deploy flow (dev → main merge in the Dataform UI), and
`/dataform-etl` depended on an agent that shipped with no plugin. Do not re-add it; the
skill's discipline patterns live on in sqlanvil-engineering-fundamentals.

## Common Development Tasks

### Adding a New Slash Command

1. Create markdown file in `<plugin>/commands/`
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
- `<plugin>/.claude-plugin/plugin.json` (version field)

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
- [SQLAnvil Docs](https://sqlanvil.com/docs/)

## Notes for Future Development

**Adding New Plugins**: Follow the sqlanvil-toolkit structure:
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
