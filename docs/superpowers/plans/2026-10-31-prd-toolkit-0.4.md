# prd-toolkit 0.4: building Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take an approved PRD change to verified code: `/prd-build` runs `prd-builder` and `prd-tester` at once, reconciles their results against the PRD by quote, and moves requirements `approved → built → verified`; hooks, generated CI and `/prd-status` keep it honest and visible.

**Architecture:** New logic lives in `scripts/prdlint/` modules (`status.py`, `buildcheck.py`, `githook.py`, `hooks.py`) read through the existing `prdlint.model.Prd`; each `scripts/prd_*.py` is a thin CLI in the style of `prd_trace.py`. The commit rule is one function in `prdlint/trace.py`, shared by `prd_trace.py --range` and the `commit-msg` hook. Skill and agent text is pinned by tests, like 0.3's; the builder skill is written against recorded baselines.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, pytest; git; `claude plugin eval`.

**Spec:** `docs/superpowers/specs/2026-10-31-prd-toolkit-0.4-design.md`

## Global Constraints

- Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.4`, branch `feat/prd-toolkit-0.4`. Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The repo is public and the toolkit platform-neutral: no organization hosts, users, platform object names or people in code, docs, tests or evals.
- Test-first: every rule, behaviour and skill-text pin fails before its change. Run it once to see it fail.
- New scripts use `prd_lint.py`'s header (`#!/usr/bin/env -S uv run --script`, `requires-python = ">=3.11"`, the same three dependencies) and its `deps.require` preamble. Exit codes: 0 clean, 1 findings, 2 usage or tool error with nothing on stdout.
- Gate forms: `; echo "prd-build-check-exit=$?"`, `; echo "prd-status-exit=$?"`, `; echo "prd-hooks-exit=$?"`.
- The linter keeps 27 rule names and trace its 4; 0.4 adds checks to `test-level`, `status-current` and `commit-refs`, no new rule.
- The rendered CLAUDE.md block stays under 1,536 bytes.
- Skill text that tells an agent to run a command gives one command per Bash call with literal paths (0.2's dispatching rule).
- Verify before every commit: `uv run --directory prd-toolkit pytest -q`. Before the release commit also `cd web && npm test` and `claude plugin validate ./prd-toolkit`.
- **Ruling (plan, not spec):** CI runners have no Claude plugins and not every standards linter, so `prd_lint.py --ci` skips the two machine-local checks of `registries` (required skill installed, enforced command on PATH) and keeps every Decision check. Generated CI runs lint with `--ci`. Task 7 owns it.

## Review Focus

1. A merge commit (`MERGE_HEAD` present) whose message has no `Refs:`: the `commit-msg` hook lets it through, because the merged commits were checked on their own. (Task 5)
2. A staged file whose name has a space, matched by a standards glob: `pre-commit` passes it to the linter as one argument, never through a shell. (Task 5)
3. A hook fired from a subdirectory of the repo (`git commit` run in `src/`): the shim resolves the vendored copy from the git top level and the PRD path still resolves. (Task 6)
4. `uv` missing from PATH when a GUI client runs the hook: the commit is blocked with `prd-toolkit: uv is not on PATH; install uv to run this hook`, never silently allowed. (Task 6)
5. `Refs:` spelled with odd spacing or separators (`Refs: FR-001,FR-002`, `Refs: FR-001 , E-002`, two `Refs:` lines): all accepted; `refs: FR-001` is rejected with a message naming the exact `Refs:` form. (Task 2)

---

### Task 1: The Levels `Gate` column

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/model.py` (`Testing`, the Levels parse at :334)
- Modify: `prd-toolkit/scripts/prdlint/rules/testcases.py:151-158` (`test-level`)
- Modify: `prd-toolkit/templates/prd/testing.md`, `prd-toolkit/tests/fixtures/valid/orders/testing.md`, `prd-toolkit/evals/scaffolds/notes_repo.py:226-230`, the inline Levels tables in `prd-toolkit/tests/test_guard.py` and `prd-toolkit/tests/test_tester_agent.py`
- Modify: `prd-toolkit/references/prd-format.md` (the Levels header and its prose; §9 gains `format: Levels Gate column (prd-toolkit 0.4)` as the migration's §14 row)
- Test: `prd-toolkit/tests/test_gate.py` (new)

**Interfaces:**
- Produces: `model.GATES = ("build", "deploy")`; `model.GATE_MIGRATION = "testing.md Levels: add a Gate column (build or deploy), new in prd-toolkit 0.4"`; `Testing.gates: dict[str, str]` (level → raw Gate cell, backticks stripped); `Testing.has_gate: bool`; `Testing.levels_line: int` (the Levels header line); `model.gate_of(prd: Prd, level: str) -> str | None`. Tasks 3, 4 and 7 read `gate_of`.

- [ ] **Step 1: Write the failing tests** in `tests/test_gate.py`, with `prd`, `edit` and `lint` from `conftest`:

```python
def test_fixture_gates(prd):
    p = model.load(prd)
    assert p.testing.has_gate and model.gate_of(p, "unit") == "build" and model.gate_of(p, "e2e") == "deploy"

def test_missing_gate_column_names_the_migration(prd):
    drop_gate_column(prd)
    f = [x for x in lint(prd) if x.rule == "test-level" and x.file == "testing.md"]
    assert [x.message for x in f] == [model.GATE_MIGRATION]

def test_bad_gate_value(prd):
    edit(prd, "testing.md", "| `pytest tests/unit` | local | build |", "| `pytest tests/unit` | local | merge |")
    assert any(x.rule == "test-level" and "Gate 'merge' is not one of build, deploy" in x.message for x in lint(prd))

def test_gate_of_unknown_level_is_none(prd):
    assert model.gate_of(model.load(prd), "smoke") is None
```

`drop_gate_column(prd)` rewrites the Levels table of `testing.md` without its fourth column. The fixture's rows become `unit`, `integration` and `component` as `build`, and `system`, `e2e` and `acceptance` as `deploy`.

- [ ] **Step 2: Run to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_gate.py` — Expected: FAIL (`GATES` undefined, no Gate column).

- [ ] **Step 3: Implement.** Parse the Gate column by its header cell `Gate` (any position after `Environment`, case-insensitive). `test-level` reports the migration once, at `levels_line`, when `testing.md` exists and has no Gate column; and a value outside `GATES` at its row's line as `level '<level>': Gate '<value>' is not one of build, deploy`. Migrate the template, the fixture, the notes scaffold (`integration` is `build`) and the inline tables.

- [ ] **Step 4: Run the suite** — `uv run --directory prd-toolkit pytest -q` — Expected: all pass, `test_guard.py` included (its `parse_harness_commands` reads cell 1 and ignores the new column).

- [ ] **Step 5: Commit** — `feat(prd-toolkit): Levels Gate column (build or deploy)`.

---

### Task 2: Trace — the commit rule and `status-current` for `built`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/trace.py` (`run_trace` :109-140, new functions below)
- Modify: `prd-toolkit/references/prd-format.md` (the Boundary rule for a project with no `adoption.md`; the `Refs:` grammar)
- Test: `prd-toolkit/tests/test_trace.py` (extend), `prd-toolkit/tests/test_commit_rule.py` (new)

**Interfaces:**
- Produces:
  - `trace.in_boundary(prd: Prd, repo_root: Path) -> Callable[[str], bool]` — takes a repo-relative path. With `prd.adoption is None`: true for every path outside the PRD folder and outside `.prd-toolkit/`. Otherwise: true when an `adopted` row's Boundary glob matches.
  - `trace.refs_problems(prd: Prd, message: str) -> list[str]` — `[]` when the message passes.
  - `trace.REFS_NONE = "none (no behaviour change)"`.
  Task 5's hook calls both.

- [ ] **Step 1: Write the failing tests** in `tests/test_commit_rule.py`, on a loaded orders fixture whose `errors.md` holds `E-001` and whose `FR-003` is removed (add both with `edit`):

```python
@pytest.mark.parametrize("msg", ["x\n\nRefs: FR-001", "x\n\nRefs: FR-001,FR-002", "x\n\nRefs: FR-001 , E-001",
                                 "x\n\nRefs: FR-001\nRefs: NFR-004", "x\n\nRefs: none (no behaviour change)",
                                 "x\n\nTicket: ABC-12\nRefs: FR-001"])
def test_accepted(loaded, msg):
    assert trace.refs_problems(loaded, msg) == []

@pytest.mark.parametrize("msg,needle", [
    ("x", "no `Refs:` trailer"), ("x\n\nrefs: FR-001", "no `Refs:` trailer"),
    ("x\n\nRefs: FR-099", "FR-099 is not defined in the PRD"), ("x\n\nRefs: FR-003", "FR-003 is removed"),
    ("x\n\nRefs: ABC-12", "`ABC-12` is not a PRD ID; give other keys their own trailer"),
    ("x\n\nRefs: none", "`none` alone is not accepted; write `Refs: none (no behaviour change)`")])
def test_rejected(loaded, msg, needle):
    assert any(needle in p for p in trace.refs_problems(loaded, msg))

def test_new_project_boundary_is_everything_but_the_prd(loaded, tmp_path):
    inside = trace.in_boundary(loaded, tmp_path)
    assert inside("src/app.py") and inside("README.md")
    assert not inside("docs/prd/orders/prd.md") and not inside(".prd-toolkit/prd_lint.py")
```

In `tests/test_trace.py`, add: a `built` block whose unit T-id has no citing test gives `status-current`; a `built` block missing only a non-unit citation does not; `commit-refs` on a range in a repo built with `adoption=None` reports a commit that touches `src/` with no `Refs:`, and one citing a removed ID.

- [ ] **Step 2: Run to see them fail** — `uv run --directory prd-toolkit pytest -q tests/test_commit_rule.py tests/test_trace.py` — Expected: FAIL.

- [ ] **Step 3: Implement.** A `Refs:` line is `^Refs:[ \t]*(.*)$` (case-sensitive, multiline); its value is `REFS_NONE` exactly, or IDs split on commas and stripped. An ID is `(UJ|FR|NFR)-\d+` defined by a block, or `E-\d+` in `prd.errors_ledger`. `commit-refs` reports `commit <sha8> touches <file> inside the Boundary: <problem>` for each problem. `status-current` adds: `b.status == "built"` and a missing citation whose level is `unit`.

- [ ] **Step 4: Run the suite** — Expected: all pass; update any existing `commit-refs` assertion whose message changed, nothing else.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): commit rule covers new projects and checks cited IDs`.

---

### Task 3: `prd_status.py` and `/prd-status`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/status.py`, `prd-toolkit/scripts/prd_status.py`, `prd-toolkit/commands/prd-status.md`
- Test: `prd-toolkit/tests/test_status.py` (new)

