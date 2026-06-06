export const plugins = [
  {
    id: 'dataform-toolkit',
    name: 'dataform-toolkit',
    version: '1.1.0',
    description: 'Comprehensive toolkit for BigQuery Dataform development with TDD workflow and ETL agent integration',
    install: '/plugin install dataform-toolkit@ihistand',
    commands: [
      { name: '/dataform-test', description: 'Test tables in dev environment', workflow: 'compile → dry-run → dev execution → validation' },
      { name: '/dataform-deploy', description: 'Deploy to production safely', workflow: 'Verify dev testing → Check tests pass → Production deploy' },
      { name: '/dataform-new-table', description: 'Create new table with TDD', workflow: 'RED (tests fail) → GREEN (tests pass) → REFACTOR' },
      { name: '/dataform-etl', description: 'Launch ETL agent', workflow: 'Complex transformations, troubleshooting, data quality' },
    ],
    skills: [
      { name: 'dataform-engineering-fundamentals', description: 'Enforces TDD workflow, ref() usage, safety practices, and documentation standards' },
    ],
    references: [
      { label: 'Dataform Documentation', url: 'https://cloud.google.com/dataform/docs' },
      { label: 'BigQuery GoogleSQL Reference', url: 'https://cloud.google.com/bigquery/docs/reference/standard-sql' },
    ],
  },
  {
    id: 'sqlanvil-toolkit',
    name: 'sqlanvil-toolkit',
    version: '1.1.0',
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
    ],
    references: [
      { label: 'SQLAnvil', url: 'https://github.com/sqlanvil/sqlanvil' },
      { label: 'SQLAnvil Docs', url: 'https://sqlanvil.com/docs/' },
    ],
  },
  {
    id: 'stl-generator-toolkit',
    name: 'stl-generator-toolkit',
    version: '1.0.0',
    description: 'Generate 3D printable STL files for woodworking jigs and fixtures using CadQuery, with pre-built scripts and parametric design patterns',
    install: '/plugin install stl-generator-toolkit@ihistand',
    commands: [
      { name: '/stl-generate', description: 'Generate custom STL for any woodworking jig', workflow: 'Gather requirements → Check pre-built scripts → Generate → Export STL' },
      { name: '/stl-circle-jig', description: 'Generate circle cutting jig for router work', workflow: 'Get outer/inner diameter → Run script → Export STL' },
      { name: '/stl-angle-wedge', description: 'Generate angle guide wedge for compound cuts', workflow: 'Get angle (1–60°) → Run script → Export STL' },
      { name: '/stl-spacing-block', description: 'Create precision spacing blocks for assembly', workflow: 'Get height/dimensions → Run script → Export STL' },
    ],
    skills: [
      { name: 'stl-generator', description: 'Pre-built CadQuery scripts, printer specs (Elegoo Neptune 4 Pro), and parametric design patterns for woodworking jigs' },
    ],
    references: [],
  },
  {
    id: 'acuantia-dataform',
    name: 'acuantia-dataform',
    version: '1.0.0',
    extends: 'dataform-engineering-fundamentals',
    description: 'Example of extending a base skill for one team\'s standards: layers Acuantia-specific patterns on top of dataform-engineering-fundamentals — ODS two-arg ref() syntax, looker_ filename conventions, and cross-project coordination',
    install: '/plugin install acuantia-dataform@ihistand',
    commands: [],
    skills: [
      { name: 'acuantia-dataform', description: 'Extends dataform-engineering-fundamentals with Acuantia-specific conventions: ODS two-arg ref(), looker_ prefixes, acuantia dataset schemas, and Looker integration patterns' },
    ],
    references: [],
  },
]
