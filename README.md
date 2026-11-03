# Claude Code Plugins by Ivan Histand

Claude Code plugins for data engineering (sqlanvil-toolkit), 3D printing workflows (stl-generator-toolkit) and living product requirements (prd-toolkit). The former dataform-toolkit plugin was retired 2026-09-15; its dataform-engineering-fundamentals skill now lives in the acuantia-gcp-dataform repo. The acuantia-dataform plugin moved to Acuantia's private team marketplace (gitlab.com/acuantia/claude-plugins) on 2026-09-01 and was removed from here on 2026-09-20.

## Available Plugins

### prd-toolkit

A living PRD as the single authority agents build, test and deploy from: a PRD folder in the repo with contracts and black-box test cases, a 39-rule linter, standards and skills registries, and skills to author and change it, plus a builder that takes an approved change to verified code and a deploy script that takes it live.

**Features:**
- **authoring-prds skill** - Interviews to `docs/prd/<project>/`, lints it, dry-runs it with prd-tester, and approves it
- **changing-prds skill** - Changes the PRD first, with new IDs and a version bump, before any code
- **building-from-prds skill** - Takes approved requirements to verified code: a builder in its own worktree, tests written by prd-tester, statuses approved, built, verified
- **deploying-from-prds skill** - Deploys a verified PRD through its runbook with `prd_deploy.py`, stopping at every human step and failure, and records Deployed rows and `verified` → `live`
- **handling-errors skill** - Records any error in `errors.md` with `prd_error.py`, proposes its class for the user to confirm, and fixes it from a failing test through `/prd-change` and `/prd-build`
- **publishing-prds skill** - Renders the PRD with `prd_publish.py` as one self-contained HTML page with per-area summaries that cite their IDs, outside the PRD folder and never committed, offered as a private Artifact
- **coordinating-prds skill** - Links PRDs across repositories (`links.md`, a pinned snapshot of the cited upstream items, `prd_links.py`) and runs a change that crosses them as one change set: one record, one approval, a build per repository in dependency order
- **Slash commands**: `/prd-new`, `/prd-adopt`, `/prd-change`, `/prd-change-set`, `/prd-context`, `/prd-build`, `/prd-status`, `/prd-deploy`, `/prd-error` and `/prd-publish`
- **Lint CLI**: `prd_lint.py` checks 39 rules; `prd_block.py` writes the CLAUDE.md block

**For full documentation:** See [prd-toolkit/README.md](./prd-toolkit/README.md)

### stl-generator-toolkit

Comprehensive toolkit for generating 3D printable STL files for woodworking jigs and fixtures using CadQuery.

**Features:**
- **stl-generator skill** - Pre-built scripts, CadQuery patterns, printer specifications (Elegoo Neptune 4 Pro), and design best practices
- **Slash commands** for common jigs:
  - `/stl-generate` - Generate custom STL files for any woodworking jig
  - `/stl-circle-jig` - Quick generation of circle cutting jigs for router work
  - `/stl-angle-wedge` - Generate angle guide wedges for compound cuts
  - `/stl-spacing-block` - Create precision spacing blocks for assembly
- **Pre-built scripts**: Circle cutting jigs, angle wedges, spacing blocks
- **Reference files**: CadQuery patterns and printer specifications

**For full documentation:** See [stl-generator-toolkit/README.md](./stl-generator-toolkit/README.md)

## Installation

### Install from GitHub

```bash
# Add this marketplace to Claude Code
/plugin marketplace add ihistand/claude-plugins

# Or use the full GitHub URL
/plugin marketplace add https://github.com/ihistand/claude-plugins
```

### Install Plugins

```bash
# Install stl-generator-toolkit
/plugin install stl-generator-toolkit@ihistand

# Install prd-toolkit
/plugin install prd-toolkit@ihistand

# Restart Claude Code for changes to take effect
```

## Usage Examples

### 3D Printing

```
User: I need a jig for cutting 300mm diameter circles for lampshade rings
Claude: /stl-circle-jig
[Generates STL file with specified dimensions, ready for 3D printing]
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
├── prd-toolkit/                  # Living PRD: skills, lint scripts, templates
├── stl-generator-toolkit/        # 3D printing STL generator
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin configuration
│   ├── skills/                   # stl-generator
│   ├── commands/                 # Slash commands
│   ├── scripts/                  # Pre-built Python scripts
│   ├── references/               # CadQuery patterns & printer specs
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

- **GitHub Repository**: [ihistand/claude-plugins](https://github.com/ihistand/claude-plugins)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Plugin Development Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Superpowers Framework](https://github.com/obra/superpowers)