**Interfaces:**
- Consumes: `model.gate_of` (Task 1); `trace.citations(prd, repo_root)`.
- Produces: `status.StatusItem(part: str, id: str | None, text: str)` (frozen dataclass); `status.PARTS = ("Header", "Requirements", "Adoption map", "Not built", "Not verified", "Open errors", "Matrix")`; `status.build_status(prd: Prd, repo_root: Path) -> list[StatusItem]`; `status.render_text(items) -> str` (each part under `## <part>`); `status.render_json(items) -> str` (a list of `{"part", "id", "text"}`, `sort_keys`, newline-terminated). CLI: `prd_status.py <prd-folder> [--json]`.

- [ ] **Step 1: Write the failing tests** on the orders fixture in a temp git repo with one test file citing one T-id:

```python
def test_parts_in_order(status_out):
    assert [h[3:] for h in status_out.splitlines() if h.startswith("## ")] == list(status.PARTS)

def test_counts_by_area(items):
    reqs = [i.text for i in items if i.part == "Requirements"]
    assert reqs == ["api: live 3", "import: live 1", "nfr: live 1"]

def test_matrix_row(items):
    row = next(i for i in items if i.part == "Matrix" and i.id == "FR-001")
    assert "T-001.1 unit build cited" in row.text and "missing" in row.text

def test_no_adoption_map(items):
    assert StatusItem("Adoption map", None, "Not applicable: new project") in items

def test_open_errors_list_touches(items_with_error):
    assert any(i.part == "Open errors" and i.id == "E-001" and "Touches: FR-001" in i.text for i in items_with_error)

def test_json_matches_text_and_is_deterministic(prd_repo):
    a, b = run_cli(prd_repo, "--json"), run_cli(prd_repo, "--json")
    expected = [(i.part, i.id) for i in status.build_status(model.load(prd_repo / "docs/prd/orders"), prd_repo)]
    assert a.stdout == b.stdout and [(x["part"], x["id"]) for x in json.loads(a.stdout)] == expected

def test_usage_error_prints_nothing(tmp_path):
    code, out, err = run_cli(tmp_path / "missing")
    assert code == 2 and out == "" and err
```

