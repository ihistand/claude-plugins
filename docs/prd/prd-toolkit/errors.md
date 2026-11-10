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
Confirmed: 2026-11-07, "Confirm the class (form)"
Touches: FR-006
Evidence: User report (/prd-error), verbatim:
    lint-cli: a directory or broken symlink named <name>.yaml in test-cases/ or contracts/ crashes lint
    (internal error, exit 2) instead of a sufficiency finding like AC-006.3.
    Repro: /private/tmp/claude-502/-Users-ihistand-projects/70d5ca74-4580-4373-ba48-6ff35310fa48/scratchpad/lintbug/ydir
Diagnosis: Reproduced once: `prd_lint.py <repro>/ydir`, where test-cases/sub.yaml is an empty directory, printed `prd_lint: internal error: IsADirectoryError: [Errno 21] Is a directory: .../test-cases/sub.yaml` and exited 2. Root cause: prdlint/model.py guards `.md` entries with `is_file()` (line 854, the E-005 fix), but the test-cases glob (line 887) and the contracts rglob (line 899) pass every `*.yaml` match, a directory or a broken symlink included, to load_yaml, whose open raises. The broken-symlink half is read from the code, not run: glob yields a dangling link and open raises FileNotFoundError. The code does what an AC says: AC-006.1 `If loading the folder raises an error other than a missing prd.md, the lint command shall print prd_lint: internal error: <exception type>: <message> to stderr ... and exit 2.` AC-006.3 gives the sufficiency finding only to `an entry of the folder whose name ends in .md`. The AC is wrong in scope: a non-file `.yaml` entry in test-cases/ or contracts/ is the same malformed-folder case E-005 fixed for `.md`, and should be a sufficiency finding at line 0, not an internal error.
Resolution: T-006.4 [integration], PRD 5.0.0, fixed in 52b85d8
Recurrence of: E-005

