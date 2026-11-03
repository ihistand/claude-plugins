# Adoption map

| Area | State | Boundary |
|---|---|---|
| lint-cli | confirmed | `prd-toolkit/scripts/prd_lint.py`, `prd-toolkit/scripts/prdlint/__init__.py`, `prd-toolkit/scripts/prdlint/model.py`, `prd-toolkit/scripts/prdlint/markdown.py`, `prd-toolkit/scripts/prdlint/yamlload.py`, `prd-toolkit/scripts/prdlint/findings.py`, `prd-toolkit/scripts/prdlint/registry.py`, `prd-toolkit/scripts/prdlint/deps.py`, `prd-toolkit/scripts/prdlint/rules/__init__.py` |
| lint-structure | not started | `prd-toolkit/scripts/prdlint/rules/structure.py`, `prd-toolkit/references/prd-format.md`, `prd-toolkit/templates/prd/**` |
| lint-ids | not started | `prd-toolkit/scripts/prdlint/rules/ids.py` |
| lint-testcases | not started | `prd-toolkit/scripts/prdlint/rules/testcases.py` |
| lint-contracts | not started | `prd-toolkit/scripts/prdlint/rules/contracts.py` |
| lint-registries | not started | `prd-toolkit/scripts/prdlint/rules/registries.py`, `prd-toolkit/scripts/prdlint/rules/errors.py` |
| trace-and-hooks | not started | `prd-toolkit/scripts/prd_trace.py`, `prd-toolkit/scripts/prdlint/trace.py`, `prd-toolkit/scripts/prd_git_hook.py`, `prd-toolkit/scripts/prdlint/githook.py`, `prd-toolkit/scripts/prd_hooks.py`, `prd-toolkit/scripts/prdlint/hooks.py`, `prd-toolkit/templates/hooks/**` |
| context | not started | `prd-toolkit/scripts/prd_context.py`, `prd-toolkit/scripts/prdlint/context.py` |
| status | not started | `prd-toolkit/scripts/prd_status.py`, `prd-toolkit/scripts/prdlint/status.py`, `prd-toolkit/scripts/prd_block.py`, `prd-toolkit/templates/claude-block.md` |
| build-check | not started | `prd-toolkit/scripts/prd_build_check.py`, `prd-toolkit/scripts/prdlint/buildcheck.py` |
| deploy | not started | `prd-toolkit/scripts/prd_deploy.py`, `prd-toolkit/scripts/prdlint/deploy.py`, `prd-toolkit/scripts/prd_drift.py`, `prd-toolkit/scripts/prdlint/drift.py` |
| errors | not started | `prd-toolkit/scripts/prd_error.py`, `prd-toolkit/scripts/prdlint/errors.py` |
| publish | not started | `prd-toolkit/scripts/prd_publish.py`, `prd-toolkit/scripts/prdlint/publish.py`, `prd-toolkit/templates/publish/**` |
| links | not started | `prd-toolkit/scripts/prd_links.py`, `prd-toolkit/scripts/prdlint/links.py`, `prd-toolkit/scripts/prdlint/changeset.py`, `prd-toolkit/scripts/prdlint/snapshot.py`, `prd-toolkit/scripts/prdlint/citations.py`, `prd-toolkit/scripts/prdlint/rules/links.py` |
| tester-guard | not started | `prd-toolkit/scripts/prd_tester_guard.py`, `prd-toolkit/hooks/**` |
| skills | not started | `prd-toolkit/skills/**`, `prd-toolkit/agents/**`, `prd-toolkit/commands/**`, `prd-toolkit/references/clarify-categories.md`, `prd-toolkit/references/contract-types.md`, `prd-toolkit/references/ears.md`, `prd-toolkit/references/quality-checklist.md`, `prd-toolkit/references/test-levels.md` |
| release | not started | `prd-toolkit/.claude-plugin/**`, `prd-toolkit/README.md`, `prd-toolkit/NOTICE`, `prd-toolkit/pyproject.toml`, `prd-toolkit/uv.lock` |