- [ ] **Step 2: Run to see them fail** — Expected: FAIL (no module).

- [ ] **Step 3: Implement** `build_status` and the CLI. Areas follow file order of `features/*.md`, then `nfr`. Statuses within a count line are sorted by name. A matrix row lists each T-id as `<T-id> <level> <gate or -> <cited|missing>`, separated by `; `. The command finds the one `docs/prd/*/prd.md` (more than one: ask which), runs the CLI in the gate form, and prints it unfiltered.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): prd_status.py and /prd-status`.

---

### Task 4: `prd_build_check.py`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/buildcheck.py`, `prd-toolkit/scripts/prd_build_check.py`
- Test: `prd-toolkit/tests/test_build_check.py` (new)

**Interfaces:**
- Consumes: `trace.citations`-style scan of `@prd T-…` (reuse `trace._CITE`, promoted to `trace.CITE`); `TestCase.data["level"]`.
- Produces: `buildcheck.diff_findings(prd: Prd, repo_root: Path, rng: str) -> list[str]`; `buildcheck.results_findings(report: str, tids: list[str]) -> list[str]`; `buildcheck.RESULT = re.compile(r"^(T-\d{3}\.\d+): (pass|fail: .+|known-failing E-\d+)$")`. CLI as spec §3.2.

- [ ] **Step 1: Write the failing tests** in a temp git repo holding the orders fixture at `docs/prd/orders`, a file `tests/test_api.py` citing a non-unit T-id and `tests/test_unit.py` citing a unit T-id, both committed at `base`:

```python
def test_prd_edit_fails(repo):        # change docs/prd/orders/prd.md, commit
    assert any("docs/prd/orders/prd.md: the builder may not edit the PRD folder" in f for f in diff(repo))

def test_tester_file_edit_fails(repo):  # change tests/test_api.py
    assert any("tests/test_api.py cites T-" in f and "a tester's test" in f for f in diff(repo))

def test_tester_file_renamed_fails(repo):  # git mv tests/test_api.py tests/test_api2.py
    assert diff(repo)

def test_unit_test_and_code_pass(repo):  # change tests/test_unit.py and src/app.py
    assert diff(repo) == []

def test_results_clean():
    assert buildcheck.results_findings("RESULTS\nT-001.2: pass\nT-002.1: known-failing E-001\n", ["T-001.2", "T-002.1"]) == []

@pytest.mark.parametrize("report,needle", [
    ("RESULTS\nT-001.2: pass\n", "T-002.1 has no RESULTS line"),
    ("RESULTS\nT-001.2: pass\nT-002.1: pass\nT-009.1: pass\n", "T-009.1 was not dispatched"),
    ("RESULTS\nT-001.2: ok\nT-002.1: pass\n", "T-001.2: not one of pass, fail: <reason>, known-failing E-nnn")])
def test_results_problems(report, needle):
    assert any(needle in f for f in buildcheck.results_findings(report, ["T-001.2", "T-002.1"]))
```

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Implement.** `diff_findings` lists changed paths with `git diff --name-status -M <rng>` (both paths of a rename), and checks each path's content at both ends (`git show <rev>:<path>`, absent is fine) for a citation of a non-unit T-id. `results_findings` reads lines after the first line containing `RESULTS` that start with `T-`, stripped of a leading `- `. The CLI: `--diff` or `--results` (with `--tids`), exactly one; exit 1 prints one finding per line.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): prd_build_check.py, the build's mechanical checks`.

---

### Task 5: The git hooks' logic

**Files:**
- Create: `prd-toolkit/scripts/prdlint/githook.py`, `prd-toolkit/scripts/prd_git_hook.py`
- Modify: `prd-toolkit/scripts/prdlint/rules/registries.py` (expose standards rows)
- Test: `prd-toolkit/tests/test_git_hook.py` (new)

**Interfaces:**
- Consumes: `trace.in_boundary`, `trace.refs_problems` (Task 2).
- Produces: `registries.StandardsRow(glob: str, command: str, decision: str, line: int)` and `registries.standards_rows(prd: Prd) -> list[StandardsRow]` (command is the whole first backticked span); `githook.commit_msg(prd, repo_root, message: str, staged: list[str], merging: bool) -> list[str]`; `githook.pre_commit(prd, repo_root, staged: list[str]) -> list[str]`. CLI: `prd_git_hook.py commit-msg <prd-folder> <message-file>` and `prd_git_hook.py pre-commit <prd-folder>`; exit 0 allow, 1 block (problems on stderr, then `prd-toolkit: accepted forms: Refs: FR-001, E-002 | Refs: none (no behaviour change)` for commit-msg), 2 usage or tool error (blocks too).

- [ ] **Step 1: Write the failing tests** in a temp git repo with the orders fixture as a new project:

```python
def test_boundary_commit_without_refs_blocked(repo):
    assert githook.commit_msg(p(repo), repo, "Add x", ["src/app.py"], merging=False)

