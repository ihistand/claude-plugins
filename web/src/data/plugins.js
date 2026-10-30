export const plugins = [
  {
    id: 'sqlanvil-toolkit',
    name: 'sqlanvil-toolkit',
    version: '1.4.6',
    description: 'Engineering best practices for sqlanvil data projects on PostgreSQL and Supabase — corrects Dataform/BigQuery priors, plus named connections (cross-warehouse sources) and the introspect workflow',
    install: '/plugin install sqlanvil-toolkit@ihistand',
    commands: [
      { name: '/sqlanvil-compile', description: 'Compile + surface config/graph errors (static, no warehouse)', workflow: 'compile → fix BigQuery-isms / config errors' },
      { name: '/sqlanvil-test', description: 'Validate models against a dev schema', workflow: 'compile → run --schema-suffix dev → validation queries' },
      { name: '/sqlanvil-run', description: 'Run/deploy to the warehouse with pre-flight checks', workflow: 'Confirm dev-tested → compile → run --credentials' },
      { name: '/sqlanvil-new-table', description: 'Create a new table via TDD', workflow: 'RED (assertions fail) → GREEN (postgres:{} model) → REFACTOR' },
      { name: '/sqlanvil-introspect', description: 'Generate a cross-warehouse source declaration', workflow: 'Named connection → introspect → ref() the FDW foreign table' },
    ],
    skills: [
      { name: 'sqlanvil-engineering-fundamentals', description: 'PostgreSQL/Supabase deltas: flat warehouse config, postgres:{} DDL, --- separators, named connections + introspect' },
      { name: 'sqlanvil-sqlx-lint', description: 'Runs the sqlanvil-sqlx-lint convention checker on .sqlx files: columns docs, ref() usage, schema suffixes, and Dataform habits sqlanvil ignores' },
    ],
    references: [
      { label: 'SQLAnvil', url: 'https://github.com/sqlanvil/sqlanvil' },
      { label: 'SQLAnvil Docs', url: 'https://sqlanvil.com/docs/' },
    ],
  },
  {
    id: 'stl-generator-toolkit',
    name: 'stl-generator-toolkit',
    version: '2.1.0',
    description: 'Generate 3D-printable STL files for woodworking jigs with build123d: a router circle-cutting trammel, exact angle wedges, spacing blocks, and custom designs, with a print-readiness check that refuses STLs that would misprint',
    install: '/plugin install stl-generator-toolkit@ihistand',
    commands: [
      { name: '/stl-generate', description: 'Design a custom jig or fixture', workflow: 'Ready script if one fits → else build123d design → export_checked → measure the part' },
      { name: '/stl-circle-jig', description: 'Router trammel for discs and rings', workflow: 'Diameters + bit + router screw pattern → pivots offset for the bit → STL' },
      { name: '/stl-angle-wedge', description: 'Wedge that holds work at an exact angle', workflow: 'Angle → printed on its side so the slope is exact → STL' },
      { name: '/stl-spacing-block', description: 'Spacing and setup blocks, single or a set', workflow: 'Height(s) → flat measuring faces, engraved labels → STL' },
    ],
    skills: [
      { name: 'stl-generator', description: 'Tested build123d scripts (jigs and a threaded light globe), a print-readiness check with overhang warnings, a guide to measuring replacement parts, and jig design rules' },
    ],
    references: [],
  },
  {
    id: 'prd-toolkit',
    name: 'prd-toolkit',
    version: '0.3.0',
    description: 'A living PRD as the single authority agents build, test and deploy from: a PRD folder with contracts and black-box test cases, a 27-rule linter and trace checks, a test agent that cannot read your code, and skills to author, adopt and change it. Includes /prd-new, /prd-adopt, /prd-change and /prd-context.',
    install: '/plugin install prd-toolkit@ihistand',
    commands: [
      { name: '/prd-new', description: 'Start a PRD for a new project', workflow: 'Interview → docs/prd/<slug>/ with contracts and test cases → lint → prd-tester dry run → approve → CLAUDE.md block' },
      { name: '/prd-adopt', description: 'Bring an existing repo, one area at a time, under a PRD', workflow: 'Bootstrap → extract as-built requirements with sources → user confirms each one → prd-tester characterization suite → trace → approve' },
      { name: '/prd-change', description: 'Change the PRD before changing behaviour', workflow: 'New or changed IDs → version bump → lint → approval → only then the code' },
      { name: '/prd-context', description: 'Print the focused context pack for one PRD task', workflow: 'Pick the PRD → decide or implement pack for an area or requirement IDs → prd_context.py prints only what the task needs' },
    ],
    skills: [
      { name: 'authoring-prds', description: 'Interviews to a PRD folder (docs/prd/<project>/) with contracts and test cases that agents build, test and deploy from; also approves and signs off a draft PRD' },
      { name: 'changing-prds', description: 'Changes the PRD first, with new IDs and a version bump, before any code, when behaviour changes in a repo that has docs/prd/' },
      { name: 'adopting-prds', description: 'Brings an existing codebase under a PRD one area at a time: extracts as-built requirements with sources, confirms intent with the user, and closes each area with characterization tests run by prd-tester' },
      { name: 'testing-from-prds', description: 'Black-box testing from the PRD alone, run by the prd-tester agent for dry runs and suites; the caller checks integrity after each dispatch' },
    ],
    references: [
      { label: 'Design spec', url: 'https://github.com/ihistand/claude-plugins/blob/main/docs/superpowers/specs/2026-10-29-prd-toolkit-design.md' },
      { label: 'Design spec (0.2)', url: 'https://github.com/ihistand/claude-plugins/blob/main/docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md' },
      { label: 'Design spec (0.3)', url: 'https://github.com/ihistand/claude-plugins/blob/main/docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md' },
    ],
  },
]
