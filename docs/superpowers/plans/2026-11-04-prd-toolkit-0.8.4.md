# prd-toolkit 0.8.4: README files and an Overview tab for each PRD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `prd_block.py` writes and checks a managed block in `docs/prd/README.md` and `docs/prd/<slug>/README.md` beside the `CLAUDE.md` block, the PRD's root README is skipped by everything that reads the PRD as its source, CI fails when any of the three blocks is stale, and the published page opens on an Overview tab built from the same facts, with §2's optional `Principles:` and `Getting started:` parts.

**Architecture:** `prdlint/overview.py` gathers the facts (§2's summary and parts, the areas and their states, open errors, links, existing files) once. `prd_block.py` fills two README templates from them and walks one list of targets, each `(path, block, position)`, for writing and `--check`; `publish.py` fills the Overview tab from them. Lint's skip goes through the toolkit's own PRD first (`lint-cli`), in the same `/prd-change` that gives that PRD its principles and getting-started steps; the digest and bump skip goes into 0.8.1's `prdlint/change.py`. `prd_hooks.py` vendors the templates and the home page, refreshes the blocks on `install`, and reports stale ones in `check --ci`.

**Tech Stack:** Python 3.11+ (`uv run --script`), pyyaml, pytest; git; Claude Code CLI (`claude plugin eval`).

**Spec:** `docs/superpowers/specs/2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md` (governed by `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md`)

## Global Constraints

- **Starts only after 0.8.3 is on `main`.** Work in `/Users/ihistand/projects/claude-plugins/.worktrees/prd-toolkit-0.8.4`, branch `feat/prd-toolkit-0.8.4`, cut from that `main`. The spec, the umbrella and this plan reach `main` with 0.8.3 (renumbered there from 0.8.3 to 0.8.4 on 2026-11-06). Never push, open a PR, or touch another repo without Ivan's request in his own words.
- Commit as Ivan Histand <ihistand@rotoplas.com>; every message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Stage by path; never `git add -A`. One implementer at a time in this worktree.
- **The toolkit's own PRD binds this branch.** `prdlint/model.py` is a `lint-cli` Boundary file: only Task 2 touches it, with the live ID Task 1 adds. Every other commit carries `Refs: none (no behaviour change)`. Never `--no-verify`. **The builder runs without isolation**: the Agent tool's `isolation: worktree` cuts from the main checkout's HEAD, not from this branch.
- The repo is public and the toolkit names no client: no app, editor or organization name in code, docs, tests or evals. Example slugs `greet`, `orders`, `notes`.
- Test-first: every behaviour and skill-text pin fails before its change. Run it once to see it fail.
- No new third-party dependency. Every file write goes through a temporary file in the same folder and `os.replace`, writing through a symlink and keeping the file's mode, as `prd_block.apply_block` does today.
- **CI parity before every commit that touches code:** `scripts/ci-local.sh`, with `HOME` set to an empty directory under the session scratchpad.
- **Vendoring:** the repo's own `.prd-toolkit/` is refreshed only by the vendor-only snippet, never by `prd_hooks.py install` (it rewrites the clone's shared `.git/hooks`):
  `uv run --project prd-toolkit python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('prd-toolkit/scripts').resolve())); from prdlint import hooks; from prdlint.model import load; r = Path('.').resolve(); s = hooks._resolve_sources(r, load(r / 'docs/prd/prd-toolkit')); hooks._vendor(r, s); hooks._ignore_record(r)"`
- **Exact names and copy** (from the spec):
  - templates `prd-toolkit/templates/readme-prd.md` and `readme-prds.md`, holding the blocks of spec sections 3 and 4 with their `{{slot}}` names, vendored to `.prd-toolkit/templates/`;
  - the vendored home page file `.prd-toolkit/HOMEPAGE`, one line; `plugin.json`'s `"homepage": "https://github.com/ihistand/claude-plugins/tree/main/prd-toolkit"`;
  - the lines `_No summary yet: prd.md §2 is empty._`, `Install the prd-toolkit plugin for Claude Code.` (no home page), and the parent row `| <slug> | - | could not be read | - |`;
  - `--check` prints `stale: <path relative to the repo root>` per stale block; `prd_hooks.py check --ci` prints `stale: <path>; run prd_block.py <prd dir>`;
  - the `files` texts: spec section 3's table, verbatim, in its order.