### E-008 Cached uv script environments accumulate without bound in ~/.cache/uv/environments-v2
Detected: 2026-11-09, user report (GitHub issue #24)
Classification: spec gap
Confirmed: 2026-11-09, "Confirm the class (form)"
Evidence: Source: GitHub issue ihistand/claude-plugins#24, filed 2026-11-09 from a disk-space review.
  ~/.cache/uv/environments-v2 held 26,888 cached script environments; uv cache size reported 454.4GiB.
  Per script: prd-git-hook 8,632; prd-block 4,485; prd-deploy 3,466; prd-lint 2,535; prd-trace 1,747;
  prd-status 1,479; prd-links 1,336; prd-change 1,221; validate-outline 692; prd-gates 602; prd-error 470; prd-hooks 54.
  Each environment about 20 MB as listed (CPython 3.13, uv 0.13.7; pyyaml, jsonschema, openapi-spec-validator).
  New prd-git-hook environments per day: Nov 1 1,271; Nov 2 1,281; Nov 3 2,645; Nov 4 764; Nov 9 1,365.
  rm -rf of the folder freed about 89 GB of disk and about 27 million files (APFS clones made the listed size overstate it).
  During the rm, two new environments appeared from hook runs in another session:
  prd-git-hook-bda7e90cb225275c and prd-lint-d26ef0960b4cb95e (16:12), so the rm ended with Directory not empty.
Diagnosis: Root cause: uv keys a cached script environment on the script's path, not its contents or dependencies. Reproduced 2026-11-09 with uv 0.13.7: running `.prd-toolkit/prd_error.py` twice from one path reused one environment; a copy in a new folder built a second; the same path with the file edited reused it. Every distinct path a prd script runs from therefore leaves one environment in `~/.cache/uv/environments-v2` that nothing removes. Two sources make new paths: (1) the unit suite builds git repositories under pytest `tmp_path`, installs the hooks there and commits, so each shim runs `uv run --script "$prd_top/.prd-toolkit/prd_git_hook.py"` from a new path, and tests run vendored copies of scripts the same way; one run of `tests/test_hooks_install.py` (33 tests) added 4 `prd-git-hook` environments, and the full suite runs on every build, review fix and CI-parity run; (2) in real repositories each clone or worktree has its own `.prd-toolkit/`, so every new worktree adds environments for each script its hooks and skills run. Sections searched and found silent on cached environments, their count or their cleanup: prd.md technical context ("Each CLI script (`prd-toolkit/scripts/prd_*.py`) is a uv script with an inline dependency header, run as `uv run --script <script>`."), testing.md Harness (Lifecycle, Clean state: "Every test starts from its own pytest `tmp_path`"), nfr.md and operations.md; no AC in the lint-cli feature covers the hooks or test setup. No PRD line bounds what a test run or a hook run may leave in the user's uv cache.
Resolution: T-019.2 [integration], PRD 6.1.0, fixed in b1e24cc057b31f2f3d599a4a2fb522f08836988a
Recurrence of: -

### E-009 sections misquotes an unnumbered level-2 heading as `## None. <title>`
Detected: 2026-11-10, adoption extract of lint-structure (prd-toolkit/scripts/prdlint/rules/structure.py:150 @5824ed1)
Classification: code bug
Confirmed: 2026-11-10, "Real bug (form) — it should: When prd.md has a level-2 heading that is not one of the fourteen sections, numbered or not, lint reports sections at its line with unexpected section '<the heading as written>', e.g. unexpected section '## Notes'; it never prints None."
Touches: FR-022
Diagnosis: The section parser gives an unnumbered level-2 heading of prd.md (`## Notes`) the number None, and the finding is built as `unexpected section '## {a[0]}. {a[1]}'`, so it prints `unexpected section '## None. Notes'`, quoting a heading that is in no file. The sibling message on line 144 (`missing section '## <n>. <title>'`) and prd-format.md ("prd.md sections": level-2 headings, exactly these) quote a heading as it is written. The Python `None` reaching the message contradicts them.
Resolution: open
Recurrence of: -

### E-010 vague-word reads code spans in an FR block's acceptance criteria
Detected: 2026-11-10, adoption extract of lint-structure (prd-toolkit/scripts/prdlint/rules/structure.py:290 @5824ed1)
Classification: code bug
Confirmed: 2026-11-10, "Real bug (form) — it should: In an FR block's ACs, vague-word ignores code spans the way it does for NFR lines: a listed word inside a code span is not reported, and a digit inside a code span does not count as a measurable number."
Touches: FR-028
Diagnosis: For an NFR block the rule blanks fenced code and inline code spans before matching (line 286). Commit 76cfa46 ("vague-word ignores code in NFR blocks") added this, and test_vague_word_ignores_inline_code_and_fences tests it. For an FR block it matches the raw AC text (`a.text`, line 290). An FR AC that names a flag such as `--secure` in a code span is therefore reported as `'secure' with no measurable number on the line`, and a digit inside a code span exempts a listed word outside it. prd-format.md ("lint ignores code spans", Requirement blocks) and the sibling NFR branch treat code as not prose.
Resolution: open
Recurrence of: -

### E-011 Markers in hidden Markdown files are scanned
Detected: 2026-11-10, adoption extract of lint-structure (prd-toolkit/scripts/prdlint/rules/structure.py:58 @5824ed1)
Classification: code bug
Confirmed: 2026-11-10, "Real bug (form) — it should: A file or folder under the PRD folder whose name starts with . is not part of the PRD: lint loads no Markdown from it, so no rule (markers, assumptions, placeholders, glossary, requirement blocks) reads it."
Touches: FR-027, FR-029, FR-030, FR-032
Diagnosis: `all_lines` yields every line of `prose(prd)`, which holds every Markdown file the loader read. The loader collects them with `rglob("*.md")` (model.py:869), which also matches hidden names such as `.notes.md` or `features/.draft.md`. markers-open and assumption-indexed therefore report markers in hidden Markdown files. The function's own docstring (structure.py:57: hidden or editor-backup files are skipped) and prd-format.md (Requirement blocks: hidden or editor-backup files are not scanned) say otherwise, and the raw-file branch (line 64) does skip any path part that starts with `.`.
Resolution: open
Recurrence of: -

### E-012 A key missing from the frontmatter is reported at a body line of prd.md
Detected: 2026-11-10, adoption extract of lint-structure (prd-toolkit/scripts/prdlint/rules/structure.py:83 @5824ed1)
Classification: code bug
Confirmed: 2026-11-10, "Real bug (form) — it should: lint looks up a frontmatter key's line only inside the frontmatter block: a present key is reported at its own line, and a missing key always at prd.md:1, whatever lines below the frontmatter start with <key>:. The language-table and sql-dialect findings use the same lookup."
Touches: FR-020, FR-021
Diagnosis: `_fm_line` scans every line of prd.md for one that starts with `<key>:`, not only the frontmatter block, and falls back to the frontmatter's line only when none does. Suppose a key is absent from the frontmatter and a later line of prd.md starts with it, for example a configuration example in a fenced block of section 4 with a `language: python` or `owner: ops` line at column 0. Then the `missing key` finding, and a language-table finding for a PRD with no `language:` key, point at that body line. The helper's name (`_fm_line`) and its fallback to `prd.frontmatter_line` say the line is the frontmatter's.
Resolution: open
Recurrence of: -

### E-013 An empty Test roots list goes unreported when a marker sits elsewhere on the Layout line
Detected: 2026-11-10, adoption extract of lint-structure (prd-toolkit/scripts/prdlint/rules/structure.py:217 @5824ed1)
Classification: code bug
Confirmed: 2026-11-10, "Real bug (form) — it should: lint reports Test roots: lists no backticked directory whenever the list after Test roots: names no backticked directory and that list itself holds no [NEEDS CLARIFICATION marker; a marker elsewhere on the Layout line does not excuse it."
Touches: FR-025
Diagnosis: When `Test roots:` lists no backticked directory, the rule skips its finding if `[NEEDS CLARIFICATION` appears anywhere on the Layout bullet's line, including the convention text before `Test roots:`. Consider the template's Layout line with its first marker kept and its roots filled in without backticks (`Test roots: tests/`). It gives no `sections` finding, and in a Draft PRD no finding at all, although the guard will then block every write. prd-format.md (testing.md, Harness) reports a `Test roots:` that lists no backticked directory and holds no marker. The comment on line 217 names the case it skips as an unfilled marker, which markers-open reports. The loader already removes markers from the Test roots text alone (model.py:575).
Resolution: open
Recurrence of: -

### E-014 A repeated prd.md section or Harness slot is reported as out of order, not as a duplicate
Detected: 2026-11-10, confirmation of Q-01 (FR-022, FR-025)
Classification: code bug
Touches: FR-022, FR-025
Diagnosis: The order checks compare the present sections, and the present Harness slots, with the expected list (structure.py:146 and :210), so a section or slot that appears twice makes the lists differ and is reported as out of order. No finding names the duplicate, which sends the author looking for a misplaced section instead of the repeated one, often left by a merge.
Resolution: open, intended: a level-2 section of prd.md that appears twice is reported at the second one's line as `duplicate section '## <n>. <title>'`, and a Harness slot that appears twice as `Harness slot '<slot>' appears twice`; out of order is reported only when the sections, or the slots, are out of order once duplicates are set aside (the owner, 2026-11-10)
Recurrence of: -

### E-015 An empty section 13 passes open-questions-empty while the PRD is Approved
Detected: 2026-11-10, confirmation of Q-02 (FR-031)
Classification: code bug
Touches: FR-031
Diagnosis: open-questions-empty reports only the first body line of section 13 that is neither empty nor `None.` (structure.py:333), so a section 13 with no text at all gives no finding. prd-format.md says section 13 is the single line `None.` when there are no open questions, so an Approved PRD with an empty section 13 passes a rule meant to require that line.
Resolution: open, intended: while the PRD is Approved, a section 13 with no text is reported at its heading line with `section 13 must be 'None.' when the PRD is Approved` (the owner, 2026-11-10)
Recurrence of: -

### E-016 The adoption.md header finding is reported at line 1, not at the header's line
Detected: 2026-11-10, confirmation of Q-03 (FR-024)
Classification: code bug
Touches: FR-024
Diagnosis: The header-mismatch finding is built with line 1 (structure.py:193) although the table's own line is known (the parsed table's line). Every other adoption.md finding points at the line to fix, a row at its own line, so this one sends the author to the file's heading instead of the header row.
Resolution: open, intended: the adoption.md header finding is reported at the table's header line (the owner, 2026-11-10)
Recurrence of: -
