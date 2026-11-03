<!-- Format: references/prd-format.md, "Requirement blocks". -->

# lint-cli: the lint command and the PRD loader

### UJ-01 An engineer lints a PRD folder and fixes what it reports
Status: live (since 1.0.0)
Flow: 1. run `prd_lint.py` on `docs/prd/<slug>`
      → 2. read each finding line, `<file>:<line>: <rule>: <message>`
      → 3. fix the file it names
      → 4. run lint again, until it prints nothing and exits 0
Traces: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006

### FR-001 Lint a PRD folder and print its findings
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:79 @d1a4146
Flow: 1. load the folder (prdlint.model.load) → 2. run every registered rule (prdlint.registry.run)
      → 3. print the loader's and the rules' findings, sorted → 4. exit 0 or 1
Acceptance (EARS):
- AC-001.1 When prd_lint.py is run on a PRD folder where neither the loader nor any rule reports a
  finding, the lint command shall print nothing and exit 0.
- AC-001.2 When the loader or a rule reports findings, the lint command shall print each finding on
  its own stdout line as `<path>:<line>: <rule>: <message>` and exit 1.
- AC-001.3 The lint command shall print the findings sorted by file path, then line number, then
  rule name.
Errors: -
Edge cases: a finding from the loader (a duplicate YAML key) and one from a rule are printed alike → AC-001.2
Tests: T-001.1 [integration], T-001.2 [integration], T-001.3 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; `prdlint/registry.py` run (lines 25-36); `prdlint/findings.py` Finding

### FR-002 Name each finding's file from the working directory
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:23 @d1a4146
Acceptance (EARS):
- AC-002.1 When the PRD folder is below the working directory, the lint command shall print a
  finding's path as the folder's path relative to the working directory joined to the file's path
  relative to the folder.
- AC-002.2 When the PRD folder is the working directory, the lint command shall print a finding's
  path as the file's path relative to the folder, with no prefix.
- AC-002.3 When the PRD folder is outside the working directory, the lint command shall print a
  finding's path as the folder's resolved absolute path joined to the file's path relative to the
  folder.
Errors: -
Tests: T-002.1 [integration], T-002.2 [integration], T-002.3 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint

### FR-003 List the rules
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:42 @d1a4146
Acceptance (EARS):
- AC-003.1 When run with `--list-rules`, the lint command shall print the name of every registered
  rule, one per line in sorted order, and exit 0, whether or not a folder argument is given and
  without reading it.
Errors: -
Edge cases: at d1a4146 the rules package imports seven modules that register 36 rules (`prdlint/rules/__init__.py:2`)
Tests: T-003.1 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; `prdlint/registry.py` RULES

### FR-004 Reject a bad command line
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:37 @d1a4146
Acceptance (EARS):
- AC-004.1 If neither a folder argument nor `--list-rules` is given, the lint command shall print its
  usage line to stderr and exit 2.
- AC-004.2 If the command line holds an unknown option or a `--sample-tids` value that is not an
  integer, the lint command shall print argparse's usage and error lines to stderr and exit 2.
- AC-004.3 When run with `-h` or `--help`, the lint command shall print its help to stdout and exit 0.
- AC-004.4 If the `--sample-tids` value is below 0, the lint command shall print
  `prd_lint: --sample-tids N must be >= 0` to stderr and exit 2 without reading the folder.
Errors: -
Tests: T-004.1 [integration], T-004.2 [integration], T-004.3 [integration], T-004.4 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint

### FR-005 Refuse a folder without prd.md
Status: verified
Source: prd-toolkit/scripts/prdlint/model.py:721 @97c04e1
Acceptance (EARS):
- AC-005.1 If the folder argument names no directory, or a directory with no regular file named
  exactly `prd.md`, the lint command shall print `prd_lint: <resolved folder>: no prd.md` to stderr
  and exit 2.
- AC-005.2 If no entry of that directory is named exactly `prd.md` and another entry's name equals
  `prd.md` ignoring case, the lint command shall append
  `; found <name>; the file name is lowercase prd.md` to that message.