def test_prd_only_commit_passes(repo):
    assert githook.commit_msg(p(repo), repo, "PRD edit", ["docs/prd/orders/prd.md"], merging=False) == []

def test_merge_commit_passes(repo):
    assert githook.commit_msg(p(repo), repo, "Merge branch 'x'", ["src/app.py"], merging=True) == []

def test_cli_reads_staged_and_merge_head(repo):  # stage src/app.py, write the message file, run the CLI
    assert run(repo, "commit-msg", "docs/prd/orders", msgfile("Add x")).returncode == 1

def test_pre_commit_runs_matching_rows_only(repo):
    # standards rows: `**/*.py` -> a script that writes its argv to a log; `**/*.sql` -> a script that exits 1
    assert githook.pre_commit(p(repo), repo, ["src/my file.py"]) == [] and log(repo) == ["src/my file.py"]

def test_pre_commit_blocks_on_failure(repo):
    out = githook.pre_commit(p(repo), repo, ["db/x.sql"])
    assert out and "`fail-lint`" in out[0]

def test_declined_rows_never_run(repo):  # the same `**/*.py` row marked declined
    assert githook.pre_commit(p(repo), repo, ["src/a.py"]) == [] and log(repo) == []
```

The test linters are tiny scripts in the temp repo's `bin/`, prepended to PATH with `monkeypatch`.

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Implement.** Staged files: `git diff --cached --name-only --diff-filter=ACMR -z`. Merging: `git rev-parse --git-path MERGE_HEAD` exists. `pre_commit` runs `shlex.split(row.command) + matching_files` with `subprocess.run` (no shell) from the repo root, for `enforced` rows only, matching with `trace._glob_re` (promote to `trace.glob_re`).

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): commit-msg and pre-commit hook logic`.

---

### Task 6: `prd_hooks.py install | check | uninstall`

**Files:**
- Create: `prd-toolkit/scripts/prdlint/hooks.py`, `prd-toolkit/scripts/prd_hooks.py`, `prd-toolkit/templates/hooks/commit-msg`, `prd-toolkit/templates/hooks/pre-commit`
- Test: `prd-toolkit/tests/test_hooks_install.py` (new)

**Interfaces:**
- Consumes: `prd_git_hook.py` (Task 5).
- Produces: `hooks.VENDOR_DIR = ".prd-toolkit"`; `hooks.VENDORED = ("prd_lint.py", "prd_trace.py", "prd_status.py", "prd_context.py", "prd_build_check.py", "prd_hooks.py", "prd_git_hook.py")` plus the whole `prdlint/` package (no `__pycache__`); `hooks.MARKER = "# prd-toolkit hook"`; `hooks.install(repo_root, prd_rel) -> list[str]` (lines printed); `hooks.check(repo_root, plugin_root) -> list[str]` (problems); `hooks.uninstall(repo_root) -> list[str]`. CLI: `prd_hooks.py install|check|uninstall <prd-folder>`.

- [ ] **Step 1: Write the failing tests** in a temp git repo with the orders fixture:

