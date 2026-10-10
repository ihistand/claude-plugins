export const plugins = [
  {
    id: 'sqlanvil-toolkit',
    name: 'sqlanvil-toolkit',
    version: '1.3.2',
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
]