- AC-005.3 If the entry named exactly `prd.md` is a directory, the lint command shall print
  `prd_lint: <resolved folder>: prd.md must be a file` to stderr and exit 2, with no lowercase-name
  hint.
Errors: -
Edge cases: `prd.md` is a directory → AC-005.3 (E-001 is open until the code does this)
Tests: T-005.1 [integration], T-005.2 [integration], T-005.3 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; `prdlint/model.py` NotAPrd

### FR-006 Report an internal error without a traceback
Status: verified
Source: prd-toolkit/scripts/prdlint/model.py:729 @97c04e1
Acceptance (EARS):
- AC-006.1 If loading the folder raises an error other than a missing prd.md, the lint command shall
  print `prd_lint: internal error: <exception type>: <message>` to stderr, print no traceback and
  nothing on stdout, and exit 2.
- AC-006.2 If a rule raises an error, the lint command shall print
  `prd_lint: internal error in rule <rule>: <exception type>: <message>` to stderr, print no finding
  on stdout, and exit 2.
- AC-006.3 If an entry of the folder whose name ends in `.md` is not a regular file, the loader shall
  report `sufficiency` at line 0 of that entry with `a .md entry that is not a file`, load no
  document from it, and lint shall go on to run the rules.
Errors: -
Edge cases: a `.md` file in the folder that is not valid UTF-8 → AC-006.1; a directory named `<name>.md` → AC-006.3, not an internal error (E-005 is open until the code does this)
Tests: T-006.1 [integration], T-006.2 [integration], T-006.3 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; `prdlint/registry.py` RuleCrash

### FR-007 Sample T-ids for the dry run
Status: verified
Source: prd-toolkit/scripts/prd_lint.py:67 @97c04e1
Acceptance (EARS):
- AC-007.1 When run with `--sample-tids N`, the lint command shall print min(N, M) distinct test
  cases chosen at random from the M loaded cases whose `level` value, as text with surrounding
  whitespace removed, is all lowercase and is not `unit`, each as `<T-id> <test-case file>` with the
  file relative to the folder, and exit 0.
- AC-007.2 When run with `--sample-tids N`, the lint command shall run no rule and print none of the
  loader's findings.
- AC-007.3 If the folder has no loaded test case whose level is not `unit`, the lint command shall
  print `prd_lint: no non-unit T-ids to sample` to stderr, nothing to stdout, and exit 1.
- AC-007.4 When run with `--sample-tids N`, the lint command shall not sample a test case that has
  no `level` value, or whose `level` holds an uppercase letter (`Unit`).
Errors: -
Edge cases: N larger than M prints every non-unit case once; N = 0 prints nothing → AC-007.1; level names are lowercase only, and lint without `--sample-tids` reports a level such as `Unit`, or a missing level, through `test-level` (lint-testcases); E-006 is open until the sample leaves them out
Tests: T-007.1 [integration], T-007.2 [integration], T-007.3 [integration], T-007.4 [integration], T-007.5 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint

### FR-008 Mark a CI run for the rules
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:76 @d1a4146
Acceptance (EARS):
- AC-008.1 When run with `--ci`, the lint command shall set the environment variable `PRD_LINT_CI`
  to `1` before the rules run.
- AC-008.2 While `PRD_LINT_CI` is `1` in its environment, the lint command shall run the rules as a
  CI run whether or not `--ci` is given: the variable is the switch, and `--ci` is a shortcut that
  sets it.
Errors: -
Edge cases: the effect (registries skips its on-PATH and installed-skill checks) belongs to lint-registries; prd_error.py sets the variable by default
Tests: T-008.1 [integration], T-008.2 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; setting PRD_LINT_CI (contracts/config.yaml)

### FR-009 Write UTF-8 in any locale
Status: live (since 1.0.0)
Source: prd-toolkit/scripts/prd_lint.py:93 @d1a4146
Acceptance (EARS):
- AC-009.1 When prd_lint.py runs as a script, it shall write stdout and stderr as UTF-8 whatever the
  locale.
