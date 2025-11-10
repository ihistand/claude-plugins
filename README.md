# Claude Code Plugins by Ivan Histand

Claude Code plugins for data engineering and business intelligence workflows.

## Available Plugins

### dataform-toolkit

Comprehensive toolkit for BigQuery Dataform development with engineering best practices.

**Features:**
- **dataform-engineering-fundamentals skill** - Enforces TDD workflow, proper ref() usage, safety practices, and comprehensive documentation
- **Slash commands** for common workflows:
  - `/dataform-test` - Test tables in dev environment with safety checks
  - `/dataform-deploy` - Deploy to production with verification
  - `/dataform-new-table` - Create tables using TDD workflow (RED-GREEN-REFACTOR)
  - `/dataform-etl` - Launch ETL agent specialized in Dataform development

**For full documentation:** See [dataform-toolkit/README.md](./dataform-toolkit/README.md)

## Installation

### Install the Marketplace

```bash
# Add this marketplace to Claude Code
/plugin marketplace add ihistand/claude-plugins
```

### Install Plugins

```bash
# Install dataform-toolkit
/plugin install dataform-toolkit@ihistand

# Restart Claude Code for changes to take effect
```

## Usage Example

After installing dataform-toolkit:

```
User: I need to create a new customer metrics table in Dataform
Claude: /dataform-new-table
[Guides through TDD workflow: write tests first, then implementation]
```

## Plugin Development

This repository follows the Claude Code plugin development best practices:

- **Marketplace structure**: Root `.claude-plugin/marketplace.json` defines available plugins
- **Plugin organization**: Each plugin in its own directory with `.claude-plugin/plugin.json`
- **Skills**: Reusable process documentation that enforces discipline
- **Commands**: Quick-access workflows for common tasks

## Repository Structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace definition
├── dataform-toolkit/             # Dataform development toolkit
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin configuration
│   ├── skills/                   # dataform-engineering-fundamentals
│   ├── commands/                 # Slash commands
│   └── README.md                 # Plugin documentation
└── README.md                     # This file
```

## Author

**Ivan Histand** - Sr Data Architect

- Email: ihistand@rotoplas.com
- GitHub: [@ihistand](https://github.com/ihistand)
- LinkedIn: [ihistand](https://linkedin.com/in/ihistand)

## License

See individual plugin directories for licensing information.

## Contributing

Contributions are welcome! Please open an issue or pull request for:
- Bug fixes
- New features for existing plugins
- New plugin proposals

## Related Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Plugin Development Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Superpowers Framework](https://github.com/obra/superpowers)
