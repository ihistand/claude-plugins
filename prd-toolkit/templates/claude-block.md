<!-- prd-toolkit:start -->
## Product requirements (managed by prd-toolkit; regenerate with prd_block.py, do not edit)

The PRD at `{{prd_path}}` (version {{version}}) is the authority for how this system behaves.

- To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD
  files only to edit them. Build an approved change with `/prd-build <area> <IDs>`. Code
  implements the PRD; it never defines behaviour the PRD lacks.
- Every behaviour change starts with `/prd-change` (skill `prd-toolkit:changing-prds`), before code.
- Gap rule: when the PRD does not say something you need (an error code, a URL, an empty
  state), stop and raise a change request with `/prd-change`. Do not guess or read the code.
- Deploy with `/prd-deploy`; never run a runbook command yourself.
- Cite the IDs a commit implements in its message: `Refs: FR-012`.
- Run `.prd-toolkit/prd_hooks.py install` once per clone:
  `uv run --script .prd-toolkit/prd_hooks.py install {{prd_path}}`.
- Lint runs inside the prd-toolkit skills; after any PRD edit, finish through `/prd-change`.

Required skills (skills registry):
{{required_skills}}

Adopted areas: {{adopted_areas}}
<!-- prd-toolkit:end -->
