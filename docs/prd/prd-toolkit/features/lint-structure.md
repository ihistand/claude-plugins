<!-- Format: references/prd-format.md, "Requirement blocks". -->

# lint-structure: the structure lint rules

### FR-020 Check the prd.md frontmatter
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:101 @5824ed1
Flow: 1. read the frontmatter the loader parsed → 2. check `prd`, `version`, `status`, `owner`, `updated`, and `language` when present
      → 3. while `contracts/schema.sql` is a file, check `sql-dialect` against sqlglot
Acceptance (EARS):
- AC-020.1 If a key among `prd`, `version`, `status`, `owner` and `updated` is absent from prd.md's frontmatter, the lint command shall report `prd.md:1: frontmatter: missing key '<key>'`, whatever lines below the frontmatter start with `<key>:`.
- AC-020.2 When the frontmatter's `prd` value does not fully match `[a-z][a-z0-9-]*` or differs from the PRD folder's name, the lint command shall report `frontmatter` at the `prd:` line with `'prd: <value>' must be a lowercase slug equal to the folder name '<folder name>'`.
- AC-020.3 When a frontmatter value is malformed, the lint command shall report `frontmatter` at that key's line with `'<key>: <value>' <reason>`: for a `version` that does not fully match `\d+\.\d+\.\d+`, `must be X.Y.Z, digits only`; for a `status` other than `Draft`, `In review` or `Approved`, `must be Draft, In review or Approved`; for an empty `owner`, `must not be empty`; for an `updated` that does not fully match `\d{4}-\d{2}-\d{2}`, `must be YYYY-MM-DD`.
- AC-020.4 When the frontmatter has a `language` key whose value does not fully match `[a-z]{2,3}`, the lint command shall report `frontmatter` at its line with `'language: <value>' must match ^[a-z]{2,3}$`, and with no `language` key it shall make no language check in this rule.
- AC-020.5 While `contracts/schema.sql` is a regular file in the PRD folder, the lint command shall report `frontmatter` with `missing key 'sql-dialect' (required because contracts/schema.sql exists)` when `sql-dialect` is absent or empty (at its frontmatter line, or at line 1 when the frontmatter has no `sql-dialect:` line), and with `'sql-dialect: <value>' is not a sqlglot dialect (<sqlglot's error text>)` at its line when sqlglot knows no such dialect.
- AC-020.6 While `contracts/schema.sql` is not a regular file, the lint command shall not check `sql-dialect`.
Errors: -
Edge cases: a prd.md with no frontmatter, or one with no closing `---`, has every key absent (the loader's frontmatter parser, lint-cli) → AC-020.1; a key's line is looked up only inside the frontmatter block, so a present key is reported at its own frontmatter line → AC-020.2, AC-020.3; a value keeps any quotes, so `status: "Approved"` is malformed → AC-020.3; `updated` is checked for its shape only (`2026-13-45` passes) → AC-020.3; a missing key whose name starts a later line of prd.md is still reported at line 1 (E-012) → AC-020.1
Tests: T-020.1 [integration], T-020.2 [integration], T-020.3 [integration], T-020.4 [integration], T-020.5 [integration], T-020.6 [integration], T-020.7 [integration], T-020.8 [integration], T-020.9 [integration], T-020.10 [integration], T-020.11 [integration], T-020.12 [integration], T-020.13 [integration], T-020.14 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; `prdlint/markdown.py` frontmatter

### FR-021 Report a PRD language with no table
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:131 @5824ed1
Acceptance (EARS):
- AC-021.1 When the frontmatter's `language` value fully matches `[a-z]{2,3}`, neither the toolkit's `references/languages/` nor a pack the PRD names has a table for it, and the toolkit's `en` table loads, the lint command shall report `language-table` at the `language:` line with `language '<code>' has no table`.
- AC-021.2 When the toolkit or a pack the PRD names has a table for the PRD's language that loads, the lint command shall report no `language-table` finding.
Errors: -
Edge cases: a value that does not match `[a-z]{2,3}` is the frontmatter rule's (AC-020.4), and this rule reports nothing for it; the reasons for a broken table file or a missing `en` table come from the language loader (packs area, not adopted), which this rule prints at the frontmatter's `language:` line, or at line 1 when the frontmatter has none, whatever lines below it start with `language:` (E-012); the toolkit ships `en` and `es`
Tests: T-021.1 [integration], T-021.2 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; `prdlint/languages.py` problem

### FR-022 Require prd.md's fourteen sections in order
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:138 @5824ed1
Acceptance (EARS):
- AC-022.1 If prd.md has no level-2 heading `## <n>. <title>` for one of the fourteen sections of prd-format.md (`1. Metadata & stack` to `14. Changelog`), the lint command shall report `prd.md:1: sections: missing section '## <n>. <title>'` for each one missing.
- AC-022.2 When the fourteen sections that prd.md has do not appear in their numbered order, once each repeated section's later headings are set aside, the lint command shall report `prd.md:1: sections: sections are out of order`, once however many are out of place.
- AC-022.3 When prd.md has a level-2 heading, numbered or not, that is not one of the fourteen sections, the lint command shall report `sections` at its line with `unexpected section '<the heading as written>'`, such as `unexpected section '## Notes'`.
- AC-022.4 When one of the fourteen sections appears more than once in prd.md, the lint command shall report `sections` at the line of each heading after the first with `duplicate section '## <n>. <title>'`.
Errors: -
Edge cases: the title matches exactly, case included, so `## 9. Version` is both a missing `## 9. Versioning` and an unexpected section → AC-022.1, AC-022.3; a heading inside a code fence is not a heading (the loader's section parser, lint-cli); an unnumbered level-2 heading is quoted as written (E-009) → AC-022.3; a repeated section is a duplicate, not out of order (E-014) → AC-022.2, AC-022.4
Tests: T-022.1 [integration], T-022.2 [integration], T-022.3 [integration], T-022.4 [integration], T-022.5 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint

### FR-023 Require the mandatory files and account for the optional ones
Status: live (since 6.2.0)
Source: prd-toolkit/scripts/prdlint/rules/structure.py:152 @5824ed1
Flow: 1. read section 1's `- Not applicable:` lines → 2. check each mandatory entry → 3. check each optional slot
Acceptance (EARS):
- AC-023.1 If a mandatory entry is absent and section 1 does not list it as not applicable, the lint command shall report `<entry without a trailing />:0: sections: mandatory '<entry>' is missing`, the mandatory entries being `features/` (present when `features/*.md` matches), `test-cases/` (present when `test-cases/*.yaml` matches) and the regular files `nfr.md`, `testing.md`, `operations.md`, `errors.md` and `contracts/errors.yaml`.
- AC-023.2 If section 1 has a Not applicable line for a mandatory entry, written with or without its trailing `/`, the lint command shall report `sections` at that line with `mandatory '<entry>' cannot be marked not applicable` and no `is missing` finding for that entry.
- AC-023.3 If no file of an optional slot exists and section 1 has no Not applicable line for any of them, the lint command shall report ``prd.md:1: sections: '<slot>' is absent and section 1 has no 'Not applicable: `<slot>` — reason' line``, the slots being `contracts/openapi.yaml`, `contracts/schema.sql`, `contracts/events.md` (filled by it or by `contracts/asyncapi.yaml`), `contracts/permissions.yaml`, `contracts/config.yaml`, `contracts/data-classification.yaml`, and the folders `contracts/dependencies/` and `contracts/fixtures/`, a folder counting as present only when it holds a file at any depth.
- AC-023.4 When section 1 has a Not applicable line for an optional slot's file, for either file of the events slot, or for a folder slot with or without its trailing `/`, the lint command shall report no `is absent` finding for that slot.
Errors: -
Edge cases: the Not applicable line's grammar (`- Not applicable:`, a backticked path, a dash, a reason) is read by the loader (lint-cli); a slot that exists and is also marked not applicable gives no finding → AC-023.4; an empty `contracts/dependencies/` folder is absent → AC-023.3
Tests: T-023.1 [integration], T-023.2 [integration], T-023.3 [integration], T-023.4 [integration], T-023.5 [integration], T-023.6 [integration], T-023.7 [integration], T-023.8 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint

### FR-024 Check section 8 and adoption.md
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:167 @5824ed1
Acceptance (EARS):
- AC-024.1 If section 8 of prd.md holds a pipe table, the lint command shall report `sections` at the section 8 heading's line with `section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there and leave "See adoption.md."`.
- AC-024.2 If section 8's body, its surrounding whitespace and one final `.` removed, is `See adoption.md` and the PRD folder has no `adoption.md`, the lint command shall report `sections` at the section 8 heading's line with `section 8 points at adoption.md but adoption.md does not exist`.
- AC-024.3 If section 8's body, read as AC-024.2 says, is `Not applicable: new project` and `adoption.md` exists, the lint command shall report `sections` at the section 8 heading's line with `section 8 says "Not applicable: new project" but adoption.md exists`.
- AC-024.4 If section 8's body holds no table, does not contain `NEEDS CLARIFICATION`, and is neither of the two bodies of AC-024.2 and AC-024.3, the lint command shall report `sections` at the section 8 heading's line with `section 8 body must be "See adoption.md." or "Not applicable: new project."`.
- AC-024.5 When section 8's body holds no table and contains `NEEDS CLARIFICATION`, the lint command shall report no `sections` finding for section 8.
- AC-024.6 If `adoption.md` exists and holds no pipe table, the lint command shall report `adoption.md:1: sections: adoption.md holds no '| Area | State | Boundary |' table`.
- AC-024.7 If the header of adoption.md's first table, each cell's backticks removed, is not `Area`, `State`, `Boundary`, the lint command shall report `sections` at the header's line with `adoption.md table header must be '| Area | State | Boundary |', not '| <its cells joined by " | "> |'`.
- AC-024.8 If the State cell of a row of adoption.md's first table, backticks removed, is not `not started`, `extracted`, `confirmed` or `adopted`, the lint command shall report `sections` at the row's line with `adoption state '<state>' for <area> must be one of not started, extracted, confirmed, adopted`.
- AC-024.9 When section 8 reads `See adoption.md.` or `See adoption.md` and adoption.md's first table has the header `| Area | State | Boundary |` and only rows in those four states, the lint command shall report no `sections` finding for section 8 or adoption.md.
Errors: -
Edge cases: the template's section 8 is a clarification marker, which markers-open reports once the PRD is in review → AC-024.5; AC-024.6 to AC-024.8 apply whatever section 8 says; adoption.md's rows are parsed by the loader (lint-cli), and an area past `not started` without its feature file is index-consistent's (lint-ids)
Tests: T-024.1 [integration], T-024.2 [integration], T-024.3 [integration], T-024.4 [integration], T-024.5 [integration], T-024.6 [integration], T-024.7 [integration], T-024.8 [integration], T-024.9 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; adoption.md

### FR-025 Check testing.md's Harness slots
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:199 @5824ed1
Acceptance (EARS):
- AC-025.1 If testing.md has no level-2 section titled `Harness` (in any case) that holds a slot bullet `- **<Slot>.**`, the lint command shall report `testing.md:1: sections: testing.md has no '## Harness' section with its slots`.
- AC-025.2 If one of the fifteen slots Lifecycle, Environment switch, Database access, Tools on the runner, Clean state, Persistent environments, Layout, HTTP requests, Fixtures, Browser identity, Assertions, Waits, Effects, Leaks and Acceptance has no bullet, the lint command shall report `sections` at the first slot bullet's line with `Harness slot '<slot>' is missing`, once per absent slot.
- AC-025.3 When the slots of AC-025.2 that are present do not appear in that order, once each repeated slot's later bullets are set aside, the lint command shall report `sections` at the first slot bullet's line with `Harness slots are out of order; the order is Lifecycle, Environment switch, Database access, Tools on the runner, Clean state, Persistent environments, Layout, HTTP requests, Fixtures, Browser identity, Assertions, Waits, Effects, Leaks, Acceptance`.
- AC-025.4 When the Harness holds a slot bullet whose name is not one of the fifteen, the lint command shall report no finding for it and leave it out of the order check.
- AC-025.5 If the Layout slot's bullet line holds no `Test roots:` text, the lint command shall report `sections` at that line with `the Harness Layout slot has no 'Test roots:' text`.
- AC-025.6 If the Layout slot's bullet line holds `Test roots:` with no backticked directory after it, and the text after `Test roots:` holds no `[NEEDS CLARIFICATION` text, the lint command shall report `sections` at that line with `Test roots: lists no backticked directory`.
- AC-025.7 When the only text after `Test roots:` is a `[NEEDS CLARIFICATION: …]` marker, the lint command shall report no `sections` finding about Test roots.
- AC-025.8 While the PRD folder has no testing.md, the lint command shall report no Harness finding.
- AC-025.9 When one of the fifteen slots has more than one bullet, the lint command shall report `sections` at the line of each bullet after the first with `Harness slot '<slot>' appears twice`.
Errors: -
Edge cases: the slots and the Test roots list are parsed by the loader (lint-cli), which reads `Test roots:` only on the Layout bullet's first line; an absent testing.md is reported as a mandatory file → AC-023.1; a marker elsewhere on the Layout line does not excuse an empty `Test roots:` list (E-013) → AC-025.6; a repeated slot is a duplicate, not out of order (E-014) → AC-025.3, AC-025.9
Tests: T-025.1 [integration], T-025.2 [integration], T-025.3 [integration], T-025.4 [integration], T-025.5 [integration], T-025.6 [integration], T-025.7 [integration], T-025.8 [integration], T-025.9 [integration], T-025.10 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; testing.md Harness; the prd-tester guard reads Test roots (tester-guard area)

### FR-026 Read prose without code and errors.md quotations
Status: live (since 6.2.0)
Source: prd-toolkit/scripts/prdlint/rules/structure.py:36 @5824ed1
Acceptance (EARS):
- AC-026.1 The lint command's prose rules (placeholder, glossary-synonym, and the Markdown part of markers-open and assumption-indexed) shall read each Markdown file the loader reads with its fenced code blocks and inline code spans blanked, keeping every line number.
- AC-026.2 The prose rules shall blank, in errors.md only, each line that starts with `Evidence:` together with the two-space-indented lines that follow it, and each line that starts with `Confirmed:`.
- AC-026.3 The prose rules shall read every other line of errors.md, and a line that starts with `Evidence:` in any other file, as prose.
Errors: -
Edge cases: a fence opens and closes on a line that starts, after optional whitespace, with three backticks or three tildes; an inline code span ends on its own line; which Markdown files the loader reads (every `.md` but the root README.md and files under `contracts/fixtures/`) is lint-cli's (FR-012, FR-015)
Tests: T-026.1 [integration], T-026.2 [integration], T-026.3 [integration], T-026.4 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; `prdlint/markdown.py` strip_code, mask_quoted

### FR-027 Report an unfilled placeholder
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:241 @5824ed1
Acceptance (EARS):
- AC-027.1 When a prose line (FR-026) holds `TBD` or `TODO` as a whole word, `???`, one of the template slots `{{project}}`, `{{owner}}`, `{{date}}` and `{{sql_dialect}}`, or text from `<` and a letter to the next `>` with no `<` or `>` between that does not start `<http://` or `<https://`, the lint command shall report `placeholder` at that line with `placeholder '<the first such text on the line>' in prose; if this is literal text, put it in backticks`.
- AC-027.2 The lint command shall not report `placeholder` for a double-brace name other than the four template slots, for `todo` or `tbd` in lowercase, for an autolink `<https://…>`, or for text in a code span.
- AC-027.3 When a string value of a YAML file the loader reads under `contracts/` or `test-cases/` holds `TBD` or `TODO` as a whole word, `???` or one of the four template slots, the lint command shall report `placeholder` at the line of the mapping key that holds the value (for a list item, the key that holds the list) with `placeholder '<the first such text>' in a YAML value`.
- AC-027.4 The lint command shall not report `placeholder` for angle-bracket text in a YAML value, nor for a YAML key or a YAML comment.
- AC-027.5 The lint command shall not report `placeholder` for a file under the PRD folder whose path, relative to the PRD folder, has a part starting with `.`.
Errors: -
Edge cases: one finding per line, naming the first match → AC-027.1; SQL and JSON files are not read by this rule; the test-case conventions `<repo>` and `<tmp>` in YAML values are not placeholders → AC-027.4; YAML under `contracts/fixtures/` is never read (lint-cli FR-012); a hidden file is not part of the PRD (E-011) → AC-027.5; a placeholder in a YAML list item is reported at the line of the key that holds the list, as intended (Q-05) → AC-027.3; HTML comments and tags in Markdown are prose, so a `TODO` inside a comment and a bare tag such as `<br>` are reported, as intended (Q-06) → AC-027.1
Tests: T-027.1 [integration], T-027.2 [integration], T-027.3 [integration], T-027.4 [integration], T-027.5 [integration], T-027.6 [integration], T-027.7 [integration], T-027.8 [integration], T-027.9 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint

### FR-028 Report a vague word without a number
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:273 @5824ed1
Acceptance (EARS):
- AC-028.1 When the text of an AC of an FR block that is not removed, its continuation lines joined, holds outside any code span a word of the PRD language table's `vague` list as a whole word in any case, and holds no digit anywhere once every AC, FR, NFR, UJ and T ID is taken out, the lint command shall report `vague-word` at the AC's first line with `'<the first such word, as written>' with no measurable number on the line`.
- AC-028.2 When such an AC holds a digit outside any code span and outside those IDs, the lint command shall report no `vague-word` finding for it.
- AC-028.3 When a body line of an NFR block, its code spans and fenced blocks blanked, holds a word of the `vague` list as a whole word in any case and no digit once those IDs are taken out, the lint command shall report `vague-word` at that line with the message of AC-028.1.
- AC-028.4 The lint command shall report no `vague-word` finding for a removed AC or its continuation lines, nor for an NFR body line whose only listed word is in a code span or a fenced block.
Errors: -
Edge cases: the English list is `fast`, `secure`, `scalable`, `robust`, `intuitive`, `seamless` and `user-friendly` (references/languages/en.yaml); the digits of an `E-nnn` or `A-nn` ID count as a number; UJ blocks, prd.md and other prose are not checked; with no usable language table the rule reports nothing and language-table says why (FR-021); a code span of an FR block's AC is not prose, so a listed word inside it is not reported and a digit inside it is no number (E-010) → AC-028.1, AC-028.2; an AC is one criterion and its continuation lines belong to it, so a number on any of its lines exempts it and the finding names its first line, as intended (Q-04) → AC-028.1
Tests: T-028.1 [integration], T-028.2 [integration], T-028.3 [integration], T-028.4 [integration], T-028.5 [integration], T-028.6 [integration], T-028.7 [integration], T-028.8 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; `references/languages/en.yaml` vague

### FR-029 Report clarification markers left open once the PRD is in review
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:298 @5824ed1
  prd-toolkit/scripts/prdlint/rules/structure.py:52 @5824ed1
Acceptance (EARS):
- AC-029.1 While prd.md's status is `In review` or `Approved`, the lint command shall report `markers-open` once at each line of a scanned file (AC-029.2 to AC-029.4) that holds `[NEEDS CLARIFICATION`, with `[NEEDS CLARIFICATION] left open while status is <status> (markers count in every text file, comments included; delete a template hint once its slot is answered)`.
- AC-029.2 The markers-open and assumption-indexed rules shall scan each Markdown file the loader reads whose path has no part starting with `.`, as FR-026 reads it, and each file under the PRD folder whose suffix is `.yaml`, `.yml`, `.sql` or `.json`, read raw so that values and comments count.
- AC-029.3 The markers-open and assumption-indexed rules shall not scan a raw file under `contracts/fixtures/`, one whose path relative to the PRD folder has a part starting with `.`, one that holds a NUL byte or is not valid UTF-8, or a file with any other suffix, such as `prd.md~` or a `.lkml` file.
- AC-029.4 While the PRD folder has a `links.md`, the markers-open and assumption-indexed rules shall not scan raw files under `contracts/upstream/`, and while it has none they shall scan them as any other.
- AC-029.5 While prd.md's status is neither `In review` nor `Approved`, the lint command shall report no `markers-open` finding.
Errors: -
Edge cases: the match needs no colon, so `[NEEDS CLARIFICATION]` counts → AC-029.1; two markers on one line give one finding → AC-029.1; a marker in a Markdown code span does not count, one in a YAML or SQL comment does → AC-029.2; a hidden Markdown file is not part of the PRD, so a marker in it does not count (E-011) → AC-029.2
Tests: T-029.1 [integration], T-029.2 [integration], T-029.3 [integration], T-029.4 [integration], T-029.5 [integration], T-029.6 [integration], T-029.7 [integration], T-029.8 [integration], T-029.9 [integration], T-029.10 [integration], T-029.11 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint

### FR-030 Index every assumption marker
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:312 @5824ed1
Acceptance (EARS):
- AC-030.1 When a line of a scanned file (AC-029.2 to AC-029.4) holds `[ASSUMPTION` as a whole word not followed by a space, `A-` digits and a colon, the lint command shall report `assumption-indexed` at that line with `[ASSUMPTION] marker has no A-nn id`, whatever the PRD's status.
- AC-030.2 When a line of a scanned file holds `[ASSUMPTION A-<n>:` and no row of a table in prd.md's section 12 has `A-<n>`, backticks removed, as its first cell, the lint command shall report `assumption-indexed` at that line with `A-<n> has no row in section 12`, whatever the PRD's status, and shall report nothing for a marker whose ID has a row.
- AC-030.3 If the third cell of a section 12 row, backticks removed, is not `open`, `confirmed`, `corrected`, or `awaiting` followed by one space, a non-space character and any text, the lint command shall report `assumption-indexed` at the row's line with `<A-id>: status '<status>' must be open, confirmed, corrected or awaiting <who>`, a row with fewer than three cells having the status `''`.
- AC-030.4 While prd.md's status is `Approved`, the lint command shall report `assumption-indexed` at each section 12 row whose status is `open` with `<A-id> is open while the PRD is Approved`.
- AC-030.5 The lint command shall report no `assumption-indexed` finding for a row whose status is `awaiting <name>`, whatever the PRD's status, nor for an `open` row while the PRD is not `Approved`.
Errors: -
Edge cases: `[ASSUMPTIONS` is not a marker (no word boundary) → AC-030.1; a marker without its colon (`A-01 text`) has no ID → AC-030.1; a bare `awaiting` is malformed → AC-030.3; a marker in a hidden Markdown file does not count (E-011) → AC-029.2, AC-030.2; when two section 12 rows hold the same A-id only the last row's status is checked, and the duplicate is id-unique's to report (lint-ids), as intended (Q-08) → AC-030.3
Tests: T-030.1 [integration], T-030.2 [integration], T-030.3 [integration], T-030.4 [integration], T-030.5 [integration], T-030.6 [integration], T-030.7 [integration], T-030.8 [integration], T-030.9 [integration], T-030.10 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; prd.md section 12

### FR-031 Require no open question once the PRD is Approved
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:329 @5824ed1
Acceptance (EARS):
- AC-031.1 While prd.md's status is `Approved`, the lint command shall report `open-questions-empty` at the first line of section 13's body whose text, stripped, is neither empty nor `None.`, with `section 13 must be 'None.' when the PRD is Approved`, and no finding for any later line.
- AC-031.2 While prd.md's status is not `Approved`, the lint command shall report no `open-questions-empty` finding.
- AC-031.3 While prd.md's status is `Approved`, if section 13 has no body line whose text, stripped, is not empty, the lint command shall report `open-questions-empty` at section 13's heading line with the message of AC-031.1.
Errors: -
Edge cases: a missing section 13 gives no finding here (FR-022 reports it); `none.` in lowercase is reported → AC-031.1; a section 13 with no text is reported (E-015) → AC-031.3
Tests: T-031.1 [integration], T-031.2 [integration], T-031.3 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; prd.md section 13

### FR-032 Report a banned glossary synonym
Status: approved
Source: prd-toolkit/scripts/prdlint/rules/structure.py:340 @5824ed1
Acceptance (EARS):
- AC-032.1 When a prose line (FR-026) outside prd.md's section 3 holds a banned synonym of section 3's glossary as a whole word in any case, optionally followed by `s`, the lint command shall report `glossary-synonym` at that line with `'<the text as written>' is a banned synonym; use '<the row's Term cell>'`, once per banned synonym per line, the banned synonyms being the comma-separated parts of the third cell of each section 3 table row with at least three cells, each part trimmed and its backticks removed.
- AC-032.2 The lint command shall report no `glossary-synonym` finding on section 3's heading or body lines, nor for a synonym inside a code span or fenced block.
- AC-032.3 The lint command shall treat a banned-synonyms part that is empty, `-`, `—` or `none` (in any case) as banning nothing.
- AC-032.4 The lint command shall report no `glossary-synonym` finding for a file under the PRD folder whose path, relative to the PRD folder, has a part starting with `.`.
Errors: -
Edge cases: YAML, SQL and JSON files are not read by this rule; the Term cell is printed as written, backticks included; a hidden file is not part of the PRD (E-011) → AC-032.4
Tests: T-032.1 [integration], T-032.2 [integration], T-032.3 [integration], T-032.4 [integration], T-032.5 [integration]  (test-cases/lint-structure.yaml)
Traces: UJ-01; cli:prd_lint; prd.md section 3