Errors: -
Tests: T-009.1 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint

### FR-010 Name a missing dependency
Status: verified
Source: prd-toolkit/scripts/prdlint/deps.py:12 @97c04e1
Acceptance (EARS):
- AC-010.1 If `pyyaml`, `sqlglot` or `openapi-spec-validator` cannot be imported, the lint command
  shall print, for the first one missing in that order,
  `prd_lint: missing Python package '<package>'. Run with: uv run --script <script name> …, or: pip install pyyaml sqlglot openapi-spec-validator`
  to stderr and exit 2.
- AC-010.2 If a package cannot be imported by another prd-toolkit script that uses the same helper,
  that script shall print
  `<script>: missing Python package '<package>'. Run with: uv run --script <script name> …, or: pip install <packages>`
  to stderr, where `<script>` is its own name without `.py` and `<packages>` lists only the packages
  of its own dependency header, and exit 2.
Errors: -
Edge cases: prd_publish.py is the one script whose header adds a package (`markdown-it-py`) → AC-010.2 (E-002 is open until the code does this)
Tests: T-010.1 [integration], T-010.2 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint; cli:prd_publish; `prdlint/deps.py` require

### FR-011 Load the test-case files
Status: verified
Source: prd-toolkit/scripts/prdlint/yamlload.py:40 @97c04e1
Acceptance (EARS):
- AC-011.1 When a `test-cases/*.yaml` file repeats a key in a mapping, the loader shall keep the
  first value and report `id-unique` at the repeat's line with
  `duplicate key '<key>' (first at line <a>, again at line <b>)`.
- AC-011.2 If a test-case file does not parse as YAML, the loader shall report `sufficiency` at the
  error's line with `YAML parse error: <problem>` and load no case from that file.
- AC-011.3 If a test-case file's top level is not a mapping, an empty file included, the loader
  shall report `sufficiency` at line 1 with `top level must be a mapping` and load no case from it.
- AC-011.4 If a test case's value is not a mapping, the loader shall report `sufficiency` at its
  key's line with `<T-id>: a test case must be a mapping` and load the case with no fields.
- AC-011.5 The loader shall read test cases only from `.yaml` files directly in `test-cases/`; a
  file in a subfolder of `test-cases/`, or with another extension, yields no finding and no case.
- AC-011.6 If a test-case file has a mapping key that is a list or a mapping, the loader shall
  report `sufficiency` at that key's line with `YAML parse error: found unhashable key`, load no
  case from that file, and lint shall go on to run the rules.
Errors: -
Edge cases: a list or mapping key → AC-011.6, not an internal error (E-003 is open until the code does this)
Tests: T-011.1 [integration], T-011.2 [integration], T-011.3 [integration], T-011.4 [integration], T-011.5 [integration], T-011.6 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint

### FR-012 Load the contract YAML files
Status: verified
Source: prd-toolkit/scripts/prdlint/model.py:711 @97c04e1
Acceptance (EARS):
- AC-012.1 When a `.yaml` file under `contracts/`, outside `contracts/fixtures/`, repeats a key, does
  not parse, has a mapping key that is a list or a mapping, or has a top level that is not a
  mapping, the loader shall report it with the messages of AC-011.1 to AC-011.3 and AC-011.6 under
  the rule `contracts-valid`, and shall keep every file that loads as a mapping under its path
  relative to the folder.
- AC-012.2 The loader shall read no file under `contracts/fixtures/`, neither as a document nor as
  contract YAML, and shall report no finding for such a file (the `classified-fixtures` rule still
  reads fixtures for real personal data).
Errors: -
Edge cases: fixture data under `contracts/fixtures/` is not scanned (prd-format.md) → AC-012.2 (E-004 is open until the code does this); a list or mapping key → AC-012.1 (E-003)
Tests: T-012.1 [integration], T-012.2 [integration], T-012.3 [integration]  (test-cases/lint-cli.yaml)
Traces: cli:prd_lint
