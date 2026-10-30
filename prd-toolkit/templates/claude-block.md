<!-- prd-toolkit:start -->
## Product requirements (managed by prd-toolkit; regenerate with prd_block.py, do not edit)

The PRD at `{{prd_path}}` (version {{version}}) is the authority for how this system behaves.

- To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD
  files only to edit them. Before writing code for an approved change, run `/prd-context <area>
  <IDs> implement`; after the code commit, run it again and refresh each STALE `Source:`. Code
  implements the PRD; it never defines behaviour the PRD lacks.
- Every behaviour change starts as a PRD change: run `/prd-change` (skill
  `prd-toolkit:changing-prds`) before touching code.
- Gap rule: when the PRD does not say something you need (an error code, a URL, an empty
  state), stop and raise a change request with `/prd-change`. Do not guess, and do not read
  the code to fill the gap.
- Cite the IDs a commit implements in its message: `Refs: FR-012`.
- Lint runs inside the prd-toolkit skills; after any PRD edit, finish through `/prd-change`.

Required skills (skills registry):
{{required_skills}}

Adopted areas: {{adopted_areas}}
<!-- prd-toolkit:end -->
