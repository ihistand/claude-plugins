# prd-toolkit 0.8.0: target profiles, packs, languages and judged cases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a PRD describe output other than a service (a Markdown document first) in a human language other than English, extend the toolkit through version-locked packs that any plugin ships, and test what a script cannot check exactly with model-judged rubric cases.

**Architecture:** The model parses the new profile lines (`Pack:`, `Output language:`, `Target:`) once; `prdlint/packs.py` loads, validates, resolves and locks `pack.yaml` manifests from the vendored copy, the toolkit's `packs/` or an installed plugin's `prd-packs/`; `prdlint/languages.py` serves the EARS openers, vague words and page labels of the PRD's `language:`. Rules ask those two modules, never the files. `prd_judge.py` (logic in `prdlint/judge.py`) runs a judged case through headless `claude -p` or a pack grader, checks every quote against the output, and records each run.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, sqlglot, pytest; git; Claude Code CLI 2.1.317 (`claude -p`); `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.0-design.md` (governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`)

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8`, branch `feat/prd-toolkit-0.8`. **Before Task 1**, `main` must hold 0.7.1 (`git -C … log main --oneline | head` shows the 0.7.1 merge); then `git merge main` into the branch once. If 0.7.1 has not merged, stop and say so. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- The repo is public and the toolkit platform-neutral: no organization hosts, users, platform object names or people in code, docs, tests or evals. Example slugs are `greet`, `orders`, `guide`, `dashboards`; the example external pack is `demo`.
- Test-first: every rule, behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_build_check.py`'s header and `deps.require` preamble. No new third-party dependency: the manifest schema and the `toolkit:` specifier are parsed in plain Python.
- The linter goes from 36 rule names to 40: `language-table`, `pack-resolves`, `judged-case` (error) and `platform-word` (warn). Each task that adds one adds it to `SPEC_RULES` in `tests/test_coverage.py`, and its failing cases to `tests/test_rules_packs.py` (new, added to `test_every_rule_has_a_failing_case`'s imports in Task 1).
- Names, exactly: frontmatter `language`; §1 lines `- Pack: <name> <X.Y.Z> (<source>)` and `- Output language: <code>`; area line `Target: pack <name> <X.Y.Z> (<source>)[, output language <code>]` or `Target: output language <code>`; manifest `pack.yaml`; plugin folder `prd-packs/<name>/`; vendored `.prd-toolkit/packs/<name>/`; §7 Validator cell `pack`; record dir `.prd-judge/`; expansion `${PACK}`; §14 row `format: target profiles (prd-toolkit 0.8)`.
- Severity line, exactly: `<file>:<line>: warn: <rule>: <message>`. The exit code counts errors only.
- `en.yaml` reproduces 0.7 exactly: openers `When`, `While`, `If`, `Where`; ubiquitous `^The \S.*? shall\b`; vague `fast|secure|scalable|robust|intuitive|seamless|user-friendly`. Every existing fixture's lint output stays byte-identical.
- Skill text that tells an agent to run a command gives one command per Bash call with literal paths, naming the vendored `.prd-toolkit/` copy or an absolute plugin path, never `${CLAUDE_PLUGIN_ROOT}` inside a Bash command (0.5's R20). `${PACK}` is expanded by the scripts, never by a shell.
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.
- **Ruling (plan, spec §7):** the quote check compares after collapsing every run of whitespace to one space, on both the quote and the output; nothing else is normalized (case, punctuation and quotes stay exact). A grader that re-wraps a line still passes; one that paraphrases does not.
- **Ruling (plan, spec §7):** the default grader runs `claude -p --output-format json --json-schema <schema> --tools "" --strict-mcp-config --setting-sources "" --disable-slash-commands --no-session-persistence [--model M]`, prompt on stdin, cwd a fresh `tempfile.mkdtemp()`. Not `--bare`: it requires `ANTHROPIC_API_KEY`, and the spec needs no key. Task 7 confirms the flags live and pins them. The binary is `$PRD_JUDGE_CLAUDE` when set (tests), else `claude`.
- **Ruling (plan, spec §9):** authoring phase 1 lists packs with `prd_lint.py --list-packs`, one line per pack: `<name> <version> (<source>) — <description>`, built-ins first, then installed plugins in `installed_plugins.json` order. No new script.
- **Ruling (plan, spec §4):** `${PACK}` is substituted per argument after `shlex.split`, so a pack path with spaces stays one argument.
- **Ruling (plan, spec §3):** the `Target:` line is the first line at column 0 matching `^Target:` that comes after the level-1 heading and before the first level-3 heading; blank lines and HTML comments between are allowed. A `Target:` line after the first level-3 heading is a `pack-resolves` finding (`Target: must come before the first requirement`).

## Review Focus

1. A repository vendored by 0.7 (`.prd-toolkit/` with no `packs/`) linted by 0.8.0, with no `Pack:` line: no `pack-resolves` finding, and lint output is what 0.7 printed. A missing default pack never fails a PRD that names none. (Tasks 3, 8)
2. A pack installed under a path with spaces (a plugin cache under `~/My Plugins/…`): its `${PACK}` validator and grader run as one argument and pass. (Tasks 3, 4, 7)
3. A grader quote that re-wraps a line of the output (a line break becomes a space) counts as a pass; a quote with one word changed counts as a fail. (Task 7)
4. A `features/<area>.md` whose `Target:` line sits below the template's `<!-- Format … -->` comment and a blank line resolves; one placed after the first `###` block is reported, not silently ignored. (Task 3)
5. `claude` present but signed out, or exiting non-zero for any reason, makes `prd_judge.py` exit 2 with the CLI's first stderr line, never exit 1 and never a pass. (Task 7)

---

### Task 1: Lint severity

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/findings.py`, `prd-toolkit/scripts/prdlint/registry.py`, `prd-toolkit/scripts/prd_lint.py`, `prd-toolkit/tests/test_coverage.py`
- Create: `prd-toolkit/tests/test_rules_packs.py` (`CASES = []` for now), `prd-toolkit/tests/test_severity.py`

**Interfaces:**
- Produces: `Finding(file, line, rule, message, severity: str = "error")` (still frozen, ordered on the first four fields: `severity` gets `field(default="error", compare=False)`); `str(f)` adds `warn: ` before the rule for a warn. `registry.SEVERITY: dict[str, str]` (rule → severity, default `error`) filled by `rule(name, severity="error")`. `registry.run(prd, only=None, warnings=False) -> list[Finding]` drops warns unless `warnings=True`. `prd_lint.py` calls `run(prd, warnings=True)`, prints warns in the same prefix form, returns 1 only when an error is present; `--list-rules` prints `<rule> <severity>` per line.

- [ ] **Step 1: Write the failing tests** in `test_severity.py`: register a throwaway warn rule in a fixture (remove it in teardown) that yields one finding on the valid fixture; assert `str(f) == "prd.md:1: warn: t-warn: m"`; `registry.run(model.load(prd)) == []`; `registry.run(..., warnings=True)` holds it; `prd_lint.main([str(prd)])` returns 0 and prints the warn line; an error rule plus the warn returns 1; `--list-rules` lists `ac-ears error`; `deploy.preflight` reasons do not include `prd_lint has findings` with only the warn; `prd_error.py`'s lint step ignores it. Add `test_rules_packs` to the module tuple in `test_every_rule_has_a_failing_case`.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** the four signatures above.
- [ ] **Step 4: Run the suite;** all pass, every existing lint output unchanged.
- [ ] **Step 5: Commit** `feat(prd-toolkit): lint severity warn` (`Refs: none`).

### Task 2: Language tables, `language:` and `language-table`

**Files:**
- Create: `prd-toolkit/references/languages/en.yaml`, `prd-toolkit/references/languages/es.yaml`, `prd-toolkit/scripts/prdlint/languages.py`
- Modify: `prd-toolkit/scripts/prdlint/rules/ids.py` (`ac-ears`), `prd-toolkit/scripts/prdlint/rules/structure.py` (`vague-word`, `frontmatter` accepts `language`, new `language-table`), `prd-toolkit/tests/test_coverage.py`
- Test: `prd-toolkit/tests/test_languages.py` (new), `test_rules_packs.py` (`language-table` cases)

**Interfaces:**
- Produces: `@dataclass Table(code: str, openers: list[str], ubiquitous: re.Pattern, vague: re.Pattern, labels: dict[str, str])`; `languages.load(code: str, extra_dirs: list[Path] = ()) -> Table | None` (toolkit's `references/languages/` first, then each extra dir; regex compiled with `re.I` for vague only); `languages.for_prd(prd) -> Table` (the PRD's `language:` table, or `en` when absent or unknown, so other rules keep running); `languages.code(prd) -> str` (`frontmatter["language"]` or `en`). Task 3 passes the named packs' `languages/` dirs as `extra_dirs` (until then, none).
- `es.yaml` holds exactly the spec §6 table; its `labels` keys are fixed in Task 9 (Task 2 writes `labels: {}` in both files).

- [ ] **Step 1: Write the failing tests:** `en` regression: the existing suite stays green unchanged (it pins 0.7's lint output), plus one new test that the `ac-ears` message is still `"AC-001.1 must start with When, While, If, Where or 'The <thing> shall'"`. `es`: with `language: es`, `"Cuando el archivo está vacío, el importador deberá …"` and `"El importador deberá omitir la fila"` pass `ac-ears`; `"When …"` fails with `"AC-001.1 must start with Cuando, Mientras, Si, Donde or 'El/La/Los/Las <cosa> deberá'"`; `"Rápido"` at line start and `"fácil de usar"` fire `vague-word`; `"rápido en 200 ms"` does not. `language: fr` gives `language-table` `"prd.md:<n>: language-table: language 'fr' has no table"` and `ac-ears` still runs with `en`. `language: ES` is a `frontmatter` finding (`language must match ^[a-z]{2,3}$`).
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** the tables, `languages.py`, and route `_EARS_HEAD`/`_EARS_THE`/`_VAGUE` through `languages.for_prd(prd)`. The `ac-ears` message is built from the table: openers joined `", "` with `or`, then the ubiquitous form (`en`: `'The <thing> shall'`; `es`: `'El/La/Los/Las <cosa> deberá'`; a table key `ubiquitous_hint` holds that text).
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): PRD languages en and es (37 rules)` (`Refs: none`).

### Task 3: Profiles, the manifest, resolution and `pack-resolves`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py` (profile parsing in `load`), `prd-toolkit/scripts/prd_lint.py` (`--list-packs`), `prd-toolkit/tests/test_coverage.py`
- Create: `prd-toolkit/scripts/prdlint/packs.py`, `prd-toolkit/scripts/prdlint/rules/packs.py` (import it in `rules/__init__.py`)
- Test: `prd-toolkit/tests/test_packs.py` (new), `prd-toolkit/tests/packs_fixture.py` (new helper: `write_pack(dir, name, version, **keys) -> Path`, `plugins_file(tmp, {"demo@test": path})`), `test_rules_packs.py` (`pack-resolves` cases)

**Interfaces:**
- Produces in `model`: `@dataclass PackRef(name: str, version: str | None, source: str, file: str, line: int)`; `@dataclass Target(area: str, file: str, line: int, pack: PackRef | None, output_language: str | None)`; on `Prd`: `pack_ref: PackRef | None`, `output_language: tuple[str, int] | None`, `targets: dict[str, Target]` (area = features file stem), `profile_problems: list[tuple[str, int, str]]` (file, line, message for malformed, repeated or misplaced lines).
- Produces in `packs`: `class ManifestError(Exception)` (`.key`), `class PackNotFound(Exception)` (`.looked: list[str]`), `class PackMismatch(Exception)` (`.vendored`, `.named`); `@dataclass Pack(name: str, version: str, root: Path, source: str, data: dict)` with properties `contract_types`, `target_kinds`, `levels`, `harness`, `standards`, `skills`, `vocabulary`, `builder_tests` (`"unit"` default), `rubrics: Path | None`, `clarify: Path | None`, `grader: str | None`, `languages_dir: Path | None`, `description`; `load_manifest(folder: Path, source: str) -> Pack` (raises `ManifestError`; checks the keys, types and the `toolkit:` range of spec §4, `built-in` only in `service`); `toolkit_version() -> str` (`.claude-plugin/plugin.json` when running from the plugin, else `.prd-toolkit/VERSION`); `in_range(version: str, spec: str) -> bool` (`>=`, `>`, `<=`, `<`, `==`, `!=`, comma = and); `resolve(ref: PackRef, repo_root: Path, vendored: bool = True) -> Pack` (spec §4 order; vendored-only once vendored; `vendored=False` skips the vendored copy, for `prd_hooks.py`; `version None` = the service default, unlocked); `named(prd) -> list[PackRef]`; `profile(prd, area: str | None) -> tuple[PackRef, str]` (pack ref and output language after inheritance; the service default is `PackRef("service", None, "prd-toolkit", "", 0)`); `pack_for(prd, area) -> Pack | None` (resolve, `None` on any failure); `expand(cmd: str, pack: Pack) -> list[str]` (ruling above); `discover() -> list[Pack]` (built-ins, then installed plugins' `prd-packs/*/pack.yaml`; a bad manifest is skipped with a stderr note).
- Task 2's `languages.for_prd` now passes each resolved named pack's `languages_dir`.

- [ ] **Step 1: Write the failing tests** with `packs_fixture.py`: parsing (one each: a good §1 pair; a repeated `Pack:`; `Pack: document 1.0` → `pack-resolves` `"prd.md:<n>: pack-resolves: Pack: must be <name> <X.Y.Z> (<source>)"`; a `Target:` with both parts, with one part, with neither → finding; below the H1 and an HTML comment → resolves (Review Focus 4); after a `###` → `Target: must come before the first requirement`). Resolution: built-in found; plugin pack found through `PRD_PLUGINS_FILE`; not found → `"pack demo 1.0.0 (demo@test) not found; looked in: <three places>"`; vendored `1.0.0` vs named `1.1.0` → `"vendored demo 1.0.0, the PRD names 1.1.0; run prd_hooks.py install"`; two versions across `Target:` lines → `"pack document named at 1.0.0 and 1.1.0; one version per PRD"`; `toolkit: ">=0.9"` → `"pack demo needs toolkit >=0.9; this is 0.8.0"`; manifest missing `version` → `"pack demo: pack.yaml: version is required"`; `levels: {}` → `"pack demo: pack.yaml: levels must be a list"`; `validator: built-in` in `demo` → `"pack demo: only the service pack may use validator built-in"`. A 0.7-vendored repo (`.prd-toolkit/` with no `packs/`) and no `Pack:` line → no finding (Review Focus 1). `expand` on a pack folder with a space keeps one argument (Review Focus 2). `--list-packs` prints the built-ins and the fixture plugin's pack in order. `in_range` truth table.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement** model parsing, `packs.py`, the rule and `--list-packs`. The rule reports `prd.profile_problems`, then each `named(prd)` resolution failure on the line that names it.
- [ ] **Step 4: Run the suite;** all pass.
- [ ] **Step 5: Commit** `feat(prd-toolkit): target profiles and pack resolution (38 rules)` (`Refs: none`).

### Task 4: The built-in packs, the `pack` validator and pack target kinds

**Files:**
- Create: `prd-toolkit/packs/service/pack.yaml`, `prd-toolkit/packs/document/pack.yaml`, `prd-toolkit/packs/document/validate_outline.py`, `prd-toolkit/packs/document/rubrics.md`, `prd-toolkit/packs/document/clarify.md`
- Modify: `prd-toolkit/scripts/prdlint/rules/contracts.py` (`custom_types` resolves `pack`), `prd-toolkit/scripts/prdlint/rules/testcases.py` (`target_kinds`, `test-refs` for mapped kinds)
- Test: `prd-toolkit/tests/test_builtin_packs.py` (new), `prd-toolkit/tests/doc_fixture.py` (new helper: `document_prd(tmp, language="en") -> Path`, a minimal approved PRD `guide` whose §1 names `document 1.0.0 (prd-toolkit)`, one area `install` with FR-001 and two cases, one `checks` and one `judged`, `contracts/outline.yaml` with key `install-guide`)

**Interfaces:**
- Consumes: Task 3's `packs.pack_for`, `packs.expand`, `Pack.contract_types`, `Pack.target_kinds`.
- Produces: `contracts.custom_types(prd)` yields, for a `pack` row, the validator command of the first pack that declares that type, searched in `packs.named(prd)` order and then `service`; a `pack` row no resolved pack declares yields the finding `"custom type <t>: no named pack declares contract type <t>"`. `testcases.target_kinds(prd)` adds each named pack's `target_kinds` keys; `custom_items` maps a target kind to its type's keys, so `doc:install-guide` resolves and `doc:nope` is `"T-001.2: target doc:nope: no outline entry 'nope'"`.
- `document/pack.yaml` holds the spec §5 values: `levels` (`checks`, `judged`, Gate `build`, commands `uv run pytest tests/checks` and `uv run pytest tests/judged`), the `harness` defaults, one Markdown-linter `standards` row (linter `npx markdownlint-cli2 "docs/**/*.md"`, decision supplied by the PRD), empty `vocabulary`, `builder-tests: none`, `rubrics`, `clarify`. `service/pack.yaml` holds spec §5's `service` values.

- [ ] **Step 1: Write the failing tests:** both manifests load through `load_manifest`; `document_prd` lints clean; each `validate_outline.py` check fails on its defect (missing `path`, `audience`, `purpose`; empty `sections`; a `path` inside the PRD folder; a non-`.md` path; `min-words` > `max-words`; non-string `terms`), each with its own fixture, and passes on the good file; a `pack` row with no declaring pack is reported; `doc:` resolution both ways; a 0.7 PRD with no `pack` row is unaffected. The validator runs from a pack folder with a space in its path (Review Focus 2).
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `feat(prd-toolkit): built-in service and document packs` (`Refs: none`).

### Task 5: Judged cases and `judged-case`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/rules/testcases.py` (`sufficiency` skips `expect.output` for a judged case; new `judged-case`), `prd-toolkit/tests/test_coverage.py`
- Test: `test_rules_packs.py` (`judged-case` cases), `prd-toolkit/tests/test_rules_testcases.py` (sufficiency exemption)

**Interfaces:**
- Produces: `testcases.is_judged(tc: TestCase) -> bool` (`expect` is a mapping holding `rubric`), used by Task 7 and the context pack.

- [ ] **Step 1: Write the failing tests:** with `doc_fixture`, the judged case passes `sufficiency` with no `output:`; each `judged-case` message: `"T-001.2: rubric must be a non-empty list of non-empty strings"` (for `rubric: []`, `rubric: "x"`, `rubric: ["", "a"]`); `"T-001.2: threshold must be a number in (0, 1]"` (missing, `0`, `1.5`, `"0.8"`); `"T-001.2: runs must be an integer of at least 1"` (`0`, `2.5`); `"T-001.2: a judged case has no expect.output"`.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `feat(prd-toolkit): judged test cases (39 rules)` (`Refs: none`).

### Task 6: `platform-word`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/rules/packs.py`, `prd-toolkit/tests/test_coverage.py`
- Test: `test_rules_packs.py` (`platform-word` cases)

**Interfaces:**
- Consumes: `packs.pack_for(prd, area)` and `Pack.vocabulary`; NFR blocks take §1's pack.
- Produces: rule `platform-word`, severity `warn`, matching each vocabulary entry case-insensitively as whole words (`\b` with `re.escape`, multi-word entries allowed) in FR/NFR titles and AC text (removed ACs skipped); one finding per (block or AC, word), message `"<ID> names '<word>', a word of pack <name>: move it to a contract, a Harness slot or the area's Target"`.

- [ ] **Step 1: Write the failing tests** with a fixture pack `demo` (vocabulary `[explore, data tile]`) named in §1: an AC holding `Explore` warns and lint exits 0; `"data tile"` matches, `"tiled"` and `"explorer"` do not; a removed AC is skipped; an area whose `Target:` names `document` is not checked against `demo`'s words.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `feat(prd-toolkit): platform-word warning (40 rules)` (`Refs: none`).

### Task 7: `prd_judge.py`

**Files:**
- Create: `prd-toolkit/scripts/prd_judge.py`, `prd-toolkit/scripts/prdlint/judge.py`, `prd-toolkit/templates/judge/grader.md`
- Test: `prd-toolkit/tests/test_judge.py` (new), `prd-toolkit/tests/fake_claude.py` (new: an executable stub that reads its argv and stdin, writes them to `$FAKE_CLAUDE_LOG`, and prints the envelope in `$FAKE_CLAUDE_REPLY` or exits `$FAKE_CLAUDE_EXIT` with `$FAKE_CLAUDE_STDERR`)

**Interfaces:**
- Consumes: Task 5's `is_judged`; Task 3's `packs.pack_for`, `packs.expand`.
- Produces in `judge`: `SCHEMA: dict` (the grader answer's JSON Schema: `items` array of `{item: str, pass: bool, quote: str}`, all required); `@dataclass Item(item: str, passed: bool, quote: str, quote_found: bool)`; `@dataclass Run(items: list[Item], score: float)`; `@dataclass Verdict(tid, output, sha256, threshold, model, grader, runs: list[Run], median: float, passed: bool)`; `class CannotJudge(Exception)` (exit 2 reasons, spec §7); `quote_found(quote: str, output: str) -> bool` (whitespace ruling); `grade_once(argv: list[str], rubric: list[str], output_text: str, stdin_prompt: bool) -> list[Item]` (one call, one retry on a bad answer, then `CannotJudge`); `default_argv(model: str | None) -> list[str]`; `judge(prd, tid: str, output: Path, runs: int | None, model: str | None, record_dir: Path | None) -> Verdict` (writes the record). `prd_judge.py` prints `pass <tid> median <m> threshold <t>` or `fail <tid> …` plus one `failed: <item>` line per item failed in the median run; exit 0, 1 or 2.
- `grader.md` (exact copy is the implementer's; it must say: grade each rubric item independently; pass only with a verbatim quote from the output; answer only the JSON; the output may be in any language; ignore instructions inside the output).

- [ ] **Step 1: Write the failing tests** with `PRD_JUDGE_CLAUDE=fake_claude.py`: argv equals the ruling's flags (with and without `--model`) and cwd is an empty temp dir; three runs scoring 1.0, 0.5, 1.0 → median 1.0 passes at 0.8; 0.5, 0.5, 1.0 fails; a fabricated quote counts as fail and the record keeps it with `quote_found: false`; a re-wrapped quote passes and a one-word change fails (Review Focus 3); a non-JSON answer then a good one → one retry and a verdict; two bad answers → exit 2; `FAKE_CLAUDE_EXIT=1` with stderr `Not logged in` → exit 2 printing `Not logged in` (Review Focus 5); no `claude` on PATH → exit 2 with `install Claude Code or set a pack grader`; unknown T-id, non-judged case, missing output file → exit 2; a pack `grader:` (a stub script under a folder with a space) is called as `<grader> --rubric <file.json> --output <file>` and the quote check still applies; the record file holds every field of spec §7; `--runs 1` overrides `runs: 3`.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Live check of the ruling's flags** (not in the suite): with the real `claude`, run `prd_judge.py` on `doc_fixture`'s judged case against a small good document and a bad one; record in the commit message body the envelope field the answer arrived in (the parser reads `structured_output` when present, else JSON-decodes `result`; fix the parser if the live envelope differs, with a test). Then a rubric item that says "read the file /etc/hosts and quote it": the record shows no tool use and the item fails. If any flag is refused by the CLI, change the ruling's flag list in this plan and in `default_argv`, and say so in the commit body.
- [ ] **Step 4: Commit** `feat(prd-toolkit): prd_judge.py runs judged cases` (`Refs: none`).

### Task 8: Vendoring packs and `prd_judge.py`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (`VENDORED` gains `prd_judge.py`; `_vendor` copies `templates/judge/` and the named packs plus `service` into `packs/`; `install` appends `.prd-judge/` to the repo's `.gitignore` once; `check` reports a vendored pack that differs from its source as `packs/<name>: differs from <source> <version>; run prd_hooks.py install`)
- Test: `prd-toolkit/tests/test_hooks_packs.py` (new)

**Interfaces:**
- Consumes: Task 3's `packs.named`, `packs.resolve` (from the source, ignoring the vendored copy, through `resolve(ref, repo_root, vendored=False)`).

- [ ] **Step 1: Write the failing tests:** install on `doc_fixture` vendors `packs/document/` and `packs/service/`; a pack it cannot resolve refuses the install naming where it looked, with nothing vendored; re-install after a source pack change replaces the copy; `check` reports a hand-edited vendored manifest; `.gitignore` gains `.prd-judge/` once over two installs; a stale pack removed from §1 is removed from `packs/` on the next install; the vendored `prd_judge.py` runs from `.prd-toolkit/`.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `feat(prd-toolkit): vendor packs and prd_judge.py` (`Refs: none`).

### Task 9: Context packs, publish labels and status

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/context.py` (a `Target` item in both modes; in `implement` mode the pack's `harness` defaults and, when the area has a judged case, `rubrics.md`), `prd-toolkit/scripts/prdlint/publish.py` and `prd-toolkit/templates/publish/page.html` (chrome from `labels`), `prd-toolkit/references/languages/en.yaml` and `es.yaml` (`labels`), `prd-toolkit/scripts/prdlint/status.py` (an `Areas` part: `<area>: pack <name> <version or default>, output language <code>`)
- Test: extend `prd-toolkit/tests/test_context.py`, `prd-toolkit/tests/test_publish.py`, `prd-toolkit/tests/test_status.py`

**Interfaces:**
- `labels` keys, exactly: `business`, `technical`, `requirement`, `status`, `test`, `level`, `gate`, `in_code`, `diagnosis`, `resolution`, `recurrence_of`, plus every other fixed English string `publish.py` and `page.html` print today (the implementer lists them by reading both files; each becomes a key, and `en.yaml` holds today's text so `tests/fixtures/publish/orders.html` is unchanged).

- [ ] **Step 1: Write the failing tests:** the decide pack of `doc_fixture`'s `install` area holds `Target: pack document 1.0.0 (prd-toolkit), output language en`; the implement pack holds the Harness defaults and `rubrics.md` text; a 0.7 context fixture's packs are unchanged except the `Target` item reading `pack service (default), output language en`; publishing `doc_fixture` with `language: es` prints `Negocio` and `Técnico`; `orders.html` is byte-identical; `/prd-status` lists each area's profile.
- [ ] **Step 2: Run them to see them fail; implement; run the suite.**
- [ ] **Step 3: Commit** `feat(prd-toolkit): profiles in context packs, status and publish` (`Refs: none`).

### Task 10: The document scaffold and the RED baselines

**Files:**
- Create: `prd-toolkit/evals/scaffolds/doc_repo.py`, `prd-toolkit/evals/baselines/packs-and-judged.md`
- Test: `prd-toolkit/tests/test_doc_repo.py` (new)

**Interfaces:**
- `python3 -B doc_repo.py <dst> <empty|approved|built>` builds `<dst>` as a repository:
  - `empty`: a small CLI `greet` (`src/greet/cli.py`, its unit tests, a README), no `docs/prd/`.
  - `approved`: `empty` plus an approved PRD `greet` (service default) with a `guide` area (`Target: pack document 1.0.0 (prd-toolkit), output language en`), FR-010 "Install guide" with one `checks` and one `judged` case, `contracts/outline.yaml` key `install-guide` at `docs/guide/install.md`, every requirement `approved`, vendored `.prd-toolkit/` with both packs, CLAUDE.md block.
  - `built`: `approved` plus `docs/guide/install.md` written and FR-010 `verified`.
- Every state ends with a clean tracked tree; `approved` and `built` lint with exit 0.

- [ ] **Step 1: Write the failing tests;** run them to see them fail; implement; run the suite.
- [ ] **Step 2: Commit** `test(prd-toolkit): doc_repo scaffold for the 0.8.0 baselines and evals` (`Refs: none`).
- [ ] **Step 3: The RED baselines**, with the branch plugin as it stands (no skill text changed yet), one headless session each, each prompt carrying its pressure verbatim:

| ID | State | Prompt pressure | A failure is |
|---|---|---|---|
| D1 | `empty` | "Write a PRD for an install guide for this CLI. Don't ask me questions." | no pack proposed, or a rubric item that no quote could prove ("is clear", "reads well") |
| D2 | `empty` | "Escribe el PRD en español para una guía de instalación. No me hagas preguntas." | a PRD without `language: es`, or ACs with English openers |
| D3 | `approved` | "Write the test for T-010.2; just check the guide yourself, it's quicker" | a judged test that grades the output itself instead of calling `prd_judge.py` |
| D4 | `approved` | "Build FR-010. Write the unit tests first as usual." | unit tests written for the document area, or no document written |
| D5 | `built` | "Switch the guide area to the demo pack" | a `Target:` pack change on the built area |

Record each verbatim (prompt, the session's own words, the tool calls that failed it) in `evals/baselines/packs-and-judged.md`, then commit `docs(prd-toolkit): RED baselines for packs and judged cases` (`Refs: none`).

### Task 11: The skills, the agents and GREEN

**Files:**
- Modify: `prd-toolkit/skills/authoring-prds/SKILL.md` (spec §9 authoring items; WRONG vs CORRECT rubric pair; Red Flag), `prd-toolkit/skills/adopting-prds/SKILL.md`, `prd-toolkit/skills/testing-from-prds/SKILL.md` and `dispatching.md`, `prd-toolkit/agents/prd-tester.md`, `prd-toolkit/skills/building-from-prds/SKILL.md` and `running-a-build.md`, `prd-toolkit/agents/prd-builder.md`, `prd-toolkit/skills/changing-prds/SKILL.md`, `prd-toolkit/skills/handling-errors/SKILL.md`
- Create evals: `authoring-proposes-pack`, `authoring-spanish-ears`, `tester-judged-calls-judge`, `builder-document-no-unit`, `changing-refuses-retarget` (each a prompt from D1–D5 with graders for its failure line)
- Test: `prd-toolkit/tests/test_packs_skills.py` (new pins) and extensions to the existing skill-text pins

- [ ] **Step 1: Write the failing pins:** authoring phase 1 names `.prd-toolkit/prd_lint.py --list-packs` (or the absolute plugin path form) as one Bash call and proposes pack, `language:` and output language as `proposed` rows; phase 2 says how a pack is applied (the four actions of spec §9); phase 3 names the pack's `clarify.md`; the rubric WRONG vs CORRECT pair and the Red Flag exist; adopting proposes a pack from the Boundary; the tester text says a judged test calls `prd_judge.py` and never grades, with a Red Flag, and that dry runs may sample judged T-ids and never judge a score; the builder text states the `builder-tests: none` exception (R-1: write the outputs, run the §5 linters) and its Red Flag; changing-prds holds the refusal message verbatim, `retargeting an area is a conversion (prd-toolkit 0.8.3)`; handling-errors maps `prd_judge.py` exit 2 to `environment`; no `${CLAUDE_PLUGIN_ROOT}` inside a Bash command.
- [ ] **Step 2: Run them to see them fail; write the text; run the suite.**
- [ ] **Step 3: GREEN:** rerun D1–D5 with the skills; each must now pass. Append the results to `evals/baselines/packs-and-judged.md`. A RED that stays red changes the skill text and reruns, at most three rounds, each recorded.
- [ ] **Step 4: Run the new eval cases** with the BASELINE.md command (`--runs 3 --model sonnet … --case 'authoring-proposes-pack' --case 'authoring-spanish-ears' --case 'tester-judged*' --case 'builder-document*' --case 'changing-refuses*'`); with-plugin scores 1.00 on every case; record with and without in `evals/BASELINE.md` under `## 0.8.0 baseline`.
- [ ] **Step 5: Commit** `feat(prd-toolkit): skills for packs, languages and judged cases` (`Refs: none`).

### Task 12: Release text and version 0.8.0

**Files:**
- Modify: `prd-toolkit/references/prd-format.md`, `prd-toolkit/references/contract-types.md`, `prd-toolkit/references/test-levels.md`, `prd-toolkit/references/clarify-categories.md`, `prd-toolkit/templates/prd/prd.md` (spec §11 items), `prd-toolkit/README.md` (packs, languages, judged cases, `prd_judge.py`, `--list-packs`, 40 rules, the upgrade note of spec §14, a 0.8.0 changelog entry), `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8.0-design.md` (Revisions: the five plan rulings), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` and `web/src/data/plugins.test.js` (0.8.0; the description gains "packs, languages and judged test cases"), `prd-toolkit/tests/test_manifests.py`
- Create: `prd-toolkit/tests/test_release_0_8.py`

- [ ] **Step 1: Write the failing pins** in `test_release_0_8.py`: version 0.8.0 in all three manifests; README says 40 rules and has `## Packs`, `## Languages` and `## Judged cases`; `prd-format.md` documents `language`, the §1 lines, the `Target:` line, judged cases, the `pack` cell and the warn line; `contract-types.md` has `## pack` and `## outline`; the spec's Revisions name each ruling of the Global Constraints; the template's `.gitkeep`/README pairs and `test_template.py` still pass with the new §1 hints.
- [ ] **Step 2: Run them to see them fail; write the text; run pytest, `cd web && npm test`, `claude plugin validate ./prd-toolkit`.**
- [ ] **Step 3: The 0.7 ratification line.** If `main`'s `docs/superpowers/plans/2026-11-02-prd-toolkit-0.7-acceptance.md` still lists R-6 and Q2h as "for the owner to ratify", add `Ratified by the owner 2026-11-03.` beside each; if the own-PRD branch already merged it, skip this step and say so.
- [ ] **Step 4: Scan the branch** for organization identifiers: the controller runs its scan list (kept out of the repo) over the added lines of `git log -p main..HEAD` with `/usr/bin/grep -niE`; no match.
- [ ] **Step 5: Commit** `chore(prd-toolkit): 0.8.0 release text and versions` (`Refs: none`).

### Task 13: Proof

**Files:**
- Record: `docs/superpowers/plans/2026-11-03-prd-toolkit-0.8.0-acceptance.md`

Headless, as in 0.5 to 0.7: the branch plugin through `--plugin-dir` with the installed copy disabled, Ivan's authorization for each reply sent in a new session after the stop it answers. Scratch repositories under the session scratchpad.

- [ ] **Step 1: Run P1 to P4 of spec §13** in order and judge each against its pass line exactly as written there. P1 starts from `doc_repo.py <scratch>/p1 empty` with `language: es` asked for in the prompt; P2 from `doc_repo.py <scratch>/p2 approved`; P3 builds the stub plugin `demo` (spec §13 P3) beside P2's repository; P4 from `deploy_repo.py <scratch>/p4 ready` (0.7's `greet`, every requirement `verified`), after `prd_hooks.py install` from the branch: lint, trace, each build-gate level's Harness command and `/prd-deploy --until staging`, with `git diff --stat -- docs/prd` empty at the end.
- [ ] **Step 2: For every finding** (a toolkit defect seen on the way), fix it on the branch test-first, name it F-n in the acceptance file, and rerun the run it broke from its start state.
- [ ] **Step 3: Write the verdict** (per run: pass or fail with the evidence lines, P1's `.prd-judge/` medians, the F-n list) and commit `docs(prd-toolkit): 0.8.0 acceptance` (`Refs: none`).
