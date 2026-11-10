# prd-toolkit Move to PRDAnvil Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move prd-toolkit, with its history, out of `ihistand/claude-plugins` into the new public repository `PRDAnvil/prd-toolkit`. It gets its own marketplace and an MIT license, and ships as its own release, 0.8.6.

**Architecture:** `git filter-repo` keeps only prd-toolkit's paths, with the same names, so no path in the PRD, the tests or CI changes. The PRD's commit references are rewritten through filter-repo's commit map. The new repository adds what the split leaves behind: the marketplace file, a root README, the LICENSE, CLAUDE.md and `.gitignore`. It then releases 0.8.6, which drops every `ihistand` name from the shipped plugin. `claude-plugins` keeps a pointer and stops shipping the toolkit.

**Tech Stack:** git, git-filter-repo a40bce548d2c, uv, pytest (the toolkit's own harness), gh, Claude Code's plugin CLI.

**Spec:** the Decisions section below (the owner's decisions of 2026-11-10, plus the ones this plan proposes). No separate design document.

## Decisions

The owner's decisions (2026-11-10):

1. The repository is `PRDAnvil/prd-toolkit`, public.
2. The toolkit is MIT-licensed. `PRDAnvil/prd_studio` stays private.
3. New commits use `Ivan Histand <ivan@badgeretl.com>`. History keeps `ihistand@rotoplas.com`.
4. The move ships as its own release.

Proposed by this plan. The owner confirms them when approving the plan:

5. **Marketplace name `prdanvil`.** Installs become `prd-toolkit@prdanvil`, and the cache path becomes `~/.claude/plugins/cache/prdanvil/prd-toolkit/<version>/`.
6. **The release is 0.8.6.** The current 0.8.6 backlog becomes 0.8.7, and conversion becomes 0.8.8. The toolkit must stay below 0.9: a private wrapper plugin's packs declare `toolkit: ">=0.8.0,<0.9"`.
7. **The layout stays.** The plugin stays in `prd-toolkit/`, and the marketplace's `source` is `./prd-toolkit`.
8. **The local clone lives at `~/projects-ivan/prdanvil/prd-toolkit`,** beside `prd_studio`.
9. **The LICENSE reads `Copyright (c) 2026 Ivan Histand`.** It sits at the repository root and in `prd-toolkit/`, and vendoring copies it into `.prd-toolkit/LICENSE`.
10. **PRD 6.2.0 becomes 6.2.1 (patch).** The PRD's hosting, repository and runbook lines change, and no AC or test case does.
11. **`claude-plugins` drops prd-toolkit from its marketplace in its own PR.** It keeps a `prd-toolkit/README.md` stub that points to the new repository, so the HOMEPAGE links in other repos' vendored copies still resolve.
12. **Issue #24 is recreated in the new repository,** and the old one is closed with a link. GitHub can't transfer an issue between owners.

## Dry run (2026-11-10, main at 3e6d7c2)

A single-branch clone of `main`, filtered with `--paths-from-file` on the 45 paths of Task 1, gave the following:

- **Commits:** 557 (31 of them merges), from 2026-10-29 (273e422, "docs: prd-toolkit design spec") to the merge of PR #29. The repository is 2.9 MB.
- **Authors:** 554 commits by `ihistand@rotoplas.com` and 3 by `ivan@badgeretl.com`. The latter are GitHub web merges of PRs #17, #21 and #23.
- **Files:** 946, the same list as those paths at 3e6d7c2. The tree hashes are equal for `prd-toolkit/`, `docs/prd/`, `.prd-toolkit/`, the workflow, `scripts/ci-local.sh` and a spec.
- **Checks:** lint exits 0 and trace exits 0.
- **SHA impact:** 17 commit references in `docs/prd/` stop resolving: 12 distinct `Source: …@<sha>`, plus `fixed in` and `approved` mentions.
  - The implement pack for lint-cli marks 19 sources `STALE: unknown commit`.
  - Every reference maps through `.git/filter-repo/commit-map` except `709d385`, which only touched `.gitignore` and was pruned. It maps to the new commit of its parent, `88a7a47`.
  - After the rewrite, lint-cli shows 1 STALE and lint-structure 0, the same as the original repository. The one STALE is FR-006's `model.py:889`, whose text appears 3 times, already true before the move.
- **Tests on the bare tree:** 22 failed and 10 errors (3596 passed); Task 4 lists them. Every one reads a file the split leaves behind: `.claude-plugin/marketplace.json` (32 reads), the root `README.md` (16), `web/src/data/plugins.js` (2) or CLAUDE.md (1). The one exception is a pre-existing flake in `test_builtin_packs.py`, which isn't caused by the split.
- **The other plugins and the docs site** (`sqlanvil-toolkit/`, `stl-generator-toolkit/`, `web/`, `scripts/sync-skills.sh`, the web spec and plan) are absent, so they don't move.

## Global Constraints

- No path under `prd-toolkit/`, `docs/prd/`, `.prd-toolkit/`, `.github/workflows/` or `scripts/` is renamed or moved.
- Each outward step waits for the owner's word in the chat: creating the repository, every push, every merge, closing an issue, and every commit to a repository other than the new one.
- Commits in the new repository are by `Ivan Histand <ivan@badgeretl.com>`, set with `git config user.email` in that clone only. Each ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Commits in `claude-plugins` stay `ihistand@rotoplas.com`.
- Every commit that touches the PRD's Boundary carries a `Refs:` trailer. The commit-msg hook and CI's trace require it: `Refs: none (no behaviour change)` when no requirement changes.
- Filter only `main`. Never push the 0.2 `-history` branch.
- The toolkit version stays below 0.9.
- Never `git stash` bare, and never `--no-verify`.
- Don't run `prd_hooks.py install` on the toolkit's own repository. Refresh its vendored copy with `prd_hooks.py vendor docs/prd/prd-toolkit`, run from the repository's `prd-toolkit/scripts/`.
- Scan new text for client names with `/usr/bin/grep -i -f <the owner's private name list>` before each push. Two specs in the moved history name a client (`2026-10-29-prd-toolkit-design.md`, `2026-10-29-prd-toolkit-0.1.md`). They are public already, and this plan leaves them as written.

## Review Focus

1. **A rewritten commit reference that points nowhere.** Every hexadecimal token in `docs/prd/` that named a commit of the old repository must name a commit of the new one. Task 2's verification checks each token.
2. **An `ihistand` install name left in the shipped plugin.** A user copies `prd-toolkit@ihistand` from the README and installs the old copy. Task 6's `test_no_old_marketplace_names` fails on it.
3. **The old install left beside the new one.** Both copies' skills load, with different versions. The upgrade note names the uninstall, and Task 8 checks `claude plugin list` shows only `prd-toolkit@prdanvil`.
4. **A copy without the license.** The plugin cache copies only `prd-toolkit/`, and a vendored `.prd-toolkit/` only what vendoring writes. Task 5 tests both.
5. **Dead links in other repos' vendored copies.** Their `.prd-toolkit/HOMEPAGE` and `docs/prd/README.md` name `github.com/ihistand/claude-plugins/tree/main/prd-toolkit` until their next toolkit upgrade. Task 9 keeps that path alive as a stub and checks it answers 200.

---

### Task 0: Merge this plan into claude-plugins first

**Files:**
- Create: `docs/superpowers/plans/2026-11-10-prd-toolkit-move-to-prdanvil.md` (in `claude-plugins`, branch `docs/prd-toolkit-move-plan`)

The plan is merged to `claude-plugins` main before the filter, so it moves with the history.

- [ ] **Step 1:** Commit the plan with `Refs: none (no behaviour change)`. Push the branch and open the PR on the owner's word. The owner merges it.
- [ ] **Step 2:** Record the merged SHA of `main` as `PIN`. Every later task filters and compares against `PIN`.

### Task 1: Filter the history into the new clone

**Files:**
- Create: `~/projects-ivan/prdanvil/prd-toolkit/` (the filtered clone)
- Create: `<scratchpad>/paths.txt` (not committed)

**Interfaces:**
- Produces: the clone on `main` at the filtered `PIN`, and `.git/filter-repo/commit-map` (old → new SHA, 40 hex characters each), which Task 2 reads.

- [ ] **Step 1: Write `paths.txt`.** One path per line:
  - `prd-toolkit/`, `docs/prd/`, `.prd-toolkit/`, `.github/workflows/prd-toolkit.yml` and `scripts/ci-local.sh`;
  - every `git ls-files docs/superpowers` path at `PIN` except the two `claude-plugins-web` files.
- [ ] **Step 2: Clone and filter.**
  1. `git clone --no-local --single-branch --branch main <claude-plugins> ~/projects-ivan/prdanvil/prd-toolkit`, then `git reset --hard PIN`.
  2. `git filter-repo --paths-from-file <scratchpad>/paths.txt`.
- [ ] **Step 3: Verify.**
  - For each of the five fixed paths, `git rev-parse HEAD:<path>` in the clone equals `git -C <claude-plugins> rev-parse PIN:<path>`.
  - `git ls-files | wc -l` equals the count of the `PIN` files under `paths.txt`.
  - `git log --format=%ae | sort -u` lists only `ihistand@rotoplas.com` and `ivan@badgeretl.com`.
- [ ] **Step 4: Configure the clone.**
  - `git config user.name "Ivan Histand"` and `git config user.email ivan@badgeretl.com`.
  - `git remote add origin git@github.com:PRDAnvil/prd-toolkit.git`.
  - Copy `commit-msg` and `pre-commit` from `<claude-plugins>/.git/hooks/` into the clone's `.git/hooks/`. They read `$top/.prd-toolkit` and `docs/prd/prd-toolkit` and name no path outside the repository.

### Task 2: Point the PRD's commit references at the new commits

**Files:**
- Modify: `docs/prd/prd-toolkit/features/lint-cli.md`, `features/lint-structure.md`, `nfr.md`, `errors.md` (the dry run's four), and any other file under `docs/prd/` holding a token Step 1 finds
- Create: `<scratchpad>/rewrite_shas.py` (not committed)

**Interfaces:**
- Consumes: Task 1's `commit-map`, and `<claude-plugins>` to resolve old short SHAs.

- [ ] **Step 1: List the tokens.** Take every `\b[0-9a-f]{7,40}\b` in `docs/prd/` that `git -C <claude-plugins> rev-parse --verify -q <t>^{commit}` resolves. That list is the rewrite set. The dry run found 17.
- [ ] **Step 2: Write `rewrite_shas.py <commit-map> <old-repo> <dir>`.**
  - For each token, take its full old SHA's new SHA, cut to the token's length, and replace the token where it isn't next to another hex digit.
  - A pruned commit (mapped to forty zeros) takes its nearest ancestor that maps to a real commit. `709d385` → `88a7a47`'s new SHA.
- [ ] **Step 3: Run it and verify.**
  - Every Step 1 token now resolves in the new clone (`git cat-file -e <t>^{commit}`).
  - `uv run --script .prd-toolkit/prd_context.py docs/prd/prd-toolkit --area lint-cli --for implement` prints exactly 1 `STALE` line, `appears 3 times`. The same command with `--area lint-structure` prints none.
  - `uv run --script .prd-toolkit/prd_lint.py docs/prd/prd-toolkit` exits 0.
- [ ] **Step 4: Commit** `docs(prd): point commit references at PRDAnvil/prd-toolkit's commits`, with `Refs: none (no behaviour change)`. A `Source:` refresh is provenance, so it takes no version bump and no §14 row.

### Task 3: Push the imported history (owner's word)

- [ ] **Step 1:** The owner says go. Run `gh repo create PRDAnvil/prd-toolkit --public --description "A living PRD as the single authority agents build, test and deploy from (Claude Code plugin)" --disable-wiki`, then `gh repo edit PRDAnvil/prd-toolkit --delete-branch-on-merge --enable-issues`.
- [ ] **Step 2:** On the owner's word, `git push -u origin main`, using `dangerouslyDisableSandbox` for the push. `main` now holds the filtered history plus Task 2's commit. CI runs only on pull requests, so this push runs none.
- [ ] **Step 3:** Cut `release/0.8.6` from `main`. Tasks 4 to 7 commit there.

### Task 4: The files the split left behind

**Files:**
- Create: `.claude-plugin/marketplace.json`, `README.md`, `LICENSE`, `prd-toolkit/LICENSE`, `CLAUDE.md`, `.gitignore`
- Modify: the tests listed in Step 1

**Interfaces:**
- Produces: `marketplace.json` with `"name": "prdanvil"` and one plugin, `{"name": "prd-toolkit", "source": "./prd-toolkit", "version": "0.8.5", "description": <the current entry's text>}`. Task 6 sets `0.8.6`. `owner` is `{"name": "PRDAnvil", "email": "ivan@badgeretl.com", "url": "https://github.com/PRDAnvil"}`.

- [ ] **Step 1: Run the suite on the bare tree** (`uv run --directory prd-toolkit pytest -q -n auto tests`). Expect what the dry run measured: 22 failed and 10 errors (3596 passed, 13 xfailed). They come from four missing files and one pre-existing flake:

  | Missing file | Reads | Tests |
  |---|---|---|
  | `.claude-plugin/marketplace.json` | 32 | `test_manifests.py`: `test_versions_agree_and_are_semver`, `test_version_is_a_release`, `test_descriptions_match_and_name_new_commands`; `test_release_0_6` to `test_release_0_8_5`: `test_versions` (11); `test_release_0_8.py::test_description_names_the_new_parts` |
  | root `README.md` | 16 | `test_release_0_5.py` (10 errors: it reads the file when the module loads); `test_final_review_07_docs.py::test_root_readme_lists_the_change_set_command_and_skill`; `test_publishing_skill.py` and `test_error_skill.py`: `test_readme_lists_the_skill_and_the_command` |
  | `web/src/data/plugins.js` | 2 | `test_manifests.py::test_web_description_matches`; `test_final_review.py::test_web_testing_skill_names_write`. These, and the `test_versions` asserts on the same file, fail first on `marketplace.json` |
  | `CLAUDE.md` | 1 | `test_vendored_copy.py::test_the_vendored_copy_matches_the_plugin` (`stale: CLAUDE.md; run prd_block.py`) |

  `test_builtin_packs.py::test_validator_fails_defect` also fails one case: `no-path` or `not-md`, whichever runs first in a session. It's pre-existing and not caused by the split; it fails the same way in a fresh `claude-plugins` worktree.
  - **Cause:** `_run` calls `uv run --script` without `--quiet`, so when the script's environment is new, stderr's first line is uv's `Installed 1 package in 1ms`.
  - **Handling:** record it with `/prd-error` before this plan runs. It doesn't block this plan.

- [ ] **Step 2: Write the files.**
  - **`LICENSE`:** the MIT text, `Copyright (c) 2026 Ivan Histand`. `prd-toolkit/LICENSE` is a byte-identical copy.
  - **`.gitignore`:** the toolkit's lines of the old one, `__pycache__/`, `.pytest_cache/`, `.venv/`, `prd-toolkit/.uv-test-cache/`, `prd-toolkit/evals/results/`, `.prd-judge/` and `.prd-review.json`.
  - **`README.md`:** the old root README's `### prd-toolkit` section (lines 7 to 23 at `PIN`) as the body, under the heading `# prd-toolkit`. Tests require that section's skill and command list: `/prd-change-set`, `**coordinating-prds skill**`, `publishing-prds`, `/prd-publish`, `handling-errors`, `/prd-error`, `/prd-deploy` and `deploying-from-prds`. Then an Install section with the install lines of Task 6, and a License line: "MIT; see LICENSE".
  - **`CLAUDE.md`:** what the old CLAUDE.md says that still applies: the toolkit is authored in place, the Skills Design Philosophy section, and the commit identity of the Global Constraints. Run `uv run --script prd-toolkit/scripts/prd_block.py docs/prd/prd-toolkit` to write the managed block.
- [ ] **Step 3: Change the tests that read a file left behind.**
  - Each assert on `web/src/data/plugins.js` comes out. There are 15 lines in 13 files: `test_final_review.py`, `test_manifests.py` and the eleven `test_release_0_*.py`. `test_manifests.py::test_web_description_matches` and `test_final_review.py::test_web_testing_skill_names_write` go entirely. The docs site stays with `claude-plugins`.
  - Asserts on `marketplace.json`, README, CLAUDE.md and `.gitignore` stay. Step 2's files satisfy them.
- [ ] **Step 4:** Run the suite. Expect every test to pass except the `ihistand` string asserts that Task 6 changes: `test_release_0_5.py::test_no_plugin_root_variable_in_shell_blocks` and the ones `test_final_review.py` builds from `PLUGIN_PATH`.
- [ ] **Step 5: Commit** `chore: the marketplace, README, LICENSE, CLAUDE.md and .gitignore of PRDAnvil/prd-toolkit`, with `Refs: none (no behaviour change)`.

### Task 5: Vendoring copies the LICENSE

**Files:**
- Modify: `prd-toolkit/scripts/prdlint/hooks.py`, where `vendor()` writes HOMEPAGE (around line 171) and `check` compares the vendored files
- Test: `prd-toolkit/tests/test_hooks_vendor.py`

**Interfaces:**
- Produces: `.prd-toolkit/LICENSE`, byte-identical to the plugin's `LICENSE`. `vendor` writes it, and `check` reports it as a stale vendored file when it differs or is missing. The plugin's root is `PLUGIN_ROOT`, as for `plugin.json`.

- [ ] **Step 1: Write the failing tests.**
  - `test_vendor_copies_the_license`: after `vendor`, `(repo / ".prd-toolkit/LICENSE").read_bytes() == (PLUGIN_ROOT / "LICENSE").read_bytes()`.
  - `test_check_reports_a_missing_license`: delete `.prd-toolkit/LICENSE` after `vendor`. `check` then exits 1, and its stdout names `.prd-toolkit/LICENSE`.
- [ ] **Step 2:** Run both. They fail because no LICENSE is written.
- [ ] **Step 3: Implement.** Copy `PLUGIN_ROOT / "LICENSE"` into the vendor directory beside `VERSION`. Add `LICENSE` to the set `vendored_sources` compares. A plugin with no LICENSE writes none and reports none.
- [ ] **Step 4:** Run `test_hooks_vendor.py` and the whole unit level. Both pass.
- [ ] **Step 5:** Run `uv run --script prd-toolkit/scripts/prd_hooks.py vendor docs/prd/prd-toolkit`, which writes `.prd-toolkit/LICENSE`. Commit `feat(prd-toolkit): vendoring copies the LICENSE`, with `Refs: none (no behaviour change)` (the hooks area is not adopted).

### Task 6: The PRD and the plugin name their new home (PRD 6.2.1, toolkit 0.8.6)

**Files:**
- Modify (through `/prd-change`):
  - `docs/prd/prd-toolkit/prd.md`: §1 Framework, Hosting and Repository; §2 Getting started step 1
  - `operations.md`: the Environments `production` row and runbook steps 1 and 2
  - `testing.md`: the Environments `production` row
- Modify:
  - `prd-toolkit/.claude-plugin/plugin.json`
  - `.claude-plugin/marketplace.json`
  - `prd-toolkit/README.md`: the install lines, the five `cache/ihistand` paths, the Version line, the changelog and License
  - `prd-toolkit/tests/test_release_0_5.py:34`
  - `prd-toolkit/tests/test_final_review.py:14`
- Create: `prd-toolkit/tests/test_release_0_8_6.py`

**Interfaces:**
- Consumes: Task 4's `marketplace.json`, and Task 5's vendored LICENSE.
- Produces: the strings later tasks rely on:
  - `/plugin marketplace add PRDAnvil/prd-toolkit`
  - `/plugin install prd-toolkit@prdanvil`
  - `~/.claude/plugins/cache/prdanvil/prd-toolkit/<version>/scripts/`
  - the homepage `https://github.com/PRDAnvil/prd-toolkit/tree/main/prd-toolkit`

- [ ] **Step 1: The PRD change.** Run `/prd-change` with the new values:
  - §1 Framework: "in the `prdanvil` marketplace".
  - §1 Hosting: "installed from the `prdanvil` marketplace".
  - §1 Repository: `https://github.com/PRDAnvil/prd-toolkit`, folder `prd-toolkit/`. Drop the sentence about the repository's other plugins.
  - §2 step 1: the two install lines above.
  - `operations.md`: the production Base URL becomes `https://github.com/PRDAnvil/prd-toolkit`. The runbook's `Run:` lines become `claude plugin marketplace update prdanvil` and `claude plugin update prd-toolkit@prdanvil --scope user`.
  - `testing.md`: production becomes "the `prdanvil` marketplace (GitHub `main` of PRDAnvil/prd-toolkit)".

  `bump` gives needs-judgment items only. Decide them patch: wording, with no AC, test expectation or result changed. Dry-run record: `no dry run (wording only)`. The owner approves in the decision inbox, and `approve` commits the change as PRD 6.2.1.
- [ ] **Step 2: Write `test_release_0_8_6.py`.** It pins:
  - `test_versions`: `plugin.json` and the marketplace entry are `0.8.6`, `.prd-toolkit/VERSION` reads `0.8.6`, and the README holds "Version 0.8.6.".
  - `test_marketplace`:
    - `marketplace.json`'s `name` is `prdanvil`, its `owner.url` is `https://github.com/PRDAnvil`, and its one plugin's `source` is `./prd-toolkit`.
    - `plugin.json`'s `license` is `MIT`, its `homepage` is the URL above, and its `author.email` is `ivan@badgeretl.com`.
  - `test_license`: `LICENSE`, `prd-toolkit/LICENSE` and `.prd-toolkit/LICENSE` are byte-identical and start with `MIT License`.
  - `test_install_lines`: the README's install block holds the two install lines above.
  - `test_upgrade_note`: the 0.8.6 changelog entry holds `claude plugin uninstall prd-toolkit@ihistand`, `/plugin marketplace add PRDAnvil/prd-toolkit` and `/plugin install prd-toolkit@prdanvil`.
  - `test_no_old_marketplace_names`: no file under `prd-toolkit/`, outside `README.md` and `tests/`, holds `prd-toolkit@ihistand`, `cache/ihistand` or `ihistand/claude-plugins`. In `README.md`, the only such text is inside the 0.8.6 upgrade note and older changelog entries.
- [ ] **Step 3:** Run it. It fails on the old names.
- [ ] **Step 4: Edit the plugin to the Interfaces values.**
  - `plugin.json`: version, license, author email and url, homepage.
  - `marketplace.json`: version.
  - README: the install lines, the cache paths, "Version 0.8.6.", the License line, and the 0.8.6 changelog entry with the upgrade note:
    1. `claude plugin uninstall prd-toolkit@ihistand` at each scope it was installed at;
    2. `/plugin marketplace add PRDAnvil/prd-toolkit`;
    3. `/plugin install prd-toolkit@prdanvil`;
    4. `/reload-plugins`;
    5. in each repository with a vendored copy, re-run `install` from the new path at its next upgrade.
  - `test_release_0_5.py:34` and `test_final_review.py:14`: the new cache path.
  - `test_release_0_8_5.py::test_versions`: loosen its `0.8.5` pins to the form `test_release_0_8_4.py` uses (`re.fullmatch(r"\d+\.\d+\.\d+", …)`, and every copy equal to `plugin["version"]`). Only the newest release test pins the current version.
- [ ] **Step 5:** Run `prd_hooks.py vendor docs/prd/prd-toolkit` (VERSION and HOMEPAGE) and `prd_block.py docs/prd/prd-toolkit` (both READMEs).
- [ ] **Step 6:** Run the unit and integration levels; both pass. Run `uv run --script prd-toolkit/scripts/prd_hooks.py check docs/prd/prd-toolkit`; it prints nothing.
- [ ] **Step 7: Commit** `feat(prd-toolkit): 0.8.6, published from PRDAnvil/prd-toolkit`, with `Refs: none (no behaviour change)`.

### Task 7: Renumber the backlog, then open the release PR

**Files:**
- Modify: `docs/superpowers/specs/2026-11-03-prd-toolkit-0.8-umbrella.md` (its release table)
- Modify: `docs/superpowers/specs/2026-11-08-prd-toolkit-0.8.6-backlog.md` (its heading and opening line; the file keeps its name, so links stay)

- [ ] **Step 1: Renumber.**
  - The umbrella's rows become: 0.8.6, "the move to PRDAnvil/prd-toolkit"; 0.8.7, "the backlog"; 0.8.8, "conversion".
  - The backlog's heading reads 0.8.7. Its item 4 reads "the 0.8.7 changelog names the PRD version it reaches: 6.2.1 or later".
- [ ] **Step 2: Check CI parity.** Run `scripts/ci-local.sh main`; every job prints `pass`. Then run the Global Constraints' client-name scan over `git diff main --name-only`; it prints nothing.
- [ ] **Step 3: Commit** `docs: 0.8.6 is the move; the backlog becomes 0.8.7`, with `Refs: none (no behaviour change)`.
- [ ] **Step 4:** On the owner's word, push `release/0.8.6` and open the PR. CI's five jobs must pass. The owner merges it.

### Task 8: Switch the installs (owner's machine)

- [ ] **Step 1:** Run `claude plugin marketplace add PRDAnvil/prd-toolkit`, then `claude plugin install prd-toolkit@prdanvil --scope user`.
- [ ] **Step 2:** Run `claude plugin uninstall prd-toolkit@ihistand` at each scope `installed_plugins.json` lists for it, then `/reload-plugins`.
- [ ] **Step 3: Verify.** `claude plugin list` shows `prd-toolkit@prdanvil` at 0.8.6 and no `prd-toolkit@ihistand`. `ls ~/.claude/plugins/cache/prdanvil/prd-toolkit/0.8.6/LICENSE` exists.
- [ ] **Step 4:** On the owner's word, recreate issue #24 in `PRDAnvil/prd-toolkit` with its text and a link back. Close the old #24 with a link to the new one.

### Task 9: claude-plugins stops shipping prd-toolkit

**Files (in `claude-plugins`, branch `chore/prd-toolkit-moved`):**
- Delete:
  - `prd-toolkit/` except `prd-toolkit/README.md`
  - `docs/prd/`, `.prd-toolkit/`, `.github/workflows/prd-toolkit.yml`, `scripts/ci-local.sh`
  - the prd-toolkit specs and plans in `docs/superpowers/` (they live on in the new repository)
- Modify:
  - `.claude-plugin/marketplace.json`: drop the prd-toolkit entry
  - `README.md`: the prd-toolkit section becomes one paragraph with the new install lines
  - `CLAUDE.md`: drop prd-toolkit from the overview and delete the managed `<!-- prd-toolkit:start -->`…`end` block
  - `web/src/data/plugins.js` and `web/src/data/plugins.test.js`: drop the prd-toolkit entry and its two tests
- Replace: `prd-toolkit/README.md` with a stub: "prd-toolkit moved to https://github.com/PRDAnvil/prd-toolkit on 2026-11-10. Install it with `/plugin marketplace add PRDAnvil/prd-toolkit` and `/plugin install prd-toolkit@prdanvil`."

- [ ] **Step 1: Remove the hooks.** Run `uv run --script ~/.claude/plugins/cache/prdanvil/prd-toolkit/0.8.6/scripts/prd_hooks.py uninstall docs/prd/prd-toolkit` in `claude-plugins`, before the deletes. Afterwards `.git/hooks/` holds no `commit-msg` or `pre-commit` from prd-toolkit.
- [ ] **Step 2:** Make the changes listed above, with `git rm` for deleted tracked files.
- [ ] **Step 3: Verify.**
  - `npm test` in `web/` passes.
  - `claude plugin validate .` passes.
  - `git ls-files | /usr/bin/grep -c "^prd-toolkit/"` prints `1`.
- [ ] **Step 4:** Commit as `ihistand@rotoplas.com`. On the owner's word, push and open the PR; the owner merges it.
- [ ] **Step 5:** After the merge, `curl -s -o /dev/null -w "%{http_code}" https://github.com/ihistand/claude-plugins/tree/main/prd-toolkit` prints `200`.

### Task 10: Downstream and bookkeeping

Each item is its own commit or merge request, on the owner's word, in its repository's own identity and workflow.

- [ ] **The private wrapper plugin's marketplace** (GitLab): change the wrapper's README install lines for prd-toolkit, per that repository's CONTRIBUTING.md (version bump and evals as it requires).
- [ ] **`PRDAnvil/prdanvil_com`:** change the two install lines in `index.html` (lines 59 and 60), committed as `ivan@badgeretl.com`.
- [ ] **`PRDAnvil/prd_studio`:** in `docs/handoffs/2026-11-10-toolkit-path-in-tests.md`, change option 1's path to `~/.claude/plugins/cache/prdanvil/prd-toolkit/<version>`.
- [ ] **The two private repositories that vendor the toolkit:** nothing now. Their vendored HOMEPAGE resolves to the Task 9 stub, and their next toolkit upgrade (`install` from the new path) writes the new HOMEPAGE and the LICENSE.
- [ ] **Memory and Artifacts:**
  - Update the prd-toolkit memory note: the repo, the clone path, the marketplace and the identity.
  - Republish the PRD page from 6.2.1, updating https://claude.ai/artifact/C9hrn2o9xGgxrvPk6tuZ3k in place.
  - Refresh the design artifact's links and its "from main at" line.
