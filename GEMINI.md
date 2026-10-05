# Gemini Context: claude-plugins

This file provides context to the Gemini CLI agent when working in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository containing data engineering and 3D-printing workflow plugins: **sqlanvil-toolkit** and **stl-generator-toolkit**. The **acuantia-dataform** plugin moved to Acuantia's private marketplace (gitlab.com/acuantia/claude-plugins) on 2026-09-01; the stale copy here was removed 2026-09-20. The former **dataform-toolkit** plugin was retired 2026-09-15; its skill now lives only in the `acuantia-gcp-dataform` repo.

**Author**: Ivan Histand (ihistand@rotoplas.com)

## Key Concepts

- **Marketplace**: The repository is a Claude Code marketplace with the ID "ihistand".
- **Plugins**: Each plugin has its own directory and manifest.
- **Skills**: Long-form guidance documents that enforce discipline and best practices.
- **Commands**: Quick-access slash commands for common workflows.

## Plugins

- **sqlanvil-toolkit**: TDD and safety practices for sqlanvil projects on PostgreSQL/Supabase; `/sqlanvil-compile`, `-test`, `-run`, `-new-table`, `-introspect`.
- **stl-generator-toolkit**: CadQuery STL generation for woodworking jigs; `/stl-*` commands.

Skill directories under each plugin are copies synced by `scripts/sync-skills.sh` from their canonical repos (see CLAUDE.md); edit the canonical skill, not the copy.