- **Ruling (plan, spec sections 3 and 9): §2's first paragraph** is the first run of non-blank lines in §2's body after removing HTML comments (`<!-- … -->`, single or multi-line) and blank lines before it, ending at the next blank line or heading, and never a paragraph that starts with a labelled part (`Goals:`, `Personas:`, `Out of scope:`, `Principles:`, `Getting started:`, or the language table's labels). In the README its lines are prefixed `> ` as they stand.
- **Ruling (plan, spec section 8): the Overview's language keys** are `overview`, `what_it_is`, `principles`, `areas`, `open_errors`, `linked_prds`, `getting_started`, `snapshot_line`, plus `part_principles` and `part_getting_started` for §2's labels (`en`: `Principles`, `Getting started`; `es`: `Principios`, `Primeros pasos`). `en` values are the spec's English text; `es` values are written in Task 4 and shown to Ivan with the Task 10 proof.
- **Ruling (plan, spec section 6): where a block goes.** `CLAUDE.md` keeps today's position (appended at the end of an existing file). A README without markers gets the block at the top: the block, a blank line, then the existing text byte for byte.
- **Ruling (plan, spec section 6): what the skills stage.** The PRD's own README is inside the PRD folder, which every skill already commits, so only `docs/prd/README.md` gains a staging line, and only where it exists.

## Review Focus

1. An existing README with CRLF line endings: the block is inserted and refreshed, and the owner's text keeps its CRLF bytes unchanged. (Task 5)
2. A §2 that opens with the template's HTML comments, or whose first paragraph is a list: the summary is the first real paragraph, never a comment, and a list keeps its markers inside the quote. (Task 4)
3. A PRD folder name with a space or non-ASCII (`docs/prd/my notes/`): the parent table's link is percent-encoded (`[my notes](my%20notes/)`) and works on GitHub. (Task 5)
4. `docs/prd/<slug>/README.md` is a symlink: the block is written through it and the link stays a link. (Task 5)
5. A §2 summary that contains the literal text `<!-- prd-toolkit:end -->`: `prd_block.py` exits 2 with `prd_block: prd.md §2 holds a prd-toolkit marker`, writing nothing, rather than writing a block that can no longer be found. (Task 5)

---

### Task 0 (controller-run): Preflight

**Files:** none.

- [ ] **Step 1:** Check `main` holds 0.8.3 (`prd-toolkit/.claude-plugin/plugin.json` says `0.8.3`) and 0.8.1's `prdlint/change.py` with `digest` and `_skipped`. Create the worktree and branch from `main`.
- [ ] **Step 2:** Run `uv run --script prd-toolkit/scripts/prd_change.py ids next docs/prd/prd-toolkit FR` and `… T-<that FR's number>`, each its own call; write the next FR, AC and T-ids to the ledger for Task 1.
- [ ] **Step 3:** If 0.8.3 is not on `main`, stop and tell Ivan.

### Task 1 (controller-run, stops for Ivan): the toolkit PRD's `/prd-change`

**Files:** `docs/prd/prd-toolkit/features/lint-cli.md`, `test-cases/lint-cli.yaml`, `prd.md` (§2, §11, §14, version), through `/prd-change`.

- [ ] **Step 1:** Run `/prd-change` with both parts of spec section 10, as one change:
  - on `lint-cli`, one new requirement, the next FR from Task 0, "lint reports no finding in the PRD folder's root `README.md`; any other `README.md` in the folder is linted as before", with one AC and one test case: a root README that holds a vague word, `FR-999` and `[NEEDS CLARIFICATION: x]` and a `contracts/dependencies/README.md` that holds a vague word: lint reports only the second;
  - in `prd.md` §2, after `Goals:`, a `Principles:` part with the seven principles of spec section 10 and a `Getting started:` part with its four steps, drafted from the design binder's Overview and shown to Ivan word for word with the diff.
  
  Minor bump (behaviour added, none changed).
- [ ] **Step 2:** The dry run through `prd-tester`, as `dispatching.md` says. Ivan approves in his own words, §2's wording included; the approval commit as step 5 says.

### Task 2 (controller-run): `/prd-build lint-cli <FR>`

**Files:** `prd-toolkit/scripts/prdlint/model.py`, `prd-toolkit/scripts/prdlint/rules/structure.py` (builder); the T-id's test under `prd-toolkit/tests/prd/` (tester).

- [ ] **Step 1:** `/prd-build lint-cli <FR>` per `running-a-build.md`, the builder **without isolation** (Global Constraints). The skip applies to `README.md` at the PRD root only, in `model.load`'s `.md` walk and in `structure.py`'s raw-file scan.
- [ ] **Step 2:** The close: `verified` and `Source:` lines; CI parity.

### Task 3: the digest and bump skip

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/change.py`
- Create: `prd-toolkit/tests/test_readme_skips.py`

**Interfaces:**
- Produces: `change.README = "README.md"`; `change._skipped(rel)` returns True for `rel == "README.md"`, at the root only.

- [ ] **Step 1: Write the failing tests** on a fixture PRD:
  - `change.digest` is equal before and after writing, then editing, a root `README.md`;
  - `prd_change.py bump` against a base without the README reports no item for it;
  - a `features/README.md` still changes the digest;
  - pins that `prd_publish.py`, `prd_context.py --for implement` and `prd_trace.py` give the same output with and without a root README holding `FR-999`.
- [ ] **Step 2: Run them to see them fail** (the digest and bump ones; the three pins may already pass, and stay as pins).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): the digest and bump skip the PRD's root README`.

### Task 4: one set of facts, and §2's two parts

**Files:**
- Create: `prd-toolkit/scripts/prdlint/overview.py`, `prd-toolkit/tests/test_overview.py`
- Modify: `prd-toolkit/references/prd-format.md` (§2's parts), `prd-toolkit/templates/prd/prd.md` (one HTML comment in §2), `prd-toolkit/references/languages/en.yaml`, `es.yaml` (the keys of the Global Constraints ruling), `prd-toolkit/tests/conftest.py` (fixtures `greet`, `orders`, `notes` under a `docs/prd/` parent; `greet` with both §2 parts, `notes` with neither and §2 opening on the template comment, a Spanish `orders` with `Principios:`)

**Interfaces:**
- Produces, in `prdlint/overview.py`:
  - `summary_paragraph(prd) -> str | None` (the plan's ruling) and `first_sentence(text: str) -> str` (up to the first `. `, `? ` or `! `, or the end);
  - `section2_part(prd, key: str) -> str | None` for `key` `"principles"` or `"getting_started"` (spec section 7);
  - `@dataclass Area(name, file, adoption: str, counts: dict[str, int])` and `@dataclass Facts(slug, version, status, owner, updated, summary, first_sentence, principles, getting_started, areas: list[Area], open_errors: int, upstreams: list[str], consumers: list[str], files: list[str])`;
  - `facts(prd) -> Facts`; a missing frontmatter key is `"unknown"`.

- [ ] **Step 1: Write the failing tests** in `test_overview.py`:
  - each `Facts` field on `greet`, `orders` and `notes`;
  - §2's parts: each label found at a line start and ended by the next labelled line or the end of §2; text on the label's own line kept; the `es` labels on `orders`; a §2 that opens with `Goals:` has no summary;
  - Review Focus 2: a template comment before the summary is skipped, and a list paragraph keeps its markers;
  - `counts` in the order `live`, `verified`, `built`, `approved`, `as-built`, with `removed` absent;
  - the template's §2 comment names both parts and lints clean (`prd_lint.py` on a fresh template copy: no new finding).
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement; write the format text, the template comment and the language keys.**
- [ ] **Step 4: Run them, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): one set of PRD facts; §2's Principles and Getting started parts`.

### Task 5: `prd_block.py` writes and checks the two READMEs

**Files:**
- Create: `prd-toolkit/templates/readme-prd.md`, `prd-toolkit/templates/readme-prds.md`, `prd-toolkit/tests/test_block_readmes.py`
- Modify: `prd-toolkit/scripts/prd_block.py`

**Interfaces:**
- Consumes: Task 4's `overview.facts`, `first_sentence`, and its fixtures.
- Produces, in `prd_block.py`:
  - `homepage() -> str | None`: `plugin.json`'s `homepage` on a plugin run, `.prd-toolkit/HOMEPAGE`'s line on a vendored run, `None` when absent;
  - `render_readme(prd, parent_written: bool) -> str` and `render_parent(parent: Path, home: str | None) -> tuple[str, list[str]]` (the block and the stderr notes);
  - `Target = tuple[Path, str, str]`, `(path, block, position)` with position `"end"` or `"top"`; `targets(prd, root, claude_md: Path) -> list[Target]`: `CLAUDE.md`, the PRD's README, and the parent README only when `prd.root.parent.name == "prd"`;
  - `_merged(path, block, position="end")`; `stale(targets) -> list[Path]`; `write(targets) -> list[Path]` (the files changed);
  - CLI unchanged in shape: `prd_block.py <prd dir> [--claude-md P] [--check]`; `--check` prints `stale: <path>` for each and exits 1, else 0; a write prints nothing and exits 0; the notes from `render_parent` go to stderr in both.

- [ ] **Step 1: Write the failing tests** in `test_block_readmes.py`:
  - every slot of spec section 3 on `greet`: frontmatter values (and `unknown` for a missing key), the summary quoted line by line, the areas from `adoption.md` and, on `notes` (no `adoption.md`), with `-`; only existing files listed, in the spec's order and text; `links.md` on `orders` with a relative path rendered as a link and a `<git URL>#<folder>` as code; `parent_link` present under `docs/prd/` and absent in a PRD at `docs/requirements/x/`;
  - an empty §2 gives `_No summary yet: prd.md §2 is empty._`;
  - the parent on `greet`, `orders`, `notes`: three rows sorted, Covers each first sentence; a fourth folder with a broken `prd.md` gives the could-not-be-read row, a stderr note and exit 0; a folder with no `prd.md` absent; the home page from `plugin.json`, from a `HOMEPAGE` file, and the fallback line with neither;
  - merging: a README without markers gets the block on top and its old text byte for byte below; a refresh rewrites only between the markers; two start markers exit 2 and write nothing; fenced markers are not markers; `CLAUDE.md` still gets its block at the end;
  - `--check`: one stale README prints one `stale:` line and exits 1; all current exits 0; a run then `--check` is 0 (idempotent);
  - Review Focus 1, 3, 4 and 5, each as its line says.
- [ ] **Step 2:** Run them and the existing `test_block.py` to see the new ones fail and the old ones pass.
- [ ] **Step 3: Write the two templates** from spec sections 3 and 4, verbatim, and implement.
- [ ] **Step 4: Run `test_block.py` and `test_block_readmes.py`, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): prd_block.py writes the PRD folders' READMEs`.

### Task 6: the published page's Overview tab

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/publish.py`, `prd-toolkit/templates/publish/page.html`, `prd-toolkit/tests/test_publish.py`, `prd-toolkit/tests/fixtures/publish/orders.html` (regenerated once)
- Create: `prd-toolkit/tests/test_publish_overview.py`

**Interfaces:**
- Consumes: Task 4's `overview.facts` and the language keys.
- Produces: `publish.overview_panel(prd, facts) -> str` (escaped HTML, the parts of spec section 8 in order, each left out when empty); the page's first radio `#tab-overview`, `checked`, with its label and panel beside the existing two; a mermaid fence anywhere on the page rendered as `<pre class="mermaid">` holding the escaped source.

- [ ] **Step 1: Write the failing tests** in `test_publish_overview.py`:
  - `#tab-overview` is first and `checked`; `#tab-business` is no longer `checked`; the Business and Technical panels are otherwise byte-identical to before (compare against the old golden with the radio lines masked);
  - each part from `greet` (all present) and absent from `notes`; the status counts line; `2 open errors; the Technical tab lists them` and `No open errors.`; the snapshot line with the version;
  - the `es` labels on `orders`;
  - a mermaid fence in §4 gives `<pre class="mermaid">` on the Overview and Technical tabs, with `<` and `&` escaped; no `<script`, `<link`, `@import` or `url(` anywhere;
  - `--summaries` with an `overview` key is refused as an unknown area, as today.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement. Regenerate the golden page once** with the fixture's own command, and read its diff: only the new radio, label, panel and the mermaid `<pre>` change.
- [ ] **Step 4: Run them and `test_publish.py`, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): the published page opens on an Overview tab`.

### Task 7: vendoring, `install` and `check --ci`

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py`, `prd-toolkit/scripts/prd_hooks.py`, `prd-toolkit/.claude-plugin/plugin.json` (`homepage`), `prd-toolkit/tests/test_hooks_install.py`
- Create: `prd-toolkit/tests/test_hooks_blocks.py`

