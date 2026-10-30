# prd-toolkit

A living PRD as the single authority agents build, test and deploy from: a PRD folder in the
repo with contracts and black-box test cases, a 27-rule linter, standards and skills
registries, and skills to author and change it. Version 0.1.0.

Design: [docs/superpowers/specs/2026-10-29-prd-toolkit-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-design.md).

## Install

```
/plugin marketplace add ihistand/claude-plugins
/plugin install prd-toolkit@ihistand
```

Restart Claude Code. The scripts run with `uv` (https://docs.astral.sh/uv/); each declares its own
dependencies (`pyyaml`, `sqlglot`, `openapi-spec-validator`) inline. A missing dependency prints an
install hint and exits 2.

## Commands and skills

| Command | Skill | Use |
|---|---|---|
| `/prd-new [slug]` | `prd-toolkit:authoring-prds` | Interview to a PRD folder `docs/prd/<slug>/`, lint it, dry-run it with a fresh agent, approve it, install the CLAUDE.md block |
| `/prd-change <description>` | `prd-toolkit:changing-prds` | Change the PRD first, with new IDs and a version bump, before any code |

## Lint CLI

```
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>   # inside Claude Code
uv run --script prd-toolkit/scripts/prd_lint.py --list-rules
uv run --script prd-toolkit/scripts/prd_lint.py docs/prd/<slug> --sample-tids 3
```

- `${CLAUDE_PLUGIN_ROOT}` is set only inside Claude Code skills and commands. From a shell, use
  the plugin's install path (its `installPath` in `~/.claude/plugins/installed_plugins.json`)
  or a checkout of this repo, as the other two lines do.
- Output is one line per violation: `<file>:<line>: <rule>: <message>`.
- Exit 0 when clean, 1 on violations, 2 on usage, dependency or internal error.
- `--list-rules` prints the 27 rules. `--sample-tids N` prints up to N randomly chosen T-ids for the authoring
  dry run, one per line with the test-case file that holds it (`T-003.1 test-cases/nfr.yaml`), never a `level: unit` case; it exits 1 with `prd_lint: no non-unit T-ids to sample`
  when the PRD has none.

## CLAUDE.md block

`prd_block.py` writes the managed block that points agents at the PRD. It is deterministic, not
written by an agent.

```
uv run --script prd-toolkit/scripts/prd_block.py docs/prd/<slug> [--claude-md PATH] [--check]
```

`--check` reports whether the block is current without writing.

## Folder layout

```
docs/prd/<project>/
├── prd.md                  index: metadata, goals, glossary, registries, ID registry, changelog
├── features/<area>.md      FR blocks with EARS acceptance criteria and T-ids
├── test-cases/<area>.yaml  one entry per T-id
├── contracts/              openapi.yaml, schema.sql, events.md, errors.yaml, permissions.yaml,
│                           config.yaml, data-classification.yaml, dependencies/, fixtures/
├── nfr.md                  NFRs with numeric bounds
├── testing.md              levels, harness, environments, sign-offs
├── operations.md           environments, deploy and rollback runbook
└── errors.md               the Error-Driven Development ledger
```

The exact syntax lint parses is `references/prd-format.md`. The starting files are in
`templates/prd/`.

## Tests and evals

```
uv run --directory prd-toolkit pytest -q
```

The plugin eval, as recorded in `evals/BASELINE.md` (the `--scaffold` flag is required by the
`changing-*` cases, and the pypi grants let `prd_lint.py` fetch its dependencies under the Bash
sandbox):

```
claude plugin eval ./prd-toolkit --runs 1 --model sonnet --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit Bash "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

## Credits

Adapted from GitHub Spec Kit, cc-sdd, BMAD-METHOD, mattpocock/skills and Anthropic's
doc-coauthoring skill. See [NOTICE](./NOTICE).
