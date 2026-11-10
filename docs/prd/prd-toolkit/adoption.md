# Adoption map

| Area | State | Boundary |
|---|---|---|
| lint-cli | adopted | `prd-toolkit/scripts/prd_lint.py`, `prd-toolkit/scripts/prdlint/__init__.py`, `prd-toolkit/scripts/prdlint/model.py`, `prd-toolkit/scripts/prdlint/markdown.py`, `prd-toolkit/scripts/prdlint/yamlload.py`, `prd-toolkit/scripts/prdlint/findings.py`, `prd-toolkit/scripts/prdlint/registry.py`, `prd-toolkit/scripts/prdlint/deps.py`, `prd-toolkit/scripts/prdlint/rules/__init__.py`, `prd-toolkit/scripts/prdlint/interface.py` |
| lint-structure | adopted | `prd-toolkit/scripts/prdlint/rules/structure.py` |
| lint-ids | not started | `prd-toolkit/scripts/prdlint/rules/ids.py` |
| lint-testcases | not started | `prd-toolkit/scripts/prdlint/rules/testcases.py` |
| lint-contracts | not started | `prd-toolkit/scripts/prdlint/rules/contracts.py` |
| lint-registries | not started | `prd-toolkit/scripts/prdlint/rules/registries.py`, `prd-toolkit/scripts/prdlint/rules/errors.py` |
| trace-and-hooks | not started | `prd-toolkit/scripts/prd_trace.py`, `prd-toolkit/scripts/prdlint/trace.py`, `prd-toolkit/scripts/prd_git_hook.py`, `prd-toolkit/scripts/prdlint/githook.py`, `prd-toolkit/scripts/prd_hooks.py`, `prd-toolkit/scripts/prdlint/hooks.py`, `prd-toolkit/templates/hooks/**` |
| context | not started | `prd-toolkit/scripts/prd_context.py`, `prd-toolkit/scripts/prdlint/context.py` |
| status | not started | `prd-toolkit/scripts/prd_status.py`, `prd-toolkit/scripts/prdlint/status.py`, `prd-toolkit/scripts/prd_block.py`, `prd-toolkit/templates/claude-block.md`, `prd-toolkit/scripts/prdlint/overview.py`, `prd-toolkit/templates/readme-prd.md`, `prd-toolkit/templates/readme-prds.md` |
| build-check | not started | `prd-toolkit/scripts/prd_build_check.py`, `prd-toolkit/scripts/prdlint/buildcheck.py` |
| deploy | not started | `prd-toolkit/scripts/prd_deploy.py`, `prd-toolkit/scripts/prdlint/deploy.py`, `prd-toolkit/scripts/prd_drift.py`, `prd-toolkit/scripts/prdlint/drift.py` |
| errors | not started | `prd-toolkit/scripts/prd_error.py`, `prd-toolkit/scripts/prdlint/errors.py` |
| publish | not started | `prd-toolkit/scripts/prd_publish.py`, `prd-toolkit/scripts/prdlint/publish.py`, `prd-toolkit/scripts/prdlint/diagrams.py`, `prd-toolkit/templates/publish/**` |
| links | not started | `prd-toolkit/scripts/prd_links.py`, `prd-toolkit/scripts/prdlint/links.py`, `prd-toolkit/scripts/prdlint/changeset.py`, `prd-toolkit/scripts/prdlint/snapshot.py`, `prd-toolkit/scripts/prdlint/citations.py`, `prd-toolkit/scripts/prdlint/rules/links.py` |
| tester-guard | not started | `prd-toolkit/scripts/prd_tester_guard.py`, `prd-toolkit/hooks/**` |
| gates | not started | `prd-toolkit/scripts/prd_gates.py`, `prd-toolkit/scripts/prdlint/gates.py`, `prd-toolkit/scripts/prdlint/formserver.py`, `prd-toolkit/scripts/prd_confirm.py`, `prd-toolkit/scripts/prdlint/confirm.py` |
| change | not started | `prd-toolkit/scripts/prd_change.py`, `prd-toolkit/scripts/prdlint/change.py`, `prd-toolkit/scripts/prdlint/change_approve.py` |
| judge | not started | `prd-toolkit/scripts/prd_judge.py`, `prd-toolkit/scripts/prdlint/judge.py` |
| packs | not started | `prd-toolkit/scripts/prdlint/packs.py`, `prd-toolkit/scripts/prdlint/languages.py`, `prd-toolkit/scripts/prdlint/rules/packs.py` |
| skills | not started | `prd-toolkit/skills/**`, `prd-toolkit/agents/**`, `prd-toolkit/commands/**`, `prd-toolkit/references/clarify-categories.md`, `prd-toolkit/references/contract-types.md`, `prd-toolkit/references/ears.md`, `prd-toolkit/references/quality-checklist.md`, `prd-toolkit/references/test-levels.md`, `prd-toolkit/references/prd-format.md`, `prd-toolkit/templates/prd/**` |
| release | not started | `prd-toolkit/.claude-plugin/**`, `prd-toolkit/README.md`, `prd-toolkit/NOTICE`, `prd-toolkit/pyproject.toml`, `prd-toolkit/uv.lock` |