**Interfaces:**
- Consumes: Task 5's `targets`, `stale`, `write`.
- Produces: `_vendor` copies `readme-prd.md` and `readme-prds.md` beside `claude-block.md` and writes `HOMEPAGE` (only when `plugin.json` has a `homepage`); `install` calls `write(targets(...))` after vendoring and adds `refreshed <path>` to its output lines for each file changed; `stale_ci` adds `stale: <path>; run prd_block.py <prd dir>` per stale block.

- [ ] **Step 1: Write the failing tests:**
  - a vendored copy holds both templates and `HOMEPAGE` equal to `plugin.json`'s `homepage`;
  - `install` on a repo with no READMEs writes both and the `CLAUDE.md` block, and says so;
  - `check --ci` with a stale README exits 1 with that line; with a hand-edited `CLAUDE.md` block, the same for `CLAUDE.md`; after `prd_block.py`, exit 0;
  - the vendored `prd_block.py` and the plugin's write the same bytes (the home page text included).
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them, then CI parity.**
- [ ] **Step 5: Commit** `feat(prd-toolkit): install refreshes the blocks; check --ci reports stale ones`.

### Task 8: the skills and the tester

Required skill: `superpowers:writing-skills`.

**Files:**
- Modify: `prd-toolkit/skills/authoring-prds/SKILL.md` (phase 2 and phase 7), `prd-toolkit/skills/adopting-prds/SKILL.md` (the bootstrap and the step 5 commit), `prd-toolkit/skills/changing-prds/SKILL.md` (step 5), `prd-toolkit/skills/coordinating-prds/running-a-change-set.md` (the close), `prd-toolkit/skills/testing-from-prds/SKILL.md`, `prd-toolkit/agents/prd-tester.md`, `prd-toolkit/skills/publishing-prds/SKILL.md`, `prd-toolkit/tests/test_publishing_skill.py`
- Create: `prd-toolkit/tests/test_readme_skills.py`; eval `prd-toolkit/evals/tester-ignores-readme/` (`case.yaml`, `prompt.md`, `scaffold.sh`, `graders/`, as `adopting-confirm-headless-fallback/`)