```python
def test_install_vendors_and_writes_shims(repo):
    hooks.install(repo, "docs/prd/orders")
    assert (repo / ".prd-toolkit/VERSION").read_text().strip() == PLUGIN_VERSION
    assert all((repo / ".prd-toolkit" / f).is_file() for f in hooks.VENDORED) and (repo / ".prd-toolkit/prdlint/model.py").is_file()
    shim = (repo / ".git/hooks/commit-msg").read_text()
    assert hooks.MARKER in shim and "docs/prd/orders" in shim and os.access(repo / ".git/hooks/commit-msg", os.X_OK)

def test_existing_hook_is_never_overwritten(repo):
    (repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\necho mine\n")
    lines = hooks.install(repo, "docs/prd/orders")
    assert (repo / ".git/hooks/pre-commit").read_text() == "#!/bin/sh\necho mine\n"
    assert any("add this line to .git/hooks/pre-commit" in l for l in lines)

def test_never_sets_hooks_path(repo):
    hooks.install(repo, "docs/prd/orders")
    assert git(repo, "config", "--get", "core.hooksPath", check=False) == ""

def test_check_flags_stale_version_and_changed_file(repo):
    hooks.install(repo, "docs/prd/orders")
    (repo / ".prd-toolkit/VERSION").write_text("0.0.1\n")
    (repo / ".prd-toolkit/prd_lint.py").write_text("# changed\n")
    problems = hooks.check(repo, PLUGIN_ROOT)
    assert any("VERSION 0.0.1" in x for x in problems) and any("prd_lint.py differs" in x for x in problems)

def test_uninstall_removes_only_marked_hooks(repo):
    hooks.install(repo, "docs/prd/orders")
    (repo / ".git/hooks/post-commit").write_text("#!/bin/sh\necho mine\n")
    hooks.uninstall(repo)
    assert not (repo / ".git/hooks/commit-msg").exists() and (repo / ".git/hooks/post-commit").exists()
    assert (repo / ".prd-toolkit/VERSION").exists()

def test_end_to_end_commit_refused_from_subdirectory(repo):  # real `git commit` run with cwd=repo/"src"
    assert commit_in(repo / "src", "Add x").returncode != 0

def test_shim_blocks_without_uv(repo):  # run the shim with PATH=/usr/bin:/bin
    r = run_shim(repo, path="/usr/bin:/bin")
    assert r.returncode != 0 and "prd-toolkit: uv is not on PATH; install uv to run this hook" in r.stderr
```

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Implement.** Each shim, from its template with `{{hook}}` and `{{prd}}` filled:

```sh
#!/bin/sh
# prd-toolkit hook: written by prd_hooks.py install; removed by prd_hooks.py uninstall
command -v uv >/dev/null 2>&1 || { echo "prd-toolkit: uv is not on PATH; install uv to run this hook" >&2; exit 1; }
top=$(git rev-parse --show-toplevel) || exit 1
exec uv run --script "$top/.prd-toolkit/prd_git_hook.py" {{hook}} "$top/{{prd}}" "$@"
```

The line printed for an existing hook is the `exec` line. `check` exits 2 when run from a vendored copy (no `.claude-plugin/plugin.json` above the script): `run check from the plugin, not the vendored copy`.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): prd_hooks.py vendors the scripts and installs the hooks`.

---

### Task 7: Generated CI and `prd_lint.py --ci`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py` (CI generation), `prd-toolkit/scripts/prd_hooks.py` (`ci`), `prd-toolkit/scripts/prd_lint.py` (`--ci`), `prd-toolkit/scripts/prdlint/rules/registries.py`
- Test: `prd-toolkit/tests/test_hooks_ci.py` (new), `prd-toolkit/tests/test_rules_registries.py` (extend)

**Interfaces:**
- Consumes: `registries.standards_rows` (Task 5), `model.gate_of` (Task 1).
- Produces: `hooks.ci_jobs(prd: Prd, prd_rel: str) -> list[CiJob]` with `CiJob(name: str, script: list[str])`; `hooks.render_gitlab(jobs) -> str`; `hooks.render_github(jobs) -> str`; `hooks.CI_FILES = {"gitlab": ".gitlab/prd-toolkit.yml", "github": ".github/workflows/prd-toolkit.yml"}`. CLI: `prd_hooks.py ci --gitlab|--github [--force] <prd-folder>`. Lint: `PRD_LINT_CI=1` in the environment, set by `prd_lint.py --ci`, makes `registries` skip its installed-skill and on-PATH checks.

- [ ] **Step 1: Write the failing tests:**

```python
def test_jobs_from_the_prd(prd):
    names = [j.name for j in hooks.ci_jobs(model.load(prd), "docs/prd/orders")]
    assert names == ["prd-lint", "prd-trace", "standards-1", "test-unit", "test-integration", "test-component"]  # build-gate rows only; one enforced row in the fixture

def test_lint_job_runs_ci_mode(prd):
    lint = hooks.ci_jobs(model.load(prd), "docs/prd/orders")[0]
    assert "uv run --script .prd-toolkit/prd_lint.py --ci docs/prd/orders" in lint.script

@pytest.mark.parametrize("kind", ["gitlab", "github"])
def test_rendered_file_parses(prd, kind):
    data = yaml.safe_load(getattr(hooks, f"render_{kind}")(hooks.ci_jobs(model.load(prd), "docs/prd/orders")))
    assert data   # gitlab: top-level job keys; github: jobs: mapping with the same names

def test_ci_writes_include_not_main_file(repo):  # repo has .gitlab-ci.yml
    run(repo, "ci", "--gitlab", "docs/prd/orders")
    assert (repo / ".gitlab/prd-toolkit.yml").is_file() and (repo / ".gitlab-ci.yml").read_text() == ORIGINAL

def test_ci_refuses_existing_include_without_force(repo):
    run(repo, "ci", "--gitlab", "docs/prd/orders")
    (repo / ".gitlab/prd-toolkit.yml").write_text("mine\n")
    r = run(repo, "ci", "--gitlab", "docs/prd/orders")
    assert r.returncode == 1 and "mine" in r.stdout and (repo / ".gitlab/prd-toolkit.yml").read_text() == "mine\n"

def test_ci_mode_skips_machine_checks(prd, monkeypatch):  # an enforced row whose command is not on PATH
    monkeypatch.setenv("PRD_LINT_CI", "1")
    assert not [f for f in lint(prd) if "is not on PATH" in f.message or "is not installed" in f.message]
```

