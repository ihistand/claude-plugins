# prd-toolkit 0.8.3: fixes from the 0.8.2 proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 0.8.2 proof's backlog: an exact `.prd-toolkit/` refresh in the toolkit's own repository, the standby promise, two `prd_change.py record` bugs, seven `prd_build_check.py` bugs and eight inbox and gate residuals, and ship it as 0.8.3.

**Architecture:** Every fix lands in the module that owns the behaviour today (`prdlint/hooks.py`, `prdlint/buildcheck.py`, `prdlint/change.py`, `prdlint/gates.py`, `prdlint/deploy.py`, `prd_gates.py`, one template) with a red-first unit test; the skill changes are pinned by `tests/test_*_skill*.py`. No new module except one test file per new surface.

**Tech Stack:** Python 3.11 scripts run with `uv run --script`, pytest, PyYAML, git; Markdown skills; one HTML template.

**Spec:** `docs/superpowers/specs/2026-11-06-prd-toolkit-0.8.3-backlog-design.md` (governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`).

## Global Constraints

- Work only in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8.3`, branch `feat/prd-toolkit-0.8.3` (cut from `main` at `f7462ef`; the spec is its first commit). Never push, open a PR, merge or touch another repository.
- Commit as `Ivan Histand <ihistand@rotoplas.com>`. Every message ends with the trailers `Refs: none (no behaviour change)` and `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never `--no-verify`; never bare `git stash`.
- **The vendored copy moves with the code.** Any commit that changes a file `.prd-toolkit/` vendors (`prd-toolkit/scripts/**`, `prd-toolkit/templates/**`, `prd-toolkit/references/languages/**`, `prd-toolkit/packs/**`) runs, before the commit, `uv run --script prd-toolkit/scripts/prd_hooks.py vendor docs/prd/prd-toolkit` (Task 1 adds it; Task 1 itself uses it once its code passes) and stages `.prd-toolkit/` in the same commit. Never `prd_hooks.py install` on this repository; never edit `.prd-toolkit/` by hand.
- **Never edit the `lint-cli` Boundary:** `prd-toolkit/scripts/prd_lint.py`, `prd-toolkit/scripts/prdlint/{__init__,model,markdown,yamlload,findings,registry,deps,interface}.py`, `prd-toolkit/scripts/prdlint/rules/__init__.py`. Importing from them is fine. Never edit `docs/prd/prd-toolkit/`.
- New tests cite no T-id and carry no `@prd` tag: these areas are not adopted.
- Code stays Python 3.11 syntax (`tests/test_py311_syntax.py`).
- A change to `prd-toolkit/skills/**` or `prd-toolkit/agents/**` follows `superpowers:writing-skills`: one pressure scenario run without the change and with it, both recorded in the task report.
- Public repository: no employer, host, user or customer names in code, tests, docs or commit messages.
- Test commands run from the worktree root. One file: `uv run --directory prd-toolkit pytest -q tests/<file>`. The unit level: `uv run --directory prd-toolkit pytest -q tests --ignore tests/prd` (about 15 minutes; Task 11 only).
- Exact strings (copy verbatim):
  - `vendored the toolkit into .prd-toolkit/ (version <X.Y.Z>)`
  - `prd_hooks: vendor runs from the plugin, not from .prd-toolkit/`
  - `<path>: differs from the plugin; refresh it with prd_hooks.py vendor`
  - `prd_build_check: <prd> is not in a git working tree`
  - `prd_gates: standby: <type>: <message>`
  - `prd_deploy: internal error: <type>: <message>`
  - the standby replacement sentence: `This repository's .prd-toolkit/ is <version or "older than 0.6">, so the inbox closes with the session that started it; run prd_hooks.py install docs/prd/<slug> from the plugin to refresh it.`

## Review Focus

1. `vendor` on a PRD that names a pack from an installed plugin (`PRD_PLUGINS_FILE`): it must vendor exactly the packs `install` vendors. Pinned in Task 1 (`test_vendor_matches_install_with_a_named_pack`).
2. A round that removes a plugin script and the vendored copy of it: `vendor` no longer writes that path, so the refresh is exact and `--diff` passes. Pinned in Task 2 (`test_refresh_that_drops_a_removed_script_passes`).
3. `--diff` run while the working tree differs from `<head>` (the caller checks a round branch it has not checked out): the comparison reads `<head>`'s tree only. Pinned in Task 2 (`test_refresh_is_judged_at_head_not_the_working_tree`).
4. A verdict whose `base` is a branch name or a short SHA, not a full SHA: the card resolves any commit-ish that `git cat-file -e <base>^{commit}` accepts. Pinned in Task 7 (`test_card_accepts_a_ref_name_as_base`).
5. A regression patch that moves a `live (since X)` block back to `approved`: `record` clears its Since and lint stays clean. Pinned in Task 5 (`test_record_clears_since_when_a_live_block_returns_to_approved`).

---

### Task 1: `prd_hooks.py vendor`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (beside `install`, line 198)
- Modify: `prd-toolkit/scripts/prd_hooks.py` (the `action` choices and dispatch, lines 23-80; module docstring line 6)
- Test: `prd-toolkit/tests/test_hooks_vendor.py` (new; reuse the repo-building helpers of `tests/test_hooks_install.py`)

**Interfaces:**
- Produces: `hooks.vendor(repo_root: Path, prd_rel: str) -> list[str]` — writes `.prd-toolkit/` with `_vendor(repo_root, sources_packs)` exactly as `install` resolves `sources_packs`, returns `["vendored the toolkit into .prd-toolkit/ (version <X.Y.Z>)"]`. Raises what `install` raises for an unresolvable pack. CLI: `prd_hooks.py vendor <prd_dir>`, exit 0 / 2. Tasks 2 and 3 call the CLI.

- [ ] **Step 1: Write the failing tests** in `tests/test_hooks_vendor.py`:
  - `test_vendor_writes_install_s_tree_and_nothing_else`: in a fresh git repo with the fixture PRD, run `prd_hooks.py vendor docs/prd/<slug>`; assert exit 0, stdout `vendored the toolkit into .prd-toolkit/ (version <plugin version>)`; the `.prd-toolkit/` file set and bytes equal a second repo's after `install`; no `.git/hooks/pre-commit`, `commit-msg` or other file `install` writes exists; `CLAUDE.md` is absent; no `.gitlab/` or `.github/` file.
  - `test_vendor_matches_install_with_a_named_pack`: the same comparison on a fixture PRD whose `Pack:` names a pack from `PRD_PLUGINS_FILE` (as `tests/test_hooks_packs.py` sets it up); `.prd-toolkit/packs/` and `pack-sources.json` equal.
  - `test_vendor_from_a_vendored_copy_exits_2`: run `.prd-toolkit/prd_hooks.py vendor …` from a repo that has one; exit 2, stderr `prd_hooks: vendor runs from the plugin, not from .prd-toolkit/`.
  - `test_vendor_rejects_ci_flags`: `vendor --force` exits 2 with the existing `--gitlab, --github and --force belong to ci` line.
  - `test_help_lists_vendor`: `prd_hooks.py --help` stdout contains `vendor`.
- [ ] **Step 2: Run** `uv run --directory prd-toolkit pytest -q tests/test_hooks_vendor.py`. Expected: FAIL (`invalid choice: 'vendor'`).
- [ ] **Step 3: Implement** `hooks.vendor` (share `install`'s pack resolution; do not duplicate it: extract the lines `install` uses into a helper both call) and the `vendor` action in `prd_hooks.py`: refuse with the exact line when `not hooks.is_plugin()`, the same `is not inside the repository` refusal as `install`, then print each returned line. Add `vendor` to the module docstring and the parser description.
- [ ] **Step 4: Run** the new file plus `tests/test_hooks_install.py tests/test_hooks_packs.py tests/test_cli.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit.** `uv run --script prd-toolkit/scripts/prd_hooks.py vendor docs/prd/prd-toolkit`; `uv run --directory prd-toolkit pytest -q tests/test_vendored_copy.py` passes. Commit `feat(prd-toolkit): prd_hooks.py vendor writes .prd-toolkit/ and nothing else`, staging the three files and `.prd-toolkit/`.

### Task 2: `--diff` accepts an exact refresh

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/buildcheck.py` (`diff_findings`, lines 39-77)
- Modify: `prd-toolkit/scripts/prd_build_check.py` (the `except` chain, lines 56-62)
- Test: `prd-toolkit/tests/test_build_check_refresh.py` (new; reuse `git`/`commit` helpers from `tests/test_build_check.py` by copying the three-line helpers, not importing test modules)

**Interfaces:**
- Consumes: the `prd_hooks.py vendor` CLI (Task 1).
- Produces: `buildcheck.ToolError(Exception)`; `buildcheck.plugin_dir(repo_root: Path, rev: str) -> str | None` (the one directory at `rev` with `<dir>/.claude-plugin/plugin.json` whose `name` is `prd-toolkit` and `<dir>/scripts/prd_hooks.py`; `None` for zero or several); `buildcheck.refresh_differences(repo_root: Path, head: str, plugin: str, prd_rel: str) -> list[str]` (sorted `.prd-toolkit/` paths whose bytes at `head` differ from what `vendor` writes, plus paths missing at `head` or present at `head` but not written by `vendor`; `[]` when exact). Task 3's skill text names the behaviour, not these names.

- [ ] **Step 1: Write the failing tests.** Fixture `plugin_repo(tmp_path)`: a git repo holding a copy of the real plugin's `.claude-plugin/`, `scripts/`, `templates/`, `references/languages/` and `packs/` under `prd-toolkit/`, the conftest `FIXTURE` PRD at `docs/prd/orders`, a `.prd-toolkit/` written by that copy's `vendor`, committed and tagged `base`. Tests, each calling `buildcheck.diff_findings(prd, root, "base..HEAD")`:
  - `test_exact_refresh_passes`: append a comment line to `prd-toolkit/scripts/prdlint/trace.py`, run the copy's `vendor`, commit; findings `[]`.
  - `test_hand_edit_of_the_vendored_copy_fails`: edit `.prd-toolkit/prdlint/trace.py` only, commit; findings `[".prd-toolkit/prdlint/trace.py: differs from the plugin; refresh it with prd_hooks.py vendor"]`.
  - `test_partial_refresh_reports_each_differing_path_in_order`: change two plugin scripts, copy only one into `.prd-toolkit/`; one `differs` line, for the other path.
  - `test_refresh_that_drops_a_removed_script_passes`: `git rm` a plugin script that `vendor` copies (add a throwaway `scripts/prdlint/zz_tmp.py` in the base so nothing real breaks), run `vendor`, commit; findings `[]`.
  - `test_refresh_is_judged_at_head_not_the_working_tree`: an exact refresh committed, then an uncommitted edit to `.prd-toolkit/prdlint/trace.py` in the working tree; findings `[]`.
  - `test_without_the_plugin_the_old_refusal_stands`: the existing `repo` fixture of `tests/test_build_check.py` (no plugin), a `.prd-toolkit/x` edit; the line is `.prd-toolkit/x: the builder may not edit the vendored .prd-toolkit/ copy`.
  - `test_two_plugin_directories_keep_the_old_refusal`: copy the plugin's `.claude-plugin/` and `scripts/prd_hooks.py` to `other/` as well; an exact refresh gets the old line for each changed `.prd-toolkit/` path.
  - `test_cli_tool_error_is_exit_2`: monkeypatch nothing; make the copied plugin's `scripts/prd_hooks.py` exit 1 at `<head>` (replace its body with `raise SystemExit(1)`, commit along with a `.prd-toolkit/` change); `prd_build_check.py --diff base..HEAD` exits 2 and stderr starts `prd_build_check: `.
- [ ] **Step 2: Run** `uv run --directory prd-toolkit pytest -q tests/test_build_check_refresh.py`. Expected: the pass cases FAIL with the old refusal.
- [ ] **Step 3: Implement.** In `diff_findings`, collect the changed `.prd-toolkit/` paths instead of appending the refusal per path. After the loop: when there are any and `plugin_dir(repo_root, head)` is a directory, extend findings with `f"{p}: differs from the plugin; refresh it with prd_hooks.py vendor"` for each `p` in `refresh_differences(...)`; otherwise the old line for each changed path, in diff order. `refresh_differences` extracts `head` with `git archive <head> | tar -x` into a `tempfile.TemporaryDirectory()`, runs `git init -q` there, runs `[sys.executable, <tmp>/<plugin>/scripts/prd_hooks.py, "vendor", prd_rel]` with `cwd=<tmp>` (environment inherited, so `PRD_PLUGINS_FILE` holds), and compares `<tmp>/.prd-toolkit/` (files only, `__pycache__` ignored) with `git ls-tree -r <head> -- .prd-toolkit` and `_show` bytes. A failing git or vendor run raises `ToolError(<first stderr line>)`. In `prd_build_check.py`, catch `buildcheck.ToolError` before the generic `except` and print `prd_build_check: <message>`, exit 2.
- [ ] **Step 4: Run** the new file and `tests/test_build_check.py`. Expected: PASS (`test_vendored_toolkit_edit_fails` unchanged).
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): --diff accepts an exact .prd-toolkit/ refresh in the toolkit's own repository`.

### Task 3: the builder refreshes the vendored copy

**Files:**
- Modify: `prd-toolkit/skills/building-from-prds/SKILL.md` (rule 4 and the builder's Red Flags)
- Modify: `prd-toolkit/agents/prd-builder.md` (its copy of rule 4)
- Test: `prd-toolkit/tests/test_building_skill.py` (pins both files)

**Interfaces:**
- Consumes: `prd_hooks.py vendor` (Task 1); `--diff`'s acceptance (Task 2).

- [ ] **Step 1: Baseline.** Per `superpowers:writing-skills`: a subagent given the current builder rules and the scenario "your fix to `prd-toolkit/scripts/prdlint/model.py` makes `tests/test_vendored_copy.py` fail in this repository, which holds the plugin" — record what it does (the proof's builder hand-ran a snippet).
- [ ] **Step 2: Write the failing pins** in `tests/test_building_skill.py`: both files contain `prd_hooks.py vendor docs/prd/<slug>`, `from the builder's own worktree`, `in the same commit`, `never prd_hooks.py install`, and a Red Flag that quotes a hand edit under `.prd-toolkit/`; neither file still says the builder never touches `.prd-toolkit/` without the exception.
- [ ] **Step 3: Run** the pin file. Expected: FAIL.
- [ ] **Step 4: Edit** rule 4 in both files with spec section 2.3's first bullet, nearly verbatim: the condition (a repository that holds the plugin: one directory with the plugin's `.claude-plugin/plugin.json` named `prd-toolkit` and its `scripts/prd_hooks.py`), the command `uv run --script <worktree>/<dir>/scripts/prd_hooks.py vendor docs/prd/<slug>` as its own Bash call, the same commit, never by hand, never `install`. Add the Red Flag. `running-a-build.md` gets no new step.
- [ ] **Step 5: Run** the pins and the with-change scenario again; record both runs in the report. Commit `docs(prd-toolkit): the builder refreshes .prd-toolkit/ with vendor in the toolkit's own repository`.

### Task 4: the standby promise checks the vendored copy

**Files:**
- Modify: `prd-toolkit/skills/adopting-prds/SKILL.md:451`, `prd-toolkit/skills/changing-prds/SKILL.md:362`, `prd-toolkit/skills/deploying-from-prds/SKILL.md:97`, `prd-toolkit/skills/handling-errors/running-an-error.md:313`
- Test: `prd-toolkit/tests/test_inbox_skills.py`

- [ ] **Step 1: Baseline** (writing-skills): a subagent following changing-prds with `.prd-toolkit/VERSION` reading `0.8.1`; record whether it promises a standby.
- [ ] **Step 2: Write the failing pin** `test_standby_promise_checks_the_vendored_version`, parametrized over the four files: each contains `.prd-toolkit/VERSION`, `below \`0.8.2\``, and the Global Constraints' replacement sentence verbatim (with `<slug>`), placed before the "Leave that `serve` running" sentence it replaces.
- [ ] **Step 3: Run** it. Expected: FAIL ×4.
- [ ] **Step 4: Edit** each of the four with spec section 3's paragraph: when `<scripts>` is `.prd-toolkit`, Read `.prd-toolkit/VERSION` once before the first `serve`; missing or below `0.8.2` → the replacement sentence in place of the standby promise; else the promise as today. Same words in all four.
- [ ] **Step 5: Run** the pin and `tests/test_inbox_skills.py` whole; run the with-change scenario; commit `docs(prd-toolkit): the decision skills promise a standby only when the vendored copy has one`.

### Task 5: `prd_change.py record` (E-016, j)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py` (`_index_rows` lines 567-588; `_record_ids` lines 528-537 and its caller in `record`, line 642)
- Test: `prd-toolkit/tests/test_change_record.py`

**Interfaces:**
- Consumes: `model.ReqBlock.since` (the loader's parse of `(since X)`), `contract_items(prd)`, `snapshot.items` / the OpenAPI op's `x-prd-ids`.
- Produces: `_contract_ids(prd: model.Prd, file: str, name: str) -> list[str]` — the UJ/FR/NFR IDs an item cites (OpenAPI: its `x-prd-ids`; any other item: each `(?:UJ|FR|NFR)-\d{3}` and `AC-\d{3}\.\d+` token in its `contract_items` text, an AC mapped to its block), filtered to blocks of the PRD it is read from.

- [ ] **Step 1: Write the failing tests** in `tests/test_change_record.py`, on the module's existing fixture:
  - `test_record_writes_since_for_an_added_live_block`: add an FR block with `Status: live (since 1.1.0)`; after `record --bump minor`, its §11 row's fifth cell is `1.1.0` and `prd_lint.py` exits 0.
  - `test_record_writes_since_when_an_existing_block_becomes_live`: change an existing block's status to `live (since 1.1.0)`; its row's Since is `1.1.0`.
  - `test_record_clears_since_when_a_live_block_returns_to_approved`: a base with a live block and Since `1.0.0`; set `Status: approved`; the row reads `approved` and an empty Since; lint exits 0.
  - `test_contract_only_change_lists_the_cited_requirement`: change only the text of a custom contract item that names `(FR-001)`; the new §14 row's IDs cell is `FR-001`, not `-`.
  - `test_openapi_operation_change_lists_its_x_prd_ids`: change one operation whose `x-prd-ids` is `[FR-002, AC-002.1]`; the IDs cell holds `FR-002` (once).
  - `test_removed_contract_item_reads_its_citations_at_the_base`: remove an item citing `FR-001`; IDs cell holds `FR-001`.
  - `test_contract_change_citing_nothing_keeps_dash`: change an item with no ID token; IDs cell `-`.
- [ ] **Step 2: Run** the file. Expected: the new tests FAIL.
- [ ] **Step 3: Implement.** `_index_rows`: wherever a row's status is taken from its block (the new-row append and the final loop), set the Since cell to `b.since or ""`. `record`: for each `BumpItem` whose `file` starts `contracts/` and whose id is not a requirement ID, add `_contract_ids` of the item, read from the working tree for an added or changed item and from the base PRD for a removed one; pass the union to `_record_ids` so ordering and AC→block mapping stay in one place. IDs not in either PRD's blocks are dropped.
- [ ] **Step 4: Run** the file plus `tests/test_change_bump.py tests/test_change_approve.py tests/test_changing_scripts.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): record writes a live block's Since and the IDs a changed contract item cites`.

### Task 6: `prd_build_check.py` fixes (E-009 to E-015)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/buildcheck.py` (`diff_findings` citation scan line 67; `results_findings` lines 80-107; `_case_entries` lines 119-137; `stale_findings` lines 140-170)
- Modify: `prd-toolkit/scripts/prd_build_check.py` (the `--stale` branch)
- Test: `prd-toolkit/tests/test_build_check.py` (add one test per item; each with a comment naming its item, e.g. `# 0.8.3 spec §5, E-012`)

**Interfaces:**
- Consumes: `model.git_toplevel(path) -> Path | None`; `prdlint.yamlload._Loader`, the first-value-wins loader (`yaml.load(text, Loader=yamlload._Loader)`; import it, never edit the module); `trace._scan`'s per-line citation rule.

- [ ] **Step 1: Write the failing tests**, one per row of spec section 5:
  - `test_e009_stale_outside_git_exits_2`: copy the fixture PRD to a non-git `tmp_path`; `prd_build_check.py <dir> --stale --tids T-001.1` exits 2, stderr `prd_build_check: <dir as loaded> is not in a git working tree`, stdout empty. Replace the old library-only `test_stale_git_failure_raises_so_the_cli_exits_2` assertion only if it contradicts; keep it otherwise.
  - `test_e010_blank_line_after_results_ends_the_block`: a report `RESULTS\n\nT-001.1: pass\n\nT-001.2: pass` with `--tids T-001.1,T-001.2`; findings report `T-001.2` as missing (the after-blank line is not read). Plus: a blank line before the first result line is still skipped.
  - `test_e011_duplicated_tid_key_keeps_the_first_value`: a test-case file with the same T-id key twice, the first matching the committed case, the second edited; `--stale` says not stale (it reads the first).
  - `test_e012_subfolder_case_files_are_not_read_at_either_end`: a case committed in `test-cases/sub/x.yaml` and the same T-id in `test-cases/a.yaml`; `--stale` compares only `test-cases/a.yaml` at both ends (edit the subfolder copy after the test's commit; not stale).
  - `test_e013_non_file_yaml_entry_is_skipped`: an empty directory `test-cases/bad.yaml`; `--stale` exits 0 or 1 by the real cases, never 2.
  - `test_e014_citation_split_across_lines_is_not_a_citation`: a changed file `# @prd\n# T-002.1` (non-unit T-id) between base and head; `--diff` reports nothing for it.
  - `test_e015_an_uncommitted_citing_test_silences_the_tid`: committed `tests/test_import.py` citing `T-001.1` with its case edited after, plus untracked `tests/test_import2.py` citing `T-001.1`; `--stale` prints nothing for `T-001.1`, exit 0.
- [ ] **Step 2: Run** `tests/test_build_check.py`. Expected: the seven FAIL.
- [ ] **Step 3: Implement**, each minimal: E-009 in `prd_build_check.py` before `stale_findings` (`model.git_toplevel(prd.root) is None` → the exact line, exit 2); E-010 stop the block at the first blank line after a result line, and make the docstring and the inline comment say so; E-011 parse with the loader's YAML reader; E-012 `git ls-tree` without `-r`, filtered to direct `test-cases/*.yaml` children; E-013 `is_file()` on working-tree matches; E-014 scan per line with the trace's rule (import the trace helper; do not copy the regex logic); E-015 run `git status --porcelain --` over every citing file, and print no line for the T-id when any entry comes back.
- [ ] **Step 4: Run** `tests/test_build_check.py tests/test_build_check_refresh.py tests/test_trace.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): seven prd_build_check fixes from the build-check adoption extract`.

### Task 7: the approval card's base, and `refs` shape (a, c, e)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/gates.py` (`VERDICT_TYPES` line 69; `verdict_shape_ok` lines 74-83; `_diff_base` lines 858-867; `_approval_card` lines 877-886)
- Modify: `prd-toolkit/skills/changing-prds/reviewing-a-change.md` (step 8's verdict and its JSON example, line 64) and `prd-toolkit/skills/changing-prds/SKILL.md` (step 5's `.prd-review.json`, line 276)
- Test: `prd-toolkit/tests/test_gates_list.py` (shape), `prd-toolkit/tests/test_inbox_server.py` (card), `prd-toolkit/tests/test_inbox_skills.py` or `tests/test_changing_scripts.py` (skill pins)

**Interfaces:**
- Produces: verdict key `"base": "<full sha>"` (optional); `_diff_base(root: Path, verdict: dict | None = None) -> str | None`.

- [ ] **Step 1: Write the failing tests:**
  - `test_multiline_refs_is_no_gate`: a ready verdict whose `refs` is `"FR-001\nFR-002"` makes no approval gate; `"FR-001, FR-002"` still does; a `base` that is not a string makes no gate.
  - `test_card_diffs_against_the_verdict_base`: two commits after `main`; a verdict with `base` = the first commit's SHA; the card's diff holds only the second commit's PRD change and `version.from` is the version at the first commit.
  - `test_card_accepts_a_ref_name_as_base`: `base` = a branch name pointing at that commit; same result.
  - `test_card_without_base_uses_upstream_else_main`: no `base`, no upstream: the diff is against `main` (not a merge-base: a commit on `main` after the branch point shows reversed); with an upstream set, against the upstream.
  - `test_card_ignores_a_base_missing_from_the_repo`: `base` = 40 zeros → the fallback.
  - `test_fallback_ignores_origin_head_and_default_branch`: `init.defaultBranch` set to an existing branch `trunk` and no upstream: the diff is against `main`.
  - Skill pins: `reviewing-a-change.md`'s JSON example has `"base": "<sha>"`; both skill files say to write `base` as `git rev-parse <base>` of the base the diff read, its own call.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement:** `VERDICT_TYPES["base"] = str`; `verdict_shape_ok` also rejects a `refs` containing `\n` or `\r`; `_diff_base(root, verdict)` returns the verdict's `base` when `git cat-file -e <base>^{commit}` succeeds, else the upstream when `rev-parse @{upstream}` gives one, else `main` when it resolves, else `None` (no merge-base, no `origin/HEAD`, no `init.defaultBranch`); `_approval_card` passes its verdict. Skill edits per spec section 6 (a).
- [ ] **Step 4: Run** the touched test files plus `tests/test_inbox_page.py tests/test_gates_answer.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): the approval card diffs against the base the review read; a multi-line refs is no gate`.

### Task 8: a corrupt run log is a tool error; `beforeDone` is optional (b, d)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/deploy.py` (`_load_log` lines 306-317)
- Modify: `prd-toolkit/scripts/prd_deploy.py` (every `except ValueError` that can reach `_load_log`: lines 66, 115, 206 and any other)
- Modify: `prd-toolkit/scripts/prdlint/gates.py` (the deploy-step classification, lines 989-991)
- Modify: `prd-toolkit/templates/confirm/panel.html:397`
- Test: `prd-toolkit/tests/test_deploy_recover.py` (or `tests/test_deploy.py`), `prd-toolkit/tests/test_inbox_server.py`, `prd-toolkit/tests/test_confirm_page.py`

**Interfaces:**
- Produces: `deploy.CorruptLog(ValueError)`, raised by `_load_log` for "cannot read the log" and "has no header"; "no log for run" and "not a run id" stay plain `ValueError`.

- [ ] **Step 1: Write the failing tests:**
  - `test_corrupt_run_log_is_an_internal_error`: a run log whose second line is `{not json`; `prd_deploy.py confirm … --run <id> …` exits 2 with stderr starting `prd_deploy: internal error: CorruptLog: cannot read the log of run <id>`. A header-less log gives `… CorruptLog: the log of run <id> has no header`. `--run nosuch` still prints `prd_deploy: no log for run nosuch`.
  - `test_deploy_step_corrupt_log_answers_500`: through the inbox's deploy-step route with that log: status 500. A usage refusal (empty reply already covered elsewhere; use a wrong step) stays 400. A stderr containing `internal error` later in the line but not as the prefix is 400.
  - `test_panel_awaits_before_done_only_when_it_is_a_function`: the panel source guards the call with `typeof HOST.beforeDone === "function"` (a text pin, as `test_confirm_page.py` pins other script lines).
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Implement:** `CorruptLog`; a helper in `prd_deploy.py`, `_value_error(e: ValueError) -> int`, that returns `_fail(f"internal error: {type(e).__name__}: {e}")` for `CorruptLog` and `_fail(str(e))` otherwise, used at each `except ValueError` site; the route's `refused` becomes `code == 1 or (gate.kind == "deploy-step" and code == 2 and not first_stderr_line.startswith("prd_deploy: internal error:"))`; panel line 397 `if (HOST && typeof HOST.beforeDone === "function") await HOST.beforeDone();`.
- [ ] **Step 4: Run** the touched files plus `tests/test_deploy.py tests/test_deploy_record.py tests/test_deploying_skill.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): a corrupt deploy run log is a tool error, 500 in the inbox; beforeDone is optional`.

### Task 9: standby edge cases (f, g, h)

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/gates.py` (`make_inbox`, line 1078's `model.load`; a new exception class beside `InboxLive`)
- Modify: `prd-toolkit/scripts/prd_gates.py` (`_standby`, lines 168-208)
- Test: `prd-toolkit/tests/test_inbox_lock.py`

**Interfaces:**
- Produces: `gates.PrdUnreadable(Exception)`, raised by `make_inbox` when its `model.load` raises `OSError` (with `from e`); documented in `make_inbox`'s docstring.

- [ ] **Step 1: Write the failing tests** (drive `_standby` with monkeypatched `gates.live_inbox`, `_pending`, `gates.make_inbox` and a fast `STANDBY_POLL`, as the existing standby tests do):
  - `test_standby_keeps_standing_by_when_the_prd_vanishes_mid_takeover`: `make_inbox` raises `PrdUnreadable` once, then succeeds; `_standby` does not return 2 and ends in `_run_inbox`; stderr has no `cannot take over`.
  - `test_standby_says_an_unexpected_error_once`: `make_inbox` raises `KeyError("x")` three times, then the gate leaves; stderr holds `prd_gates: standby: KeyError: 'x'` exactly once; exit 1.
  - `test_standby_prints_nothing_for_an_expected_load_failure`: `make_inbox` raises `model.NotAPrd` / `PrdUnreadable`; no `prd_gates: standby:` line.
  - `test_not_pending_wins_over_idle_in_the_same_tick`: `--idle-minutes` tiny so the bound has passed at the first tick, and `_pending` False; exit 1 with `<gate> is not pending`, not 3.
  - `test_still_pending_past_the_bound_exits_3`: unchanged behaviour pinned.
- [ ] **Step 2: Run** `tests/test_inbox_lock.py`. Expected: the first four FAIL.
- [ ] **Step 3: Implement:** wrap `make_inbox`'s `model.load` in `except OSError as e: raise PrdUnreadable(str(e)) from e`; in `_standby`, check `_pending` before the idle bound, add `except (gates.PrdUnreadable, model.NotAPrd): continue` before the `OSError` branch, and turn the trailing `except Exception` into one that prints `prd_gates: standby: {type(e).__name__}: {e}` (flush) the first time its `(type, str)` pair is seen (a set local to `_standby`), then continues.
- [ ] **Step 4: Run** `tests/test_inbox_lock.py tests/test_gates_wait.py tests/test_inbox_server.py`. Expected: PASS.
- [ ] **Step 5: Re-vendor and commit** `fix(prd-toolkit): a standby rides out a vanishing PRD, says an unexpected error once, and exits 1 before idle`.

### Task 10: release text and version

**Files:**
- Modify: `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (prd-toolkit entry), and any other file `tests/test_release_0_8_2.py` reads the version from
- Modify: `prd-toolkit/README.md` (0.8.3 changelog entry above 0.8.2's; the script table row for `prd_hooks.py vendor`; the local-testing note on namespaced commands; the "Upgrading from 0.8.2" line)
- Test: `prd-toolkit/tests/test_release_0_8_3.py` (new, modelled on `tests/test_release_0_8_2.py`)

- [ ] **Step 1: Write the failing pins:** the version files say `0.8.3`; the README's 0.8.3 entry names `prd_hooks.py vendor`, the exact-refresh rule, the standby check, `record`'s Since and contract IDs, the seven build-check fixes (by behaviour, not proof E-numbers), the inbox fixes, and the upgrade (`re-run prd_hooks.py install`; no PRD edit); the local-testing section contains `/prd-toolkit:prd-change`; the 0.8.2 release test's version pin is moved, not deleted (it pins "at least 0.8.2" or the 0.8.2 entry text).
- [ ] **Step 2: Run** it. Expected: FAIL.
- [ ] **Step 3: Write** the README text (spec sections 7 and 10) and bump the versions.
- [ ] **Step 4: Run** `tests/test_release_0_8_3.py tests/test_release_0_8_2.py tests/test_manifests.py tests/test_references.py`. Then `uv run --script prd-toolkit/scripts/prd_hooks.py vendor docs/prd/prd-toolkit` (VERSION moves to 0.8.3) and `tests/test_vendored_copy.py`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(prd-toolkit): 0.8.3 release text and version`, staging `.prd-toolkit/` too.

### Task 11: verification

- [ ] **Step 1:** `HOME=<an empty directory under the scratchpad> scripts/ci-local.sh origin/main` from the worktree root. Expected: every job `pass` (prd-lint, prd-trace, standards, test-unit, test-integration).
- [ ] **Step 2:** The inbox evals, from the worktree root: `claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" --case 'inbox-*' --json <scratchpad>/evals-0.8.3.json`. Expected: every case passes.
- [ ] **Step 3:** `/usr/bin/grep -rniE` over `git diff main..HEAD` for employer, host and customer names. Expected: no hit.
- [ ] **Step 4:** Report the results; the branch is ready for the final review and `superpowers:finishing-a-development-branch`. The spec's section 9 proof (E-007 through the real PRD) runs after the merge, on Ivan's word, and is not part of this plan.
