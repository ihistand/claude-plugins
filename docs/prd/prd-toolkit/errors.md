<!-- Format: references/prd-format.md, "errors.md".
Entry lines in order: Detected, Classification, Confirmed, Touches, Evidence (at most 20 lines, continuation lines indented two spaces), Diagnosis, Resolution, Recurrence of. -->

# Error ledger

### E-001 A prd.md directory gets the lowercase-name hint
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/model.py:713 @d1a4146)
Classification: code bug
Touches: FR-005
Diagnosis: When the folder holds a directory named exactly `prd.md`, `load` sets `names["prd.md"]` but `is_file()` is false, so it enters the refusal branch. Then `next(n for n in names if n.lower() == "prd.md")` finds that same entry, and the message reads `no prd.md; found prd.md; the file name is lowercase prd.md`, which tells the user to rename prd.md to prd.md. The comment at model.py:710 says the hint is for case-insensitive filesystems, where `PRD.md` "exists" as prd.md, and test_cli.py:28-33 tests only the `PRD.md` case. The search does not leave out the exact name.
Resolution: open
Recurrence of: -

### E-002 The shared missing-package message always names prd_lint and its packages
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/deps.py:13 @d1a4146)
Classification: code bug
Touches: FR-010
Diagnosis: `deps.require` is documented as a general "Optional-import helper" (deps.py:1). Thirteen CLI scripts call it (prd_trace.py:17, prd_publish.py:19, prd_links.py:23 and others), and so do library modules (publish.py:16, context.py:14, snapshot.py:14). Its message always starts `prd_lint:` and always suggests `pip install pyyaml sqlglot openapi-spec-validator`. Under prd_publish.py, a missing `markdown-it-py` therefore prints `prd_lint: missing Python package 'markdown-it-py'. …, or: pip install pyyaml sqlglot openapi-spec-validator`. That names the wrong script and gives a pip command that does not install the missing package. The sibling scripts prefix their own messages with their own names (`prd_links: <why>`, commit 9b231d3; `prd_hooks: …`, commit 53041c6). The text is right for prd_lint itself, so FR-010's case cannot show the bug.
Resolution: open
Recurrence of: -

### E-003 An unhashable YAML mapping key crashes the load instead of being reported
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/yamlload.py:35 @d1a4146)
Classification: code bug
Touches: FR-011, FR-012
Diagnosis: `_Loader.construct_line_map` runs `if key in data` on whatever the key node builds. A sequence or mapping key (`? [a, b]` or `{a: 1}: x`) builds a list or a LineDict, and that line raises `TypeError: unhashable type`. A TypeError is not a `yaml.YAMLError`, so it escapes `load_yaml`'s `except yaml.YAMLError` (yamlload.py:57) and `model.load`. prd_lint then exits 2 with `prd_lint: internal error: TypeError: …` and reports no finding. The docstring (yamlload.py:46-50) says a parse error becomes a `sufficiency` or `contracts-valid` finding and that the loader "Returns (None, findings) on error". PyYAML's own SafeConstructor, which this loader replaces for mappings, raises `ConstructorError("found unhashable key")`, a YAMLError, for the same input. FR-011's and FR-012's cases use only scalar keys.
Resolution: open
Recurrence of: -

### E-004 The loader reads fixture data under contracts/fixtures/ as PRD documents and contract YAML
Detected: 2026-11-03, adoption extract of lint-cli (prd-toolkit/scripts/prdlint/model.py:717 @d1a4146)
Classification: code bug
Touches: FR-012
Diagnosis: `load` reads every `*.md` below the folder into its documents (model.py:717) and every `*.yaml` below `contracts/` into its contract YAML (model.py:758), reporting their parse errors, duplicate keys and non-mapping top levels under `contracts-valid`; neither glob leaves out `contracts/fixtures/`. prd-format.md (lines 168-169) says fixture data under `contracts/fixtures/` is not scanned, and the sibling `all_lines` skips raw YAML/SQL/JSON fixture files (rules/structure.py:62-64) but starts from `prose(prd)`, which walks fixture `.md` files too. So a fixture `.md` is read by placeholder, glossary-synonym, id-format, schema-refs, markers-open and assumption-indexed, and a fixture `.yaml` by the loader's contracts-valid findings, placeholder's YAML-value check, id-format and id-removed-reused.
Resolution: open
Recurrence of: -