- [ ] **Step 1: Write the failing pins:** each of the four skills, where it commits after `prd_block.py`, names `docs/prd/README.md` among the files it stages, "when it exists"; `testing-from-prds` and `prd-tester.md` hold the rule "The PRD folder's root `README.md` is a guide generated from the PRD, never a source for a test or a question."; authoring phase 2 and the adoption bootstrap offer `Principles:` and `Getting started:` and say neither is required; `publishing-prds` names three tabs, Overview first, and says the Overview takes no summary; no `${CLAUDE_PLUGIN_ROOT}` inside a Bash command.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: The eval's RED baseline:** scaffold a PRD whose root README states a behaviour (`greet` answers in French) that no feature file states; dispatch the tester in write mode for the area's T-ids on the unchanged skills; record in `evals/BASELINE.md` whether a test or question drew on the README.
- [ ] **Step 4: Edit the skills and the agent.**
- [ ] **Step 5: Run the pins, then the eval at 3 runs** (`claude plugin eval`); record the with/without scores. Below 3/3 is fixed in the skill text, never the grader.
- [ ] **Step 6: CI parity. Commit** `feat(prd-toolkit): the skills stage the READMEs, offer §2's parts and publish three tabs; the tester never reads a README`.

### Task 9: release text, 0.8.4, and this repository's READMEs

