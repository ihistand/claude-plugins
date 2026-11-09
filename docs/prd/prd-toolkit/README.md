<!-- prd-toolkit:start -->
# prd-toolkit — product requirements

This folder is the living PRD for **prd-toolkit**: the requirements that say what it does, kept in
step with the code. The code implements this PRD, and a change in behaviour starts here, not in
the code. It is maintained with prd-toolkit, a Claude Code plugin (see [../README.md](../README.md) to set it up).

Version 6.1.0 · Approved · Owner: Ivan Histand · Updated 2026-11-09

## What this PRD covers

> prd-toolkit keeps a living PRD folder in a repository and makes agents build, test and deploy
> from it: a linter and trace checks for the folder, a black-box test agent, and skills that
> author, adopt, change, build, deploy, handle errors in, publish and link PRDs.

## Areas

| Area | Adoption | File |
|---|---|---|
| lint-cli | adopted | [features/lint-cli.md](features/lint-cli.md) |

## What is in this folder

| Path | Holds |
|---|---|
| `prd.md` | The overview: goals, glossary, architecture, the requirement index, open questions, changelog |
| `features/` | One file per area: requirements (`FR-nnn`) and their acceptance criteria (`AC-nnn.n`) |
| `test-cases/` | The test cases for each criterion (`T-nnn.n`), which the tests cite |
| `contracts/` | The interfaces the code must match: commands, configuration, schemas, APIs |
| `testing.md` | How the tests are run, at which level and gate |
| `errors.md` | The error ledger: every bug, its class and its fix (`E-nnn`) |
| `operations.md` | Environments and the deploy runbook |
| `nfr.md` | Non-functional requirements (`NFR-nnn`) |
| `adoption.md` | Which areas of the existing code are under this PRD, and their state |

## Reading and changing it

- Read `prd.md`, then the area you care about. With the plugin: `/prd-status` for where every
  requirement stands, `/prd-context <area>` for one area, `/prd-publish` for a readable page.
- Don't edit these files by hand. A change in behaviour starts with `/prd-change` and is built
  with `/prd-build`; a bug starts with `/prd-error`. Lint and the git hooks check every commit.
<!-- prd-toolkit:end -->
