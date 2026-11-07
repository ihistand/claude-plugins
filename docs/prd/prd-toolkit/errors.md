<!-- Format: references/prd-format.md, "errors.md".
Entry lines in order: Detected, Classification, Confirmed, Touches, Evidence (at most 20 lines, continuation lines indented two spaces), Diagnosis, Resolution, Recurrence of. -->

# Error ledger

### E-001 A prd.md directory gets the lowercase-name hint
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/model.py:713 @d1a4146)
Classification: code bug
Confirmed: 2026-11-03, "Real bug — it should: When prd.md is a directory, lint says prd.md must be a file and exits 2. The lowercase-name hint appears only when a different name matches prd.md ignoring case."
Touches: FR-005
Diagnosis: When the folder holds a directory named exactly `prd.md`, `load` sets `names["prd.md"]` but `is_file()` is false, so it enters the refusal branch. Then `next(n for n in names if n.lower() == "prd.md")` finds that same entry, and the message reads `no prd.md; found prd.md; the file name is lowercase prd.md`, which tells the user to rename prd.md to prd.md. The comment at model.py:710 says the hint is for case-insensitive filesystems, where `PRD.md` "exists" as prd.md, and test_cli.py:28-33 tests only the `PRD.md` case. The search does not leave out the exact name.
Resolution: T-005.3 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-002 The shared missing-package message always names prd_lint and its packages
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/deps.py:13 @d1a4146)
Classification: code bug
Confirmed: 2026-11-03, "Real bug — it should: The missing-package message names the script that failed and only the packages that script needs."
Touches: FR-010
Diagnosis: `deps.require` is documented as a general "Optional-import helper" (deps.py:1). Thirteen CLI scripts call it (prd_trace.py:17, prd_publish.py:19, prd_links.py:23 and others), and so do library modules (publish.py:16, context.py:14, snapshot.py:14). Its message always starts `prd_lint:` and always suggests `pip install pyyaml sqlglot openapi-spec-validator`. Under prd_publish.py, a missing `markdown-it-py` therefore prints `prd_lint: missing Python package 'markdown-it-py'. …, or: pip install pyyaml sqlglot openapi-spec-validator`. That names the wrong script and gives a pip command that does not install the missing package. The sibling scripts prefix their own messages with their own names (`prd_links: <why>`, commit 9b231d3; `prd_hooks: …`, commit 53041c6). The text is right for prd_lint itself, so FR-010's case cannot show the bug.
Resolution: T-010.2 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-003 An unhashable YAML mapping key crashes the load instead of being reported
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/yamlload.py:35 @d1a4146)
Classification: code bug
Confirmed: 2026-11-03, "Real bug — it should: A YAML key that is a list or a mapping is reported as a finding at its line, like any other malformed YAML, and lint keeps going"
Touches: FR-011, FR-012
Diagnosis: `_Loader.construct_line_map` runs `if key in data` on whatever the key node builds. A sequence or mapping key (`? [a, b]` or `{a: 1}: x`) builds a list or a LineDict, and that line raises `TypeError: unhashable type`. A TypeError is not a `yaml.YAMLError`, so it escapes `load_yaml`'s `except yaml.YAMLError` (yamlload.py:57) and `model.load`. prd_lint then exits 2 with `prd_lint: internal error: TypeError: …` and reports no finding. The docstring (yamlload.py:46-50) says a parse error becomes a `sufficiency` or `contracts-valid` finding and that the loader "Returns (None, findings) on error". PyYAML's own SafeConstructor, which this loader replaces for mappings, raises `ConstructorError("found unhashable key")`, a YAMLError, for the same input. FR-011's and FR-012's cases use only scalar keys.
Resolution: T-011.6 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-004 The loader reads fixture data under contracts/fixtures/ as PRD documents and contract YAML
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/model.py:717 @d1a4146)
Classification: code bug
Confirmed: 2026-11-03, "Real bug — it should: Lint skips everything under contracts/fixtures/, as prd-format.md says."
Touches: FR-012
Diagnosis: `load` reads every `*.md` below the folder into its documents (model.py:717) and every `*.yaml` below `contracts/` into its contract YAML (model.py:758), reporting their parse errors, duplicate keys and non-mapping top levels under `contracts-valid`; neither glob leaves out `contracts/fixtures/`. prd-format.md (lines 168-169) says fixture data under `contracts/fixtures/` is not scanned, and the sibling `all_lines` skips raw YAML/SQL/JSON fixture files (rules/structure.py:62-64) but starts from `prose(prd)`, which walks fixture `.md` files too. So a fixture `.md` is read by placeholder, glossary-synonym, id-format, schema-refs, markers-open and assumption-indexed, and a fixture `.yaml` by the loader's contracts-valid findings, placeholder's YAML-value check, id-format and id-removed-reused.
Resolution: T-012.2 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-005 A directory named `<name>.md` in the PRD folder is an internal error
Detected: 2026-11-03, lint-cli characterization suite, T-006.3 (prd-toolkit/scripts/prdlint/model.py:717 @709d385)
Classification: code bug
Confirmed: 2026-11-03, "Real bug (Recommended)"
Touches: FR-006
Diagnosis: `load` reads every path that `prd_dir.rglob("*.md")` yields with `read_text` (model.py:717) and does not check that it is a file, so a directory named `notes.md` raises `IsADirectoryError`. prd_lint reports it as `prd_lint: internal error: IsADirectoryError: [Errno 21] Is a directory: '…/notes.md'` and exits 2, where AC-006.3 (the owner's answer to Q-03) wants a `sufficiency` finding and the rules run.
Resolution: T-006.3 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-006 --sample-tids samples a case with no level or a non-lowercase level
Detected: 2026-11-03, lint-cli characterization suite, T-007.5 (prd-toolkit/scripts/prd_lint.py:67 @709d385)
Classification: code bug
Confirmed: 2026-11-03, "Real bug (Recommended)"
Touches: FR-007
Diagnosis: The sample keeps every loaded case whose `str(level).strip()` is not `unit` (prd_lint.py:67). A case with no `level` gives `""` and one with `level: Unit` gives `Unit`, so both are sampled. T-007.5 printed `T-009.1 test-cases/odd.yaml` and `T-009.2 test-cases/odd.yaml` beside the nine expected lines, where AC-007.4 (the owner's answer to Q-02) samples neither.
Resolution: T-007.5 [integration], PRD 1.0.1, fixed in dcfcd15
Recurrence of: -

### E-007 lint crashes (internal error, exit 2) on a directory or broken symlink named `<name>.yaml` in test-cases/ or contracts/
Detected: 2026-11-07, user report (/prd-error)
Classification: invalid requirement
Touches: FR-006
Evidence: User report (/prd-error), verbatim:
    lint-cli: a directory or broken symlink named <name>.yaml in test-cases/ or contracts/ crashes lint
    (internal error, exit 2) instead of a sufficiency finding like AC-006.3.
    Repro: /private/tmp/claude-502/-Users-ihistand-projects/70d5ca74-4580-4373-ba48-6ff35310fa48/scratchpad/lintbug/ydir
Diagnosis: Reproduced once: `prd_lint.py <repro>/ydir`, where test-cases/sub.yaml is an empty directory, printed `prd_lint: internal error: IsADirectoryError: [Errno 21] Is a directory: .../test-cases/sub.yaml` and exited 2. Root cause: prdlint/model.py guards `.md` entries with `is_file()` (line 854, the E-005 fix), but the test-cases glob (line 887) and the contracts rglob (line 899) pass every `*.yaml` match, a directory or a broken symlink included, to load_yaml, whose open raises. The broken-symlink half is read from the code, not run: glob yields a dangling link and open raises FileNotFoundError. The code does what an AC says: AC-006.1 `If loading the folder raises an error other than a missing prd.md, the lint command shall print prd_lint: internal error: <exception type>: <message> to stderr ... and exit 2.` AC-006.3 gives the sufficiency finding only to `an entry of the folder whose name ends in .md`. The AC is wrong in scope: a non-file `.yaml` entry in test-cases/ or contracts/ is the same malformed-folder case E-005 fixed for `.md`, and should be a sufficiency finding at line 0, not an internal error.
Resolution: -
Recurrence of: E-005
