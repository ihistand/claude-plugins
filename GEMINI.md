# Gemini Context: claude-plugins

This file provides context to the Gemini CLI agent when working in this repository.

## Project Overview

This is a Claude Code plugin marketplace repository containing data engineering and 3D-printing workflow plugins: **sqlanvil-toolkit**, **acuantia-dataform**, and **stl-generator-toolkit**. The former **dataform-toolkit** plugin was retired 2026-09-15; its skill now lives only in the `acuantia-gcp-dataform` repo.

**Author**: Ivan Histand (ihistand@rotoplas.com)

## Key Concepts

- **Marketplace**: The repository is a Claude Code marketplace with the ID "ihistand".
- **Plugins**: Each plugin has its own directory and manifest.
- **Skills**: Long-form guidance documents that enforce discipline and best practices.
- **Commands**: Quick-access slash commands for common workflows.

## Plugins

- **sqlanvil-toolkit**: TDD and safety practices for sqlanvil projects on PostgreSQL/Supabase; `/sqlanvil-compile`, `-test`, `-run`, `-new-table`, `-introspect`.
- **acuantia-dataform**: Acuantia-specific Dataform conventions layered on `dataform-engineering-fundamentals` (which lives in the `acuantia-gcp-dataform` repo).
- **stl-generator-toolkit**: CadQuery STL generation for woodworking jigs; `/stl-*` commands.

Skill files under each plugin are copies synced from `~/projects/claude-skills` by `scripts/sync-skills.sh`; edit the canonical skill, not the copy.
