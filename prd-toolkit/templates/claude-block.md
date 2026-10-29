<!-- prd-toolkit:start -->
## Product requirements (managed by prd-toolkit; regenerate with prd_block.py, do not edit)

The PRD at `{{prd_path}}` (version {{version}}) is the authority for how this system behaves.

- Read the PRD, not the code, to learn what the system must do. Code implements the PRD; it
  never defines behaviour the PRD lacks.
- Every behaviour change starts as a PRD change: run `/prd-change` (skill
  `prd-toolkit:changing-prds`) before touching code.
- Gap rule: when the PRD does not say something you need (an error code, a URL, an empty
  state), stop and raise a change request with `/prd-change`. Do not guess, and do not read
  the code to fill the gap.
- Cite the IDs a commit implements in its message: `Refs: FR-012`.
- Lint the PRD after every edit: `uv run --script <prd-toolkit>/scripts/prd_lint.py {{prd_path}}`.

Required skills (skills registry):
{{required_skills}}

Adopted areas: {{adopted_areas}}
<!-- prd-toolkit:end -->