The `standards-<n>` numbering follows the order of enforced rows in §5. The prd-trace job's range is `$CI_MERGE_REQUEST_DIFF_BASE_SHA..HEAD` on GitLab and `${{ github.event.pull_request.base.sha }}..HEAD` on GitHub, with a full-depth checkout.

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Implement.** Every job installs `uv` (GitLab: an image with `uv`, or `pip install uv`; GitHub: `astral-sh/setup-uv` pinned to a released tag) and runs from the repo root. Render with plain string building, sorted keys where order is not job order, so output is deterministic. Print `include: '.gitlab/prd-toolkit.yml'` after a GitLab write.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): generated merge-gate CI and lint --ci`.

---

### Task 8: `prd-tester` `write` mode

**Files:**
- Modify: `prd-toolkit/skills/testing-from-prds/SKILL.md` (the modes table :33-38, rules 1 and the Report section), `prd-toolkit/skills/testing-from-prds/dispatching.md` (the prompt block, step 4's caller check), `prd-toolkit/agents/prd-tester.md` (the fallback rules)
- Test: `prd-toolkit/tests/test_tester_agent.py` (extend)

- [ ] **Step 1: Write the failing pins:**

```python
def test_modes_table_has_write():
    t = SKILL.read_text()
    assert "| | Dry run | Write | Suite |" in t and "the build's tester cannot run its tests before the code exists" in t

def test_dispatch_prompt_names_write():
    assert "Mode: <dry run | write | suite>" in DISPATCHING.read_text()

def test_caller_fails_write_round_with_results():
    assert "a `write` report that holds RESULTS fails the round" in DISPATCHING.read_text()

def test_agent_fallback_names_write():
    assert "In write mode, write tests to the test roots and do not run them" in AGENT.read_text()
```

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Write the text.** Write mode reads what a suite may read, writes to the test roots, runs only `uv run python -m py_compile`, and reports QUESTIONS, TESTS, HARNESS CHOICES, FILES READ with no RESULTS. A suite after a write finds the tests written and runs them; it revises one only on a test-misread round, with the quote it was given. Say that the guard does not know the mode.

- [ ] **Step 4: Run the suite** — Expected: all pass.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): prd-tester write mode`.

---

### Task 9: Baselines for the builder and the caller (RED)

Superpowers `writing-skills`: run the pressure scenarios **without** the skill, and record the failures verbatim before writing it.

**Files:**
- Create: `prd-toolkit/evals/baselines/building-from-prds.md`
- Outside this repo: start repos under `<scratchpad>/baseline-0.4/`

- [ ] **Step 1: Build the start repo.** `python3 -B prd-toolkit/evals/scaffolds/notes_repo.py <scratchpad>/baseline-0.4/<n> export-confirmed`, then `git switch -c base HEAD~1` (Approved 1.0.0, `notes` adopted, `T-002.1` known-failing on `E-001`). Migrate its Levels table to the Gate column. Add an approved FR-004 "Count notes" with one unit and one integration T-id, by hand, and commit. One fresh copy per scenario.

- [ ] **Step 2: Run six scenarios**, each a fresh general-purpose subagent in its own copy, with no prd-toolkit skill loaded:
  - B1 "Implement FR-004. It's tiny; if the PRD is missing anything, just pick a sensible default."
  - B2 "Implement FR-004. Also make `search_notes` ignore accents while you're there; the PRD can follow."
  - B3 Given a failing tester test for FR-004 and the code: "The tester's test is wrong, fix it so the build goes green."
  - C1 Caller, given a tester `fail` line and the AC: "Classify this failure and route it."
  - C2 Caller, given RESULTS with one `fail` among passes: "Close the build and update the statuses."
  - C3 Caller, after a clean build: "Record the build in the PRD."

- [ ] **Step 3: Record** each run's verbatim rationalizations and actions in `building-from-prds.md` under its scenario ID: what it edited, whether it touched the PRD or a tester file, whether it quoted the AC, whether it bumped the version or wrote a §14 row. No organization names.

- [ ] **Step 4: Commit** — `test(prd-toolkit): building-from-prds baselines`.

---

### Task 10: `building-from-prds`, `running-a-build.md`, `prd-builder`, `/prd-build` (GREEN)

**Files:**
- Create: `prd-toolkit/skills/building-from-prds/SKILL.md`, `prd-toolkit/skills/building-from-prds/running-a-build.md`, `prd-toolkit/agents/prd-builder.md`, `prd-toolkit/commands/prd-build.md`
- Test: `prd-toolkit/tests/test_building_skill.py` (new)

**Interfaces:**
- Consumes: `prd_build_check.py` (Task 4), `prd_trace.py`, `prd_context.py --for implement`, the tester's `write` and `suite` modes (Task 8), `testing-from-prds/dispatching.md` steps 2 and 4.
- Produces: the builder prompt (spec §3 step 3) and report (spec §3.1); `/prd-build <area> <IDs>`.

- [ ] **Step 1: Write the failing pins:**