**Files:**
- Modify: `prd-toolkit/README.md` (the READMEs, the Overview tab, §2's two parts, the upgrade note of spec section 14 with the `CLAUDE.md` watch item, the known limit, the 0.8.4 changelog entry), `prd-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `web/src/data/plugins.js` (version `0.8.4`), the repo's `.prd-toolkit/` (vendor-only snippet)
- Create: `prd-toolkit/tests/test_release_0_8_3.py` (as `test_release_0_7_1.py`), `docs/prd/README.md` and `docs/prd/prd-toolkit/README.md` (by `prd_block.py`, never by hand)

- [ ] **Step 1: Write the failing pins:** the three version files say `0.8.4`; the README names both READMEs, the markers, `check --ci`'s new failure, the upgrade watch item, the Overview tab and §2's two optional parts; the changelog entry names the `lint-cli` FR of Task 1.
- [ ] **Step 2: Run them to see them fail.**
- [ ] **Step 3: Write the text; bump the versions; run the vendor-only snippet;** then `uv run --script .prd-toolkit/prd_block.py docs/prd/prd-toolkit`, its own call, which writes the two READMEs and refreshes `CLAUDE.md`.
- [ ] **Step 4: Run the pins, CI parity,** `uv run --script .prd-toolkit/prd_block.py --check docs/prd/prd-toolkit; echo "prd-block-exit=$?"` (0), lint and trace (each `; echo "prd-…-exit=$?"`, both 0).
- [ ] **Step 5: Commit** `feat(prd-toolkit): 0.8.4 release text, version and the PRD READMEs`, staging `docs/prd/README.md`, `docs/prd/prd-toolkit/README.md` and `CLAUDE.md` by path.

### Task 10 (controller-run, with Ivan): Proof

**Files:** none committed but the proof record in the changelog entry.

- [ ] **Step 1:** Make the PRD's README stale on purpose in the working tree (edit a line inside the block); run `scripts/ci-local.sh`: the `check --ci` job fails with `stale: docs/prd/prd-toolkit/README.md; run prd_block.py docs/prd/prd-toolkit`. Restore with `prd_block.py`; the job passes. Nothing is committed.
- [ ] **Step 2 (Ivan):** reads `docs/prd/README.md` and `docs/prd/prd-toolkit/README.md`. On his request in his own words, push and open the PR; CI passes; he reads both on GitHub and confirms they explain the folders to someone new.
- [ ] **Step 3:** `/prd-publish` on the toolkit's own PRD: the page opens on the Overview tab with its principles, its architecture, `lint-cli` as the adopted area and its getting-started steps. Drive Chrome over the page published into the design artifact (`prd-toolkit-prd.html`, replacing the 2.1.0 snapshot) and check the mermaid diagram draws; show Ivan the page and the `es` label values; he confirms it.
- [ ] **Step 4:** Record what was proven (the commits, the CI run, the published version) in the changelog entry. Commit `docs(prd-toolkit): 0.8.4 proof record`.
