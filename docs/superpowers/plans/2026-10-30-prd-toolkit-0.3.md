# prd-toolkit 0.3: tasks and context packs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every PRD task a focused context pack (`prd_context.py`, `/prd-context`), move the adoption map out of `prd.md`, and route the skills through the pack.

**Architecture:** The pack logic lives in `scripts/prdlint/context.py` and reads the existing `prdlint.model.Prd`; `scripts/prd_context.py` is a thin CLI in the style of `prd_trace.py`. The adoption map moves from `prd.md` §8 to `adoption.md`, read once by `model._adoption()`; every consumer goes through `Prd.adoption`. Skill and block text changes are pinned by tests, like 0.2's.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, pytest; git for staleness; `claude plugin eval` for evals.

**Spec:** `docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md`

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.3`, branch `feat/prd-toolkit-0.3`. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The repo is public and the toolkit platform-neutral: no organization hosts, users, platform object names or people in code, docs, tests or evals.
- Test-first: every rule, behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_lint.py`'s header (`#!/usr/bin/env -S uv run --script`, `requires-python = ">=3.11"`, the same three dependencies) and its `deps.require` preamble.
- Gate form for the new script: `; echo "prd-context-exit=$?"`. Exit 0 pack and sources current, 1 pack with a stale source, 2 usage or tool error with nothing on stdout.
- The linter keeps 27 rule names; 0.3 adds checks to `sections` and `index-consistent`, no new rule.
- The rendered CLAUDE.md block stays under 1,536 bytes.
- Skill text that tells an agent to run a command gives one command per Bash call with literal paths (0.2's dispatching rule).
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.

## Review Focus

1. A `Source:` field holding several `<path>:<line> @<sha>` refs across continuation lines: every ref gets its own excerpt and its own staleness check. (Task 4)
2. A cited line past the end of the file, after the file shrank: the window clamps, the excerpt is flagged stale, nothing crashes. (Task 4)
3. One area slug that is a prefix of another (`import` and `import-batch`): §13 and §14 matching treats a hyphen as part of the word, so `import` does not match `import-batch`. (Task 3)
4. `prd_context.py` run from a directory other than the repo top level, with a relative PRD path: `Source:` paths still resolve against the git top level. (Task 4)
5. A cited source file that is not valid UTF-8: the excerpt is read with replacement characters, never a crash. (Task 4)

---

### Task 1: `adoption.md` replaces the §8 table

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py` (`AdoptionRow`, `_adoption`, `load`)
- Modify: `prd-toolkit/scripts/prdlint/rules/structure.py:146-160` (`_adoption_findings`)
- Modify: `prd-toolkit/scripts/prdlint/rules/ids.py:182-184` (finding file)
- Modify: `prd-toolkit/scripts/prd_block.py:51-63` (`_adopted_areas`)
- Modify: `prd-toolkit/tests/test_trace.py` (`build` helper), `prd-toolkit/evals/scaffolds/notes_repo.py` (§8 table → `adoption.md`)
- Modify: `prd-toolkit/references/prd-format.md` (folder table, §8 row at :81, §9 sentence, a `## Tasks` section after `## Folder`), `prd-toolkit/templates/prd/prd.md:74-78`
- Modify: `prd-toolkit/skills/adopting-prds/SKILL.md` (:24, :90, :114 and every other "§8" or "adoption map" that means the table), `prd-toolkit/skills/adopting-prds/extract-prompt.md:10,101`
- Test: `prd-toolkit/tests/test_adoption_file.py` (new)

**Interfaces:**
- Produces: `model.ADOPTION_FILE = "adoption.md"`; `Prd.adoption: list[AdoptionRow] | None`, `None` exactly when `adoption.md` is absent; `AdoptionRow.line` is a line of `adoption.md`. Task 3 reads `prd.adoption`.

- [ ] **Step 1: Write the failing tests** in `tests/test_adoption_file.py`, using the `prd` fixture (a new project: §8 body `Not applicable: new project.`) and `edit`/`lint`/`fired` from `conftest`. A helper `adopt(prd, rows)` writes `adoption.md` (`# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n` + rows) and edits §8's body to `See adoption.md.`.

```python
def test_new_project_fixture_stays_clean(prd):
    assert lint(prd) == []

def test_adoption_file_is_read_into_the_model(prd):
    adopt(prd, "| import | adopted | `src/import/**` |\n| api | not started | `src/api/**` |\n")
    rows = model.load(prd).adoption
    assert [(r.area, r.state, r.boundary) for r in rows] == [("import", "adopted", ["src/import/**"]), ("api", "not started", ["src/api/**"])]
    assert rows[0].line == 5

def test_no_adoption_file_means_none(prd):
    assert model.load(prd).adoption is None

def test_table_left_in_section_8_names_the_migration(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |")
    msgs = [f.message for f in lint(prd) if f.rule == "sections"]
    assert 'section 8: the adoption map moved to adoption.md in prd-toolkit 0.3; move the table there and leave "See adoption.md."' in msgs

def test_pointer_without_file(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "See adoption.md.")
    assert any(f.file == "prd.md" and "adoption.md does not exist" in f.message for f in lint(prd))

def test_not_applicable_with_file(prd):
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | State | Boundary |\n|---|---|---|\n| import | adopted | `src/**` |\n")
    assert any('says "Not applicable: new project" but adoption.md exists' in f.message for f in lint(prd))

def test_other_section_8_body(prd):
    edit(prd, "prd.md", "Not applicable: new project.", "Areas are listed elsewhere.")
    assert any('section 8 body must be "See adoption.md." or "Not applicable: new project."' in f.message for f in lint(prd))

def test_bad_header_and_state_report_adoption_md(prd):
    adopt(prd, "| import | half-done | `src/**` |\n")
    found = [f for f in lint(prd) if f.rule == "sections" and f.file == "adoption.md"]
    assert [f.line for f in found] == [5]
    (prd / "adoption.md").write_text("# Adoption map\n\n| Area | Status | Files |\n|---|---|---|\n| import | adopted | `src/**` |\n")
    assert any(f.file == "adoption.md" and "header must be '| Area | State | Boundary |'" in f.message for f in lint(prd))

def test_index_consistent_reports_adoption_md(prd):
    adopt(prd, "| billing | adopted | `src/billing/**` |\n")
    assert any(f.rule == "index-consistent" and f.file == "adoption.md" and f.line == 5 for f in lint(prd))

def test_block_lists_adopted_areas_from_adoption_md(prd):
    adopt(prd, "| import | adopted | `src/**` |\n| api | confirmed | `src/api/**` |\n")
    assert "Adopted areas: import" in prd_block.render_block(model.load(prd), "docs/prd/orders")
```

Each file-level message ends in the exact strings above. A §8 body is compared after stripping whitespace and one trailing `.`.

- [ ] **Step 2: Run them to see them fail**

Run: `uv run --directory prd-toolkit pytest -q tests/test_adoption_file.py`
Expected: FAIL (the table-in-§8 test passes clean, the `adoption.md` tests find no rows).

- [ ] **Step 3: Implement.** `_adoption(docs)` reads the first table of `docs["adoption.md"]` (`None` when the key is absent, `[]` when the file has no table). `_adoption_findings` checks the §8 body against `ADOPTION_FILE in prd.docs`, then the `adoption.md` header (a missing table is `adoption.md holds no '| Area | State | Boundary |' table`) and states, all with file `adoption.md` except the §8 body findings (file `prd.md`, line of §8). `ids.py` reports `adoption.md`. `prd_block._adopted_areas` uses `prd.adoption`; with `None` it keeps today's "Not applicable: new project" check of the §8 body.

- [ ] **Step 4: Migrate the other §8 users.** `test_trace.build` writes `adoption.md` and `See adoption.md.`; `notes_repo.py` writes `adoption.md` and the pointer, and its state variants substitute rows in `adoption.md`. Run: `uv run --directory prd-toolkit pytest -q`. Expected: all pass.

- [ ] **Step 5: Docs and skill text.** `prd-format.md`: the folder table lists `adoption.md` (optional: present for an adopted project); the §8 row says the body is `See adoption.md.` or `Not applicable: new project.` and the table lives in `adoption.md`; §9 gains "A toolkit format migration, such as moving the adoption map, is a patch."; the `## Tasks` section is spec section 2's quoted text verbatim. Template §8 marker names the two bodies. adopting-prds: the bootstrap creates `adoption.md` and writes `See adoption.md.` into §8; every "§8" meaning the table becomes "`adoption.md`". Add to `tests/test_adoption_file.py`, failing first:

```python
def test_format_reference_has_the_tasks_table():
    text = (ROOT / "references/prd-format.md").read_text()
    assert "## Tasks" in text and "| New sub-project |" in text and "| Bug fix |" in text
    assert "A toolkit format migration, such as moving the adoption map, is a patch." in text

def test_adopting_skill_names_adoption_md_not_section_8_table():
    text = (ROOT / "skills/adopting-prds/SKILL.md").read_text()
    assert "`adoption.md`" in text and "See adoption.md." in text
    assert "replace §8's marker with the" not in text
```

- [ ] **Step 6: Run the suite** — `uv run --directory prd-toolkit pytest -q` — Expected: all pass.

- [ ] **Step 7: Commit** — `git add -A prd-toolkit && git commit -m "feat(prd-toolkit): the adoption map moves to adoption.md"` (with the trailer).

---

### Task 2: `Touches:` in `errors.md`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py` (`ErrorEntry`, `_errors_ledger`)
- Modify: `prd-toolkit/scripts/prdlint/rules/ids.py` (`index_consistent`)
- Modify: `prd-toolkit/references/prd-format.md:257-270`, `prd-toolkit/skills/adopting-prds/SKILL.md:148`, `prd-toolkit/skills/adopting-prds/extract-prompt.md:89-95`
- Test: `prd-toolkit/tests/test_touches.py` (new)

**Interfaces:**
- Produces: `ErrorEntry.touches: list[tuple[str, int]]` (requirement ID, line), empty when the entry has no `Touches:` line; `ErrorEntry.end: int`, the entry's last line (the line before the next heading, or the file's last line). Task 3 slices entry text with `line` and `end`.

- [ ] **Step 1: Write the failing tests.** Append to the fixture's `errors.md` with `edit`/write in each test:

```python
OPEN = "\n### E-002 Duplicate check ignores case\nDetected: 2026-10-30, review\nClassification: code bug\nTouches: FR-001, NFR-004\nDiagnosis: keys compare case-sensitively\nResolution: open\nRecurrence of: -\n"

def test_touches_is_parsed(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    e = model.load(prd).errors_ledger["E-002"]
    assert [t for t, _ in e.touches] == ["FR-001", "NFR-004"] and e.open
    assert model.load(prd).errors_ledger["E-001"].touches == []

def test_entry_end_line(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    led = model.load(prd).errors_ledger
    assert led["E-001"].end < led["E-002"].line and led["E-002"].end == len((prd / "errors.md").read_text().rstrip("\n").split("\n"))

def test_dangling_touches_is_index_consistent(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN.replace("NFR-004", "FR-099"))
    found = [f for f in lint(prd) if f.rule == "index-consistent" and f.file == "errors.md"]
    assert [f.message for f in found] == ["E-002 Touches FR-099, which no block defines"]

def test_valid_touches_lints_clean(prd):
    (prd / "errors.md").write_text((prd / "errors.md").read_text() + OPEN)
    assert lint(prd) == []

def test_format_and_extract_prompt_document_touches():
    assert "Touches: <requirement IDs or ->" in (ROOT / "references/prd-format.md").read_text()
    assert "Touches:" in (ROOT / "skills/adopting-prds/SKILL.md").read_text().split("APPARENT BUGS", 1)[1][:400]
```

- [ ] **Step 2: Run to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_touches.py` — Expected: FAIL (`ErrorEntry` has no `touches`).

- [ ] **Step 3: Implement.** `Touches:` is a comma-separated list of `UJ-nn`/`FR-nnn`/`NFR-nnn` IDs; `-` means none. `index_consistent` yields `Finding("errors.md", line, "index-consistent", f"{e} Touches {id}, which no block defines")`. `prd-format.md`'s entry grammar gains `Touches: <requirement IDs or ->` after `Classification:`, marked optional, with the spec section 4 sentence. Adopting step 2 writes each APPARENT BUGS entry with its `Touches:` line; the extract prompt's report line stays and now says the bootstrap copies it into the entry.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): errors.md entries name the requirements they touch`.

---

### Task 3: `prd_context.py`, the `decide` and repo packs

**Files:**
- Create: `prd-toolkit/scripts/prdlint/context.py`, `prd-toolkit/scripts/prd_context.py`
- Create: `prd-toolkit/tests/context_fixture.py` (helper), `prd-toolkit/tests/test_context.py`

**Interfaces:**
- Consumes: `model.load`, `Prd.adoption` (Task 1), `ErrorEntry.touches/.end` (Task 2), `rules.contracts.custom_items`.
- Produces, in `prdlint/context.py`:

```python
PARTS = ("Header", "Stack", "Glossary", "Requirements", "Code", "Levels", "Cited", "Known defects", "Open questions", "History")
PARTS_REPO = ("Header", "Stack", "Areas")

@dataclass
class Item:
    part: str
    id: str | None
    file: str          # PRD-relative; repo-relative for Code items
    line: int | None
    text: str
    stale: bool = False

class ContextError(Exception): ...   # every exit-2 condition

def build_pack(prd: Prd, area: str | None, req: list[str] | None, mode: str = "decide",
               context: int = 20, repo_root: Path | None = None, display: str = "") -> list[Item]
def render_text(items: list[Item]) -> str
def render_json(items: list[Item]) -> str
```

  `prd_context.py main(argv) -> int` parses the spec's arguments, prints `render_text` or `render_json`, and returns the exit code. `--req` splits on commas, strips whitespace and uppercases.

- [ ] **Step 1: Write the fixture helper** `context_prd(tmp_path) -> Path`: copies `fixtures/valid/orders` to `tmp_path/docs/prd/orders`, then:
  - writes `adoption.md` with rows `import | adopted | \`src/import/**\`` and `api | confirmed | \`src/api/**\``, and sets §8 to `See adoption.md.`;
  - adds `NFR-004` to FR-002's `Traces:` line;
  - adds glossary rows `| importer | The job that loads an orders file | loader |` (FR-001 uses the word) and `| invoice | A bill sent after shipping | bill |` (no block uses it);
  - appends E-002 (open, `Touches: FR-001`), E-003 (open, `Touches: FR-002`), E-004 (open, no `Touches:`) to `errors.md`;
  - replaces §13's `None.` with `- Q-01 Should FR-001 skip blank rows?`, `- Q-02 Does the import area accept CSV only?`, `- Q-03 Is AC-002.1 still wanted?`, `- Q-04 Who owns the product?`, `- Q-05 Should import-batch retry?`;
  - appends §14 rows `| 1.1.0 | 2026-10-30 | import: blank rows | FR-001 |`, `| 1.2.0 | 2026-10-30 | api: 410 for deleted | FR-003 |`, and three more import rows (1.3.0, 1.4.0, 1.5.0), bumping the frontmatter version to 1.5.0.

  It asserts `lint(root) == []` before returning, so every context test runs on a valid PRD.

- [ ] **Step 2: Write the failing tests** in `tests/test_context.py`. `pack(root, *args)` runs `main` with `capsys` and returns `(exit, stdout, stderr)`; `parts(stdout)` splits on `## ` headings.

```python
def test_area_pack_holds_the_area_and_what_it_cites(ctx):
    code, out, _ = pack(ctx, "--area", "import")
    assert code == 0
    for s in ("### FR-001 Import an orders file", "IMPORT_DUPLICATE:", "IMPORT_EMPTY:", "### E-002", "| importer |", "Q-01", "Q-02", "## Stack"):
        assert s in out

def test_focus_area_pack_leaves_out_everything_else(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    for s in ("FR-002", "FR-003", "UJ-01", "### NFR-004", "ORDER_NOT_FOUND:", "### E-003", "### E-004", "### E-001", "| invoice |", "Q-03", "Q-04", "Q-05", "1.2.0"):
        assert s not in out
    assert "expect:" not in out   # no test-cases text; every case in the fixture has `expect:`
    assert "1 open errors.md entries name no requirement" in out
    assert "3 other open questions in prd.md §13" in out

def test_history_is_the_last_three_area_rows(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    hist = parts(out)["History"]
    assert [v for v in ("1.0.0", "1.1.0", "1.3.0", "1.4.0", "1.5.0") if v in hist] == ["1.3.0", "1.4.0", "1.5.0"]

def test_req_pulls_traced_uj_and_its_assumption(ctx):
    _, out, _ = pack(ctx, "--area", "api", "--req", "fr-002")
    assert "### FR-002" in out and "### UJ-01" in out and "| A-01 |" in out and "### NFR-004" in out
    assert "### FR-003" not in out and "### E-003" in out and "Q-03" in out

def test_cross_area_id_is_labelled(ctx):
    _, out, _ = pack(ctx, "--area", "api", "--req", "FR-002,FR-001")
    assert "(area: import)" in out

def test_slug_prefix_does_not_match(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    assert "Q-05" not in out

def test_repo_pack_lists_areas(ctx):
    code, out, _ = pack(ctx)
    assert code == 0 and "## Areas" in out and "import" in out and "adopted" in out and "src/api/**" in out
    assert "## Requirements" not in out

def test_repo_pack_without_adoption_file_lists_feature_slugs(prd):
    _, out, _ = pack(prd)
    assert "api" in parts(out)["Areas"] and "import" in parts(out)["Areas"]

@pytest.mark.parametrize("args", [["--area", "billing"], ["--area", "import", "--req", "FR-099"], ["--req", "FR-001"], ["--for", "implement"]])
def test_exit_2_prints_nothing(ctx, args):
    code, out, err = pack(ctx, *args)
    assert code == 2 and out == "" and err

def test_size_line_matches_the_bytes(ctx):
    _, out, _ = pack(ctx, "--area", "import")
    m = re.search(r"pack ([\d,]+) bytes .*prd\.md ([\d,]+); features/import\.md ([\d,]+)", out)
    body = out.split("\n## Stack", 1)[1]
    assert int(m[1].replace(",", "")) == len(("## Stack" + body).encode())
    assert int(m[2].replace(",", "")) == (ctx / "prd.md").stat().st_size

def test_json_matches_text_and_runs_are_identical(ctx):
    _, text, _ = pack(ctx, "--area", "api")
    _, js, _ = pack(ctx, "--area", "api", "--json")
    items = json.loads(js)
    assert {i["part"] for i in items} == set(parts(text)) and all(set(i) == {"part", "id", "file", "line", "text", "stale"} for i in items)
    assert pack(ctx, "--area", "api")[1] == text
```

- [ ] **Step 3: Prove the focus test can fail.** Temporarily make `build_pack` add every block of the PRD to Requirements; run `test_focus_area_pack_leaves_out_everything_else`; it must fail; revert. Record the failing output in the task report.

- [ ] **Step 4: Run all of them to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_context.py` — Expected: FAIL (no module `prd_context`).

- [ ] **Step 5: Implement.** Rules the tests leave open:
  - **Size line**: `pack <n> bytes (~<n/4 rounded, as 4.6k> tokens, bytes / 4); prd.md <n>; features/<area>.md <n>`, numbers with thousands commas. `<n>` counts the UTF-8 bytes of the rendered text from the `## Stack` heading to the end. The repo pack omits the features field.
  - **Header** lines: `PRD: <display> version <v> mode <mode>`, `Area: <slug> (<state>; Boundary: <globs>)` with state `-` and no Boundary when the area has no adoption row, then the size line.
  - **Block text** is the heading line plus the block's body lines, trailing blank lines dropped.
  - **Word match** for glossary terms and slugs: `(?<![\w-])<term>(?![\w-])`, case-insensitive for glossary terms, exact for slugs and IDs.
  - **Cited**: NFR IDs named in a selected block's text and not already selected; `Errors:` codes with their `contracts/errors.yaml` value dumped as `yaml.safe_dump({code: value}, sort_keys=False)`; `<type>:<name>` tokens whose type and key appear in `custom_items(prd)`, dumped the same way from the file that holds the key; `A-nn` inside `[ASSUMPTION` markers, with the §12 table header and that row.
  - **Questions**: the `- ` items of §13 with their indented continuation lines.
  - **Order**: items keep PRD file order within each part.
  - **Valid area**: one with an adoption row or a `features/<area>.md`. A `not started` area with no features file gives an empty Requirements part.
  - **Display path**: relative to the working directory when it is under it, as `prd_lint._display_root` does.

- [ ] **Step 6: Run to see them pass**, then the suite — Expected: all pass.

- [ ] **Step 7: Commit** — `feat(prd-toolkit): prd_context.py prints a task's decide pack`.

---

### Task 4: `implement` packs, code excerpts and staleness

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/context.py`, `prd-toolkit/scripts/prd_context.py`
- Test: `prd-toolkit/tests/test_context_implement.py` (new)

**Interfaces:**
- Consumes: Task 3's `build_pack`, `Item`, `ContextError`; `model.repo_root`.
- Produces: `Code` items (`file` repo-relative, `line` the cited line, `stale` set) and one `Levels` item; `main` returns 1 when any `Code` item is stale.

- [ ] **Step 1: Write the failing tests.** A fixture `repo(tmp_path)` runs `git init` in `tmp_path`, writes `src/importer.py` (60 numbered lines `line 1` … `line 60`) and `src/legacy.bin` (bytes `b"ok\xff\xfe\n" * 30`), commits them, copies `context_prd` to `docs/prd/orders`, sets FR-001's `Source:` to `src/importer.py:30 @<sha>` with a continuation line `  src/legacy.bin:3 @<sha>`, commits again and returns `(root, prd, sha)`.

```python
def test_excerpt_window_and_exit_0(repo):
    root, prd, sha = repo
    code, out, _ = pack(prd, "--area", "import", "--for", "implement", "--context", "5")
    code_part = parts(out)["Code"]
    assert code == 0 and "line 25" in code_part and "line 35" in code_part and "line 24" not in code_part and "line 36" not in code_part
    assert "STALE" not in out and "## Levels" in out and "pytest tests/integration" in out

def test_every_ref_of_a_multi_line_source(repo):
    _, prd, _ = repo
    out = pack(prd, "--area", "import", "--for", "implement")[1]
    assert "src/importer.py:30" in out and "src/legacy.bin:3" in out and "�" in out

def test_changed_file_is_stale_exit_1(repo):
    root, prd, sha = repo
    (root / "src/importer.py").write_text("changed\n" * 10)
    commit(root, "change")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and f"STALE: changed since {sha}" in out
    assert "   10  changed" in out and "   11  " not in parts(out)["Code"]   # window clamped to the 10-line file

def test_unknown_sha_and_missing_file_are_stale(repo):
    root, prd, sha = repo
    edit(prd, "features/import.md", f"src/importer.py:30 @{sha}", "src/importer.py:30 @0000000")
    edit(prd, "features/import.md", f"src/legacy.bin:3 @{sha}", f"src/gone.py:3 @{sha}")
    code, out, _ = pack(prd, "--area", "import", "--for", "implement")
    assert code == 1 and "STALE: unknown commit 0000000" in out and "STALE: file missing" in out

def test_runs_from_another_directory(repo, monkeypatch):
    root, prd, _ = repo
    monkeypatch.chdir(prd / "features")
    code, out, _ = pack(Path(".."), "--area", "import", "--for", "implement")
    assert code == 0 and "line 30" in out

def test_implement_outside_git_exits_2(ctx):
    code, out, err = pack(ctx, "--area", "import", "--for", "implement")
    assert code == 2 and out == "" and "git" in err

def test_decide_ignores_staleness(repo):
    root, prd, _ = repo
    (root / "src/importer.py").write_text("x\n")
    assert pack(prd, "--area", "import")[0] == 0
```

`commit(root, msg)` is a helper in the same file (`git add -A` then `git commit -qm`, with `-c user.name=t -c user.email=t@example.com`).

- [ ] **Step 2: Run to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_context_implement.py` — Expected: FAIL (no `Code` part).

- [ ] **Step 3: Implement.** Refs match `(?P<path>[^\s@]+):(?P<line>\d+)\s+@(?P<sha>[0-9a-fA-F]{4,40})` over the whole `Source:` text. Staleness, in order: `git cat-file -e <sha>^{commit}` fails → `unknown commit <sha>`; the file is missing → `file missing`; `git log --format=%H <sha>..HEAD -- <path>` prints anything → `changed since <sha>`. A cited line past the file's end clamps the window to the file and is stale with `line <n> is past the end (<len> lines)` when no other reason applies. An item's text is the heading `### <path>:<line> @<sha>`, then `STALE: <reason>; the cited line may have moved` when stale, then lines as `f"{n:>5}  {text}"` read with `errors="replace"`. "Outside a git work tree" is `git rev-parse --is-inside-work-tree` failing from the PRD folder. Code and Levels sit after Requirements, per `PARTS`.

- [ ] **Step 4: Run to see them pass**, then the suite — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): implement packs carry staleness-checked code excerpts`.

---

### Task 5: Routing — `/prd-context`, skills and the managed block

**Files:**
- Create: `prd-toolkit/commands/prd-context.md`
- Modify: `prd-toolkit/skills/changing-prds/SKILL.md` (rules list :33-46, step 1 :83-88, step 5 :117-127)
- Modify: `prd-toolkit/skills/adopting-prds/SKILL.md` (step 3 "How to ask" :187 and the checklist file paragraph)
- Modify: `prd-toolkit/templates/claude-block.md`
- Test: `prd-toolkit/tests/test_context_routing.py` (new); update any `tests/test_block.py` assertion on the replaced bullet

**Interfaces:**
- Consumes: `prd_context.py`'s CLI (Tasks 3–4).
- Produces: the command `/prd-context <area> [IDs] [implement]`; the script form the skills use:
  `uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_context.py" docs/prd/<slug> --area <area> --req <IDs>; echo "prd-context-exit=$?"`.

- [ ] **Step 1: Write the failing pins.**

```python
BULLET = ("To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD\n"
          "  files only to edit them. Before writing code for an approved change, run `/prd-context <area>\n"
          "  <IDs> implement`. Code implements the PRD; it never defines behaviour the PRD lacks.")

def test_block_bullet():
    t = (ROOT / "templates/claude-block.md").read_text()
    assert BULLET in t and "Read the PRD, not the code, to learn" not in t

def test_block_stays_small(prd):
    adopt(prd, "".join(f"| area-{i:02} | adopted | `src/a{i}/**` |\n" for i in range(20)))
    add_required_skills(prd, 4)   # the fixture's skills rows plus four more, all required
    assert len(prd_block.render_block(model.load(prd), "docs/prd/orders").encode()) < 1536

def test_changing_step_1_runs_the_decide_pack():
    step1 = section(CHANGING, "1. **Restate the change**", "2. **Edit the PRD.**")
    assert "scripts/prd_context.py" in step1 and 'echo "prd-context-exit=$?"' in step1
    assert "read whole PRD files only to edit them" in (ROOT / "skills/changing-prds/SKILL.md").read_text()
    assert "Grep the PRD folder for each ID" not in step1

def test_changing_step_5_hands_off_the_implement_pack():
    step5 = section(CHANGING, "5. **Approval, then commit.**", "## Red Flags")
    assert "/prd-context <area> <changed IDs> implement" in step5

def test_adopting_previews_come_from_the_implement_pack():
    how = section(ADOPTING, "**How to ask.**", "**The checklist file.**")
    assert "--for implement --req" in how and "prd-context-exit" in how

def test_command_maps_arguments():
    t = (ROOT / "commands/prd-context.md").read_text()
    assert t.startswith("---\ndescription: ") and "scripts/prd_context.py" in t and "--for implement" in t and "--req" in t and "prd-context-exit" in t
```

`section(path, start, end)` returns the text between the two markers. `adopt` is imported from Task 1's test module. `add_required_skills(prd, n)` appends `n` rows `| Skill <i> | example:skill-<i> | required |` to the §6 table with `edit`. The test renders the block without linting, so the 20 areas need no feature files.

- [ ] **Step 2: Run to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_context_routing.py` — Expected: FAIL.

- [ ] **Step 3: Write the text.**
  - **The command**: find the one `docs/prd/*/prd.md` (more than one: ask which); map the first argument that is neither an ID nor `implement` to `--area`, ID arguments to one `--req`, and `implement` to `--for implement`; run the script in the gate form; print its output; on `prd-context-exit=1`, re-read the regions marked STALE before relying on them.
  - **changing-prds**:
    - a new non-negotiable rule 6, **Read whole PRD files only to edit them**, which says to work from the pack and to open another PRD file only for what its closing lines name;
    - step 1 runs the script for the area and the IDs the change touches, with no `--area` for a new sub-project and with the entry's `Touches:` IDs for a bug fix. This replaces "Grep the PRD folder for each ID and code";
    - step 5 ends with "Hand off: write the code from `/prd-context <area> <changed IDs> implement`."
  - **adopting step 3**: each preview and checklist item is the output of `prd_context.py … --area <area> --for implement --req <ID>`, run in the gate form, one Bash call per requirement.
  - **Block**: the first bullet becomes `BULLET`.

- [ ] **Step 4: Run the suite** — Expected: all pass; `uv run --directory prd-toolkit pytest -q tests/test_block.py` included.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): tasks run through /prd-context`.

---

### Task 6: Eval `change-uses-context-pack` and the §8 eval updates

**Files:**
- Create: `prd-toolkit/evals/change-uses-context-pack/{case.yaml,scaffold.sh,prompt.md,graders/*.md}`
- Modify: `prd-toolkit/evals/baselines/adopting-prds.md`, `prd-toolkit/evals/baselines/authoring-prds.md`, any grader that reads §8, `prd-toolkit/evals/BASELINE.md`
- Test: `prd-toolkit/tests/test_eval_graders.py` (its existing checks must cover the new eval)

- [ ] **Step 1: Write the eval.**
  - `scaffold.sh` copies `changing-major-bump/scaffold.sh` unchanged in form: the orders fixture in a fresh git repo, whose two areas are `import` and `api`.
  - `prompt.md` uses the same frontmatter as `changing-major-bump/prompt.md` with the body: "An import file with a blank line between rows should skip the blank line instead of failing. Do not ask me questions."
  - The graders:
    - `skill-fired.md`: changing-prds is invoked (copy the existing one);
    - `ran-pack.md`: `type: tool_used`, `tool: Bash`, `input_match: 'prd_context\.py'`, `min: 1`;
    - `no-other-area.md`: `tool: Read`, `input_match: '"file_path"\s*:\s*"[^"]*features/api\.md"'`, `min: 0`, `max: 0`;
    - `no-test-cases-read.md`: `tool: Read`, `input_match: '"file_path"\s*:\s*"[^"]*/test-cases/'`, `min: 0`, `max: 0`.
  - The prose of each grader says what it checks. Ordering ("before the first PRD edit") is pinned by Task 5's step 1 text, because graders cannot check order. Say that in `ran-pack.md`.

  `no-test-cases-read.md` assumes changing-prds does not read test cases to revise them. If the run shows it must (step 2 revises test cases whose AC changed), narrow the grader to `test-cases/api\.yaml` and record why in `BASELINE.md`.

- [ ] **Step 2: Update the §8 evals.** Grep the `evals/` tree for `Adoption map`, `§8` and `| Area | State |`, and point each check at `adoption.md`.

- [ ] **Step 3: Run the grader tests** — `uv run --directory prd-toolkit pytest -q tests/test_eval_graders.py` — Expected: pass.

- [ ] **Step 4: Run the evals.** Use the command in `evals/BASELINE.md`: the new eval, `adoption-second-area-minor`, `adopting-trigger`, `changing-major-bump`, and `changing-new-id-not-reused`. Record the pass rates in `BASELINE.md` as 0.2 did. A failing grader is investigated and fixed in the skill text, with a pin, not by loosening the grader.

- [ ] **Step 5: Commit** — `test(prd-toolkit): eval that a change works from the context pack`.

---

### Task 7: Release 0.3.0 text and versions

**Files:**
- Modify: `prd-toolkit/.claude-plugin/plugin.json` (version, description adds `/prd-context`), `.claude-plugin/marketplace.json:25`, `web/src/data/plugins.js:44` and its command list, `prd-toolkit/README.md` (:5 version, a 0.3.0 bullet after :120, the command list), the root `README.md` if it lists the toolkit's commands
- Modify: `docs/superpowers/specs/2026-10-29-prd-toolkit-design.md:491-492` (the milestone table)
- Test: `web` tests that pin the plugin text; `prd-toolkit/tests/test_references.py` if it pins the README

- [ ] **Step 1: Update the pins first**, so the web and README tests fail on the old text.

- [ ] **Step 2: Write the text.**
  - **Versions**: 0.3.0 everywhere.
  - **README 0.3.0 bullet**: `/prd-context` and `prd_context.py` (decide and implement packs); `adoption.md`; `Touches:` in `errors.md`; changing-prds works from the pack. Upgrade note: "Upgrading a 0.2 PRD: it fails `sections` until §8's table moves to `adoption.md` and §8 reads `See adoption.md.`, a patch bump."
  - **Base spec §9**: insert the 0.3 row ("Tasks and context packs: `prd_context.py`, `/prd-context`, `adoption.md`, `Touches:`" | "The adopted Looker area migrated and one change made from the pack"). Renumber the old 0.3 row to 0.4 and the old 0.4 row to 0.5. Add a note citing the 0.3 spec.

- [ ] **Step 3: Verify** — `uv run --directory prd-toolkit pytest -q`, `cd web && npm test`, `claude plugin validate ./prd-toolkit` — Expected: all pass, and validate prints no errors.

- [ ] **Step 4: Commit** — `chore(prd-toolkit): release 0.3.0`.

---

### Task 8: Proof on the Looker PRD (interactive)

**Starts only when** the 0.2 PR has merged and Ivan has approved the first adopted area of the Looker PRD. Ivan drives it in his own session. The controller gives him the pastes and records the results.

**Files:**
- Create: `docs/superpowers/plans/2026-10-30-prd-toolkit-0.3-acceptance.md`
- Outside this repo (Ivan's session, his branch): the Looker PRD folder

- [ ] **Step 1: Rebase.** Run `git rebase main` on `feat/prd-toolkit-0.3` after the 0.2 merge. Rerun the suite.
- [ ] **Step 2: Migrate.** In the Looker PRD, move the §8 table to `adoption.md`, write `See adoption.md.`, bump the patch version and add the §14 row `format: adoption map moved to adoption.md (prd-toolkit 0.3)`. The `prd-lint-exit=` value must be `0`. Record `prd.md` bytes before and after. Committing and pushing on that repo need Ivan's go-ahead.
- [ ] **Step 3: Measure.** Record the size lines of three packs for the adopted area: `decide` for the whole area, `decide --req <one FR>` and `implement --req <one FR>`. Compare them with `prd.md` plus the area's features file. Pass: the single-FR `decide` pack is under 20,000 bytes.
- [ ] **Step 4: One real change.** Ivan picks one small change, for example one of the area's open `E-nnn` fixes. He runs it through changing-prds with 0.3 loaded. From the transcript, list every Read of a PRD file that was neither the pack nor a file the change edited. Pass: none. Each one found is a pack gap: fix it with a test on this branch, or list it as a later item.
- [ ] **Step 5: Write the acceptance note.** Record the numbers, the gaps and their dispositions. It names no hosts, users, platform objects or people. Grep it for the organization's name before committing. Commit: `docs(prd-toolkit): 0.3 acceptance`.

---

### Task 9: Pull request

- [ ] **Step 1:** Use superpowers:finishing-a-development-branch. Rerun the suite, `npm test` and `claude plugin validate`.
- [ ] **Step 2:** Ask Ivan before pushing. Then push `feat/prd-toolkit-0.3` and open a PR to `main` on GitHub `ihistand/claude-plugins`. The body lists every "Ruling:" line from the SDD ledger, the milestone renumbering and the upgrade note, and ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Name no reviewers.