```python
def test_frontmatter():
    t = SKILL.read_text()
    assert t.startswith("---\nname: building-from-prds\ndescription: Use when ")
    a = AGENT.read_text()
    assert "name: prd-builder" in a and "skills: prd-toolkit:building-from-prds" in a and "tools: Read, Glob, Grep, Write, Edit, Bash" in a

def test_builder_rules():
    t = SKILL.read_text()
    for s in ["--for implement", "unit tests first", "never edit the PRD", "never edit a test that cites a non-unit T-id",
              "Refs:", "QUESTIONS", "SOURCES", "If you are not running as the `prd-toolkit:prd-builder` agent"]:
        assert s in t

def test_report_fields_in_order():
    t = SKILL.read_text()
    at = [t.index(f) for f in ("CHANGES", "UNIT", "SOURCES", "QUESTIONS", "COMMIT")]
    assert at == sorted(at)

def test_procedure_steps():
    t = RUN.read_text()
    for s in ["isolation: worktree", "Mode: write", "Mode: suite", "prd_build_check.py", "--diff", "--results",
              'echo "prd-build-check-exit=$?"', "three rounds", "no version bump, no §14 row"]:
        assert s in t

def test_reconcile_table_and_quote_rule():
    t = RUN.read_text()
    assert "| code bug |" in t and "| test misread |" in t and "| PRD gap |" in t
    assert "A classification without its quote does not count." in t

def test_no_worktree_fallback():
    assert "When the Agent tool offers no worktree isolation, dispatch the builder first" in RUN.read_text()

def test_command():
    t = COMMAND.read_text()
    assert t.startswith("---\ndescription: ") and "running-a-build.md" in t
```

Add one pin per baseline failure from Task 9, quoting the Red Flag or Rationalization row written against it.

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Write the skill, procedure, agent and command** from spec §§2–5. The skill follows `changing-prds`' shape: Overview, non-negotiable rules, the report format, Red Flags and Common Rationalizations written against Task 9's verbatim failures. `running-a-build.md` is spec §3 as numbered steps, each command in the gate form, one per Bash call, with literal paths, plus the close (spec §5): the block and §11 row moved together, `Source:` written from SOURCES, no version bump, no §14 row, no re-approval.

- [ ] **Step 4: Rerun the six scenarios with the skill** loaded (`--plugin-dir`), and record pass or fail per scenario in `building-from-prds.md`. A scenario that still fails gets a new Red Flag or rule and a pin, then runs again (REFACTOR).

- [ ] **Step 5: Run the suite** — Expected: all pass.

- [ ] **Step 6: Commit** — `feat(prd-toolkit): building-from-prds, prd-builder and /prd-build`.

---

### Task 11: changing-prds hand-off, the managed block and `prd-format.md`

**Files:**
- Modify: `prd-toolkit/skills/changing-prds/SKILL.md` (step 5), `prd-toolkit/templates/claude-block.md`, `prd-toolkit/references/prd-format.md` (`Source:` for built blocks; the status moves)
- Test: `prd-toolkit/tests/test_context_routing.py` (update `BULLET` and the step 5 pin)

- [ ] **Step 1: Update the pins first:**

```python
BULLET = ("To learn what an area does, run `/prd-context <area>` and work from its pack; read whole PRD\n"
          "  files only to edit them. Build an approved change with `/prd-build <area> <IDs>`. Code\n"
          "  implements the PRD; it never defines behaviour the PRD lacks.")

def test_block_names_hook_install():
    assert "Run `.prd-toolkit/prd_hooks.py install` once per clone" in (ROOT / "templates/claude-block.md").read_text()

def test_changing_step_5_hands_off_to_prd_build():
    step5 = section(CHANGING, "5. **Approval, then commit.**", "## Red Flags")
    assert "/prd-build <area> <changed IDs>" in step5 and "Code written outside `/prd-build`" in step5

def test_format_source_and_statuses():
    t = (ROOT / "references/prd-format.md").read_text()
    assert "where the code that implements the block is" in t and "A status move is progress, not behaviour" in t
```

`test_block_stays_small` stays and must still pass.

- [ ] **Step 2: Run to see them fail** — Expected: FAIL.

- [ ] **Step 3: Write the text** per spec §9; wrap the bullet at the template's width.

- [ ] **Step 4: Run the suite** — Expected: all pass, `tests/test_block.py` included.

- [ ] **Step 5: Commit** — `feat(prd-toolkit): changes hand off to /prd-build`.

---

### Task 12: Evals

**Files:**
- Create: `prd-toolkit/evals/building-trigger/`, `building-not-for-plain-code/`, `builder-stays-out-of-prd/`, `build-gap-stops/`, `build-close-no-bump/` (each `case.yaml`, `prompt.md`, `graders/*.md`, and `scaffold.sh` where it needs a repo)
- Create: `prd-toolkit/evals/scaffolds/build_repo.sh` (Task 9 step 1's start repo, scripted)
- Modify: `prd-toolkit/evals/BASELINE.md`
- Test: `prd-toolkit/tests/test_eval_graders.py` (its existing checks must cover the new evals)

- [ ] **Step 1: Write the evals.**
  - `building-trigger`: prompt "FR-004 is approved; build it." Graders: `skill-fired` (building-from-prds), a `tool_used` Agent call whose input names `prd-builder`.
  - `building-not-for-plain-code`: a repo with no `docs/prd/`, prompt "Add a `--version` flag to the CLI." Grader: building-from-prds not invoked.
  - `builder-stays-out-of-prd`: graders on the builder's Write/Edit calls: none under `docs/prd/`, none on `tests/test_notes.py` (the tester's file).
  - `build-gap-stops`: FR-004's AC says "the count of notes" and its integration test case leaves archived notes unstated, with an archived note in the fixture. Graders: changing-prds invoked after the build starts, no Edit of a block's `Status:` line.
  - `build-close-no-bump`: graders: an Edit writes `Status: verified` for FR-004; no Edit changes `version:` in `prd.md`; no Edit adds a §14 row.
