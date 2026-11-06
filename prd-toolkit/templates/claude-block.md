<!-- prd-toolkit:start -->
## Product requirements (by prd_block.py; do not edit)

The PRD at `{{prd_path}}` (version {{version}}) is the authority.

- To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD
  files only to edit them. Build an approved change with `/prd-build <area> <IDs>`. Code
  implements the PRD; it never defines behaviour the PRD lacks.
- {{change_line}}
- Gap rule: if the PRD is silent on what you need, stop and raise it with `/prd-change`.
  Do not guess or read the code to fill the gap.
- Deploy with `/prd-deploy`; never run a runbook command yourself.
- A bug, a failing test, an error or a failed deploy goes to `/prd-error` (skill
  `prd-toolkit:handling-errors`) before any code changes.
- Commits cite IDs: `Refs: FR-012`.
- Run `.prd-toolkit/prd_hooks.py install` once per clone:
  `uv run --script .prd-toolkit/prd_hooks.py install {{prd_path}}`.
- Lint runs inside the prd-toolkit skills; after any PRD edit, finish through `/prd-change`.

Required skills:
{{required_skills}}

Adopted areas: {{adopted_areas}}
<!-- prd-toolkit:end -->