- [ ] **Step 2: Run the grader tests** — `uv run --directory prd-toolkit pytest -q tests/test_eval_graders.py` — Expected: pass.
- [ ] **Step 3: Run every eval** with the command in `evals/BASELINE.md` (`--allow-tools Write Edit Bash Agent` plus the two pypi WebFetch grants). Record pass rates. A failing grader is fixed in the skill text with a pin, never by loosening the grader.
- [ ] **Step 4: Commit** — `test(prd-toolkit): building evals`.

---

### Task 13: Release 0.4.0 text and versions

**Files:**
- Modify: `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json:25-26`, `web/src/data/plugins.js:44-58` (version, description, `/prd-build` and `/prd-status` commands, the `building-from-prds` skill, the 0.4 spec link), `prd-toolkit/README.md` (version, a 0.4.0 bullet, commands, the folder tree's `.prd-toolkit/`), the root `README.md` if it lists the toolkit's commands
- Test: the `web` tests that pin plugin text

- [ ] **Step 1: Update the pins first**, so the web tests fail on the old text.
- [ ] **Step 2: Write the text.** Versions 0.4.0. The description adds `/prd-build` and `/prd-status`. The README 0.4.0 bullet: `/prd-build` with `prd-builder` and the tester's `write` mode; `/prd-status`; hooks and generated CI from a vendored `.prd-toolkit/`; the Levels `Gate` column. Upgrade note: "Upgrading a 0.3 PRD: lint fails `test-level` until `testing.md`'s Levels table has a Gate column (build or deploy), a patch bump."
- [ ] **Step 3: Verify** — `uv run --directory prd-toolkit pytest -q`, `cd web && npm test`, `claude plugin validate ./prd-toolkit` — Expected: all pass; validate prints no errors.
- [ ] **Step 4: Commit** — `chore(prd-toolkit): release 0.4.0`.

---

### Task 14: Proof — hello-world, slice 1

The controller runs steps 1, 2 and 5. Steps 3 and 4 are real sessions: Ivan drives them, or authorizes headless runs whose prompts carry his approvals, as 0.3's step 5 did. All of it happens in a scratch repo under the session scratchpad, never committed here, never pushed.

**Files:**
- Create: `prd-toolkit/evals/scaffolds/hello_repo.py`, `docs/superpowers/plans/2026-10-31-prd-toolkit-0.4-acceptance.md`
- Outside this repo: `<scratchpad>/proof-0.4/hello`

- [ ] **Step 1: Scaffold.** `hello_repo.py <dst>` runs `git init`, writes `TICKET.md` with spec §11's text and a `.gitignore` (`.venv/`, `__pycache__/`, `.pytest_cache/`), and commits. A pytest test in this repo runs it into `tmp_path` and checks the one commit and the two files. Commit: `test(prd-toolkit): hello-world scaffold`.
- [ ] **Step 2: Load the branch.** Disable any installed prd-toolkit, so it does not shadow the branch (0.2 Later item 3), and run from `--plugin-dir /Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.4/prd-toolkit`.
- [ ] **Step 3: Author and build FR-001.**
  - `/prd-new` from `TICKET.md`, through every gate, dry run included: Approved, 1.0.0.
  - `prd_hooks.py install docs/prd/hello`, then `prd_hooks.py ci --github docs/prd/hello`; commit both with `Refs: none (no behaviour change)`.
  - Commit a file under `src/` with no `Refs:`: it must be refused. Record the output.
  - `/prd-build <area> FR-001`.
- [ ] **Step 4: Change and build FR-002.** `/prd-change` adds `--shout` (FR-002, a minor bump), then `/prd-build <area> FR-002`. Its `implement` pack must show FR-001's `Source:` excerpt.
- [ ] **Step 5: Check and record.**
  - The `prd-lint-exit=` and `prd-trace-exit=` values are `0`; FR-001 and FR-002 are `verified`; `/prd-status` shows both with every T-id `cited`.
  - Each generated CI job's script lines exit 0 when run locally.
  - From the transcripts: every read of a PRD file that was neither a pack, a pack's closing-line pointer, nor a file edited (each one is a **pack gap**); every reconcile classification and whether it carried its quote; the round counts.
  - Write the acceptance note: outputs, numbers, gaps and dispositions. Grep it for the organization's name before committing. Commit: `docs(prd-toolkit): 0.4 acceptance`.

---

### Task 15: Pull request

- [ ] **Step 1:** Use superpowers:finishing-a-development-branch. Rerun the suite, `npm test` and `claude plugin validate`. Check the whole branch history, not only the tip, for organization names.
- [ ] **Step 2:** Ask Ivan before pushing. Then push `feat/prd-toolkit-0.4` and open a PR to `main` on GitHub `ihistand/claude-plugins`. The body lists every "Ruling:" line from the SDD ledger and this plan (the `--ci` ruling included), the milestone split and the upgrade note, and ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Name no reviewers.
